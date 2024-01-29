#!/usr/bin/env python3
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

output = {}


def import_from_repo_token(_repo, _token, _path_clone):
    global output
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
        output['clone'] = f"Repo <{_repo_name}> cloned to path <{_path_clone}>"
    else:
        success = False
        output['clone'] = f"Error cloning repo <{_repo_name}>. Error: <{value}>"

    return success, output


def cp_content(_path_clone, _path_import, _content):
    global output
    try:
        subprocess.run(['cp', '-r'] + glob.glob(_path_clone+"/"+_content) + [_path_import], text=True, capture_output=True)
        success = True
        output['import'] = f"Content <{_path_clone}/{_content}> imported to <{_path_import}>"
    except Exception as error:
        success = False
        output['import'] = f"Error importing content <{_path_clone}/{_content}> to <{_path_import}> . Error: <{error}>"

    return success, output


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
        output['remove'] = f"Cloned content <{_path_clone}> removed"
    else:
        success = False
        output['remove'] = f"Error removing cloned content <{_path_clone}. Error: <{value}>"

    return success, output


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

    msg_ret = "Repo has been imported successfully"
    success, output = import_from_repo_token(repo, token, path_clone)
    if success:
        success_cp, output = cp_content(path_clone, path_import, content)
        if not success_cp:
            msg_ret = "No files to import from repo"
        success_rm, output = rm_clone(path_clone)
        if not success_rm:
            msg_ret = "Repo clon has not been removed"
    else:
        msg_ret = "Repo has not been imported"

    if success:
        module.exit_json(failed=False, msg=msg_ret, content=output)
    else:
        module.fail_json(failed=True, msg=msg_ret, content=output)


if __name__ == "__main__":
    main()
