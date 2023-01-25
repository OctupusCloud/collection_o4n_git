#!/usr/local/bin/python3
# By Ed Scrimaglia
#
from __future__ import print_function, unicode_literals

DOCUMENTATION = """
---
module: o4n_model_validation
version_added: "2.0"
author: "Ed Scrimaglia"
short_description: validate values in data model against defined rules
description:
  - Recibe el Data Model como atributo desde el ansible module
  - Analiza los valores del Data Model contra una serie de reglas predeterminadas
notes:
  - Testeado en linux
reglas de validacion aplicadas:
  - Core Devices:
      Stp:
        - If Stp active true THEN Vlan active must be true.
        - If Stp active false THEN Vlan active must be false.
      Interfaces:
        Svi:
          - IF Svi active true THEN Vlan active must be true.
          - IF Svi active false THEN Vlan active must be false.
          - IF vrf active true THEN Svi active must be true.
          - IF additional_commands true THEN Svi active must be true.
          - IF additional_commads active true THEN variable must be nxos_svi_commands.
        Trunk:
          - IF Trunk's active true THEN  Vlan's active must be true.
          - IF additional_commands true THEN Trunk active must be true.
          - IF additional_commads active true THEN variable must be nxos_trunk_commands.
  - Distribution Devices:
      Interfaces:
        Trunk:
          - IF Trunk's active true THEN  Vlan's active must be true.
          - IF additional_commands true THEN Trunk active must be true.
          - IF additional_commads active true THEN variable must be nxos_trunk_commands.
  - Access Devices:
      Interfaces:
        Trunk:
          - IF Trunk's active true THEN  Vlan's active must be true.
          - IF additional_commands active true THEN Trunk active must be true.
          - IF additional_commads active true THEN variable must be nxos_trunk_commands.
        Access:
          - IF Access's active true THEN  Vlan's active must be true.
          - IF additional_commads active true AND mode access THEN variable must be nxos_access_commands.
          - IF additional_commads active true AND mode trunk THEN variable must be nxos_trunk_commands.
          - IF allowed true THEN mode must be trunk.
  - HSRP_Config Devices:
      Interfaces:
        - IF Interfaces's active is true or false AND Svi exists THEN  Svi's active must be true.
        - IF additional_commands true THEN Interfaces active must be true.
        - IF additional_commads active true THEN variable must be nxos_hsrp_commands.

  - Static_Route_Config:
      No rules needed.

options:
  data_model:
    description:
      Data Model del CU
    required: True
"""

EXAMPLES = """
tasks:
  - name: Data Model values validation
    o4n_model_values_validation:
      data_model: "{{ Data_Model }}"
    register: output
"""

from ansible.module_utils.basic import AnsibleModule
import ast

# Vars
rules_dict = {}
vlans_status_dict = {}


