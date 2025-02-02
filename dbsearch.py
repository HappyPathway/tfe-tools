#!/usr/bin/env python3

import glob
import json
import subprocess
from github import Github
import os
from collections import defaultdict
from tempfile import NamedTemporaryFile
import re
import sys
from tfe_tools.common import find_interesting_records, query_match, get_current_tf_version, clone, tf_version, tf_init, sanitize_path

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

def main(value, github_base, basedir, workspaces=None, key=None, resource_type=None, current_tf_version=None, show_id=None):
    g = Github(
        os.environ.get("GITHUB_USER"), 
        os.environ.get("GITHUB_TOKEN"), 
        base_url="{0}/api/v3".format(github_base)
    )
    results, interest = find_interesting_records(key, value, resource_type, workspaces)
    if show_id:
        print(
            json.dumps(
                results,
                separators=(',',':'),
                indent=4,
                sort_keys=True
            )
        )
        sys.exit(0)

    for ws_data in interest:
        os.chdir(basedir)
        repo = g.get_repo(ws_data.get('repo'))
        repo_path = os.path.join(
            basedir,
            repo.name
        )
        if not os.path.isdir(repo_path):
            clone(repo.ssh_url)
            print(repo.ssh_url)
        os.chdir(repo_path)
        if ws_data.get('terraform_version') != current_tf_version:
            tf_version(ws_data.get('terraform_version'))

        try:
            tf_init()
        except: 
            pass
        print("# Workspace: ", ws_data.get('workspace'))
        print("# Repo: ", repo.ssh_url)

        for rsc in ws_data.get('addresses'):
            cmd = "terraform state show '{0}'".format(rsc)
            print("# {0}".format(cmd))
            os.system(cmd)
            print("##\n")

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("--key")
    p.add_option("--query")
    p.add_option("--type", default=None)
    p.add_option("-g", dest="github_base",   default="https://github.example.com")
    p.add_option("-b", dest='basedir',      default=os.path.join(os.environ.get("HOME"), "git/workspaces"))
    p.add_option("-w", "--workspace", dest="workspaces", action="append", default=None)
    p.add_option("--id", dest="show_id", default=False, action="store_true")
    opt, arg = p.parse_args()
    current_tf_version = get_current_tf_version()
    main(
        opt.query, 
        opt.github_base, 
        opt.basedir, 
        workspaces=opt.workspaces, 
        key=opt.key, 
        resource_type=opt.type,
        current_tf_version=current_tf_version,
        show_id=opt.show_id
    )
    print("Setting Terraform Version back to {0}".format(current_tf_version))
    tf_version(current_tf_version)
