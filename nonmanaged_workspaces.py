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
from tfe.core import workspace
from tfe.core.organization import Organization
from tfe.core.workspace import Workspace
from tfe.core import session
from requests import Session
from urllib.parse import urlencode, quote_plus
from pathlib import Path
import helpers
import re

def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path
 
def pprint(j_obj, indention=4, sort_keys=True):
     print(
         json.dumps(
             j_obj,
             separators=(',', ':'),
             indent=indention,
             sort_keys=sort_keys
         )
     )

def managed_workspaces():
    with open("./reports/managed_workspaces.json", "r") as ws_file:
        return json.loads(ws_file.read())
    
def main(terraform_url, terraform_org, output, workspace_name=False):
    tkn = helpers.tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )
    tfe_session = Session()
    tfe_session.headers = {
        "Authorization": "Bearer {0}".format(tkn), 
        "Content-Type": "application/vnd.api+json"
    }
    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    workspaces = list()
    print("Retrieving Complete List of Workspaces...")
    ws = org.workspaces()
    _managed_ws = managed_workspaces()
    for ws in sorted(ws, key=lambda ws: ws.name):
        try:
            print(ws.name)
            if ws not in _managed_ws:
                workspaces.append(ws.name)
        except:
            pass
    
    with open(output, 'w') as output_file:
        output_file.write(
            json.dumps(
                workspaces,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )
# with open(, "w") as output:


if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("--org", dest="terraform_org", default="clover")
    p.add_option("-o", dest='output', default=os.path.join(os.path.dirname(__file__), "./reports/nonmanaged-workspaces.json"))
    p.add_option("-w", dest="workspace", default=None)
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.output, opt.workspace)
    