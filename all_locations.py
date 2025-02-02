import subprocess
import json
import os
from collections import defaultdict
import copy

def find_mod_source(source):
    script = "find_all_mods.py"
    inputfile = "reports/tf_mods.json"
    cmd = "python3 {0}/utils/{1} {2} {3}"
    inputfile = os.path.join(os.path.dirname(__file__), inputfile)
    cmd = cmd.format(os.path.dirname(__file__), script, source, inputfile)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return json.loads(str(out.decode('utf-8')))

def find_ws_source(source):
    script = "find_all_ws.py"
    inputfile = "reports/tf_ws_mods.json"
    cmd = "python3 {0}/utils/{1} {2} {3}"
    inputfile = os.path.join(os.path.dirname(__file__), inputfile)
    cmd = cmd.format(os.path.dirname(__file__), script, source, inputfile)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return json.loads(str(out.decode('utf-8')))

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
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-s", "--source")
    p.add_option("-m", "--modules", default=False, action="store_true")
    p.add_option("-w", "--workspaces", default=False, action="store_true")
    opt, args = p.parse_args()

    main(opt.source, opt.modules, opt.workspaces)
