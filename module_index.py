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

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

#############################
def modules():
    for tf_file_name in glob("./*.tf"):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('module'):
                    for module in hcl_data.get('module'):
                        yield module.get(list(module.keys())[0])
            except:
                continue

def resources():
    for tf_file_name in glob("./*.tf"):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('resource'):
                    for rsc in hcl_data.get('resource'):
                        yield rsc
            except:
                continue

##############################
def tfe_token(tfe_api, config):
    with open(sanitize_path(config), 'r') as fp:
        obj = hcl2.load(fp)
    return obj.get('credentials')[0].get(tfe_api).get('token')[0]


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
    

def markdown(metadata, outputfile):
    for module, meta in metadata.items():
        outputfile.write("h2. {0}\n".format(module))
        outputfile.write("h4. Description: \n{0}\n".format(metadata.get(module).get('description')))
        outputfile.write("h4. URL: \n{0}\n".format(metadata.get(module).get('https_url')))
        outputfile.write("h4. SSH: \n{0}\n".format(metadata.get(module).get('ssh_url')))
        outputfile.write("h4. Terraform Enterprise: \n{0}\n".format(metadata.get(module).get('tf_link')))
        if meta.get("embedded_modules"):
            outputfile.write("h4. Embedded Modules\n")
            for mod in meta.get("embedded_modules", []):
                outputfile.write("[{0}]\n".format(mod))
        if meta.get("resources"):
            outputfile.write("h4. Embedded Resources\n")
            outputfile.write("{code:theme=Midnight|language=bash}\n")
            for rsc in meta.get("resources", []):
                outputfile.write("{0}\n".format(rsc))
            outputfile.write("{code}\n")
        outputfile.write("\n\n")




def main(github_base, terraform_base, terraform_url, base_dir, output):
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
    repo_meta = dict()
    os.chdir(base_dir)

    for mod in sorted(tf_mods, key=lambda x: "terraform-{0}-{1}".format(x.get('provider'), x.get('name'))):
        os.chdir(base_dir)
        repo_name = mod.get('source').replace(
            "{0}/".format(github_base), 
            ''
        )
        mod_name = "terraform-{0}-{1}".format(mod.get('provider'), mod.get('name'))
        try:
            repo = g.get_repo(repo_name)
            tf_link = "{0}/app/{1}/modules/show/{2}".format(terraform_base, mod.get('namespace'), mod.get('id'))
            repo_meta[mod_name] = dict(
                ssh_url=repo.ssh_url,
                https_url=repo.html_url,
                description=repo.description,
                tf_link=tf_link,
                embedded_modules=list(),
                resources=list()
            )
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
            for module in modules():
                # terraform.corp.clover.com/clover/service-ha/google
                # print(module, module.get('source')[0])
                if module.get('source'):
                    mod_src = list(module.get('source'))[0]
                    mod_src_parts = mod_src.split('/') # clover/singleinstance/google
                    namespace = mod_src_parts[1]
                    source = "/".join(mod_src_parts[-3:])
                    embedded_tf_link = "{0}/app/{1}/modules/show/{2}".format(terraform_base, namespace, source)
                    # print(embedded_tf_link)
                    if embedded_tf_link not in repo_meta[mod_name]['embedded_modules']:
                        repo_meta[mod_name]['embedded_modules'].append(embedded_tf_link)

            for rsc in resources():
                if list(rsc.keys())[0] not in repo_meta[mod_name]['resources']:
                    repo_meta[mod_name]['resources'].append(list(rsc.keys())[0])

        except UnknownObjectException:
            pass

    shutil.rmtree(base_dir)
    with open(sanitize_path(output), 'w') as outputfile:
        markdown(repo_meta, outputfile)

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-g", default="https://github.corp.clover.com", dest="github_base")
    p.add_option("-t", default="https://terraform.corp.clover.com", dest="terraform_base")
    p.add_option("-u", default="terraform.corp.clover.com", dest="terraform_url")
    p.add_option("-b", dest='base_dir', default=mkdtemp(prefix="/tmp/"))
    p.add_option("-o", dest="output", default=os.path.join(os.environ.get("PWD"), "modules.md"))
    opt, arg = p.parse_args()
    main(opt.github_base, opt.terraform_base, opt.terraform_url, opt.base_dir, opt.output)