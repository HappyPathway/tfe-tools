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
from tfe import Workspace as TFEWorkspace
import re
from collections import defaultdict
from helpers import tfe_token

class TFEException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


def main(terraform_url, terraform_org):
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
    ws = org.workspaces()
    workspace_variables = defaultdict(list)
    for x in sorted(ws, key=lambda ws: ws.name):
        tfe_ws = TFEWorkspace(api="https://{0}".format(terraform_url), atlas_token=tkn, organization=terraform_org, workspace_name=x.name)
        for variable in tfe_ws.existing_variables:
            workspace_variables[x.name].append(variable.get('key'))
    
    with open(os.path.join(os.path.dirname(__file__), "./reports/ws_variables.json"), "w") as output:
        output.write(
           json.dumps(
               workspace_variables,
                separators=(',' ':'),
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
    