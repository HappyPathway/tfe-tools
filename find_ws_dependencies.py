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
from tfe.core.workspace import Workspace
from tfe.core import session
import re
from tfe_tools.common import tfe_token, mod_dependencies, sanitize_path, get_requests_session

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


class TFEException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


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


def dependencies(ws_name):
    module_source_regex = re.compile('source\s*=\s*"terraform.example.com/example/(?P<module>[^"]*)"')
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


def main(terraform_url, terraform_org, github_base, basedir, git_namespace, workspace):
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
    ws = Workspace()
    ws.organization = org
    ws.name = workspace
    ws.get()
    os.chdir(basedir)
    repo = g.get_repo(ws.vcs_repo.get('identifier'))
    clone(repo.ssh_url)
    os.chdir(
        os.path.join(
            basedir,
            ws.vcs_repo.get('identifier').replace("{0}/".format(git_namespace), "")
        )
    )
    dependencies = mod_dependencies(ws.name, config=True)
    shutil.rmtree(basedir)
    print(json.dumps(dependencies, sort_keys=True, indent=4, separators=(',', ':')))

if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.example.com")
    p.add_option("-o", dest="terraform_org", default="example")
    p.add_option("-g", dest="github_base",   default="https://github.example.com")
    p.add_option("-n", dest="git_namespace", default="example")
    p.add_option("-b", dest='base_dir',      default=mkdtemp(prefix="/tmp/"))
    p.add_option("-w", dest="workspace")
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.github_base, opt.base_dir, opt.git_namespace, opt.workspace)
