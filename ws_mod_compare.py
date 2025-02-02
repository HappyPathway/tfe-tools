#!/usr/bin/env python3
import json
import semantic_version
import os
from collections import defaultdict
import re

ws_list = json.loads(open(os.path.expandvars(os.path.join(os.path.dirname(__file__), "./reports/tf_ws_mods.json"))).read())
mod_versions = json.loads(open(os.path.expandvars(os.path.join(os.path.dirname(__file__), "./reports/mod_versions.json"))).read())

mod_cache = dict()

'''
def get_latest(mod_source):
    if not mod_source in cache:
        for x in ws_list.values():
            for mod in x:
                if mod.get('versions').get('source') == mod_source:
                    cache[mod_source] = mod.get('versions').get('version')
    return cache.get(mod_source)
'''
def get_latest(mod_source):
    for mod in mod_versions:
        # print(mod, mod_versions.get(mod).get('latest_version'))
        if mod_versions.get(mod).get('source') == mod_source:
            return mod_versions.get(mod).get('latest_version')


def cmp_version(actual_version_string, latest, mod_version):
    mod_semver = semantic_version.Version(str(mod_version))
    latest_semver = semantic_version.Version(str(latest))
    if '~>' in actual_version_string:
        if len(actual_version_string.split('.')) == 2:
            if mod_semver.major < latest_semver.major:
                return False
            else:
                return True
        if len(actual_version_string.split('.')) == 3:
            if (mod_semver.major < latest_semver.major) or (mod_semver.minor < latest_semver.minor):
                return False
            else:
                return True
    elif mod_semver < latest_semver:
        return False
    elif ">=" in actual_version_string:
        return True
    else:
        return True


def main():
    needs_update = defaultdict(list)
    version_regex = re.compile('(\d+\.)?(\d+\.)?(\*|\d+)$')
    requires_updates = set()
    for ws, _d in ws_list.items():
        for mod in _d:
            mod_source = mod.get('versions').get('source')
            actual_version_string = mod.get('versions').get('version')
            m = version_regex.search(mod.get('versions').get('version'))
            if m:
                mod_version = m.group(0)
                if len(mod_version.split('.')) < 3:
                    mod_version = "{0}.0".format(mod_version)
            else:
                print("Failed: {0}".format(mod.get('versions').get('version')))

            latest = get_latest(mod_source)
            if not cmp_version(actual_version_string, latest, mod_version):
                requires_updates.add(ws)
                needs_update[ws].append(
                    dict(
                        module=mod_source,
                        latest_version=latest,
                        actual_version=actual_version_string
                    )
                )

    with open(os.path.join(os.path.dirname(__file__), "./reports/mod_update.json"), "w") as output:
        output.write(
            json.dumps(
                needs_update, 
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

if __name__ == '__main__':
    main()