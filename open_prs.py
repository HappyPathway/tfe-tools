#!/usr/bin/env python3
from collections import defaultdict
import os
import json
import sys
import hcl2
from glob import glob
import subprocess
from tempfile import mkdtemp
import shutil
from github import Github
from github.GithubException import UnknownObjectException as gheUnknownObjectException
from tfe.core.organization import Organization
from tfe.core import session
from tfe.core.registry_module import RegistryModule
from configparser import RawConfigParser
import urllib

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


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


def get_mod_repos(g, github_base):
    rm = RegistryModule()
    tf_mods = modlist(rm, [], rm.list_url)
    for mod in sorted(tf_mods, key=lambda x: "terraform-{0}-{1}".format(x.get('provider'), x.get('name'))):
        repo_name = mod.get('source').replace(
            "{0}/".format(github_base), 
            ''
        )
        mod_name = "terraform-{0}-{1}".format(mod.get('provider'), mod.get('name'))
        yield g.get_repo(repo_name)

def get_ws_repos(g, session, terraform_org):
    org = Organization(terraform_org)
    ws = org.workspaces()
    for x in sorted(ws, key=lambda ws: ws.name):
        if x.vcs_repo:
            yield g.get_repo(x.vcs_repo.get('identifier'))


def get_prs(repo, github_user):
    pull_requests = defaultdict(list)
    for pull in repo.get_pulls():
        if not pull.merged and pull.user.login == github_user:
            pr = dict(
                title=pull.title,
                url=pull.html_url
            )
            pr['reviews'] = list()
            for review in pull.get_reviews():
                pr['reviews'].append(dict(approver=review.user.login, state=review.state))
            pull_requests[repo.name].append(pr)
    return pull_requests
    

def main(terraform_url, terraform_org, github_base, github_user, localonly=False):
    g = Github(
        os.environ.get("GITHUB_USER"), 
        os.environ.get("GITHUB_TOKEN"), 
        base_url="{0}/api/v3".format(github_base)
    )

    tkn = tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )
    
    session.TFESession("https://{0}".format(terraform_url), tkn)
    pull_requests = defaultdict(list)
    if not localonly:
        for repo in get_ws_repos(g, session, terraform_org):
            prs = get_prs(repo, github_user)
            if prs:
                pull_requests['workspace'].append(prs)


        for repo in get_mod_repos(g, github_base):
            prs = get_prs(repo, github_user)
            if prs:
                pull_requests['modules'].append(prs)
    else:
        rcp = RawConfigParser()
        rcp.read_file(open(os.path.join(os.getcwd(), '.git/config')))
        for sec in rcp.sections():
            if 'remote' in sec:
                url = rcp.get(sec, 'url')
                if urllib.parse.urlparse(github_base).hostname in url:
                    org = url.split('/')[-2].split(':')[-1]
                    repo_name = url.split('/')[-1].rstrip('.git')
                    repo = g.get_repo(os.path.join(org, repo_name))
                    pull_requests = get_prs(repo, github_user)

    if len(pull_requests):
        print(
            json.dumps(
                pull_requests,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )
    else:
        print("Good job! No Open/Lingering Pull Requests in any repo")
   
  
   


if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("-o", dest="terraform_org", default="clover")
    p.add_option("-g", dest="github_base",   default="https://github.corp.clover.com")
    p.add_option("-u", dest="user", default=os.environ.get("GITHUB_LOGIN"))
    p.add_option("-l", dest="localonly", action="store_true", default=False)
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.github_base, opt.user, opt.localonly)
    