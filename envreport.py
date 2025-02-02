#!/usr/bin/env python3
from google.cloud import firestore

from collections import defaultdict
import os
import json
import hashlib
from tfe_tools.common import sanitize_path, tfe_token, get_requests_session, mod_dependencies
from projects import project_types
class WorkspaceAddrs(object):

    def __init__(self, workspace):
        self.workspace = workspace
        self.mod_addrs = defaultdict(set)
        self.mod_addrs['embedded_modules'] = defaultdict(set)
        with open(os.path.join(os.getcwd(), f"reports/statedb/{workspace}.json")) as workspace_data:
            self._data = json.loads(workspace_data.read())
        
        for x in self._data.get('resources'):
            if not x.get('tf_address').startswith('module'):
                self.mod_addrs['resources'].add(x.get('tf_address'))
                continue
            mods = x.get('tf_address').split("module.")
            if len(mods) <= 2:
                self.mod_addrs['top_level_modules'].add([_x.strip('.') for _x in mods][-1].split('.')[0].split('[')[0])
            if len(mods) > 2:
                top_level_mod = [_x.strip('.') for _x in mods][1]
                sub_level_mod = [_x.strip('.') for _x in mods][2].split('.')[0].split('[')[0]
                self.mod_addrs['embedded_modules'][top_level_mod].add(sub_level_mod)

        self.mod_addrs['repo'] = self._data.get('repo')
        self.mod_addrs['resources'] = self.resources # list(self.mod_addrs['resources'])
        self.mod_addrs['top_level_modules'] = list(self.mod_addrs['top_level_modules'])
        for top_level_mod in self.mod_addrs['embedded_modules']:
            self.mod_addrs['embedded_modules'][top_level_mod] = list(self.mod_addrs['embedded_modules'][top_level_mod])
        self.mod_addrs = dict(self.mod_addrs)

    def __repr__(self):
        return json.dumps(self.mod_addrs, separators=(',', ':'), indent=4, sort_keys=True)
    
    def __str__(self):
        return "{0} => {1}".format(
            self.workspace,
            json.dumps(self.mod_addrs, separators=(',', ':'), indent=4, sort_keys=True)
        )
    
    @property
    def data(self):
        return self.mod_addrs
    
    @property
    def resources(self):
        resources = defaultdict(set)
        for resource in self._data.get('resources'):
            if resource.get('tf_address').startswith('module.'):
                continue
            resources[resource.get('resource_type')].add(resource.get('name'))
        for k, v in resources.items():
            resources[k] = list(v)
        return dict(resources)


    @property
    def modules(self):
        return self.mod_addrs.get('top_level_modules')

    @property
    def embedded_modules(self):
        return self.mod_addrs.get('embedded_modules')

def cmp_projects(db, cmp_projects):
    workspace_data = dict()
    workspaces = set()
    cmp_projects_inverse = dict()
    for k, v in cmp_projects.items():
        cmp_projects_inverse[v] = k
    for project in cmp_projects.values():
        docs = db.collection('service-instances').where('data.project', '==', project).stream()
        for doc in docs:
            data = doc.to_dict()
            workspace_name = data.get('data').get('workspace')
            workspaces.add((project, workspace_name))

    for workspace in workspaces:
        project = workspace[0]
        project_type = cmp_projects_inverse.get(project)
        workspace_name = workspace[1]
        if project_type not in workspace_data:
            workspace_data[project_type] = dict()
        workspace_data[project_type][f"{workspace_name}"] = WorkspaceAddrs(workspace_name).data
    return workspace_data, [workspace[0] for workspace in workspaces]

def main(output, project_type):
    db = firestore.Client(project='example-infra-db')
    output = sanitize_path(output)
    if not os.path.isdir(output):
        os.makedirs(output)
    
    workspace_data, workspaces = cmp_projects(db, project_types.get(project_type))
    with open(os.path.join(output, f"{project_type}-workspaces.json"), "w") as outputfile:
        outputfile.write(
            json.dumps(
                workspaces,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

    with open(os.path.join(output, f"{project_type}.json"), "w") as outputfile:
        outputfile.write(
            json.dumps(
                workspace_data,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )
    # prod_workspace_data = cmp_projects(db, prod_projects)
    # project_types = defaultdict(dict)
    # # we're getting the workspace type and project name for each type of project in nastaging.
    # for k, v in nastaging_projects.items():
    #     # now we're gonna loop over every workspace that is in that gcp project. 
    #     # we're going to just build a flat list of resources.
    #     # we'll use the flat list to compare against the same in prod.
    #     for workspace in nastaging_workspace_data.get(v).values():
    #         project_types


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--output", default=os.path.join(os.getcwd(), "reports/environments"))
    parser.add_option("--project")
    opt, args = parser.parse_args()
    main(opt.output, opt.project)
