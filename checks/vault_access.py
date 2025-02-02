#!/usr/bin/env python3
import json
import sys
import os
from collections import defaultdict
from tfe_tools.common import find_interesting_records, sanitize_path, tfe_token, get_requests_session, mod_dependencies

def main(output):
    with open("./reports/datasources/vault_generic_secret.json") as datasource_input:
        datasources = json.loads(datasource_input.read())
    with open("./reports/resources/vault_generic_secret.json") as resources_input:
        resources = json.loads(resources_input.read())
    workspaces = defaultdict(lambda: defaultdict(dict))
    for k, v in datasources.items():
        if len(v):
            workspaces[k]['read'] = v
    for k, v in resources.items():
        workspaces[k]['write'] = v.get('path')
    with open(output, 'w') as output:
        output.write(
            json.dumps(
                workspaces,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("--output", default=os.path.join(
        os.path.join(
            os.path.dirname(__file__),
            os.path.pardir
        ), 
        "reports/vault_access.json"
    ))
    opt, arg = p.parse_args()
    main(opt.output)
