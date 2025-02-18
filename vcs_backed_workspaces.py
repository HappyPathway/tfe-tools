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

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


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
        token = self._get_token()
        session = Session()
        session.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json"
        }
        return session

    def _get_token(self):
        config_path = os.path.join(os.environ.get("HOME"), ".terraformrc")
        with open(config_path, 'r') as fp:
            obj = hcl2.load(fp)
        return obj.get('credentials')[0].get("terraform.corp.clover.com").get('token')

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


def tfe_token(tfe_api, config):
    if sanitize_path(config):
        with open(sanitize_path(config), 'r') as fp:
            obj = hcl2.load(fp)
        return obj.get('credentials')[0].get(tfe_api).get('token')
    elif sanitize_path("${HOME}/.terraform.d/credentials.tfrc.json"):
        with open(sanitize_path("${HOME}/.terraform.d/credentials.tfrc.json"), 'r') as fp:
            d = json.loads(fp.read())
            return d.get('credentials').get(tfe_api).get('token')
    else:
        raise TFEException("Could not find credentials file")


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return path
    else:
        return None
 
def clone(repo_clone_url):
    p = subprocess.Popen(
        "git clone {0}".format(repo_clone_url),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    if p.returncode > 0:
        raise GitException("Could not clone {0}".format(repo_clone_url))


def dependencies(ws_name):
    module_source_regex = re.compile('source\s*=\s*"terraform.corp.clover.com/clover/(?P<module>[^"]*)"')
    dependencies = list()
    for tf_file_name in glob("*.tf"):
        with open(tf_file_name, 'r') as tf_file:
            for line in tf_file.read().splitlines():
                m = module_source_regex.search(line)
                if m:
                    d = m.groupdict().get('module')
                    url_parts = d.split('/')
                    dependencies.append("terraform-{0}-{1}".format(url_parts[1], url_parts[0]))
    return dependencies


def main(terraform_url, terraform_org, check):
    workspaces = defaultdict(list)
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
    for x in sorted(ws, key=lambda ws: ws.name):
        workspace = Workspace(x.name, terraform_org)
        if not workspace.vcs_repo:
            workspaces["not_vcs_backed"].append(x.name)
        else:
            workspaces["vcs_backed"].append(x.name)
    print(
        json.dumps(
            sorted(list(workspaces.get(check))),
            separators=(',', ':'),
            indent=4
        )
    )

if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("-o", dest="terraform_org", default="clover")
    p.add_option("-b", dest='base_dir',      default=mkdtemp(prefix="/tmp/"))
    p.add_option("-c", dest="check", default="not_vcs_backed")
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.check)
    
