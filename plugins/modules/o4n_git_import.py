#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

DOCUMENTATION = """
---
module: o4n_git_import
version_added: "2.0"
author: "Ed Scrimaglia"
short_description: import some files from a repository to a local path
description:
    - clone a git repository
    - select files from cloned content
    - copy files to a local path
    - remove clone content
notes:
    - Testeado en linux
options:
    token:
        description:
            repository access token
        required: True
    repo:
        description:
            repository url to be cloned
        required: True
    path_clone:
        description:
            path where the repository will be cloned
        required: True
    path_import:
        description:
            path where cloned repository (path_cloned) content will copied
        required: True
    content:
        description:
            files selection to be copied to path_import
        required: False
        default: "*.*"
"""

EXAMPLES = """
tasks:
  - name: Import Repo
      o4n_git_import:
        token: "{{ token }}"
        repo: origin
        path_clone: "./temp"
        path_import: "../files
        content: "Docu*"
      register: salida

  - name: Import Repo
      o4n_git_import:
        token: "{{ token }}"
        repo: origin
        path_clone: "./temp"
        path_import: "../files
      register: salida
"""

from ansible.module_utils.basic import AnsibleModule
import subprocess
import glob


def import_from_repo_token(_repo, _token, _path_clone):
    _repo_name = _repo.replace("https://", "")
    cmd_git = f"git clone https://{_token}@{_repo_name} {_path_clone}"
    cmd_list = cmd_git.split()
    result = subprocess.run(cmd_list, text=True, capture_output=True)
    result_code = result.returncode
    error_list = result.stderr.split("\n")
    value = ""
    if len(error_list) > 0:
        remote = [ele for ele in error_list if "remote" in ele]
        if len(remote) > 0:
            remote_list = remote[0].split(":")
            if len(remote_list) == 2:
                value = remote_list[1].strip()
        else:
            fatal = [ele for ele in error_list if "fatal" in ele]
            if len(fatal) > 0:
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
    result = subprocess.run(['cp', '-r'] + glob.glob(_path_clone+"/"+_content) + [_path_import], text=True, capture_output=True)
    result_code = result.returncode
    value = "source file does not exist"
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
        if len(remote) > 0:
            remote_list = remote[0].split(":")
            if len(remote_list) == 2:
                value = remote_list[1].strip()
        else:
            value = result.stderr.strip()
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
    