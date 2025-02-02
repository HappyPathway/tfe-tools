#!/usr/bin/env python3
import json
from collections import defaultdict

with open("./reports/tf_ws_mods.json") as mods:
    mod_data = json.loads(mods.read())

mod_used_count = defaultdict(int)
  
ws_dependencies = dict()
for ws in mod_data:
    ws_mods = set()
    for mod in mod_data.get(ws):
        url_parts = mod.get('versions').get('source').split('/')
        mod_name = "terraform-{0}-{1}".format(url_parts[-1], url_parts[-2])
        ws_mods.add(mod_name)
    ws_dependencies[ws] = list(ws_mods)
    for mod in ws_mods:
        mod_used_count[mod] += 1

with open("./reports/workspace_module_dependencies.json", "w") as output:
    output.write(
        json.dumps(
            ws_dependencies,
            separators=(',', ':'),
            indent=4,
            sort_keys=True
        )
    )