#!/usr/bin/env python3
from glob import glob
import hcl2 # uses python-hcl2==3.0.5
import os
import re
import json
import string
import random

def nonce():
    # printing punctuation
    letters = string.punctuation
    return ''.join(random.choice(letters) for i in range(10))

def get_required_variables():
    # ^var\.[a-zA-Z0-9._-]+$
    required_variables = set()
    reggie = re.compile('var\.([a-zA-Z0-9_-]+)')
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        if tf_file_name in ['variables.tf', 'interface.tf']:
            continue

        with open(tf_file_name, 'r') as tf_file:
            for line in tf_file.readlines():
                m = reggie.findall(line)
                if m and not line.startswith('#'):
                    [required_variables.add(match) for match in m]
    return required_variables

def get_defined_variables():
    defined_variables = set()
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('variable'):
                    for var in hcl_data.get('variable'):
                        var_name = list(var.keys())[0]
                        defined_variables.add(var_name)
            except:
                continue
    return defined_variables

def get_defaulted_variables():
    defaulted_variables = set()
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('variable'):
                    for var in hcl_data.get('variable'):
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
                            defaulted_variables.add(var_name)
            except:
                continue
    return defaulted_variables

def check_variable(var_name):
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

def main(opt, options):    
    defined_variables = get_defined_variables()
    required_variables = get_required_variables()
    defaulted_variables = get_defaulted_variables()
    unused_variables = sorted([x for x in defined_variables if not check_variable(x)])
    missing_variables = sorted([x for x in required_variables if not x in defined_variables])
    nondefaulted_variables = set(defined_variables).symmetric_difference(set(defaulted_variables))

    if [x for x in options if getattr(opt, x)] == []:
        rew_var = set(required_variables)
        def_var = set(defined_variables)
        print("Missing Vraiables: ", json.dumps(list(rew_var - def_var), separators=(',', ':'), indent=4, sort_keys=True))
        print("Unused Variables: ", json.dumps(list(def_var - rew_var), separators=(',', ':'), indent=4, sort_keys=True))
        return

    if opt.unused or opt.all:
        print(
            "Unused Variables: ",
            json.dumps(
                unused_variables,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.missing or opt.all:
        pprint(
            opt.raw,
            "Missing Variables: ",
            json.dumps(
                missing_variables,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.required or opt.all:
        pprint(
            opt.raw,
            "Required Variables: ",
            json.dumps(
                sorted(list(required_variables)),
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.defined or opt.all:
        pprint(
            opt.raw,
            "Defined Variables: ",
            json.dumps(
                sorted(list(defined_variables)),
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )
    
    if opt.defaulted or opt.all:
        pprint(
            opt.raw,
            "Defaulted Variables: ",
            json.dumps(
                sorted(list(defaulted_variables)),
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.nondefaulted or opt.all:
        pprint(
            opt.raw,
            "Nondefaulted Variables: ",
            json.dumps(
                sorted(list(nondefaulted_variables)),
                separators=(',',':'),
                indent=4,
                sort_keys=True
            )
        )

    if opt.check:
        if not missing_variables and not unused_variables:
            print("OK!")

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    options = ["required", "defined", "unused", "missing", "check", "all", 'defaulted', 'nondefaulted']
    for x in options:
        p.add_option(f"--{x}", dest=x, default=False, action="store_true")
    p.add_option("--raw", action="store_true", default=False)
    opt, args = p.parse_args()
    main(opt, options)