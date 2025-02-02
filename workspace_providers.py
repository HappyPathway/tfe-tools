#!/usr/bin/env python3
import os
import json
import sys
import hcl2
from glob import glob
import subprocess
from tempfile import mkdtemp
import shutil
from github import Github
from github.GithubException import UnknownObjectException as gheUnknownObjectException
from tfe.core.organization import Organization
from tfe.core import session
from helpers import tfe_token

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

def terraform_config():
    for tf_path in glob("*.tf"):
        with open(tf_path) as tf_file:
            tf_data = hcl2.loads(tf_file.read())
            print(tf_path, tf_data.keys())
            if 'terraform' in tf_data.keys():
                return tf_data.get('terraform')
            else:
                continue
    return None

def provider_config():
    providers = list()
    for tf_path in glob("*.tf"):
        with open(tf_path) as tf_file:
            tf_data = hcl2.loads(tf_file.read())
            print(tf_path, tf_data.keys())
            if 'provider' in tf_data.keys():
                providers.append(tf_data.get('provider'))
            else:
                continue
    return providers

def tf_init():
    subprocess.check_call("terraform init", shell=True)

def tf_validate():
    subprocess.check_call("terraform validate", shell=True)

def tf_env():
    subprocess.check_call("/usr/local/bin/tfenv install min-required")
    subprocess.check_call("/usr/local/bin/tfenv use min-required")

def dump(data, path):
    with open(path, "w") as output:
        output.write(
            json.dumps(
                data,
                separators=(',', ':'),
                indent=4,
                sort_keys=True
            )
        )

def get_providers(path):
    providers = list()
    with open(os.path.join(path, ".terraform.lock.hcl"), "r") as tf_lock:
        data = hcl2.loads(tf_lock.read())
    for provider in data.get('provider'):
        provider_path = list(provider.keys())[0]
        provider_version = provider.get(provider_path).get('version')
        providers.append(
            dict(
                version=provider_version,
                path=provider_path
            )
        )
    return providers

def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path
 
def clone(repo_clone_url):
    p = subprocess.Popen(
        "git clone {0}".format(repo_clone_url),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    if p.returncode > 0:
        raise GitException("Could not clone {0}".format(repo_clone_url))


def dependencies():
    dependencies = list()
    for tf_file_name in glob("./*.tf"):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('module'):
                    for module in hcl_data.get('module'):
                        source = list(module.values())[0].get('source')[0]
                        version = list(module.values())[0].get('version')[0]
                        version_info = dict(source=source, version=version)
                        if version_info not in dependencies:
                            dependencies.append(
                                dict(
                                    filename=os.path.basename(tf_file_name), 
                                    versions=version_info
                                )
                            )
            except:
                continue
    return dependencies


def main(terraform_url, terraform_org, github_base, basedir, git_namespace):
    if not os.path.isdir(basedir):
        os.makedirs(basedir)

    g = Github(
        os.environ.get("GITHUB_USER"), 
        os.environ.get("GITHUB_TOKEN"), 
        base_url="{0}/api/v3".format(github_base)
    )

    tkn = tfe_token(terraform_url, 
        os.path.join(
            os.environ.get("HOME"), 
            ".terraformrc"
        )
    )
    session.TFESession("https://{0}".format(terraform_url), tkn)
    org = Organization(terraform_org)
    ws = org.workspaces()
    tf_providers = dict()
    tf_configs = dict()
    failed_configs = list()
    failed_prov = list()
    for x in sorted(ws, key=lambda ws: ws.name):
        ws_name = x.name
        os.chdir(basedir)
        print(ws_name)
        try:
            repo = g.get_repo(x.vcs_repo.get('identifier'))
        except AttributeError:
            continue
        except gheUnknownObjectException:
            continue
        try:
            clone(repo.ssh_url)
        except GitException:
            continue
        except gheUnknownObjectException:
            continue
        os.chdir(
            os.path.join(
                basedir,
                x.vcs_repo.get('identifier').replace("{0}/".format(git_namespace), "")
            )
        )
        print(os.getcwd())
        try:
            cfg = terraform_config()
        except:
            failed_configs.append(ws_name)
        if cfg:
            tf_configs[ws_name] = cfg
        try:
            prov = provider_config()
        except:
            failed_prov.append(ws_name)
        if prov:
            tf_providers[ws_name] = prov

    dump(
        tf_configs,
        os.path.join(os.path.dirname(__file__), "./reports/ws_providers_tf_configs.json")
    )

    dump(
        failed_configs,
        os.path.join(os.path.dirname(__file__), "./reports/ws_providers_failed_configs.json")
    )

    dump(
        tf_providers,
        os.path.join(os.path.dirname(__file__), "./reports/ws_providers.json")
    )

    dump(
        failed_prov,
        os.path.join(os.path.dirname(__file__), "./reports/ws_providers_failed_prov.json")
    )

    shutil.rmtree(basedir)

if __name__ == "__main__":
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-t", dest="terraform_url", default="terraform.corp.clover.com")
    p.add_option("-o", dest="terraform_org", default="clover")
    p.add_option("-g", dest="github_base",   default="https://github.corp.clover.com")
    p.add_option("-n", dest="git_namespace", default="clover")
    p.add_option("-b", dest='base_dir',      default=os.path.join(os.getcwd(), "workspaces"))
    opt, arg = p.parse_args()
    main(opt.terraform_url, opt.terraform_org, opt.github_base, opt.base_dir, opt.git_namespace)
    

'''
for ws in d:
    for _provider in d.get(ws):
        for provider in _provider:
            if 'google' in provider or 'google-beta' in provider:
                if 'version' in provider.get('google', provider.get('google-beta')):
                    print(ws, list(provider.keys())[0],  provider.get('google', provider.get('google-beta')).get('version'))
'''