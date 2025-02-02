#!/usr/bin/env python3
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))
from tfe_tools.common import find_interesting_records

reports_default_dir = os.path.join(
    os.path.join(
        os.path.dirname(__file__), 
        os.path.pardir
    ),
    "reports/statedb/*.json"
)

default_output = os.path.join(
    os.path.join(
        os.path.dirname(__file__), 
        os.path.pardir
    ),
    "reports/managed_zones.json"
)


def main(base_dir, output):
    zones = list()
    data = find_interesting_records(
        "clover", 
        "terraform.corp.clover.com", 
        "google_dns_managed_zone", 
        "dns_name",
        base_dir
    )
    for k, v in data.items():
        for record in v:
            if record.get('dns_name').endswith("clover.network."):
                zones.append(record.get('dns_name'))
    with open(output, 'w') as output:
        output.write(
            json.dumps(
                zones, 
                separators=(',', ':'), 
                indent=4, 
                sort_keys=True
            )
        )

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("--dir", default=reports_default_dir)
    p.add_option("--output", default=default_output)
    opt, arg = p.parse_args()
    main(opt.dir, opt.output)
