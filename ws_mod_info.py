#!/usr/bin/env python3
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
from collections import defaultdict
from urllib.parse import urlencode, quote_plus
from requests import Session

ws_modules = defaultdict(list)
workspace_projects = dict()

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


class TFEException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


def tfe_token(tfe_api, config):
    if sanitize_path(config):
        with open(sanitize_path(config), 'r') as fp:
            obj = hcl2.load(fp)
        return obj.get('credentials')[0].get(tfe_api).get('token')
    elif sanitize_path("${HOME}/.terraform.d/credentials.tfrc.json"):
        with open(sanitize_path("${HOME}/.terraform.d/credentials.tfrc.json"), 'r') as fp:
            d = json.loads(fp.read())
            return d.get('credentials').get(tfe_api).get('token')
    else:
        raise TFEException("Could not find credentials file")


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return path
    else:
        return None
 
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


def get_state(tkn, workspace_name, terraform_url="terraform.corp.clover.com", terraform_org="clover"):
    tfe_session = Session()
    tfe_session.headers = {
        "Authorization": "Bearer {0}".format(tkn), 
        "Content-Type": "application/vnd.api+json"
    }
    url = "https://{0}/api/v2/state-versions".format(terraform_url)
    url_params = {
        "filter[organization][name]": terraform_org,
        "filter[workspace][name]": workspace_name
    }
    resp = tfe_session.get(url, params=urlencode(url_params, quote_via=quote_plus))
    data = resp.json()
    if not len(data.get('data')):
        return dict()
    last_state = data.get('data')[0]
    state_url = last_state.get('attributes').get('hosted-state-download-url')
    state_resp = tfe_session.get(state_url)
    state_data = state_resp.json()
    return state_data

def dependencies(tkn, ws_name):
    state = get_state(tkn, ws_name)
    found_modules = set()
    projects = get_projects(state)
    workspace_projects[ws_name] = projects

    for rsc in state.get('resources', []):
        if rsc.get('module'): 
            found_modules.add(rsc.get('module').split('.')[1])
    
    if not len(found_modules):
        return 
    
    for tf_file_name in glob("*.tf"):
        with open(tf_file_name, 'r') as tf_file:
            try:
                data = hcl2.loads(tf_file.read())
            except:
                print(f"Failed: {ws_name}:{tf_file_name}")
                return 
            
            if 'module' in data:
                for hcl_module in data.get('module'):
                    for module in found_modules:
                        if hcl_module.get(module):
                            ws_modules[ws_name].append(
                                dict(
                                    source= hcl_module.get(module).get('source'),
                                    module = module
                                )
                            )

def get_projects(state):
    workspace_projects = set()
    for rsc in state.get('resources', []):
        for instance in rsc.get('instances', []):
            if instance.get('attributes').get('project'):
                project = instance.get('attributes').get('project')
                workspace_projects.add(project)
    return list(workspace_projects)
    

def main(terraform_url, terraform_org, github_base, basedir, git_namespace):
    g = Github(
        os.environ.get("GITHUB_USER"), 
        os.environ.get("GITHUB_TOKEN"), 
        base_url="{0}/api/v3".format(github_base)
    )

    try:
        tkn = tfe_token(terraform_url, 
            os.path.join(
                os.environ.get("HOME"), 
                ".terraformrc"
            )
        )
    except TFEException:
        sys.stderr.write("Could not find credentials file. exiting.\n")
        sys.exit(1)

    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    print("Retrieving workspaces...")
    ws = org.workspaces()
    mods = dict()
    for x in sorted(ws, key=lambda ws: ws.name):
        print(x.name)
        os.chdir(basedir)
        try:
            repo = g.get_repo(x.vcs_repo.get('identifier'))
        except AttributeError:
            continue
        except gheUnknownObjectException:
            continue
        try:
            clone(repo.ssh_url)
        except GitException:
            continue
        except gheUnknownObjectException:
            continue
        os.chdir(
            os.path.join(
                basedir,
                x.vcs_repo.get('identifier').replace("{0}/".format(git_namespace), "")
            )
        )
        try:
            dependencies(tkn, x.name)
        except FileNotFoundError:
            continue
    shutil.rmtree(basedir)
    with open(os.path.join(os.path.dirname(__file__), "./reports/ws_mod_info.json"), "w") as output:
        output.write(
            json.dumps(
                ws_modules,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )
    with open(os.path.join(os.path.dirname(__file__), "./reports/ws_projects.json"), "w") as output:
        output.write(
            json.dumps(
                workspace_projects,
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
    