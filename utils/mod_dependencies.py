#!/usr/bin/env python3
import json
import os
from tfe_tools.common import sanitize_path, tfe_token, get_requests_session, mod_dependencies

def main(module, input):
    with open(input, "r") as tf_mods:
        tf_mods = json.loads(tf_mods.read())
    used_mods = set()
    latest_version = sorted(tf_mods.get(module).keys(), reverse=True)[1]
    for mod in tf_mods.get(module).get(latest_version):
        url_parts= mod.get('versions').get('source').split('/')
        mod_name = "terraform-{0}-{1}".format(url_parts[-1], url_parts[-2])
        used_mods.add(mod_name)
    return list(used_mods)

def list_all(input):
    with open(input, "r") as tf_mods:
        tf_mods = json.loads(tf_mods.read())
    for mod in tf_mods:
        yield mod

if __name__ == '__main__':
    usage = "usage: %prog <mod_name> <input_file>"
    from optparse import OptionParser
    opt, args = OptionParser(usage=usage).parse_args()
    if not len(args) > 1:
        args.append(os.path.join(os.path.dirname(__file__), '../reports/tf_mods.json'))
    if args[0] == 'all':
        mod_dependencies = dict()
        for mod in list_all(args[1]):
            dependencies = main(mod, args[1])
            mod_dependencies[mod] = dependencies
        output_path = os.path.join(
            os.path.dirname(__file__),
            "../reports/mod_dependencies.json"
        )
        with open(output_path, "w") as output:
            output.write(
                json.dumps(
                    mod_dependencies,
                    separators=(',', ':'),
                    indent=4,
                    sort_keys=True
                )
            )
    else:
        dependencies = main(*args)
        print(
            json.dumps(
                dependencies,
                separators=(',', ':'),
                indent=4
            )
        )
