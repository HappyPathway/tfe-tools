#!/usr/bin/env python3
import json
import os

def main(mod_source, input_file):
    with open(input_file) as input:
        d = json.loads(input.read())

    workspaces = list()
    for ws, deps in d.items():
        for dep in deps:
            if dep.get('versions').get('source') == mod_source:
                dep_dict = dict(
                        workspace = ws,
                        version = dep.get('versions').get('version')
                    )
                if dep_dict not in workspaces:
                    workspaces.append(
                        dep_dict
                    )
    return workspaces
    

if __name__ == '__main__':
    usage = "usage: %prog <mod_source_string> <input_file>"
    from optparse import OptionParser
    opt, args = OptionParser(usage=usage).parse_args()
    if not len(args) > 1:
        args.append(os.path.join(os.path.dirname(__file__), '../reports/tf_ws_mods.json'))
    workspaces = main(*args)
    print(
        json.dumps(
            workspaces,
            separators=(',', ':'),
            indent=4
        )
    )