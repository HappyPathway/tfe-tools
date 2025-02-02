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
from requests import Session
from urllib.parse import urlencode, quote_plus
from collections import defaultdict


def tfe_token(tfe_api, config):
    with open(sanitize_path(config), 'r') as fp:
        obj = hcl2.load(fp)
    return obj.get('credentials')[0].get(tfe_api).get('token')[0]


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path
 


def main(terraform_url, terraform_org, workspace_name):
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
    url_params = {
        "filter[organization][name]": terraform_org,
        "filter[workspace][name]": workspace_name
    }
    resp = tfe_session.get(url, params=urlencode(url_params, quote_via=quote_plus))
    data = resp.json()
    last_state = data.get('data')[0]
    providers = last_state.get('attributes').get('providers')
    rsc_counts = defaultdict(int)
    for provider, resources in providers.items():
        for count in resources.values():
            rsc_counts[provider] += count

    total_resources = 0
    for rsc_count in rsc_counts.values():
        total_resources += rsc_count
    rsc_counts['Total'] = total_resources
    print(
        json.dumps(
            rsc_counts,
            separators=(',', ':'),
            indent=4,
            sort_keys=True
        )
    )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", dest="terraform_url", default="terraform.corp.clover.com")
    parser.add_argument("--org", dest="terraform_org", default="clover")
    parser.add_argument("-w", dest="workspace_name")
    args = parser.parse_args()
    main(args.terraform_url, args.terraform_org, args.workspace_name)
