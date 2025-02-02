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

def find_all_addresses(state):
    resources = list()
    for rsc in state.get('resources'):
        # print(rsc.keys())
        if rsc.get('mode') != 'managed':
            continue
        # only resources that have for_each or count set should have an index_key
        if has_index_key(rsc):
            for instance in rsc.get('instances'): 
                # this would be the case for any resource that has count or for_each set and is in an embedded module
                data = dict(
                    resource_type=rsc.get('type')
                )
                index_key = stringify_index_key(instance)
                data['rsc_id'] = helpers.get_attr(instance, 'id')
                data['name'] = rsc.get('name')
                if rsc.get('module'):
                    data['tf_address'] = "{0}.{1}.{2}[{3}]".format(rsc.get('module'), rsc.get('type'), rsc.get('name'), index_key)
                    resources.append(data)
                # this would be the case for any resource that has count or for_each set and is in the root module
                else:
                    data['tf_address'] = "{0}.{1}[{2}]".format(rsc.get('type'), rsc.get('name'), index_key)
                    resources.append(data)
        else:
            data = dict(
                resource_type=rsc.get('type')
            )
            data['rsc_id'] = helpers.get_attr(rsc, 'id')
            data['name'] = helpers.get_attr(rsc, 'name')
            # this would be the case for any resource that does not have count or for_each set and is in an embedded module
            if rsc.get('module'):
                data['tf_address'] = "{0}.{1}.{2}".format(rsc.get('module'), rsc.get('type'), rsc.get('name'))
                resources.append(data)
            # this would be the case for any resource that does not have count or for_each set and is in the root module
            else:
                data['tf_address'] = "{0}.{1}".format(rsc.get('type'), rsc.get('name'))
                resources.append(data)
    return resources
    
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
    except TypeError:
        return None
    state_url = last_state.get('attributes').get('hosted-state-download-url')
    state_resp = tfe_session.get(state_url)
    state_data = state_resp.json()
    return state_data


def scan_workspace(workspace, url, tfe_session, terraform_org, output_dir):
    print("scanning {0}".format(workspace.name))
    state = get_state(url, tfe_session, terraform_org, workspace.name)
    if not state:
        return

    addrs = find_all_addresses(state)
    ws_data = dict(
        resources=addrs
    )
    if workspace.vcs_repo:
        ws_data['repo'] = workspace.vcs_repo.get('identifier')
    else:
        ws_data['repo'] = None
    ws_data["workspace"] = workspace.name
    ws_data["terraform_version"] = workspace.terraform_version
    with open(os.path.join(output_dir, "{0}.json".format(workspace.name)), 'w') as _out:
        _out.write(
            json.dumps(
                ws_data,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

def main(terraform_url, terraform_org, output_dir, workspace_name=False):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if not os.path.isdir(output_dir):
        sys.stderr.write("Directory Does Not Exist\n")
        sys.exit(1)

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
    if not workspace_name:
        print("Retrieving Complete List of Workspaces...")
        org = Organization(terraform_org)
        ws = org.workspaces()
        for ws in sorted(ws, key=lambda ws: ws.name):
            workspace = Workspace(ws.name, terraform_org)
            scan_workspace(workspace, url, tfe_session, terraform_org, output_dir)
    else:
        workspace = Workspace(workspace_name, terraform_org)
        scan_workspace(workspace, url, tfe_session, terraform_org, output_dir)

    
# with open(, "w") as output:


if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("--org", dest="terraform_org", default="clover")
    p.add_option("-o", dest='output', default=os.path.join(os.path.dirname(__file__), "./reports/statedb"))
    p.add_option("-w", dest="workspace", default=None)
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.output, opt.workspace)
    
