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

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)



def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path
 

def tf_version(terraform_version):
    subprocess.run("/usr/local/bin/tfenv install {0}".format(terraform_version), 
        shell=True,
        stdout=open("/dev/null", "w"), 
        stderr=open("/dev/null",)
    )
    subprocess.run("/usr/local/bin/tfenv use {0}".format(terraform_version),
        shell=True,
        stdout=open("/dev/null", "w"), 
        stderr=open("/dev/null",)
    )

def tf_init():
    subprocess.run("terraform init -upgrade", 
        shell=True, 
        stdout=open("/dev/null", "w"), 
        stderr=open("/dev/null",)
    )
    
def get_current_tf_version():
    p = subprocess.Popen(
        "tfenv list | grep '*' | awk '{ print $2 }'", 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    return str(out.decode('utf-8'))

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


def query_match(rsc, key, value, resource_type):
    if not key and value:
        val_regex = re.compile(value)
        for k, v in rsc.items():
            if v and val_regex.search(v):
                return True

    elif key and value:
        val_regex = re.compile(value)
        for k, v in rsc.items():
            if ((key and k == key) or not key) and v and val_regex.search(v):
                if (resource_type and resource_found) or not resource_type:
                    return True

    elif not key and not value and resource_type:
        resource_type_regex = re.compile(resource_type)
        for k, v in rsc.items():
            resource_found = resource_type_regex.search(rsc.get("resource_type"))
            if (resource_type and resource_found):
                    return True
    return False


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


def find_interesting_records(key, value, resource_type, workspaces=[], base_dir="./reports/statedb/*.json"):
    interest = defaultdict(dict)
    statefiles = list()
    if not workspaces:
        for x in glob.glob(base_dir):
            statefiles.append(x)
    else:
        for workspace in workspaces:
            for x in glob.glob("./reports/statedb/{0}.json".format(workspace)):
                statefiles.append(x)
    
    results = list()
    for x in sorted(statefiles):
        with open(x) as state:
            data = json.loads(state.read())
        interest[data.get("repo")]['addresses'] = list()
        interest[data.get("repo")]['workspace'] = data.get('workspace')
        interest[data.get("repo")]['terraform_version'] = data.get('terraform_version')
        interest[data.get('repo')]['repo'] = data.get("repo")
        for rsc in data.get('resources'):
            if not rsc.get('rsc_id'):
                continue
            if query_match(rsc, key, value, resource_type):
                results.append(
                    dict(
                        workspace=data.get('workspace'),
                        resource_id=rsc.get('rsc_id'),
                        tf_address=rsc.get('tf_address'),
                        resource_type=rsc.get("resource_type")
                    )
                )
                interest[data.get("repo")]['addresses'].append(rsc.get('tf_address'))
    return results, [interest.get(repo_name) for repo_name in interest if interest.get(repo_name).get('addresses')]

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
    p.add_option("-g", dest="github_base",   default="https://github.corp.clover.com")
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