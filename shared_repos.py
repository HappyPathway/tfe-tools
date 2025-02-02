#!/usr/bin/env python3
import os
import json
import sys
from typing import DefaultDict
import hcl2
from glob import glob
import subprocess
from tempfile import mkdtemp
import shutil
from github import Github
from github.GithubException import UnknownObjectException as gheUnknownObjectException
from tfe.core.organization import Organization
from tfe.core import session
from helpers import tfe_token

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


# def tfe_token(tfe_api, config):
#     with open(sanitize_path(config), 'r') as fp:
#         obj = hcl2.load(fp)
#     return obj.get('credentials')[0].get(tfe_api).get('token')[0]


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path
 


def main(terraform_url, terraform_org, github_base, basedir, git_namespace):
    g = Github(
        os.environ.get("GITHUB_USER"), 
        os.environ.get("GITHUB_TOKEN"), 
        base_url="{0}/api/v3".format(github_base)
    )

    tkn = tfe_token(terraform_url, os.path.join(os.environ.get('HOME'), '.terraformrc'))
    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    ws = org.workspaces()
    repos = DefaultDict(list)
    for x in sorted(ws, key=lambda ws: ws.name):
        print(x.name)
        os.chdir(basedir)
        try:
            repo = g.get_repo(x.vcs_repo.get('identifier'))
            repos[repo.name].append(x.name)
        except AttributeError:
            continue
        except gheUnknownObjectException:
            continue
       
    shared_repos = dict()
    for repo in repos:
        print(repo)
        if len(repos.get(repo)) > 1:
            shared_repos[repo] = repos.get(repo)

    with open(os.path.join(os.path.dirname(__file__), "./reports/shared_repos.json"), "w") as output:
        output.write(
            json.dumps(
                shared_repos,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("-o", dest="terraform_org", default="clover")
    p.add_option("-g", dest="github_base",   default="https://github.corp.clover.com")
    p.add_option("-n", dest="git_namespace", default="clover")
    p.add_option("-b", dest='base_dir',      default=mkdtemp(prefix="/tmp/"))
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.github_base, opt.base_dir, opt.git_namespace)
    