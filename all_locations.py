import subprocess
import json
import os
from collections import defaultdict
import copy
from tfe_tools.common import find_mod_source, find_ws_source, sanitize_path, tfe_token, get_requests_session, mod_dependencies

def main(source, dump_modules, dump_workspaces):
    # terraform.corp.clover.com/clover/datacenter_infra/google 
    source_parts = source.split("/")
    calling_modules = find_mod_source(source)
    calling_modules.append("terraform-{0}-{1}".format(source_parts[-1], source_parts[-2]))

    source_tpl = "terraform.corp.clover.com/clover/{0}/{1}"
    workspaces = defaultdict(list)
    workspace_set = set()
    for _mod in calling_modules:
        _mod_parts = _mod.split('-')
        calling_workspaces = find_ws_source(
            source_tpl.format(_mod_parts[-1], _mod_parts[1])
            )
        for workspace in calling_workspaces:
            workspace_set.add(workspace.get('workspace'))
            if workspace.get('workspace') not in workspaces[_mod]:
                workspaces[workspace.get('workspace')].append(_mod)

    workspace_copy = copy.deepcopy(workspaces)
    for k, v in workspace_copy.items():
        if not v:
            workspaces.pop(k)

    if dump_workspaces:
        print(
            json.dumps(
                sorted(list(set(workspaces.keys()))),
                separators=(',',':'),
                indent=4,
                sort_keys=True
            )
        )

    if dump_modules:
        print(
            json.dumps(
                sorted(list(calling_modules)),
                separators=(',',':'),
                indent=4,
                sort_keys=True
            )
        )

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", required=True)
    parser.add_argument("-m", "--modules", action="store_true", default=False)
    parser.add_argument("-w", "--workspaces", action="store_true", default=False)
    args = parser.parse_args()

    main(args.source, args.modules, args.workspaces)
