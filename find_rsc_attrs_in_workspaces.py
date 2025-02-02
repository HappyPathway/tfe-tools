#!/usr/bin/env python3
import json
from dbsearch import find_interesting_records, query_match
from updatedb import get_state, find_all_addresses
from collections import defaultdict
from tfe_tools.common import get_requests_session, get_attr, filter_type
import os

def main(terraform_org, terraform_url, resource_type, attrs, base_dir="./reports/statedb/*.json"):
    data, _ = find_interesting_records(None, None, resource_type, None, base_dir=base_dir)
    workspaces = defaultdict(list)
    statefiles = defaultdict(list)
    url = "https://{0}/api/v2/state-versions".format(terraform_url)
    if not type(attrs) == type(list()):
        attrs = [attrs]
    for record in data:
        workspaces[record.get('workspace')].append(record.get('tf_address'))
    tfe_session = get_requests_session()
    for workspace in list(workspaces.keys()):
        if os.environ.get("TFE_TOOLS_DEBUG"):
            print(f"getting state for workspace: {workspace}")
        state = get_state(url, tfe_session, terraform_org, workspace)
        try:
            for instance in filter_type(state, resource_type):
                instance_dict = dict()
                for attr in attrs:
                    attr_value = get_attr(instance, attr)
                    if os.environ.get("TFE_TOOLS_DEBUG"):
                        print("\t", attr, attr_value)
                    instance_dict[attr] = attr_value
                statefiles[workspace].append(instance_dict)
        except:
            pass
    return statefiles

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("--org", dest="terraform_org", default="clover")
    p.add_option("--url", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("--type",dest="resource_type")
    p.add_option("--attr", action="append")
    p.add_option("--output", default=os.path.join(os.path.dirname(__file__), "reports/resources"))
    opt, args = p.parse_args()
    data = main(opt.terraform_org, opt.terraform_url, opt.resource_type, opt.attr)
    workspace_dict = defaultdict(lambda: defaultdict(list))
    for k, v in data.items():
        for resource in v:
            for attr in resource.keys():
                if resource.get(attr) not in workspace_dict[k][attr]:
                    workspace_dict[k][attr].append(resource.get(attr))
    
    with open(os.path.join(opt.output, f"{opt.resource_type}.json"), 'w') as output:
        output.write(
            json.dumps(
                workspace_dict,
                separators=(',', ':'),
                indent=4,
                sort_keys=True           
            )
        )
