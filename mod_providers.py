import os
import hcl2
import subprocess
import sys
import shutil
import json
from glob import glob
from tempfile import mkdtemp
from tfe.core.organization import Organization
from tfe.core import session
from tfe.core.registry_module import RegistryModule
from github import Github
from collections import defaultdict
from github.GithubException import UnknownObjectException
from functools import partial

class GitException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


def defined_variables():
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        with open(tf_file_name, 'r') as tf_file:
            try:
                hcl_data = hcl2.loads(tf_file.read())
                if hcl_data.get('variable'):
                    for var in hcl_data.get('variable'):
                        var_name = list(var.keys())[0]
                        yield dict(var=var_name, meta=var.get(var_name))
            except:
                continue


def check_variable(var_name):
    for tf_file_name in glob(os.path.join(os.getcwd(), "./*.tf")):
        # if tf_file_name.endswith("variables.tf"):
        #     continue
        with open(tf_file_name, 'r') as tf_file:
            if f"var.{var_name}" in tf_file.read():
                return True
    return False

def get_unused_vars():
    unused_vars = list()
    for var in defined_variables():
        var_name = var.get('var')
        if not check_variable(var_name):
            unused_vars.append(var_name)
    return unused_vars

def tf_init():
    subprocess.check_call("terraform init", shell=True)

def tf_validate():
    subprocess.check_call("terraform validate", shell=True)

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

def terraform_config(path):
    for tf_path in glob("*.tf"):
        with open(tf_path) as tf_file:
            tf_data = hcl2.loads(tf_file.read())
            print(tf_path, tf_data.keys())
            if 'terraform' in tf_data.keys():
                return tf_data.get('terraform')
            else:
                continue
    return None


#############################
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

##############################
def tfe_token(tfe_api, config):
    with open(sanitize_path(config), 'r') as fp:
        obj = hcl2.load(fp)
    return obj.get('credentials')[0].get(tfe_api).get('token')


def sanitize_path(config):
    path = os.path.expanduser(config)
    path = os.path.expandvars(path)
    path = os.path.abspath(path)
    return path


def modlist(rm, mods, list_url):
    rm_list = rm.list(list_url)
    for mod in rm_list.get('modules'):
        mods.append(mod)
    if rm_list.get('meta').get('next_url'):
        url_prefix = rm.list_url
        url = "{0}?offset={1}".format(url_prefix, rm_list.get('meta').get('next_offset'))
        modlist(rm, mods, url)
    return mods


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
    
def pull_commit(commit):
    p = subprocess.Popen(
        "git checkout {0}".format(commit.sha),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = p.communicate()
    if p.returncode > 0:
        raise GitException("Could not pull {0}.\n\t{1}".format(commit.sha, err.decode("utf-8")))
    

def main(github_base, terraform_base, terraform_url, base_dir, cleanup):
    g = Github(
        os.environ.get("GITHUB_USER"), 
        os.environ.get("GITHUB_TOKEN"), 
        base_url="{0}/api/v3".format(github_base)
    )

    tkn = tfe_token(terraform_url, 
        "{0}/.terraformrc".format(
            os.environ.get("HOME")
        )
    )

    session.TFESession(terraform_base, tkn)
    Organization("clover")
    rm = RegistryModule()
    tf_mods = modlist(rm, [], rm.list_url)
    mod_providers = dict()
    failed_init = list()
    failed_validate = list()
    tf_configs = dict()
    unused_mod_vars = dict()
    # repo_tags = defaultdict(list)
    os.chdir(base_dir)

    for mod in sorted(tf_mods, key=lambda x: "terraform-{0}-{1}".format(x.get('provider'), x.get('name'))):
        os.chdir(base_dir)
        repo_name = mod.get('source').replace(
            "{0}/".format(github_base), 
            ''
        )
        mod_name = "terraform-{0}-{1}".format(mod.get('provider'), mod.get('name'))
        print("Scanning {0}".format(mod_name))
        try:
            repo = g.get_repo(repo_name)
            try:
                clone(repo.ssh_url)
            except GitException:
                sys.stderr.write(
                    GitException.msg
                )
                continue
            os.chdir(
                os.path.join(
                    base_dir,
                    mod_name
                )
            )
            try:
                tf_init()
            except:
                failed_init.append(mod_name)

            try:
                tf_validate()
            except:
                failed_validate.append(mod_name)

            try:
                providers = get_providers(
                    os.path.join(
                        base_dir,
                        mod_name
                    )
                )
            except FileNotFoundError:
                failed_init.append(mod_name)
            
            try:
                cfg = terraform_config(
                    os.path.join(
                        base_dir,
                        mod_name
                    )
                )
                if cfg:
                    tf_configs[mod_name] = cfg
            except:
                pass
            unused_vars = get_unused_vars()
            if len(unused_vars):
                unused_mod_vars[mod_name] = unused_vars
            mod_providers[mod_name] = providers

        except UnknownObjectException:
            print(repo_name)
    
    if cleanup:
        shutil.rmtree(base_dir)

    dump(
        mod_providers,
        os.path.join(os.path.dirname(__file__), "./reports/mod_providers.json")
    )

    dump(
        list(set(failed_init)),
        os.path.join(os.path.dirname(__file__), "./reports/mod_providers_failed_init.json")
    )
    
    dump(
        list(set(failed_validate)),
        os.path.join(os.path.dirname(__file__), "./reports/mod_providers_failed_validate.json")
    )
    
    dump(
        tf_configs,
        os.path.join(os.path.dirname(__file__), "./reports/mod_providers_tf_configs.json")
    )

    dump(
        unused_mod_vars,
        os.path.join(os.path.dirname(__file__), "./reports/mod_unused_vars.json")
    )

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("-g", default="https://github.corp.clover.com", dest="github_base")
    p.add_option("-t", default="https://terraform.corp.clover.com", dest="terraform_base")
    p.add_option("-u", default="terraform.corp.clover.com", dest="terraform_url")
    p.add_option("-b", dest='base_dir', default=os.path.join(os.getcwd(), "workspaces"))
    p.add_option("-c", dest="cleanup", default=False, action="store_true")
    opt, arg = p.parse_args()
    main(opt.github_base, opt.terraform_base, opt.terraform_url, opt.base_dir, opt.cleanup)