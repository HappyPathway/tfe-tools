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
from helpers import tfe_token

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


# def tfe_token(tfe_api, config):
#     with open(sanitize_path(config), 'r') as fp:
#         obj = hcl2.load(fp)
#     return obj.get('credentials')[0].get(tfe_api).get('token')[0]


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path
 


def main(terraform_url, terraform_org, output, workspace_name, serial):
    output_dir = os.path.dirname(sanitize_path(output))
    if not os.path.isdir(output_dir):
        sys.stderr.write("Directory Does Not Exist\n")
        sys.exit(1)

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
    state_url = last_state.get('attributes').get('hosted-state-download-url')
    state_resp = tfe_session.get(state_url)
    state_data = state_resp.json()
    if not serial:
        with open(sanitize_path(output), 'w') as output_file:
            output_file.write(
                json.dumps(
                    state_data,
                    separators=(',', ':'),
                    indent=4
                )
            )
    else:
        print(state_data.get('serial')+1)
    sys.exit(0)
        


if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("--org", dest="terraform_org", default="clover")
    p.add_option("-w", dest="workspace_name")
    p.add_option("-o", dest='output', default=os.path.join(os.environ.get("PWD"), "statefile.json"))
    p.add_option("--serial", default=False, action="store_true")
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.output, opt.workspace_name, opt.serial)
    
