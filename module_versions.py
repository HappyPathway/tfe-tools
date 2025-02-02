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
import semantic_version
import helpers

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

##############################
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
    

def main(terraform_base, terraform_url):
    # tkn = tfe_token(terraform_url, 
    #     "{0}/.terraformrc".format(
    #         os.environ.get("HOME")
    #     )
    # )
    tkn = helpers.tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )

    session.TFESession(terraform_base, tkn)
    Organization("clover")
    rm = RegistryModule()
    tf_mods = modlist(rm, [], rm.list_url)
    mod_versions = dict()
    '''
    module "service-ha" {
  source  = "terraform.corp.clover.com/clover/service-ha/google"
  version = "7.0.2"
  # insert required variables here
}
    '''
    for mod in sorted(tf_mods, key=lambda x: "terraform-{0}-{1}".format(x.get('provider'), x.get('name'))):
        mod_name = "terraform-{0}-{1}".format(mod.get('provider'), mod.get('name'))
        print(mod_name)
        mod_versions[mod_name] = dict(
            latest_version=mod.pop('version'),
            source = "{0}/{1}/{2}/{3}".format(
                terraform_url, 
                mod.pop('namespace'),
                mod.pop('name'),
                mod.pop('provider')
            ),
            attributes=mod
        )

    with open(os.path.join(os.path.dirname(__file__), "./reports/mod_versions.json"), "w") as output:
        output.write(
            json.dumps(
                mod_versions,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", default="https://terraform.corp.clover.com", dest="terraform_base")
    p.add_option("-u", default="terraform.corp.clover.com", dest="terraform_url")
    opt, arg = p.parse_args()
    main(opt.terraform_base, opt.terraform_url)