#!/usr/bin/env python3
import json

def main(module_source):
    workspaces = list()
    with open("./reports/mod_versions.json") as mod_versions_file:
        mod_versions = json.loads(mod_versions_file.read())

    with open("./reports/tf_ws_mods.json") as tf_ws_mods_file:
        tf_ws_mods = json.loads(tf_ws_mods_file.read())

    mod_version_data = mod_versions.get(module_source)
    for k, v in tf_ws_mods.items():
        if module_source in v:
            workspaces.append(k)

    return dict(
        info=mod_version_data, 
        workspaces=workspaces
    )

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    _, args = p.parse_args()
    for arg in args:
        print(
            json.dumps(
                main(arg),
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )