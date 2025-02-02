#!/usr/bin/env python3 
from datetime import datetime, timedelta
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

def tfe_token(tfe_api, config):
    with open(sanitize_path(config), 'r') as fp:
        obj = hcl2.load(fp)
    return obj.get('credentials')[0].get(tfe_api).get('token')[0]

def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path

def main(terraform_url, terraform_org):
    tkn = tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )

    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    ws = org.workspaces()
    for _ws in ws:
        try:
            run = [run for run in _ws.runs][0]
            status = run.status
            github_user = None
            tfe_user = None
            if status in ['cost_estimated', 'planned']:
                planned_at = run.details.get('data').get('attributes').get('status-timestamps').get('planned-at')
                for data in run.details.get('included'):
                    if data.get('type') == 'ingress-attributes':
                        github_user = data.get('attributes').get('sender-username')
                    if data.get('type') == 'users':
                        tfe_user = data.get('attributes').get('username')
                    if tfe_user:
                        triggered_by = tfe_user
                    else:
                        triggered_by = github_user
                yield _ws.name, planned_at, triggered_by, status
        except IndexError:
            pass
    

if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("-o", dest="terraform_org", default="clover")
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org)
    for ws in main(opt.terraform_url, opt.terraform_org):
        print(
            "\nWorkspace: {0}".format(ws[0]),
            "\n\tPlanned: {0}".format(ws[1]),
            "\n\tTriggered By: {0}".format(ws[2]),
            "\n\tStatus: {0}".format(ws[3])
        )