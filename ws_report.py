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
from python_terraform import Terraform

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

def find_terraform_workspace(ws_name):
    # d.get('terraform')[0].get('backend')[0].get('remote').get('workspaces')[0].get('prefix')[0]
    workspace_name = None
    for tf_config_file in glob("*.tf"):
        try:
            with open(tf_config_file) as config:
                d = hcl2.loads(config.read())
        except:
            continue
        tf = d.get('terraform')
        if tf:
            backend = d.get('terraform')[0].get('backend')
            if backend:
                remote = backend[0].get('remote').get('remote')
                if remote:
                    workspace_config = remote.get('workspaces')
                    if workspace_config:
                        if 'prefix' in workspace_config[0].keys():
                            prefix = workspace_config[0].get('prefix')[0]
                            workspace_name = ws_name.replace(prefix, '')
                            break
                        elif 'name' in workspace_config[0].keys():
                            workspace_name = workspace_config[0].get('name')
                            break
    return workspace_name

def init_and_pull_state(ws):
    subprocess.call(
        "/usr/local/bin/tfenv install {0}".format(ws.terraform_version), 
        shell=True,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )

    subprocess.call(
        "/usr/local/bin/tfenv use {0}".format(ws.terraform_version), 
        shell=True,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    
    try:
        ws_name = find_terraform_workspace(ws.name)
        if ws_name:
            subprocess.call("terraform workspace select {0}".format(ws_name), 
                shell=True,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
        os.system("terraform init")

    except FileExistsError:
        return

    p = subprocess.Popen("terraform state pull", 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    if p.returncode > 0:
        print(err.decode('utf-8'))
    try:
        j_out = json.loads(out.decode('utf-8'))
    except json.decoder.JSONDecodeError:
        print("Could not pull state from {0}".format(ws.name))
        return dict()
    return j_out


def main(terraform_url, terraform_org, github_base, basedir, git_namespace):
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
    org = Organization(terraform_org)
    ws = org.workspaces()
    ws_report = list()
    for ws in sorted(ws, key=lambda ws: ws.name):
        os.chdir(basedir)
        try:
            repo = g.get_repo(ws.vcs_repo.get('identifier'))
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
                ws.vcs_repo.get('identifier').replace("{0}/".format(git_namespace), "")
            )
        )
        try:
            rscs = init_and_pull_state(ws).get('resources')
            if rscs:
                ws_report.append(dict(workspace=ws.name, resources=len(rscs)))
        except FileNotFoundError:
            continue
    shutil.rmtree(basedir)
    with open(os.path.join(os.environ.get("PWD"), "ws_rsc_count.json"), "w") as output:
        output.write(
            json.dumps(
                ws_report,
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
    