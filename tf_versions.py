#!/usr/bin/env python3
from ensurepip import version
import os
import json
from posixpath import sep
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
from helpers import tfe_token

def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path
 

def main(terraform_url, terraform_org):
    tkn = tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )
    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    ws = org.workspaces()
    version_dict = defaultdict(list)
    for x in sorted(ws, key=lambda ws: ws.name):
        version_dict[x.terraform_version].append(x.name)
    with open(os.path.join(os.getcwd(), "./reports/tf_versions.json"), 'w') as tf_version:
        tf_version.write(
            json.dumps(
                version_dict,
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
    main(opt.terraform_url, opt.terraform_org)
    