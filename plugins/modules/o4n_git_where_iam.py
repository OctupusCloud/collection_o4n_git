#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

DOCUMENTATION = """
---
module: o4n_git_where_iam
version_added: "2.0"
author: "Ed Scrimaglia"
short_description: show ansible module current directory
description:
    - Detect where the current directory is
notes:
    - Testeado en linux
options:
    state:
        description:
            set or unset git remote
        required: True
"""

EXAMPLES = """
tasks:
  - name: Set remote
      o4n_git_where_iam:
        state: present
      register: salida
"""

# Python Modules
import os
from ansible.module_utils.basic import AnsibleModule


# Functions
def get_current_dir(_state):
    ret_msg = ""
    success = False
    output = {}
    if _state == "present":
        try:
            current_dir = os.getcwd()
            ret_msg = "Current directory was registerd"
            output["directory"] = current_dir
            success = True
        except Exception as error:
            success = False
            output["directory"] = "unknown"
            ret_msg = f"Current directory can not be gathered, error: {error}"
    else:
        success = True
        output["directory"] = "unknown"
        ret_msg = f"Set parameter values is {_state}, set parameter value to present"

    return ret_msg, success, output


# Main
def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, type='str', choices=["present", "absent"]),
        )
    )

    state = module.params.get("state")

# Lógica del modulo
    msg_get, success, output = get_current_dir(state)
    
# Retorno del módulo
    if success:
        module.exit_json(failed=False, msg=msg_get, content=output)
    else:
        module.fail_json(failed=True, msg=msg_get, content=output)


if __name__ == "__main__":
    main()
