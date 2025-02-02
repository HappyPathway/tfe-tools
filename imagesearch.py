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
from collections import defaultdict

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


def scan_workspace(workspace, url, tfe_session, terraform_org, image_dict):
    state = get_state(url, tfe_session, terraform_org, workspace.name)
    if not state or 'resources' not in state:
        return 
    for x in state.get('resources'):
        if x.get('mode') == 'managed' and x.get('type') == 'google_compute_instance' and x.get('name') == 'service_instances':
            for instance in x.get('instances'):
                image = instance.get('attributes').get('boot_disk')[0].get('initialize_params')[0].get('image')
                project = instance.get('attributes').get('project')
                image_dict[project].add(image)

def main(terraform_url, terraform_org):
    image_dict = defaultdict(set)
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
    ws = org.workspaces()
    for ws in sorted(ws, key=lambda ws: ws.name):
        print(ws.name)
        scan_workspace(ws, url, tfe_session, terraform_org, image_dict)

    actual_dict = dict()
    for k, v in image_dict.items():
        actual_dict[k] = list(v)

    print(
        json.dumps(
            dict(actual_dict),
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
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org)
    