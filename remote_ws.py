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
    '''
    {
      "mode": "data",
      "type": "terraform_remote_state",
      "name": "network_vars",
      "provider": "provider[\"terraform.io/builtin/terraform\"]",
      "instances": [
        {
          "schema_version": 0,
          "attributes": {
            "backend": "remote",
            "config": {
              "value": {
                "hostname": "terraform.corp.clover.com",
                "organization": "clover",
                "workspaces": {
                  "name": "network-vars"
    '''
    workspaces = set()
    for rsc in state.get('resources'):
        # print(rsc.keys())
        if rsc.get('mode') != 'data':
            continue
        if rsc.get('type') != 'terraform_remote_state':
            continue
        for instance in rsc.get('instances'):
            workspaces.add(
                instance.get('attributes').get('config').get('value').get('workspaces').get('name'))
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

def get_state(url, tfe_session, terraform_org, workspace_name):
    url_params = {
        "filter[organization][name]": terraform_org,
        "filter[workspace][name]": workspace_name
    }
    resp = tfe_session.get(url, params=urlencode(url_params, quote_via=quote_plus))
    data = resp.json()
    try:
        last_state = data.get('data')[0]
    except IndexError:
        return None
    state_url = last_state.get('attributes').get('hosted-state-download-url')
    state_resp = tfe_session.get(state_url)
    state_data = state_resp.json()
    return state_data


def scan_workspace(workspace, url, tfe_session, terraform_org):
    print(f"Scanning {workspace.name}")
    state = get_state(url, tfe_session, terraform_org, workspace.name)
    if not state:
        return
    return find_all_references(state)

def main(terraform_url, terraform_org, output, workspace_name=False):
    remote_workspaces = dict()
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
    url = "https://{0}/api/v2/state-versions".format(terraform_url)
    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    if not workspace_name:
        print("Retrieving Complete List of Workspaces...")
        ws = org.workspaces()
        for ws in sorted(ws, key=lambda ws: ws.name):
            try:
                remote_workspaces[ws.name] = list(scan_workspace(ws, url, tfe_session, terraform_org))
            except:
                pass

    else:
        ws = Workspace()
        ws.organization = org
        ws.name = workspace_name
        ws.get()
        # scan_workspace(ws, url, tfe_session, terraform_org, output_dir)
        try:
            remote_workspaces[ws.name] = list(scan_workspace(ws, url, tfe_session, terraform_org))
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
# with open(, "w") as output:


if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("--org", dest="terraform_org", default="clover")
    p.add_option("-o", dest='output', default=os.path.join(os.path.dirname(__file__), "./reports/remote-workspaces.json"))
    p.add_option("-w", dest="workspace", default=None)
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.output, opt.workspace)
    