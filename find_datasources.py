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
from tfe_tools.common import sanitize_path, tfe_token, get_requests_session, mod_dependencies
import re

def get_self_links(state):
    self_link_regex = re.compile('"self_link":"(?P<self_link>.*)",$')
    self_links = set()
    for line in state.readlines():
        m = self_link_regex.search(line)
        if m:
            self_links.add(m.groupdict().get('self_link'))


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

def find_all_addresses(state, data_source_type=None, attr=None):
    resources = set()
    if not state or not state.get('resources'):
        return resources
    for rsc in state.get('resources'):
        if rsc.get('mode') != "data":
            continue
        if data_source_type and rsc.get('type') == data_source_type:
            if rsc.get('instances'):
                for instance in rsc.get('instances'): 
                    _attr = helpers.get_attr(instance, attr)
                    print(f"\t{_attr}")
                    resources.add(_attr)
            else:
                _attr = helpers.get_attr(rsc, attr)
                print(f"\t{_attr}")
                resources.add(_attr)
    return resources
    
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


def scan_workspace(workspace, url, data_source_type, attr, tfe_session, terraform_org):
    print(workspace)
    state = get_state(url, tfe_session, terraform_org, workspace.name)
    addrs = find_all_addresses(state, data_source_type, attr)
    return addrs
    

def main(terraform_url, terraform_org, data_source_type, attr, workspace_name=False):
    tkn = tfe_token(terraform_url, 
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
    workspace_data_sources = dict()
    if not workspace_name:
        ws = org.workspaces()
        for ws in sorted(ws, key=lambda ws: ws.name):
            data = list(scan_workspace(ws, url, data_source_type, attr, tfe_session, terraform_org))
            workspace_data_sources[ws.name] = data
    else:
        ws = Workspace()
        ws.organization = org
        ws.name = workspace_name
        ws.get()
        data = list(scan_workspace(ws, url, data_source_type, attr, tfe_session, terraform_org))
        workspace_data_sources[workspace_name] = data
    return workspace_data_sources
    
# with open(, "w") as output:


if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-u", dest="terraform_url")
    p.add_option("--org", dest="terraform_org")
    p.add_option("-o", dest='output', default=os.path.join(os.path.dirname(__file__), "./reports/"))
    p.add_option("-w", dest="workspace", default=None)
    p.add_option("-t", dest="type")
    p.add_option("-a", dest="attr", default=None)
    opt, arg = p.parse_args()
    data = main(opt.terraform_url, opt.terraform_org, opt.type, opt.attr, opt.workspace)
    output_dir = os.path.join(opt.output, "datasources")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if not os.path.isdir(output_dir):
        sys.stderr.write("Directory Does Not Exist\n")
        sys.exit(1)
    with open(os.path.join(output_dir, f"{opt.type}.json"), 'w') as output:
        output.write(
            json.dumps(
                {k: v for k,v in data.items() if len(v) > 0},
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )
