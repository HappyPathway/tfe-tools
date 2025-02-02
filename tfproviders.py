#!/usr/bin/env python3
from glob import glob
import hcl2 # uses python-hcl2==3.0.5
import os
import re
import json
import string
import random
from collections import defaultdict

def nonce():
    # printing punctuation
    letters = string.punctuation
    return ''.join(random.choice(letters) for i in range(10))

def get_provider_aliases():
    defined_providers = defaultdict(list)
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('provider'):
                    for var in hcl_data.get('provider'):
                        for provider in list(var.keys()):
                            # if 'alias' in var.get(provider).keys():
                            defined_providers[provider].append(var.get(provider).get('alias', "default"))
            except:
                continue
    return defined_providers

def get_required_providers():
    # ^var\.[a-zA-Z0-9._-]+$
    required_providers = set()
    reggie = re.compile('resource \"*([a-zA-Z0-9]+)_')
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            for line in tf_file.readlines():
                m = reggie.findall(line)
                if m and not line.startswith('#'):
                    [required_providers.add(match) for match in m]
    return required_providers

def get_defined_providers():
    defined_providers = set()
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('provider'):
                    for var in hcl_data.get('provider'):
                        var_name = list(var.keys())[0]
                        defined_providers.add(var_name)
            except:
                continue
    return defined_providers

def get_defaulted_providers():
    defaulted_providers = set()
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('provider'):
                    for var in hcl_data.get('provider'):
                        # print(json.dumps(
                        #     var,
                        #     separators=(',', ':'),
                        #     indent=4,
                        #     sort_keys=True
                        # ))
                        var_name = list(var.keys())[0]
                        # print(var.get(var_name))
                        _nonce = nonce()
                        _default = var.get(var_name).get('default', _nonce)
                        if _default != _nonce:
                            defaulted_providers.add(var_name)
            except:
                continue
    return defaulted_providers

def check_provider(var_name):
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            if f"var.{var_name}" in tf_file.read():
                return True
    return False

def pprint(raw, prompt, data):
    if raw:
        print(
            data
        )
    else:
        print(
            prompt,
            data
        )

def main(opt):
    defined_providers = get_defined_providers()
    required_providers = get_required_providers()
    defaulted_providers = get_defaulted_providers()
    unused_providers = sorted([x for x in defined_providers if not check_provider(x)])
    missing_providers = sorted([x for x in required_providers if not x in defined_providers])
    nondefaulted_providers = set(defined_providers).symmetric_difference(set(defaulted_providers))

    if opt.unused or opt.all:
        print(
            "Unused providers: ",
            json.dumps(
                unused_providers,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.missing or opt.all:
        pprint(
            opt.raw,
            "Missing providers: ",
            json.dumps(
                missing_providers,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.required or opt.all:
        pprint(
            opt.raw,
            "Required providers: ",
            json.dumps(
                sorted(list(required_providers)),
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.defined or opt.all:
        pprint(
            opt.raw,
            "Defined providers: ",
            json.dumps(
                sorted(list(defined_providers)),
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )
    
    if opt.defaulted or opt.all:
        pprint(
            opt.raw,
            "Defaulted providers: ",
            json.dumps(
                sorted(list(defaulted_providers)),
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.nondefaulted or opt.all:
        pprint(
            opt.raw,
            "Nondefaulted providers: ",
            json.dumps(
                sorted(list(nondefaulted_providers)),
                separators=(',',':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.check:
        if not missing_providers and not unused_providers:
            print("OK!")

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    for x in ["required", "defined", "unused", "missing", "check", "all", 'defaulted', 'nondefaulted']:
        p.add_option(f"--{x}", dest=x, default=False, action="store_true")
    p.add_option("--raw", action="store_true", default=False)
    opt, args = p.parse_args()
    main(opt)