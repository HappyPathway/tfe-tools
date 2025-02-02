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

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

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

def main(github_base, terraform_base, terraform_url, base_dir, resource_type):
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
    mod_resources = set()
    # repo_tags = defaultdict(list)
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
            try:
                clone(repo.ssh_url)
            except GitException:
                sys.stderr.write(
                    GitException.msg
                )
                print(f"Couln't clone {repo_name}")
            os.chdir(
                os.path.join(
                    base_dir,
                    mod_name
                )
            )
            for x in glob("*.tf"):
                with open(x) as tf_file:
                    try:
                        tf_data = hcl2.loads(tf_file.read())
                    except:
                        print(f"Coulndt parse {x} in {repo_name}")
                        continue
                    
                    if 'resource' not in tf_data.keys():
                        continue
                    for resource in tf_data.get('resource'):
                        if resource_type in resource.keys():
                            for k, v in resource.items(): 
                                mod_resources.add(mod_name)
                    
        except UnknownObjectException:
            print(repo_name)
 
    print(
        json.dumps(
            sorted(list(mod_resources)),
            separators=(',', ':'),
            indent=4,
            sort_keys=True
        )
    )

        

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-g", default="https://github.corp.clover.com", dest="github_base")
    p.add_option("--tfe", default="https://terraform.corp.clover.com", dest="terraform_base")
    p.add_option("-u", default="terraform.corp.clover.com", dest="terraform_url")
    p.add_option("-b", dest='base_dir', default=mkdtemp(prefix="/tmp/"))
    p.add_option("-t", dest="resource_type")
    opt, arg = p.parse_args()
    main(opt.github_base, opt.terraform_base, opt.terraform_url, opt.base_dir, opt.resource_type)