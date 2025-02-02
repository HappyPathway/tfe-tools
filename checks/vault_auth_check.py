#!/usr/bin/evn python3
import requests

def vault_auth_check(token, policy):
    headers = {
        "X-Vault-Token": token,
        "X-Vault-Namepsace": "terraform"
    }
    resp = requests.get(
        "https://vault-usprod01.prod.dsm01.clover.network:8200/v1/auth/token/lookup-self",
        headers=headers,
        verify=False
    ).json()
    print(resp)
    policies = resp.get('data').get('policies')
    if policy in policies:
        return dict(access_ok=True, policies=policies)
    else:
        return dict(access_ok=False, policies=policies)
    
if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--token")
    parser.add_option("--policy")
    opt, arg = parser.parse_args()
    print(vault_auth_check(opt.token, opt.policy))