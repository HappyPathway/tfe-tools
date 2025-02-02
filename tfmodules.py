#!/usr/bin/env python3
from glob import glob
import hcl2
import os
import re
import json
from collections import defaultdict
def get_required_modules():
    # ^var\.[a-zA-Z0-9._-]+$
    required_modules = set()
    reggie = re.compile('module\.([a-zA-Z0-9_-]+)')
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            for line in tf_file.readlines():
                m = reggie.search(line)
                if m:
                    required_modules.add(m[0])
    return required_modules

def get_defined_modules():
    defined_modulesource = set()
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            hcl_module = hcl2.loads(tf_file.read())
            if hcl_module.get('module'):
                modules = hcl_module.get('module')
                for module in modules:
                    for key in list(module.keys()):
                        defined_modulesource.add(f"module.{key}")
    return defined_modulesource

def check_modules(module):
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            if module in tf_file.read():
                return True
    return False

defined_modules = get_defined_modules()
required_modules = get_required_modules()
missing_modulesources = required_modules - defined_modules

print(
    "Missing modules: ",
    json.dumps(
        list(missing_modulesources),
        separators=(',', ':'),
        indent=4,
        sort_keys=True
    )
)