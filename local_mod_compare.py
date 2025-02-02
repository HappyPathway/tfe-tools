#!/usr/bin/env python3
import hcl2
from glob import glob
import subprocess
from tempfile import mkdtemp
import shutil
from github import Github
from github.GithubException import UnknownObjectException as gheUnknownObjectException
from tfe.core.organization import Organization
from tfe.core import session
import json
import os
import semantic_version
from collections import defaultdict
import re

mod_versions = json.loads(
    open(
        os.path.expandvars(
            os.path.join(os.path.dirname(__file__), "./reports/mod_versions.json")
        )
    ).read())

mod_cache = dict()


def get_latest(mod_source):
    for mod in mod_versions:
        # print(mod, mod_versions.get(mod).get('latest_version'))
        if mod_versions.get(mod).get('source') == mod_source:
            return mod_versions.get(mod).get('latest_version')


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path


def tfe_token(tfe_api, config):
    with open(sanitize_path(config), 'r') as fp:
        obj = hcl2.load(fp)
    return obj.get('credentials')[0].get(tfe_api).get('token')[0]


#############################
def dependencies():
    dependencies = list()
    for tf_file_name in glob("./*.tf"):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('module'):
                    for module in hcl_data.get('module'):
                        mod_name = list(module.keys())[0]
                        source = list(module.values())[0].get('source')[0]
                        version = list(module.values())[0].get('version')[0]
                        version_info = dict(source=source, version=version)
                        if version_info not in dependencies:
                            x = dict(
                                    mod=mod_name,
                                    filename=os.path.basename(tf_file_name), 
                                    versions=version_info
                                )
                            dependencies.append(x)
            except:
                continue
        
    return dependencies


def cmp_version(actual_version_string, latest, mod_version):
    mod_semver = semantic_version.Version(str(mod_version))
    latest_semver = semantic_version.Version(str(latest))
    if '~>' in actual_version_string:
        if len(actual_version_string.split('.')) == 2:
            if mod_semver.major < latest_semver.major:
                return False
            else:
                return True
        if len(actual_version_string.split('.')) == 3:
            if (mod_semver.major < latest_semver.major) or (mod_semver.minor < latest_semver.minor):
                return False
            else:
                return True
    elif mod_semver < latest_semver:
        return False
    elif ">=" in actual_version_string:
        return True
    else:
        return True


def main():
    needs_update = defaultdict(list)
    version_regex = re.compile('(\d+\.)?(\d+\.)?(\*|\d+)$')
    requires_updates = set()
    for dep in dependencies():
        # print(json.dumps(dep, separators=(',',':'), indent=4, sort_keys=True))
        latest = get_latest(dep.get('versions').get('source'))
        mod_source = dep.get('versions').get('source')
        actual_version_string = dep.get('versions').get('version')
        m = version_regex.search(dep.get('versions').get('version'))
        if m:
            mod_version = m.group(0)
            if len(mod_version.split('.')) < 3:
                mod_version = "{0}.0".format(mod_version)
        if not cmp_version(actual_version_string, latest, mod_version):
            print("File: {0}: \n\tMod: module.{1}\n\tSource: {2} \n\tActual: {3} \n\tLatest: {4}\n".format(dep.get('filename'), dep.get('mod'), mod_source, actual_version_string, latest))


if __name__ == '__main__':
    main()