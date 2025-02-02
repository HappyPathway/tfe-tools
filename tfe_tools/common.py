import subprocess
import json
import os
from collections import defaultdict
import copy
import sys
import hcl2
from glob import glob
from requests import Session

class TFEException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path

def tfe_token(tfe_api, config):
    if os.environ.get("TFE_TOKEN"):
        return os.environ.get("TFE_TOKEN")
    elif os.path.isfile(sanitize_path(config)):
        with open(sanitize_path(config), 'r') as fp:
            obj = hcl2.load(fp)
        return obj.get('credentials')[0].get(tfe_api).get('token')
    elif sanitize_path("${HOME}/.terraform.d/credentials.tfrc.json"):
        with open(sanitize_path("${HOME}/.terraform.d/credentials.tfrc.json"), 'r') as fp:
            d = json.loads(fp.read())
            return d.get('credentials').get(tfe_api).get('token')
    else:
        raise TFEException("Could not find credentials file")

def get_requests_session(terraform_url="terraform.corp.clover.com"):
    tkn = tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )
    tfe_session = Session()
    tfe_session.headers = {
        "Authorization": "Bearer {0}".format(tkn), 
        "Content-Type": "application/vnd.api+json"
    }
    return tfe_session

def mod_dependencies(mod_name, config=False):
    dependencies = dict()
    for tf_file_name in glob("*.tf"):
        with open(tf_file_name, 'r') as tf_file:
            d = hcl2.loads(tf_file.read())
            if not d.get('module'):
                continue
            for module in d.get('module'):
                module_key = list(module.keys())[0]
                if not config:
                    module_source = module.get(module_key).get('source')
                    dependencies[module_key] = module_source
                else:
                    dependencies[module_key] = module.get(module_key)
    return dependencies

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

def get_latest_versions():
    d = json.loads(open(os.path.expandvars(os.path.join(os.path.dirname(__file__), "./reports/mod_versions.json"))).read())
    modules = dict()
    for module in d:
        modules[d.get(module).get('source')] = d.get(module).get('latest_version')
    return modules

def get_data(cmp):
    with open(os.path.join(os.getcwd(), f"reports/environments/{cmp}.json")) as cmp_a_data:
        cmp_data_json = json.loads(cmp_a_data.read())
    
    cmp_data = dict()
    cmp_data['embedded_modules'] = list()
    cmp_data['resources'] = list()
    cmp_data['top_level_modules'] = list()
    for project_type in cmp_data_json:
        for workspace in cmp_data_json.get(project_type):
            cmp_data['embedded_modules'].extend(workspace.get('embedded_modules'))
            cmp_data['resources'].extend(workspace.get('resources'))
            cmp_data['top_level_modules'].extend(workspace.get('top_level_modules'))
    return cmp_data

def find_interesting_records(key, value, resource_type, workspaces=[], base_dir="./reports/statedb/*.json"):
    interest = defaultdict(dict)
    statefiles = list()
    if not workspaces:
        for x in glob.glob(base_dir):
            statefiles.append(x)
    else:
        for workspace in workspaces:
            for x in glob.glob("./reports/statedb/{0}.json".format(workspace)):
                statefiles.append(x)
    
    results = list()
    for x in sorted(statefiles):
        with open(x) as state:
            data = json.loads(state.read())
        interest[data.get("repo")]['addresses'] = list()
        interest[data.get("repo")]['workspace'] = data.get('workspace')
        interest[data.get("repo")]['terraform_version'] = data.get('terraform_version')
        interest[data.get('repo')]['repo'] = data.get("repo")
        for rsc in data.get('resources'):
            if not rsc.get('rsc_id'):
                continue
            if query_match(rsc, key, value, resource_type):
                results.append(
                    dict(
                        workspace=data.get('workspace'),
                        resource_id=rsc.get('rsc_id'),
                        tf_address=rsc.get('tf_address'),
                        resource_type=rsc.get("resource_type")
                    )
                )
                interest[data.get("repo")]['addresses'].append(rsc.get('tf_address'))
    return results, [interest.get(repo_name) for repo_name in interest if interest.get(repo_name).get('addresses')]

def query_match(rsc, key, value, resource_type):
    if rsc.get('resource_type') != resource_type:
        return False
    if rsc.get(key) != value:
        return False
    return True

def get_attr(instance, attr):
    return getattr(instance, attr, None)

def filter_type(instances, instance_type):
    return [instance for instance in instances if isinstance(instance, instance_type)]

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
