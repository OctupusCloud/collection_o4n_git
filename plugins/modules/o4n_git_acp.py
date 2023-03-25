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
    - "Add files for trucking"
    - "Commit -a"
    - "Push content"
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
        default: "." meaning all files and directories
    force:
        description:
            define if push will be forced
        required: False
        default: False
"""

EXAMPLES = """
tasks:
  - name: Set remote
      o4n_git_acp:
        origin: origin
        branch: main
        files: "*.txt"
        comment: Refactoring
        force: true
      register: salida
"""

# Python Modules
import os
from ansible.module_utils.basic import AnsibleModule


# Methods
def git_acp(_origin, _branch, _comment, _add_files, _force):
    output = {}
    try:
        force_param = "--force" if _force else ""
        set_add_command = f"git add {_add_files}"
        os.system(set_add_command)
        set_commit_command = f"git commit -a -m {_comment}"
        os.system(set_commit_command)
        set_push_command = f"git push {force_param} {_origin} {_branch}"
        os.system(set_push_command)
        success = True
        output = {
            "add": f"Files added for tracking: {_add_files}",
            "commit": f"Commit type -a, comment: {_comment}",
            "push": f"Push to {_origin}, branch {_branch} has been successful"
        }
    except Exception as error:
        success = False
        output = {"push": f"Push to {_origin}, branch {_branch} has failed. Error {error}"}

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
            force=dict(required=False, type='str', choises=['True', 'False'], default='False')
        )
    )

    origin = module.params.get("origin")
    branch = module.params.get("branch")
    files = module.params.get("files")
    comment = module.params.get("comment")
    force = module.params.get("comment")

    # Lógica del modulo
    Output, success = git_acp(origin, branch, comment, files, force)

    # Retorno del módulo
    if success:
        module.exit_json(failed=False, msg="success", content=Output)
    else:
        module.fail_json(failed=True, msg="fail", content=Output)


if __name__ == "__main__":
    main()
