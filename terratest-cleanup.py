#!/usr/bin/env python3
# Imports the Google Cloud client library
from google.cloud import storage
import os
import json
from collections import defaultdict
import shutil
import git
from github import Github

def clone(repo, base_dir):
    print(f"clonging {repo.name} into {base_dir}")
    if os.path.isdir(os.path.join(base_dir, repo.name)):
        shutil.rmtree(os.path.join(base_dir, repo.name))
        os.makedirs(os.path.join(base_dir, repo.name))
        
    git.Repo.clone_from(
        repo.ssh_url,
        os.path.join(base_dir, repo.name), 
        branch=repo.default_branch
    )

def main(bucket_name, base_dir, github_base, git_org, module):
    # Instantiates a client
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    tests = defaultdict(list)
    g = Github(
        os.environ.get("GITHUB_USER"), 
        os.environ.get("GITHUB_TOKEN"), 
        base_url="{0}/api/v3".format(github_base)
    )
    if not os.path.isdir(base_dir):
        os.makedirs(base_dir)

    for blob in bucket.list_blobs():
        if module and not blob.name.startswith(module):
            continue
        module_name = blob.name.split("/")[0]
        test_name = blob.name.split("/")[-2]
        tests[module_name].append(test_name)

    for module_name in tests.keys():
        repo = g.get_repo(os.path.join(git_org, module_name))
        clone(repo, base_dir)
        for test in tests.get(module_name):
            os.chdir(f"{base_dir}/{module_name}/examples/{test}")
            # os.system("terraform init")
            # os.system("terraform destroy")

    # print(
    #     json.dumps(
    #         tests,
    #         separators=(',', ':'),
    #         indent=4,
    #         sort_keys=True
    #     )
    # )

if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.add_option("--bucket", default="clover-terratest-state")
    p.add_option("-b", dest='base_dir', default=os.path.join(os.getcwd(), "terratest_statefiles"))
    p.add_option("-g", default="https://github.corp.clover.com", dest="github_base")
    p.add_option("-o", default="clover", dest="git_org")
    p.add_option("--module")
    opt, args = p.parse_args()
    main(opt.bucket, opt.base_dir, opt.github_base, opt.git_org, opt.module)
