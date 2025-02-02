#!/usr/bin/env python3
import os
import json
import sys
from tfe.core.workspace import Workspace
import hcl2
from glob import glob
import subprocess
from tempfile import mkdtemp
import shutil
from github import Github
from github.GithubException import UnknownObjectException as gheUnknownObjectException
from tfe.core.organization import Organization
from tfe.core import session
from tfe.core.variable import Variable
from tfe.core.tfe import TFEObject
import hvac

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VaultException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


class VaultClient:

    '''
        Class Vault
    '''

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def login(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.client = hvac.Client(
            url = self.url,
            namespace = self.namespace,
            verify = False
        )
        try:
            self.client.auth.ldap.login(
                username = self.username,
                password = self.password,
                mount_point = self.mount_point
            )
        except hvac.exceptions.InvalidRequest as exp:
            raise VaultException(exp)

        if not self.client.is_authenticated:
            raise VaultException("Could not authenticate")

        self.client.secrets.kv.default_kv_version = 1

    def read(self, path):
        try:
            return self.client.read(path)
        except hvac.exceptions.Forbidden as exp:
            raise VaultException(exp)


def tfe_token(tfe_api, config):
    with open(sanitize_path(config), 'r') as fp:
        obj = hcl2.load(fp)
    return obj.get('credentials')[0].get(tfe_api).get('token')[0]


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path


def create_var(org, ws, k, v):
    var = Variable()
    var.organization = org
    var.workspace = ws
    var.key = k
    var.value = v
    var.sensitive = True
    var.workspace_id = ws.id
    var.category = "terraform"
    var.hcl = False
    var.create()

def main(terraform_url, terraform_org, workspace_name, vc, vault_path, dryrun):
    tkn = tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )
    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    ws = Workspace(organization=org, name=workspace_name)
    print(vault_path)
    data = vc.read(vault_path).get("data")
    print(json.dumps(data, separators=(',', ':'), indent=4, sort_keys=True))
    for k, v in data.items():
        if dryrun:
            print("create_var({0}, {1}, {2}, {3})".format(org.name, ws.name, k, v))
        else:
            try:
                create_var(org, ws, k, v)
            except:
                print(k, "failed... please enter manually")
                print(v)
        
    

if __name__ == "__main__":
    from optparse import OptionParser, OptionGroup
    p = OptionParser()
    p.add_option("-d", 
        dest="dryrun", 
        help="specify -d to run in dry-run", 
        action="store_true", 
        default=False
    )

    tfe = OptionGroup(p, "Terraform Options")
    tfe.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    tfe.add_option("-o", dest="terraform_org", default="clover")
    tfe.add_option("-w", dest="terraform_workspace")
    p.add_option_group(tfe)

    vault = OptionGroup(p, "Vault Options")
    vault.add_option("-n", dest="vault_namespace", default="terraform")
    vault.add_option("-u", dest="vault_username", default=os.environ.get("LDAP_USERNAME"))
    vault.add_option("-p", dest="vault_password", default=os.environ.get("LDAP_PASSWORD"))
    vault.add_option("-m", dest="vault_mount_point", default="prod-ldap")
    vault.add_option("--url", dest="vault_url", default="https://vault-usprod01.corp.clover.com")
    vault.add_option("--path", dest="vault_path")
    p.add_option_group(vault)
    
    opt, arg = p.parse_args()
    vc = VaultClient(
        username=opt.vault_username,
        password=opt.vault_password,
        namespace=opt.vault_namespace,
        url=opt.vault_url,
        mount_point=opt.vault_mount_point
    )
    vc.login()

    main(
        opt.terraform_url, 
        opt.terraform_org,
        opt.terraform_workspace,
        vc,
        opt.vault_path,
        opt.dryrun
    )
    