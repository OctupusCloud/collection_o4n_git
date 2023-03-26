#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

DOCUMENTATION = """
---
module: o4n_git_acp
version_added: "2.0"
author: "Ed Scrimaglia"
short_description: push content to a Git repository
description:
    - Add files for trucking
    - Commit
    - Push content
notes:
    - Testeado en linux
options:
    origin:
        description:
            the origin name in the URL set in Git remote
        required: True
    branch:
        description:
            the branch name to be pushed
        required: False
        default: main
    files:
        description:
            files to be tracked by Git
        required: False
        default: "."
    force:
        description:
            define if push will be forced
        required: False
        default: False
    path:
        description:
            path where add, commit and push must be applied
        required: True
    remote:
        description:
            repository to be set as remote by git remote add
        required: True

"""

EXAMPLES = """
tasks:
  - name: Set remote
      o4n_git_acp:
        origin: origin
        remote: git@github.com:repository.git
        branch: main
        path: "./"
        files: "*.txt"
        comment: Refactoring
        force: true
      register: salida
"""

# Python Modules
import os
import subprocess
import re
from ansible.module_utils.basic import AnsibleModule

# Global Var
output = {}


# Methods
def get_current_dir():
    global output
    success = False
    try:
        current_dir = os.getcwd()
        success = True
        directory = current_dir
    except Exception:
        directory = "unknown"

    return success, directory


def set_remote(_path, _origin, _remote_repo, _branch):
    global output
    success = False
    working_path = ""
    _path = re.sub(r"^\.", "", _path)
    _path = re.sub(r"^\/", "", _path)
    try:
        success_dir, working_dir = get_current_dir()
        if success_dir:
            working_path = working_dir + "/" + _path
            output['directory'] = working_path
            os.chdir(working_path)
            set_remote_command = f"git remote remove {_origin}"
            os.system(set_remote_command)
            os.system("git init")
            os.system("git config user.name 'oction automation'")
            os.system("git config user.email 'oction@octupus.com'")
            set_branch_command = f"git branch -M {_branch}"
            os.system(set_branch_command)
            set_remote_command = f"git remote add {_origin} {_remote_repo}"
            os.system(set_remote_command)
            output['remote'] = f"Remote {_remote_repo} set successfully as {_origin}, branch {_branch}"
            success = True
    except Exception as error:
        output['remote'] = f"Remote {_remote_repo} can not be set, error: {error}"

    return output, working_path, success


def git_acp(_origin, _branch, _comment, _files, _force, _path):
    global output
    try:
        os.chdir(_path)
        # git add
        set_command = f"git add {_files}"
        cmd_list = set_command.split()
        result = subprocess.run(cmd_list, text=True, capture_output=True)
        if result.stdout:
            std_out = result.stdout.replace("\n", " ")
            output['add'] = f"{std_out}"
        elif result.stderr:
            std_err = result.stderr.replace("\n", " ")
            output['add'] = f"{std_err}"
        else:
            output['add'] = f"files {_files} tracked"

        # git commit
        set_command = "git commit -m"
        # os.system(set_command)
        cmd_list = set_command.split()
        cmd_list.append(_comment)
        result = subprocess.run(cmd_list, text=True, capture_output=True)
        if result.stdout:
            std_out = result.stdout.replace("\n", " ")
            output['commit'] = f"{std_out}"
        elif result.stderr:
            std_err = result.stderr.replace("\n", " ")
            output['commit'] = f"{std_err}"
        else:
            pass

        # git push
        force = "--force" if _force else ""
        set_command = f"git push {force} {_origin} {_branch}"
        output['force'] = force
        cmd_list = set_command.split()
        result = subprocess.run(cmd_list, text=True, capture_output=True)
        if result.stdout:
            std_out = result.stdout.replace("\n", " ")
            output['push'] = f"{std_out}"
        elif result.stderr:
            std_err = result.stderr.replace("\n", " ")
            output['push'] = f"{std_err}"
        else:
            pass

        # Delete remote settings
        # set_command = f"git remote remove {_origin}"
        # cmd_list = set_command.split()
        # result = subprocess.run(cmd_list, text=True, capture_output=True)
        # if result.stdout:
        #     std_out = result.stdout.replace("\n", " ")
        #     output['remove'] = f"{std_out}"
        # elif result.stderr:
        #     std_err = result.stderr.replace("\n", " ")
        #     output['remove'] = f"{std_err}"
        # else:
        #     output['remove'] = f"Origin {_origin} removed from git remote"

        success = True

    except Exception as error:
        success = False
        output = {"push": f"Pushing branch {_branch} to {_origin} has failed. Error {error}"}

    return output, success


# Main
def main():
    module = AnsibleModule(
        argument_spec=dict(
            origin=dict(required=True, type='str'),
            remote=dict(required=True, type='str'),
            branch=dict(required=False, type='str', default='main'),
            files=dict(required=False, type='str', default='.'),
            comment=dict(required=False, type='str', default='new commit'),
            force=dict(required=False, type='str', default='present'),
            path=dict(required=True, type='str')
        )
    )

    origin = module.params.get("origin")
    remote = module.params.get("remote")
    branch = module.params.get("branch")
    files = module.params.get("files")
    comment = module.params.get("comment")
    force = module.params.get("force")
    path = module.params.get("path")

    # Lógica del modulo
    output, working_path, success = set_remote(path, origin, remote, branch)
    if success:
        force = "--force" if force.lower() in ["present"] else ""
        output, success = git_acp(origin, branch, comment, files, force, working_path)

    # Retorno del módulo
    if success:
        module.exit_json(failed=False, msg="success", content=output)
    else:
        module.fail_json(failed=True, msg="fail", content=output)


if __name__ == "__main__":
    main()
