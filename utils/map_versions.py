import json
with open("./reports/mod_versions.json") as mod_versions:
    d = json.loads(mod_versions.read())
d
modules = list()
for module in d:
    modules.append(dict(source=module.get('source'), latest_version=module.get('latest_version')))
for module in d:
    modules.append(dict(source=d.get(module).get('source'), latest_version=d.get(module).get('latest_version')))
modules
modules = dict()
for module in d:
    modules[d.get(module).get('source')] = d.get(module).get('latest_version')
modules
with open("./reports/latest_versions.json", "w") as report:
    report.write(
    json.dumps(
    modules,
    separators=(',', ':'),
    indent=4,
    sort_keys=True
    )
    )