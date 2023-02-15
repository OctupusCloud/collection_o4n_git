#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

DOCUMENTATION = """
---
module: o4n_git_import
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
    state:
        description:
            set or unset git remote
        required: True
    origin:
        description:
            the origin
        required: False
        default: origin
    branch:
        description:
            branch to be used
        required: True
        default: M
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
        state: present
        origin: origin
        branch: main
        remote: git@github.com:repository.git
        path: /src/path
      register: salida

  - name: Delete git remote
     o4n_git_set_remote:
        state: absent
        remote: git@github.com:repository.git
        path: /src/path
    register: salida
"""

import os
from ansible.module_utils.basic import AnsibleModule
import subprocess


def import_from_repo_token(_repo, _token, _path_clone):
    _repo_name = _repo.replace("https://","")
    cmd_git = f"git clone https://{_token}@{_repo_name} {_path_clone}"
    cmd_list = cmd_git.split()
    result = subprocess.run(cmd_list, text=True, capture_output=True)
    result_code = result.returncode
    error_list = result.stderr.split("\n")
    value = ""
    if len(error_list) > 0:
        remote = [ele for ele in error_list if "remote" in ele]
        fatal = [ele for ele in error_list if "fatal" in ele]
        if len(remote) > 0:
            remote_list = remote[0].split(":")
            if len(remote_list) == 2:
                value = remote_list[1].strip()
        if len(fatal):
            fatal_list = fatal[0].split(":")
            if len(fatal_list) == 2:
                value = fatal_list[1].strip()
    if result_code == 0:
        success = True
        msg_ret = f"Repo <{_repo_name}> cloned to path <{_path_clone}>"
    else:
        success = False
        msg_ret = f"Error cloning repo <{_repo_name}>. Error: <{value}>"
    return success, msg_ret


def cp_content(_path_clone, _path_import, _content):
    cmd_cp = f"cp -R {_path_clone}/{_content} {_path_import}"
    result = subprocess.run(cmd_cp, text=True, capture_output=True, shell=True)
    result_code = result.returncode
    error_list = result.stderr.split("\n")
    value = ""
    if len(error_list) > 0:
        remote = [ele for ele in error_list if "remote" in ele]
        fatal = [ele for ele in error_list if "fatal" in ele]
        if len(remote) > 0:
            remote_list = remote[0].split(":")
            if len(remote_list) == 2:
                value = remote_list[1].strip()
        else:
            value = result.stderr.strip()
        if len(fatal):
            fatal_list = fatal[0].split(":")
            if len(fatal_list) == 2:
                value = fatal_list[1].strip()
    if result_code == 0:
        success = True
        msg_ret = f"Content <{_path_clone}/{_content}> imported to <{_path_import}>"
    else:
        success = False
        msg_ret = f"Error importing content <{_path_clone}/{_content}> to <{_path_import}> . Error: <{value}>"
    return success, msg_ret


def rm_clone(_path_clone):
    cmd_rm = f"rm -rf {_path_clone}"
    cmd_list = cmd_rm.split()
    result = subprocess.run(cmd_list, text=True, capture_output=True)
    result_code = result.returncode
    error_list = result.stderr.split("\n")
    value = ""
    if len(error_list) > 0:
        remote = [ele for ele in error_list if "remote" in ele]
        fatal = [ele for ele in error_list if "fatal" in ele]
        if len(remote) > 0:
            remote_list = remote[0].split(":")
            if len(remote_list) == 2:
                value = remote_list[1].strip()
        else:
            value = result.stderr.strip()
        if len(fatal):
            fatal_list = fatal[0].split(":")
            if len(fatal_list) == 2:
                value = fatal_list[1].strip()
    if result_code == 0:
        success = True
        msg_ret = f"Cloned content <{_path_clone}> removed"
    else:
        success = False
        msg_ret = f"Error removing cloned content <{_path_clone}. Error: <{value}>"
    return success, msg_ret
    

def main():
    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True, type='str'),
            repo=dict(required=True, type='str'),
            path_clone=dict(required=True, type='str'),
            path_import=dict(required=True, type='str'),
            content=dict(required=False, type='str', default='*.*')
        )
    )

    token = module.params.get("token")
    repo = module.params.get("repo")
    path_clone = module.params.get("path_clone")
    path_import = module.params.get("path_import")
    content = module.params.get("content")

    ret_msg = {}
    success_clone, msg_clone = import_from_repo_token(repo, token, path_clone)
    ret_msg['clone'] = msg_clone
    if success_clone:
        success_cp, msg = cp_content(path_clone, path_import, content)
        ret_msg['import'] = msg
        success, msg = rm_clone(path_clone)
        ret_msg['remove'] = msg

    if success_clone and success_cp and success:
        module.exit_json(failed=False, msg=ret_msg)
    else:
        module.fail_json(failed=True, msg=ret_msg)

if __name__ == "__main__":
    main()