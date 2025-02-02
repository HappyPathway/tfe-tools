#!/usr/bin/env python3
import os
import json
import sys
import hcl
import subprocess
from tempfile import mkdtemp
import shutil
from github import Github
from github.GithubException import UnknownObjectException as gheUnknownObjectException
from tfe.core.organization import Organization
from tfe.core import session


class OperationException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

def str_to_bool(option, opt_str, value, parser):
    setattr(parser.values, option.dest, value.lower() in ('yes', 'true', 't', '1'))

def tfe_token(tfe_api, config):
    with open(sanitize_path(config), 'r') as fp:
        obj = hcl.load(fp)
    return obj.get('credentials').get(tfe_api).get('token')


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path

def run_command(command, cwd=None):
    """Run a shell command."""
    p = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd
    )
    out, err = p.communicate()
    if p.returncode > 0:
        raise OperationException(f"Command failed: {command}\nError: {err.decode()}")
    return out.decode().strip()

def clone_or_update(repo_clone_url, directory):
    # Extract the repository name from the URL
    # Assume the repository will be cloned into a directory named after the repository name in the current working directory
    repo_dir = os.path.join(os.getcwd(), directory)
    if os.path.isdir(repo_dir):
        print('Repository directory exists. Updating...')
        try:
            os.chdir(repo_dir)  # Change to the repo directory
            # Reset changes
            run_command("git reset --hard HEAD")
            # Try to checkout the main branch, fallback to master if main doesn't exist
            try:
                run_command("git checkout main")
            except OperationException:
                run_command("git checkout master")
            # Pull the latest changes
            run_command("git pull")
            print('Repository updated.')
        except OperationException as e:
            raise OperationException(f"Could not update repository: {e.msg}")
    else:
        print('Cloning repository...')
        try:
            run_command(f"git clone {repo_clone_url} '{repo_dir}'")
            print('Repository cloned.')
        except OperationException as e:
            raise OperationException(f"Could not clone repository: {e.msg}")

def tf_inspect(terraform_version):
    cmd = "tfenv use {0}".format(terraform_version)
    print("Executing {0}".format(cmd))
    p = subprocess.Popen(cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    os.system("terraform init -upgrade")
    with open("./.terraform/modules/modules.json", "r") as tf_mods:
        return json.loads(tf_mods.read())

def main(terraform_url, terraform_org, github_base, basedir, git_namespace, ws_name, remove_basedir, tf_upgrade):
    g = Github(
        os.environ.get("GITHUB_USER"),
        os.environ.get("GITHUB_TOKEN"),
        base_url="{0}/api/v3".format(github_base)
    )
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_reports_dir = os.path.join(script_dir, "./reports/workspaces")
    if not os.path.isdir(workspace_reports_dir):
        os.makedirs(workspace_reports_dir)
        
    tkn = tfe_token(terraform_url,
        os.path.join(
            os.environ.get("HOME"),
            ".terraformrc"
        )
    )
    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    ws= org.workspaces()

    for x in sorted(ws, key=lambda x: x.name):
        if ws_name and ws_name != x.name:
            continue
        print("scanning {0}".format(x.name))
        os.chdir(basedir)
        
        try:
            repo = g.get_repo(x.vcs_repo.get('identifier'))
            directory = x.vcs_repo.get('identifier').replace("{0}/".format(git_namespace), "")
        except AttributeError:
            continue
        try:
            clone_or_update(repo.ssh_url, directory)
        except OperationException:
            continue
        except gheUnknownObjectException:
            continue
        os.chdir(
            os.path.join(
                basedir,
                directory
            )
        )
        try:
            # "Key":"datacenter-infra-iad01.infra-puppet.mdb-provision",
            # "Source":"terraform.corp.clover.com/clover/mdb-provision/clover",
            # "Version":"0.3.7"
            mods = list()

            if tf_upgrade:
               print("Upgrading Terraform...")
               for mod in tf_inspect(x.terraform_version).get("Modules"):
                   mods.append(
                       dict(
                           key=mod.get('Key'),
                           source=mod.get('Source'),
                           version=mod.get('Version')
                       )
                   )
        except FileNotFoundError:
            continue
        if remove_basedir:
          shutil.rmtree(basedir)
        with open(os.path.join(workspace_reports_dir, f"{ws_name}_mods.json"), "w") as output:
            output.write(
                json.dumps(
                    mods,
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
    p.add_option("-r", dest='remove_basedir', type='string', action='callback', callback=str_to_bool, default=False)
    p.add_option("-u", dest='tf_upgrade', type='string', action='callback', callback=str_to_bool, default=True)
    p.add_option("--ws", dest="ws_name")
    opt, arg = p.parse_args()
    main(
        opt.terraform_url,
        opt.terraform_org,
        opt.github_base,
        opt.base_dir,
        opt.git_namespace,
        opt.ws_name,
        opt.remove_basedir,
        opt.tf_upgrade
    )
