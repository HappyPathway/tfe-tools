#!/usr/bin/env python3
from collections import defaultdict
import os
import json
from tfe_tools.common import sanitize_path
from projects import project_types
import sys

def get_data(cmp):
    with open(os.path.join(os.getcwd(), f"reports/environments/{cmp}.json")) as cmp_a_data:
        cmp_data_json = json.loads(cmp_a_data.read())
    
    cmp_data = dict()
    cmp_data['embedded_modules'] = list()
    cmp_data['resources'] = list()
    cmp_data['top_level_modules'] = list()
    for project_type in cmp_data_json:
        for workspace in cmp_data_json.get(project_type):
            cmp_data['embedded_modules'].extend(workspace.get('embedded_modules'))
            cmp_data['resources'].extend(workspace.get('resources'))
            cmp_data['top_level_modules'].extend(workspace.get('top_level_modules'))
    return cmp_data

def main(cmp_a, cmp_b):
    _cmp_a = get_data(cmp_a)
    _cmp_b = get_data(cmp_b)
    diff = defaultdict(dict)
    
    diff['embedded_modules'][cmp_a] = sorted(list(
        set(_cmp_a.get('embedded_modules')).difference(set(_cmp_b.get('embedded_modules')))
    ))
    diff['embedded_modules'][cmp_b] = sorted(list(
        set(_cmp_b.get('embedded_modules')).difference(set(_cmp_a.get('embedded_modules')))
    ))

    diff['top_level_modules'][cmp_a] = sorted(list(
        set(_cmp_a.get('top_level_modules')).difference(set(_cmp_b.get('top_level_modules')))
    ))
    diff['top_level_modules'][cmp_b] = sorted(list(
        set(_cmp_b.get('top_level_modules')).difference(set(_cmp_a.get('top_level_modules')))
    ))

    diff['resources'][cmp_a] = sorted(list(
        set(_cmp_a.get('resources')).difference(set(_cmp_b.get('resources')))
    ))
    diff['resources'][cmp_b] = sorted(list(
        set(_cmp_b.get('resources')).difference(set(_cmp_a.get('resources')))
    ))

    print(
        json.dumps(
            diff,
            separators=(',', ':'),
            indent=4,
            sort_keys=True
        )
    )
if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    opt, args = parser.parse_args()
    if len(args) != 2:
        sys.stderr.write("Must specific two environments!\n")
        sys.exit(1)
    main(args[0], args[1])
