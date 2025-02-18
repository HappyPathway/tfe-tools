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
import re
from collections import defaultdict
from helpers import tfe_token

class TFEException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

class Workspace:
    def __init__(self, workspace_name, organization):
        self.workspace_name = workspace_name
        self.organization = organization
        self.session = self._create_session()

    def _create_session(self):
        token = tfe_token("terraform.corp.clover.com", os.path.join(os.environ.get("HOME"), ".terraformrc"))
        session = Session()
        session.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json"
        }
        return session

    def get_state(self):
        url = f"https://terraform.corp.clover.com/api/v2/state-versions"
        url_params = {
            "filter[organization][name]": self.organization,
            "filter[workspace][name]": self.workspace_name
        }
        resp = self.session.get(url, params=urlencode(url_params, quote_via=quote_plus))
        data = resp.json()
        try:
            last_state = data.get('data')[0]
        except IndexError:
            return None
        state_url = last_state.get('attributes').get('hosted-state-download-url')
        state_resp = self.session.get(state_url)
        state_data = state_resp.json()
        return state_data

    def list_resources(self):
        state = self.get_state()
        if not state:
            return []
        return state.get('resources', [])

    def find_dependencies(self):
        state = self.get_state()
        if not state:
            return set()
        return self._find_all_references(state)

    def _find_all_references(self, state):
        workspaces = set()
        for rsc in state.get('resources'):
            if rsc.get('mode') != 'data':
                continue
            if rsc.get('type') != 'terraform_remote_state':
                continue
            for instance in rsc.get('instances'):
                workspaces.add(instance.get('attributes').get('config').get('value').get('workspaces').get('name'))
        return workspaces

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
        tfe_ws = Workspace(x.name, terraform_org)
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
