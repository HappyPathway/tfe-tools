#!/usr/bin/env python3
import json
from collections import defaultdict
import os
import sys

from tfe_tools.common import get_latest_versions, sanitize_path, tfe_token, get_requests_session, mod_dependencies

def main(terraform_base, terraform_url):
    mod_version_main(terraform_base, terraform_url)
    latest_versions = get_latest_versions()
    try:
        with open(".terraform/modules/modules.json") as modules:
            modules = json.loads(modules.read())
    except FileNotFoundError:
        sys.stderr.write("Could not find .terraform/modules/modules.json file. Either this workspace does not contain modules, or terraform init has not been run!\n")
        sys.exit(1)
        
    staging_module_keys = defaultdict(list)
    module_keys = defaultdict(list)

    for mod in modules.get('Modules'):
        latest = latest_versions.get(mod.get('Source'))
        if latest != mod.get('Version'):
            key = '.'.join(mod.get('Key').split('.')[1:])
            staging_module_keys[mod.get('Key').split('.')[0]].append(key)
    for mod, _list in staging_module_keys.items():
        while("" in _list) :
            _list.remove("")
        if not len(_list):
            module_keys['RootModules'].append(mod)
        else:
            module_keys[mod] = _list
    return module_keys

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", default="https://terraform.example.com", dest="terraform_base")
    p.add_option("-u", default="terraform.example.com", dest="terraform_url")
    opt, arg = p.parse_args()
    print(
        json.dumps(
            main(opt.terraform_base, opt.terraform_url),
            separators=(',', ':'),
            indent=4,
            sort_keys=True
        )
    )