# Functions
def core_stp_rules(_dataModel, module):
    ret_msg_dict = {}
    status = True
    _dataModel = ast.literal_eval(_dataModel)
    core_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Core"]["Template"]["vlans"]
    if len(core_vlan_list) > 0:
        for vlan_dict_ele in core_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_status = vlan_dict_ele["active"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    device_id_stp_status = device["stp"]["active"]
                    if (not vlan_status and device_id_stp_status) or (vlan_status and not device_id_stp_status):
                        ret_msg_dict[
                            device_name] = f"Vlan {vlan_id}, status {vlan_status}, es diferente de device {device_name}, STP status {device_id_stp_status}"
                        module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                    else:
                        ret_msg_dict[
                            device_name] = f"Vlan {vlan_id}, status {vlan_status} and device {device_name} STP status {device_id_stp_status}, match the rules"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Core Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Core"
        status = True
    rules_dict["core_stp"] = ret_msg_dict

    return rules_dict, status


def core_svi_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    vlans_status_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    core_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Core"]["Template"]["vlans"]
    if len(core_vlan_list) > 0:
        ####
        vlan_list = []
        ####
        for vlan_dict_ele in core_vlan_list:
            ####
            device_list = []
            ####
            vlan_id = vlan_dict_ele["id"]
            vlan_status = vlan_dict_ele["active"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    svi_interface = device["interfaces"]["svi"]
                    if len(svi_interface.keys()) > 0:
                        device_name = device["name"]
                        device_name = device["name"]
                        svi_status = svi_interface["active"]
                        svi_name = svi_interface["name"]
                        ####
                        svi_in_device_dic = {
                            "name": svi_name,
                            "status": svi_status
                        }
                        ####
                        check_svi_name_status, msg_check_svi = parse_svi_interface_name(svi_name, vlan_id, "vlan")
                        match1 = check_svi_name_status
                        match2 = (not vlan_status and svi_status) or (vlan_status and not svi_status)
                        if not match1:
                            ret_msg_dict[
                                device_name] = f"{msg_check_svi} en device {device_name}"
                            module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                        elif match2:
                            ret_msg_dict[
                                device_name] = f"Vlan {vlan_id}, status {vlan_status}, es diferente de SVI interface {svi_name}, status {svi_status} en device {device_name}"
                            module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                        else:
                            ret_msg_dict[
                                device_name] = f"Vlan {vlan_id}, status {vlan_status} and SVI interface {svi_name}, status {svi_status}, match the rules en device {device_name}"
                            status = True

                        ####
                        device_list.append({
                            "name": device_name,
                            "svi": svi_in_device_dic
                            })
                        ####
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay SVI interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Core Devices a configurar para la Vlan {vlan_id}"
                status = True

            ####
            vlan_list.append({
                "id": vlan_id,
                "status": vlan_status,
                "devices": device_list
            })
            ####
        ####
        vlans_status_dict = vlan_list
        ####
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Core"
        status = True

    rules_dict["core_svi_interfaces"] = ret_msg_dict

    return rules_dict, status, vlans_status_dict


def core_svi_vrf_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    core_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Core"]["Template"]["vlans"]
    if len(core_vlan_list) > 0:
        for vlan_dict_ele in core_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    svi_interface = device["interfaces"]["svi"]
                    if len(svi_interface.keys()) > 0:
                        svi_status = svi_interface["active"]
                        svi_name = svi_interface["name"]
                        svi_vrf = svi_interface["vrf"]["active"]
                        if not svi_status and svi_vrf:
                            ret_msg_dict[
                                device_name] = f"SVI interface {svi_name}, status {svi_status}, es diferente de SVI VRF, status {svi_vrf} en device {device_name}"
                            module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                        else:
                            ret_msg_dict[
                                device_name] = f"SVI interface {svi_name}, status {svi_status} and SVI VRF status: {svi_vrf}, match the rules en en device {device_name}"
                            status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay SVI interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Core Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Core"
        status = True
    rules_dict["core_vrf"] = ret_msg_dict

    return rules_dict, status


def core_svi_add_commands_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    core_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Core"]["Template"]["vlans"]
    if len(core_vlan_list) > 0:
        for vlan_dict_ele in core_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    svi_interface = device["interfaces"]["svi"]
                    if len(svi_interface.keys()) > 0:
                        svi_status = svi_interface["active"]
                        svi_name = svi_interface["name"]
                        svi_additional_commands = svi_interface["additional_commands"]["active"]
                        add_commands_list_len = len(svi_interface["additional_commands"]["commands"])
                        not_match1 = (not svi_status and svi_additional_commands)
                        not_match2 = (svi_additional_commands and add_commands_list_len <= 0)
                        if not_match1:
                            ret_msg_dict[
                                device_name] = f"Interface {svi_name}, status {svi_status}, es diferente de SVI Additional Commands, status {svi_additional_commands} en device {device_name}"
                            module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                        elif not_match2:
                            ret_msg_dict[
                                device_name] = f"Interface {svi_name}, SVI Additional Commands list Length {add_commands_list_len} en device {device_name}"
                            module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                        else:
                            ret_msg_dict[
                                device_name] = f"Interface {svi_name}, status {svi_status} and SVI Additional Commands, status {svi_additional_commands}, match the rules en device {device_name}"
                            status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay SVI interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Core Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Core"
        status = True
    rules_dict["core_svi_additional_commands"] = ret_msg_dict

    return rules_dict, status


def core_trunk_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    core_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Core"]["Template"]["vlans"]
    if len(core_vlan_list) > 0:
        for vlan_dict_ele in core_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_status = vlan_dict_ele["active"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    trunk_interfaces = device["interfaces"]["trunk"]
                    if len(trunk_interfaces) > 0:
                        for trunk in trunk_interfaces:
                            trunk_status = trunk["active"]
                            trunk_name = trunk["name"]
                            if not vlan_status and trunk_status:
                                ret_msg_dict[
                                    trunk_name] = f"Vlan {vlan_id}, status {vlan_status}, es diferente de Trunk interface {trunk_name}, status {trunk_status} en {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[trunk_name])
                            else:
                                ret_msg_dict[
                                    trunk_name] = f"Vlan {vlan_id}, status {vlan_status} and Trunk interface {trunk_name} status {trunk_status}, match the rules en {device_name}"
                                status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay Trunk interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Core Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Core"
        status = True
    rules_dict["core_trunk_interfaces"] = ret_msg_dict

    return rules_dict, status


def core_trunk_add_commands_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    core_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Core"]["Template"]["vlans"]
    if len(core_vlan_list) > 0:
        for vlan_dict_ele in core_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    trunk_interfaces = device["interfaces"]["trunk"]
                    if len(trunk_interfaces) > 0:
                        for trunk in trunk_interfaces:
                            trunk_status = trunk["active"]
                            trunk_name = trunk["name"]
                            trunk_additional_commands = trunk["additional_commands"]["active"]
                            add_commands_list_len = len(trunk["additional_commands"]["commands"])
                            not_match1 = (not trunk_status and trunk_additional_commands)
                            not_match2 = (trunk_additional_commands and add_commands_list_len <= 0)
                            if not_match1:
                                ret_msg_dict[
                                    device_name] = f"Interface {trunk_name}, status {trunk_status}, es diferente de Trunk Additional Commands, status {trunk_additional_commands} en device {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                            elif not_match2:
                                ret_msg_dict[
                                    device_name] = f"Interface {trunk_name}, Trunk Additional Commands list Length {add_commands_list_len} en device {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                            else:
                                ret_msg_dict[
                                    device_name] = f"Interface {trunk_name}, status {trunk_status} and Trunk Additional Commands, status {trunk_additional_commands}, match the rules en device {device_name}"
                                status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay Trunk interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Core Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Core"
        status = True
    rules_dict["core_trunk_additional_commands"] = ret_msg_dict

    return rules_dict, status


def dist_trunk_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    dist_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Distribution"]["Template"]["vlans"]
    if len(dist_vlan_list) > 0:
        for vlan_dict_ele in dist_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_status = vlan_dict_ele["active"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    trunk_interfaces = device["interfaces"]["trunk"]
                    if len(trunk_interfaces) > 0:
                        for trunk in trunk_interfaces:
                            trunk_status = trunk["active"]
                            trunk_name = trunk["name"]
                            if not vlan_status and trunk_status:
                                ret_msg_dict[
                                    trunk_name] = f"Vlan {vlan_id}, status {vlan_status}, es diferente de Trunk interface {trunk_name}, status {trunk_status} en {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[trunk_name])
                            else:
                                ret_msg_dict[
                                    trunk_name] = f"Vlan {vlan_id}, status {vlan_status} and Trunk interface {trunk_name} status {trunk_status}, match the rules en {device_name}"
                                status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay Trunk interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Distribution Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Distribution"
        status = True
    rules_dict["dist_trunk_interfaces"] = ret_msg_dict

    return rules_dict, status


def dist_trunk_add_commands_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    dist_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Distribution"]["Template"]["vlans"]
    if len(dist_vlan_list) > 0:
        for vlan_dict_ele in dist_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    trunk_interfaces = device["interfaces"]["trunk"]
                    if len(trunk_interfaces) > 0:
                        for trunk in trunk_interfaces:
                            trunk_status = trunk["active"]
                            trunk_name = trunk["name"]
                            trunk_additional_commands = trunk["additional_commands"]["active"]
                            add_commands_list_len = len(trunk["additional_commands"]["commands"])
                            not_match1 = (not trunk_status and trunk_additional_commands)
                            not_match2 = (trunk_additional_commands and add_commands_list_len <= 0)
                            if not_match1:
                                ret_msg_dict[
                                    device_name] = f"Interface {trunk_name}, status {trunk_status}, es diferente de Trunk Additional Commands, status {trunk_additional_commands} en device {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                            elif not_match2:
                                ret_msg_dict[
                                    device_name] = f"Interface {trunk_name}, Trunk Additional Commands list Length {add_commands_list_len} en device {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                            else:
                                ret_msg_dict[
                                    device_name] = f"Interface {trunk_name}, status {trunk_status} and Trunk Additional Commands, status {trunk_additional_commands}, match the rules en device {device_name}"
                                status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay Trunk interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Distribution Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Distribution"
        status = True
    rules_dict["dist_trunk_additional_commands"] = ret_msg_dict

    return rules_dict, status


def access_trunk_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    access_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Access"]["Template"]["vlans"]
    if len(access_vlan_list) > 0:
        for vlan_dict_ele in access_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_status = vlan_dict_ele["active"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    trunk_interfaces = device["interfaces"]["trunk"]
                    if len(trunk_interfaces) > 0:
                        for trunk in trunk_interfaces:
                            trunk_status = trunk["active"]
                            trunk_name = trunk["name"]
                            if not vlan_status and trunk_status:
                                ret_msg_dict[
                                    trunk_name] = f"Vlan {vlan_id}, status {vlan_status}, es diferente de Trunk interface {trunk_name}, status {trunk_status} en {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[trunk_name])
                            else:
                                ret_msg_dict[
                                    trunk_name] = f"Vlan {vlan_id}, status {vlan_status} and Trunk interface {trunk_name} status {trunk_status}, match the rules en {device_name}"
                                status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay Trunk interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Access Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Access"
        status = True
    rules_dict["access_trunk_interfaces"] = ret_msg_dict

    return rules_dict, status


def access_trunk_add_commands_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    access_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Access"]["Template"]["vlans"]
    if len(access_vlan_list) > 0:
        for vlan_dict_ele in access_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    trunk_interfaces = device["interfaces"]["trunk"]
                    if len(trunk_interfaces) > 0:
                        for trunk in trunk_interfaces:
                            trunk_status = trunk["active"]
                            trunk_name = trunk["name"]
                            trunk_additional_commands = trunk["additional_commands"]["active"]
                            add_commands_list_len = len(trunk["additional_commands"]["commands"])
                            not_match1 = (not trunk_status and trunk_additional_commands)
                            not_match2 = (trunk_additional_commands and add_commands_list_len <= 0)
                            if not_match1:
                                ret_msg_dict[
                                    device_name] = f"Interface {trunk_name}, status {trunk_status}, es diferente de Access Trunk Additional Commands, status {trunk_additional_commands} en device {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                            elif not_match2:
                                ret_msg_dict[
                                    device_name] = f"Interface {trunk_name}, Access Trunk Additional Commands list Length {add_commands_list_len} en device {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                            else:
                                ret_msg_dict[
                                    device_name] = f"Interface {trunk_name}, status {trunk_status} and Access Trunk Additional Commands, status {trunk_additional_commands}, match the rules en device {device_name}"
                                status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay Access Trunk interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Access Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Access"
        status = True
    rules_dict["access_trunk_additional_commands"] = ret_msg_dict

    return rules_dict, status


def access_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    access_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Access"]["Template"]["vlans"]
    if len(access_vlan_list) > 0:
        for vlan_dict_ele in access_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_status = vlan_dict_ele["active"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    access_interfaces = device["interfaces"]["access"]
                    if len(access_interfaces) > 0:
                        for access in access_interfaces:
                            access_status = access["active"]
                            access_name = access["name"]
                            if not vlan_status and access_status:
                                ret_msg_dict[
                                    access_name] = f"Vlan {vlan_id}, status {vlan_status}, es diferente de Access interface {access_name}, status {access_status} en {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[access_name])
                            else:
                                ret_msg_dict[
                                    access_name] = f"Vlan {vlan_id}, status {vlan_status} and Access interface {access_name} status {access_status}, match the rules en {device_name}"
                                status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay Access interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Access Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Access"
        status = True
    rules_dict["access_interfaces"] = ret_msg_dict

    return rules_dict, status


def access_add_commands_interfaces_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    access_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Access"]["Template"]["vlans"]
    if len(access_vlan_list) > 0:
        for vlan_dict_ele in access_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    access_interfaces = device["interfaces"]["access"]
                    if len(access_interfaces) > 0:
                        for access in access_interfaces:
                            access_status = access["active"]
                            access_name = access["name"]
                            access_additional_commands = access["additional_commands"]["active"]
                            add_commands_list_len = len(access["additional_commands"]["commands"])
                            not_match1 = (not access_status and access_additional_commands)
                            not_match2 = (access_additional_commands and add_commands_list_len <= 0)
                            if not_match1:
                                ret_msg_dict[
                                    device_name] = f"Interface {access_name}, status {access_status}, es diferente de Access Additional Commands, status {access_additional_commands} en device {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                            elif not_match2:
                                ret_msg_dict[
                                    device_name] = f"Interface {access_name}, Access Additional Commands list Length {add_commands_list_len} en device {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                            else:
                                ret_msg_dict[
                                    device_name] = f"Interface {access_name}, status {access_status} and Access Additional Commands, status {access_additional_commands}, match the rules en device {device_name}"
                                status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay Access interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Access Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Access"
        status = True
    rules_dict["access_additional_commands"] = ret_msg_dict

    return rules_dict, status


def access_allowed_mode_rules(_dataModel, module):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    access_vlan_list = _dataModel["Spec"]["Config"]["Vlans_Config"]["Spec"]["Access"]["Template"]["vlans"]
    if len(access_vlan_list) > 0:
        for vlan_dict_ele in access_vlan_list:
            vlan_id = vlan_dict_ele["id"]
            vlan_devices = vlan_dict_ele["devices"]
            if len(vlan_devices) > 0:
                for device in vlan_devices:
                    device_name = device["name"]
                    access_interfaces = device["interfaces"]["access"]
                    if len(access_interfaces) > 0:
                        for access in access_interfaces:
                            access_allowed = access["allowed"]
                            access_mode = access["mode"]
                            access_name = access["name"]
                            if access_allowed and access_mode != "trunk":
                                ret_msg_dict[
                                    access_name] = f"Access interface {access_name}, modo {access_mode}, es incompatible con Access allowed status {access_allowed} en {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[access_name])
                            else:
                                ret_msg_dict[
                                    access_name] = f"Access interface {access_name}, modo {access_mode} and Access allowed status {access_allowed}, match the rules en {device_name}"
                                status = True
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay Access interfaces a configurar para la Vlan {vlan_id} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Access Devices a configurar para la Vlan {vlan_id}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay Vlans a configurar en los devices de Access"
        status = True
    rules_dict["access_allowed_mode"] = ret_msg_dict

    return rules_dict, status


def hsrp_rules(_dataModel, module, _vlans_status_dict):
    status = True
    ret_msg_dict = {}
    _dataModel = ast.literal_eval(_dataModel)
    hsrp_group_list = _dataModel["Spec"]["Config"]["HSRP_Config"]["Spec"]["hsrp"]
    if len(hsrp_group_list) > 0:
        for hsrp in hsrp_group_list:
            hsrp_group = hsrp["group"]
            hsrp_devices = hsrp["devices"]
            if len(hsrp_devices) > 0:
                for device in hsrp_devices:
                    device_name = device["name"]
                    hsrp_interfaces = device["interfaces"]
                    if len(hsrp_interfaces) > 0:
                        for inter in hsrp_interfaces:
                            inter_name = inter["name"]
                            inter_status = inter["active"]
                            success, msg, vlanId = get_vlan_svi_interface(inter_name, "vlan")
                            if success:
                                for vlan_dic in _vlans_status_dict:
                                    vlan_id_dic = vlan_dic["id"]
                                    vlans_status_dic = vlan_dic["status"]
                                    for dev_dic in vlan_dic["devices"]:
                                        svi_name_dic = dev_dic["svi"]["name"]
                                        svi_status_dic = dev_dic["svi"]["status"]

                                        match1 = int(vlan_id_dic) == int(vlanId)
                                        match2 = svi_name_dic == inter_name
                                        match3 = not vlans_status_dic and not svi_status_dic

                                        if match1 and match2 and match3:
                                            ret_msg_dict[
                                                inter_name+" "+device_name] = f"Interface {inter_name}, status {inter_status}, no debe estar en la sección HSRP en device {device_name}, Vlan {vlanId} status es {vlans_status_dic}"
                                            module.fail_json(msg="fail", content=ret_msg_dict[inter_name])
                                        else:
                                            inter_additional_commands = inter["additional_commands"]["active"]
                                            add_commands_list_len = len(inter["additional_commands"]["commands"])
                                            not_match1 = not inter_status and inter_additional_commands
                                            not_match2 = inter_additional_commands and add_commands_list_len <= 0
                                            if not_match1:
                                                ret_msg_dict[
                                                    device_name] = f"Interface {inter_name}, status {inter_status}, es diferente de HSRP Additional Commands, status {inter_additional_commands} en device {device_name}"
                                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                                            elif not_match2:
                                                ret_msg_dict[
                                                    device_name] = f"Interface {inter_name}, HSRP Additional Commands list Length {add_commands_list_len} en device {device_name}"
                                                module.fail_json(msg="fail", content=ret_msg_dict[device_name])
                                            else:
                                                ret_msg_dict[
                                                    device_name] = f"Interface {inter_name}, status {inter_status} and HSRP Additional Commands, status {inter_additional_commands}, match the rules en device {device_name}"
                                                status = True
                            else:
                                ret_msg_dict[
                                    inter_name] = f"{msg} en device {device_name}"
                                module.fail_json(msg="fail", content=ret_msg_dict[inter_name])
                    else:
                        ret_msg_dict[
                            "comment"] = f"No hay HSRP interfaces a configurar para el HSRP Group {hsrp_group} en device {device}"
                        status = True
            else:
                ret_msg_dict["comment"] = f"No hay Devices a configurar para el HSRP Group {hsrp_group}"
                status = True
    else:
        ret_msg_dict["comment"] = "No hay HSRP Groups a configurar"
        status = True

    rules_dict["hsrp_rules"] = ret_msg_dict

    return rules_dict, status


def parse_svi_interface_name(_intname, _vlan, _splitter):
    success_parse, msg_parse, vlan = get_vlan_svi_interface(_intname, _splitter)
    if success_parse:
        if _vlan == vlan:
            success = True
            msg = f"interface SVI name {_intname.lower()}, matchs the rules"
        else:
            success = False
            msg = f"invalid interface name. Name is {_intname.lower()}. Must be vlan{_vlan}"
    else:
        msg = msg_parse
    return success, msg


def get_vlan_svi_interface(_intname, _splitter):
    vlanId = False
    try:
        sectors = _intname.lower().split(_splitter.lower())
        if len(sectors) == 2:
            vlanId = int(sectors[1])
            msg = f"Interface name {_intname.lower()}, Vlan ID {vlanId}"
            success = True
        else:
            msg = f"invalid interface name. Name is {_intname.lower()}."
            success = False
    except Exception as error:
        success = False
        msg = f"invalid interface name. Name is {_intname.lower()}."
    return success, msg, vlanId


# Main
def main():
    success = True
    module = AnsibleModule(
        argument_spec=dict(
            data_model=dict(required=True)
        )
    )

    dataModel = module.params.get("data_model")
    ret_msg, success = core_stp_rules(dataModel, module)
    ret_msg, success, vlans_status_dict = core_svi_interfaces_rules(dataModel, module)
    ret_msg, success = core_svi_add_commands_interfaces_rules(dataModel, module)
    ret_msg, success = core_svi_vrf_interfaces_rules(dataModel, module)
    ret_msg, success = core_trunk_interfaces_rules(dataModel, module)
    ret_msg, success = core_trunk_add_commands_interfaces_rules(dataModel, module)
    ret_msg, success = dist_trunk_interfaces_rules(dataModel, module)
    ret_msg, success = dist_trunk_add_commands_interfaces_rules(dataModel, module)
    ret_msg, success = access_trunk_interfaces_rules(dataModel, module)
    ret_msg, success = access_trunk_add_commands_interfaces_rules(dataModel, module)
    ret_msg, success = access_interfaces_rules(dataModel, module)
    ret_msg, success = access_add_commands_interfaces_rules(dataModel, module)
    ret_msg, success = access_allowed_mode_rules(dataModel, module)
    ret_msg, success = hsrp_rules(dataModel, module, vlans_status_dict)

    if success:
        module.exit_json(msg="succes", content=ret_msg)


if __name__ == "__main__":
    main()
