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
from tfe.core import session
from requests import Session
from urllib.parse import urlencode, quote_plus
from pathlib import Path
import helpers
import re

class Workspace:
    def __init__(self, workspace_name, organization):
        self.workspace_name = workspace_name
        self.organization = organization
        self.session = self._create_session()

    def _create_session(self):
        token = helpers.tfe_token("terraform.corp.clover.com", os.path.join(os.environ.get("HOME"), ".terraformrc"))
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

def get_self_links(state):
    self_link_regex = re.compile('"self_link":"(?P<self_link>.*)",$')
    self_links = set()
    for line in state.readlines():
        m = self_link_regex.search(line)
        if m:
            self_links.add(m.groupdict().get('self_link'))

def item_generator(json_input, lookup_key):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield v
            else:
                yield from item_generator(v, lookup_key)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item, lookup_key)

def get_attr(rsc, attr):
    try:
        attr = [x for x in item_generator(rsc, attr)][0]
        return attr
    except IndexError:
        return None

def has_index_key(rsc):
    instances = rsc.get('instances')
    if len([ x for x in filter(lambda x: x.get('index_key', "SENTINEL") != "SENTINEL", instances)]):
        return True
    else:
        return False

def stringify_index_key(instance):
    index_key = instance.get('index_key')
    try:
        int(index_key)
        return str(index_key)
    except:
        return '"{0}"'.format(index_key)

def find_all_references(state):
    workspaces = set()
    for rsc in state.get('resources'):
        if rsc.get('mode') != 'data':
            continue
        if rsc.get('type') != 'terraform_remote_state':
            continue
        for instance in rsc.get('instances'):
            workspaces.add(instance.get('attributes').get('config').get('value').get('workspaces').get('name'))
    return workspaces

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

def scan_workspace(workspace):
    print(f"Scanning {workspace.workspace_name}")
    state = workspace.get_state()
    if not state:
        return
    return workspace.find_dependencies()

def main(terraform_url, terraform_org, output, workspace_name=False):
    remote_workspaces = dict()
    if not workspace_name:
        print("Retrieving Complete List of Workspaces...")
        org = Organization(terraform_org)
        ws = org.workspaces()
        for ws in sorted(ws, key=lambda ws: ws.name):
            try:
                workspace = Workspace(ws.name, terraform_org)
                remote_workspaces[ws.name] = list(scan_workspace(workspace))
            except:
                pass
    else:
        workspace = Workspace(workspace_name, terraform_org)
        try:
            remote_workspaces[workspace_name] = list(scan_workspace(workspace))
        except:
            pass

    with open(output, 'w') as output_file:
        output_file.write(
            json.dumps(
                remote_workspaces,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("--org", dest="terraform_org", default="clover")
    p.add_option("-o", dest='output', default=os.path.join(os.path.dirname(__file__), "./reports/remote-workspaces.json"))
    p.add_option("-w", dest="workspace", default=None)
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.output, opt.workspace)
