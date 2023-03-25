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
"""

EXAMPLES = """
tasks:
  - name: Set remote
      o4n_git_acp:
        origin: origin
        branch: main
        path: "./"
        files: "*.txt"
        comment: Refactoring
        force: true
      register: salida
"""

# Python Modules
import os
from ansible.module_utils.basic import AnsibleModule


# Methods
def git_acp(_origin, _branch, _comment, _files, _force, _path):
    output = {}
    try:
        os.chdir(_path)
        force_param = "--force" if _force else ""
        set_add_command = f"git add '{_files}'"
        os.system(set_add_command)
        set_commit_command = f"git commit -m '{_comment}'"
        os.system(set_commit_command)
        set_push_command = f"git push {force_param} {_origin} {_branch}"
        os.system(set_push_command)
        success = True
        output = {
            "add": f"Files added for tracking: {_files}",
            "commit": f"Commit -m {_comment}",
            "push": f"Pushing branch {_branch} to {_origin} has been successful"
        }
    except Exception as error:
        success = False
        output = {"push": f"Pushing branch {_branch} to {_origin} has failed. Error {error}"}

    return output, success


# Main
def main():
    Output = {}
    module = AnsibleModule(
        argument_spec=dict(
            origin=dict(required=True, type='str'),
            branch=dict(required=False, type='str', default='main'),
            files=dict(required=False, type='str', default='.'),
            comment=dict(required=False, type='str', default='new commit'),
            force=dict(required=False, type='str', choises=['True', 'False'], default='False'),
            path=dict(required=True, type='str')
        )
    )

    origin = module.params.get("origin")
    branch = module.params.get("branch")
    files = module.params.get("files")
    comment = module.params.get("comment")
    force = module.params.get("force")
    path = module.params.get("path")

    # Lógica del modulo
    Output, success = git_acp(origin, branch, comment, files, force, path)

    # Retorno del módulo
    if success:
        module.exit_json(failed=False, msg="success", content=Output)
    else:
        module.fail_json(failed=True, msg="fail", content=Output)


if __name__ == "__main__":
    main()
