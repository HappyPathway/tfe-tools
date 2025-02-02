#!/usr/bin/env python3
import requests
from requests import Session
import hcl
import os
import sys
import json
import helpers

def list_workspaces(session, api, org):
    url = "https://{0}/api/v2/organizations/{1}/workspaces".format(api, org)
    resp = session.get(url)
    for x in resp.json().get('data'):
        yield x

def list_runs(session, api, ws):
    url = "https://{0}/api/v2/workspaces/{1}/runs".format(api, ws)
    resp = session.get(url)
    for x in resp.json().get('data'):
        yield x

def list_states(session, api, ws_name, org):
    url =  "https://{0}/api/v2/state-versions?filter%5Bworkspace%5D%5Bname%5D={1}&filter%5Borganization%5D%5Bname%5D={2}".format(api, ws_name, org)
    resp = session.get(url)
    return resp.json()

def get_state_version(session, api, state_id):
    url = "https://{0}/api/v2/state-versions/{1}".format(api, state_id)
    resp = session.get(url)
    return resp.json()
    
def get_cost_estimate(session, api, c_id):
    url = "https://{0}/api/v2/cost-estimates/{1}".format(api, c_id)
    resp = session.get(url)
    return resp.json().get("data")

def get_plan(session, api, plan_id):
    url = "https://{0}/api/v2/plans/{1}".format(api, plan_id)
    resp = session.get(url)
    json_output = resp.json().get("data").get("links").get("json-output")
    resp = session.get(os.path.join("https://{0}/{1}".format(api, json_output)))
    return resp.json()

def sanitize_path(path):
    path = os.path.abspath(path)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return path

def init(api):
    token = helpers.tfe_token(api, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )
    # with open("{0}/.terraformrc".format(os.environ.get("HOME"))) as tfc:
    #     tfc = hcl.loads(tfc.read())
    # token = tfc.get("credentials").get(api).get("token")
    session = Session()
    session_headers = {
        "Authorization": "Bearer {0}".format(token),
        "Content-Type": "application/vnd.api+json"
    }
    session.headers = session_headers
    return session

def main(opt):
    os.chdir(os.getcwd())
    base_dir = sanitize_path(opt.output)
    session = init(opt.api)
    
    ws_id = None
    for ws in list_workspaces(session, opt.api, opt.org):
        if ws.get("attributes").get("name") == opt.workspace:
            ws_id = ws.get("id")

    print(ws_id)
    for run in list_runs(session, opt.api, ws_id):
        if opt.run and run.get("id") != opt.run:
            continue
        
        plan = run.get("relationships").get("plan")
        run_path = os.path.join(base_dir, "plan.json")
        with open(run_path, "w") as output:
            output.write(
                json.dumps(
                    get_plan(session, opt.api, plan.get("data").get("id")),
                    separators=(',', ':'),
                    indent=4,
                    sort_keys=True
                )
            )

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("--api", dest="api", default="terraform.corp.clover.com")
    p.add_option("--org", dest="org", default="clover")
    p.add_option("-w", dest="workspace")
    p.add_option("-o", dest="output")
    p.add_option("-r", dest="run")
    opt, arg = p.parse_args()
    main(opt)