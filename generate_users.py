#!/usr/bin/env python3
import requests
from requests import Session
import os
import hcl2
import json
from jinja2 import Template
from tfe_tools.common import sanitize_path, tfe_token, get_requests_session, mod_dependencies

class TerraformClientException(Exception):
    def __init__(self, *args, **kwargs):
        self.message = kwargs.get('message')
        super().__init__(*args)

    def __repr__(self):
        return self.messsage

    def __str__(self):
        return self.messsage


def init_session(terraform_url):
    token = tfe_token(terraform_url, 
        "{0}/.terraformrc".format(
            os.environ.get("HOME")
        )
    )
    session = Session()
    session.headers = {
        "Authorization": "Bearer {0}".format(token), 
        "Content-Type": "application/vnd.api+json"
    }
    return session


def get_user_page_count(session):
    resp = session.get("https://terraform.corp.clover.com/api/v2/admin/users")
    try:
        resp.raise_for_status()
    except Exception as err:
        TerraformClientException(message=err)
    resp = resp.json()
    meta = resp.get('meta')
    return meta.get('pagination').get('total-pages')


def get_users(session, page=1):
    users = list()
    for pg in range(1, get_user_page_count(session)):
        resp = session.get("https://terraform.corp.clover.com/api/v2/admin/users?page%5Bnumber%5D={0}".format(pg))
        try:
            resp.raise_for_status()
        except Exception as err:
            TerraformClientException(message=err)
        resp = resp.json()
        for user in resp.get('data'):
            users.append(user)
    return users
    

def get_user_template():
    return Template('''
    resource "tfe_organization_membership" "{{ username }}" {
        organization = "{{ org }}"
        email = "{{ email }}"
    }''')



def get_team_page_count(session, org):
    resp = session.get("https://terraform.corp.clover.com/api/v2/organizations/{0}/teams".format(org))
    try:
        resp.raise_for_status()
    except Exception as err:
        TerraformClientException(message=err)
    resp = resp.json()
    meta = resp.get('meta')
    return meta.get('pagination').get('total-pages')


def get_teams(session, org):
    teams = list()
    for pg in range(0, get_team_page_count(session, org)):
        resp = session.get("https://terraform.corp.clover.com/api/v2/organizations/{0}/teams?page%5Bnumber%5D={1}".format(org, pg+1))
        try:
            resp.raise_for_status()
        except Exception as err:
            TerraformClientException(message=err)
        resp = resp.json()
        print(json.dumps(resp, separators=(',', ':'), indent=4, sort_keys=True))
        for team in resp.get('data'):
            teams.append(team)
    return teams

def get_team_template():
    return Template('''
    resource "tfe_team" "{{ team_name|lower }}" {
        organization = "{{ org }}"
        name = "{{ team_name }}"
    }''')



def main(tfe_api, org, users_output, teams_output):
    session = init_session(tfe_api)
    user_tpl = get_user_template()
    team_tpl = get_team_template()

    for team in get_teams(session, org):
        print(json.dumps(team.get('attributes'), separators=(',', ':'), indent=4, sort_keys=True))

    with open(sanitize_path(users_output), "w") as output:
        for user in get_users(session):
            output.write(
                user_tpl.render(
                    username=user.get('attributes').get('username'), 
                    email=user.get('attributes').get('email'),
                    org=org
                )
            )


if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-u", default="terraform.corp.clover.com", dest="terraform_url")
    p.add_option("-o", default="clover", dest="org")
    p.add_option("--users-output", default=os.path.join(os.environ.get("PWD"), "tfe_users.tf"))
    p.add_option("--teams-output", default=os.path.join(os.environ.get("PWD"), "tfe_teams.tf"))
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.org, opt.users_output, opt.teams_output)
