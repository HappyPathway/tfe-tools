#!/usr/bin/env python3
import os
import hcl2
import subprocess
import sys
import shutil
import json
from glob import glob
from tempfile import mkdtemp
from tfe.core.organization import Organization
from tfe.core import session
from tfe.core.registry_module import RegistryModule
from github import Github
from collections import defaultdict
from github.GithubException import UnknownObjectException
from functools import partial
import re
from helpers import tfe_token
import sys
import shlex

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

#############################
def dependencies(mod_name):
    module_source_regex = re.compile('source\s*=\s*"terraform.corp.clover.com/clover/(?P<module>[^"]*)"')
    dependencies = list()
    for tf_file_name in glob("*.tf"):
        with open(tf_file_name, 'r') as tf_file:
            for line in tf_file.read().splitlines():
                m = module_source_regex.search(line)
                if m:
                    d = m.groupdict().get('module')
                    url_parts = d.split('/')
                    dependencies.append("terraform-{0}-{1}".format(url_parts[1], url_parts[0]))
    return dependencies

# ##############################
# def tfe_token(tfe_api, config):
#     with open(sanitize_path(config), 'r') as fp:
#         obj = hcl2.load(fp)
#     return obj.get('credentials')[0].get(tfe_api).get('token')


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


def clone(repo_clone_url):
    p = subprocess.Popen(
        "git clone {0}".format(repo_clone_url),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    if p.returncode > 0:
        sys.stderr.write(str(err.decode('utf-8')))
        raise GitException("Could not clone {0}".format(repo_clone_url))
    
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
    

def main(github_base, terraform_base, terraform_url, base_dir, callback=None):
    callbacks = dict()
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
    mod_versions = defaultdict(set)
    no_deps = list()
    # repo_tags = defaultdict(list)
    os.chdir(base_dir)

    try:
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
                    clone(repo.ssh_url)
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
                # for tag in repo.get_tags():
                #     # repo_tags[repo_name].append(tag)
                #     pull_commit(tag.commit)
                if callback:
                    p = subprocess.Popen(callback, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out, err = p.communicate()
                    callbacks[mod_name] = dict(
                        out=str(out.decode('utf-8')),
                        err=str(err.decode('utf-8'))
                    )
                    print(
                        json.dumps(
                            dict(
                                module=mod_name, 
                                out=str(out.decode('utf-8')).strip(),
                                err=str(err.decode('utf-8').strip())
                            ),
                            separators=(',', ':'),
                            indent=4,
                            sort_keys=True
                        )
                    )
                dep = dependencies(mod_name)
                if len(dep):
                    # mod_versions[mod_name]["source"] = "{0}/{1}/{2}/{3}".format(
                    #     terraform_url, 
                    #     mod.get('namespace'), 
                    #     mod.get('name'), 
                    #     mod.get('provider')
                    # )
                    mod_versions[mod_name] = dep
                else:
                    no_deps.append(mod_name)
                    print(f"\t {mod_name} does not have any module dependencies")
            except UnknownObjectException:
                print(repo_name)
    except KeyboardInterrupt:
        print(json.dumps(
            callbacks,
            separators=(',', ':'),
            indent=4,
            sort_keys=True
        ))
        sys.exit(1)
        
    for m in mod_versions:
        deps = mod_versions.get(m)
        deps = list(set(deps))
        mod_versions[m] = deps
    shutil.rmtree(base_dir)

    with open(os.path.join(os.environ.get("PWD"), "./tf_mods_callbacks.json"), "w") as output:
        output.write(json.dumps(
            callbacks,
            separators=(',', ':'),
            indent=4,
            sort_keys=True
        ))
        
    with open(os.path.join(os.path.dirname(__file__), "./reports/tf_mods.json"), "w") as output:
        output.write(
            json.dumps(
                mod_versions,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )
    
    with open(os.path.join(os.path.dirname(__file__), "./reports/tf_mods_no_deps.json"), "w") as output:
        output.write(
            json.dumps(
                no_deps,
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
    p.add_option("-b", dest='base_dir', default=mkdtemp(prefix="/tmp/"))
    p.add_option("--callback", default=None)
    opt, arg = p.parse_args()
    main(opt.github_base, opt.terraform_base, opt.terraform_url, opt.base_dir, opt.callback)
