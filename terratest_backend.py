#!/usr/bin/env python3
import os
import hcl2
import subprocess
import sys
import json
from glob import glob
from tempfile import mkdtemp
from tfe.core.organization import Organization
from tfe.core import session
from tfe.core.registry_module import RegistryModule
from github import Github
from github.GithubException import UnknownObjectException
from jinja2 import Template
import git
from collections import defaultdict
import shutil

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

#############################
def example_dirs():
    examples = list()
    for _dir in glob("./examples/*"):
        if os.path.isdir(_dir):
            examples.append(_dir)
    return examples

##############################
def tfe_token(tfe_api, config):
    with open(sanitize_path(config), 'r') as fp:
        obj = hcl2.load(fp)
    return obj.get('credentials')[0].get(tfe_api).get('token')


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path


def modlist(rm, mods, list_url):
    rm_list = rm.list(list_url)
    for mod in rm_list.get('modules'):
        mods.append(mod)
    if rm_list.get('meta').get('next_url'):
        url_prefix = rm.list_url
        url = "{0}?offset={1}".format(url_prefix, rm_list.get('meta').get('next_offset'))
        modlist(rm, mods, url)
    return mods


def clone(repo, base_dir):
    if os.path.isdir(os.path.join(base_dir, repo.name)):
        shutil.rmtree(os.path.join(base_dir, repo.name))
        os.makedirs(os.path.join(base_dir, repo.name))
        
    git.Repo.clone_from(
        repo.ssh_url,
        os.path.join(base_dir, repo.name), 
        branch=repo.default_branch
    )
    # p = subprocess.Popen(
    #     "git clone {0}".format(repo_clone_url),
    #     shell=True,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE
    # )
    # out, err = p.communicate()
    # if p.returncode > 0:
    #     raise GitException("Could not clone {0}".format(repo_clone_url))
    
def pull_commit(commit):
    p = subprocess.Popen(
        "git checkout {0}".format(commit.sha),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    if p.returncode > 0:
        raise GitException("Could not pull {0}.\n\t{1}".format(commit.sha, err.decode("utf-8")))
    
def get_template():
    with open("./templates/terratest_backend.j2") as tpl_file:
        t = Template(tpl_file.read())
    return t


def main(github_base, terraform_base, terraform_url, base_dir, bucket_name):
    g = Github(
        os.environ.get("GITHUB_USER"), 
        os.environ.get("GITHUB_TOKEN"), 
        base_url="{0}/api/v3".format(github_base)
    )

    tkn = tfe_token(terraform_url, 
        "{0}/.terraformrc".format(
            os.environ.get("HOME")
        )
    )

    session.TFESession(terraform_base, tkn)
    Organization("clover")
    rm = RegistryModule()
    tf_mods = modlist(rm, [], rm.list_url)
    mod_examples = defaultdict(list)
    tpl = get_template()
    # repo_tags = defaultdict(list)
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)

    os.chdir(base_dir)

    for mod in sorted(tf_mods, key=lambda x: "terraform-{0}-{1}".format(x.get('provider'), x.get('name'))):
        os.chdir(base_dir)
        repo_name = mod.get('source').replace(
            "{0}/".format(github_base), 
            ''
        )
        mod_name = "terraform-{0}-{1}".format(mod.get('provider'), mod.get('name'))
        print("Scanning {0}".format(mod_name))
        try:
            repo = g.get_repo(repo_name)
            try:
                clone(repo, base_dir)
            except GitException:
                sys.stderr.write(
                    GitException.msg
                )
                continue
            os.chdir(
                os.path.join(
                    base_dir,
                    mod_name
                )
            )
            examples = example_dirs()
            if len(examples):
                for example in examples:
                    template = tpl.render(
                        bucket_name=bucket_name,
                        mod_name=mod_name,
                        test_name=os.path.basename(example)
                    )
                    with open(os.path.join(example, "backend.tf"), 'w') as backend_tf:
                        backend_tf.write(template)
                    mod_examples[mod_name].append(os.path.basename(example))

        except UnknownObjectException:
            print(repo_name)
        
    with open(os.path.join(os.path.dirname(__file__), "./reports/tf_mod_tests.json"), "w") as output:
        output.write(
            json.dumps(
                mod_examples,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )
    

        

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-g", default="https://github.corp.clover.com", dest="github_base")
    p.add_option("-t", default="https://terraform.corp.clover.com", dest="terraform_base")
    p.add_option("-u", default="terraform.corp.clover.com", dest="terraform_url")
    p.add_option("-b", dest='base_dir', default=os.path.join(os.getcwd(), "terratest_repos"))
    p.add_option("--bucket", default="clover-terratest-state")
    opt, arg = p.parse_args()
    main(opt.github_base, opt.terraform_base, opt.terraform_url, opt.base_dir, opt.bucket)