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
    if _state == "present":
        try:
            current_dir = os.getcwd()
            ret_msg = f"Current directory is  {current_dir}"
            success = True
        except Exception as error:
            success = False
            ret_msg = f"Current directory can not be gathered, error: {error}"
    else:
        success = True
        ret_msg = f"Set parameter values is {_state}, set parameter value to present"

    return ret_msg, success


# Main
def main():
    Output = {}
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, type='str', choices=["present", "absent"]),
        )
    )

    state = module.params.get("state")

# Lógica del modulo
    module_success = False
    msg_get, success = get_current_dir(state)
    
# Retorno del módulo
    if success:
        module.exit_json(failed=False, msg="success", content=msg_get)
    else:
        module.fail_json(failed=True, msg="fail", content=msg_get)


if __name__ == "__main__":
    main()
