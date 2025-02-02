#!/usr/bin/evn python3
import json
from collections import defaultdict
# gcloud compute shared-vpc associated-projects list clover-vpc-prod
# added clover-usprod
prod_projects = [
    "clover-usprod",
    "clover-ce-prod-database",
    "clover-clover-ds-prod",
    "clover-prod-gfo",
    "clover-prod-databases",
    "clover-prod-apps",
    "clover-prod-kubernetes"
]

with open("./reports/ws_projects.json") as ws_projects:
    ws_projects = json.loads(ws_projects.read())

workspaces = defaultdict(list)
for project in prod_projects:
    for ws in ws_projects:
        if project in ws_projects.get(ws):
            workspaces[ws].append(project)

print(
    json.dumps(
        workspaces,
        separators=(',', ':'),
        indent=4,
        sort_keys=True
    )
)
