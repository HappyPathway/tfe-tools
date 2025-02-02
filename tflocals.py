#!/usr/bin/env python3
from glob import glob
import hcl2
import os
import re
import json

def get_required_locals():
    # ^var\.[a-zA-Z0-9._-]+$
    required_locals = set()
    reggie = re.compile('local\.([a-zA-Z0-9_-]+)')
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            for line in tf_file.readlines():
                m = reggie.search(line)
                if m:
                    required_locals.add(m.groups()[0])
    return required_locals

def get_defined_locals():
    defined_locals = set()
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            # try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('locals'):
                    for var in hcl_data.get('locals'):
                        for local_name in list(var.keys()):
                            defined_locals.add(local_name)
            # except:
                # continue
    return defined_locals

def check_local(local_name):
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            if f"local.{local_name}" in tf_file.read():
                return True
    return False

defined_locals = get_defined_locals()
required_locals = get_required_locals()
unused_locals = [x for x in defined_locals if not check_local(x)]
missing_locals = [x for x in required_locals if not x in defined_locals]
print(
    "Unused Locals: ",
    json.dumps(
        unused_locals,
        separators=(',', ':'),
        indent=4,
        sort_keys=True
    )
)

print(
    "Missing Locals: ",
    json.dumps(
        missing_locals,
        separators=(',', ':'),
        indent=4,
        sort_keys=True
    )
)


print(
    "Defined Locals: ",
    json.dumps(
        list(defined_locals),
        separators=(',', ':'),
        indent=4,
        sort_keys=True
    )
)