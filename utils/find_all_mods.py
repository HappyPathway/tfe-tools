#!/usr/bin/env python3
import json
from tfe_tools.common import sanitize_path, tfe_token, get_requests_session, mod_dependencies

def main(mod_source, input_file):
    with open(input_file) as input:
        d = json.loads(input.read())

    mods = set()
    for k, v in d.items():
        for _, version in v.items():
            if type(version) == type(list()):
                for dep in version:
                    if dep.get('versions'):
                        for __x, __y in dep.get('versions').items():
                            if __y == mod_source:
                                mods.add(k)
    # return mods
    print(
        json.dumps(
            list(mods),
            separators=(',', ':'),
            indent=4
        )
    )

if __name__ == '__main__':
    from optparse import OptionParser
    opt, args = OptionParser().parse_args()
    main(*args)
