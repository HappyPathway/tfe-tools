#!/usr/bin/env python3
import os
import json
import hcl2
import subprocess
from tfe.core.organization import Organization
from tfe.core import session
from prettytable import PrettyTable
import semantic_version
from helpers import tfe_token

def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path


def main(terraform_url, terraform_org, sort_by, output):
    pt = PrettyTable()
    sort_dict = {
        "workspace": "Workspace",
        "version": "Version",
        "latest": "Latest Change"
    }
    pt.field_names = ["Workspace", "Version", "Latest Change"]
    tkn = tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )
    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    ws = org.workspaces()
    for x in sorted(ws, key=lambda ws: ws.terraform_version):
        pt.add_row([x.name, x.terraform_version, x.latest_change_at])
    pt.sortby = sort_dict.get(sort_by, "Workspace")
    pt.align['Workspace'] = 'l'
    pt.align['Version'] = 'r'
    pt.align['Latest Change'] = 'l'

    # defaults to printing output
    # if a file is specified and it doesn't exist but the containing directory does we'll write to it
    # if a file is specified and the directory doesn't exist then we'll resort to just printing it out
    if not output:
        print(pt)
    elif os.path.isdir(os.path.dirname(output)):
        with open(output, 'w') as out:
            out.write(str(pt))
    else:
        print(pt)

if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("-o", dest="terraform_org", default="clover")
    p.add_option("-s", dest="sort_by", choices=['workspace', 'version', 'latest'])
    p.add_option("--output", default=os.path.join(os.path.dirname(__file__), "ws_versions.txt"))
    
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.sort_by, opt.output)
    