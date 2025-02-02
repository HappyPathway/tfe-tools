#!/usr/bin/env python3
from glob import glob
import hcl2
import os
import re
import json
from collections import defaultdict
def get_required_data_source():
    # ^var\.[a-zA-Z0-9._-]+$
    required_data_sources = set()
    reggie = re.compile('data\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)')
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            for line in tf_file.readlines():
                m = reggie.search(line)
                if m:
                    required_data_sources.add(m[0])
    return required_data_sources

def get_defined_data_sources():
    defined_datasource = set()
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            hcl_data = hcl2.loads(tf_file.read())
            if hcl_data.get('data'):
                data = hcl_data.get('data')
                for _data in data:
                    for k, v in _data.items():
                        for _k, _v in v.items():
                            defined_datasource.add(f"data.{k}.{_k}")
                # for data in hcl_data.get('data'):
                #     var_name = 
                #     defined_variables.add(var_name)
    return defined_datasource

def check_data_source(data_source):
    class DSource(object):
        type = data_source.split('.')[1]
        name = data_source.split('.')[2]
    data_source_obj = DSource()
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            if f"data.{data_source_obj.type}.{data_source_obj.name}" in tf_file.read():
                return True
    return False

defined_data_sources = get_defined_data_sources()
required_data_sources = get_required_data_source()
unused_datasources = [x for x in defined_data_sources if not check_data_source(x)]
missing_datasources = required_data_sources - defined_data_sources
print(
    "Unused Datasources: ",
    json.dumps(
        unused_datasources,
        separators=(',', ':'),
        indent=4,
        sort_keys=True
    )
)

print(
    "Missing Datasources: ",
    json.dumps(
        list(missing_datasources),
        separators=(',', ':'),
        indent=4,
        sort_keys=True
    )
)