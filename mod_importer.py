#!/usr/bin/env python3
import os
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
from jinja2 import Template
import json

MOD_TEMPLATE = '''
module "{{ mod_rsc_name }}" {
  source                  = "terraform.corp.clover.com/clover/module/tfe"
  name                    = "{{ mod_name }}"
  github_codeowners_team  = "nit"
  github_repo_description = "{{ mod_description }}"
  github_repo_topics = [
    "terraform",
    "github-repos",
    "module"
  ]
  github_org_teams = local.github_org_teams
}
'''
IMPORT_TEMPLATE = '''terraform import module.{{ mod_rsc_name }}.tfe_registry_module.registry-module {{ mod.id }}
terraform import module.{{ mod_rsc_name }}.github_repository.repo {{ repo_name }}
terraform import module.{{ mod_rsc_name }}.github_branch_protection.main {{ repo_name }}:main
terraform import module.{{ mod_rsc_name }}.github_branch_default.default_main_branch {{ repo_name }}
terraform import module.{{ mod_rsc_name }}.github_repository_file.codeowners {{ repo_name }}/CODEOWNERS
'''

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

def main(github_base, terraform_base, terraform_url, terraform_org, output):
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
    mod_template = Template(MOD_TEMPLATE)
    script_template = Template(IMPORT_TEMPLATE)
    session.TFESession(terraform_base, tkn)
    Organization(terraform_org)
    rm = RegistryModule()
    tf_mods = modlist(rm, [], rm.list_url)
    with open(output, 'w') as output:
        for mod in sorted(tf_mods, key=lambda x: "terraform-{0}-{1}".format(x.get('provider'), x.get('name'))):
            repo_name = mod.get('source').replace(
                "{0}/".format(github_base), 
                ''
            )
            mod_name = "terraform-{0}-{1}".format(mod.get('provider'), mod.get('name'))
            print("# Scanning {0}".format(mod_name))
            # print(
            #     json.dumps(
            #         mod,
            #         separators=(',', ':'),
            #         indent=4,
            #         sort_keys=True
            #     )
            # )
            repo = g.get_repo(repo_name)
            data =  mod_template.render(
                mod_description = repo.description,
                mod_rsc_name    = "_".join(mod.get('name').split("-")),
                mod_name        = mod_name,
                org             = terraform_org,
                mod             = mod,
                repo_name       = repo.name
            )
            print(script_template.render(
                mod_description = repo.description,
                mod_rsc_name    = "_".join(mod.get('name').split("-")),
                mod_name        = mod_name,
                org             = terraform_org,
                mod             = mod,
                repo_name       = repo.name
            ))
            output.write(data)

            
    

        

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-g", default="https://github.corp.clover.com", dest="github_base")
    p.add_option("-t", default="https://terraform.corp.clover.com", dest="terraform_base")
    p.add_option("-u", default="terraform.corp.clover.com", dest="terraform_url")
    p.add_option("-o", dest="org", default="clover")
    p.add_option("-b", dest='output', default=os.path.join(os.getcwd(), "modules.tf"))
    opt, arg = p.parse_args()
    main(opt.github_base, opt.terraform_base, opt.terraform_url, opt.org, opt.output)