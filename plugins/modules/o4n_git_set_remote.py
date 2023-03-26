#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

DOCUMENTATION = """
---
module: o4n_git_set_remote
version_added: "2.0"
author: "Ed Scrimaglia"
short_description: set git branch and it remote in a directory
description:
    - Detect if already exists a remote git linked to the directory
    - Set the origin/remote link
    - Set the main branch
notes:
    - Testeado en linux
options:
    origin:
        description:
            the origin
        required: False
        default: origin
    branch:
        description:
            branch to be used
        required: True
    remote:
        description:
            repository to be set as remote by git
        required: True
    path:
        description:
            directory where to set the remote
        required: False
        default: ./
"""

EXAMPLES = """
tasks:
  - name: Set remote
      o4n_git_set_remote:
        origin: origin
        branch: main
        remote: git@github.com:repository.git
        path: /src/path
      register: salida
"""

# Python Modules
import os
from ansible.module_utils.basic import AnsibleModule


def set_remote(_path, _origin, _remote_repo, _branch):
    try:
        os.chdir(_path)
        set_remote_command = f"git remote remove {_origin}"
        os.system(set_remote_command)
        os.system("git init")
        os.system("git config user.name 'oction automation'")
        os.system("git config user.email 'oction@octupus.com'")
        set_branch_command = f"git branch -M {_branch}"
        os.system(set_branch_command)
        set_remote_command = f"git remote add {_origin} {_remote_repo}"
        os.system(set_remote_command)
        msg = f"Remote {_remote_repo} set successfully, branch {_branch}"
        success = True
    except Exception as error:
        success = False
        msg = f"Remote can not be set, error: {error}"

    return msg, success


# Main
def main():
    Output = {}
    module = AnsibleModule(
        argument_spec=dict(
            origin=dict(required=False, type='str', default='origin'),
            branch=dict(required=False, type='str', default='main'),
            remote=dict(required=True, type='str'),
            path=dict(required=False, type='str', default='./')
        )
    )

    origin = module.params.get("origin")
    branch = module.params.get("branch")
    remote = module.params.get("remote")
    path = module.params.get("path")

# Lógica del modulo
    msg_remote, success = set_remote(path, origin, remote, branch)
    Output['state'] = 'present'
    Output['msg'] = msg_remote
    Output['remote'] = remote

# Retorno del módulo
    if success:
        module.exit_json(failed=False, msg="success", content=Output)
    else:
        module.fail_json(failed=True, msg="fail", content=Output)


if __name__ == "__main__":
    main()
