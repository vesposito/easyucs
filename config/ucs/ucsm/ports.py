# coding: utf-8
# !/usr/bin/env python

""" ports.py: Easy UCS Deployment Tool """
from ucsmsdk.mometa.fabric.FabricBreakout import FabricBreakout
from ucsmsdk.mometa.fabric.FabricDceSwSrvEp import FabricDceSwSrvEp
from ucsmsdk.mometa.fabric.FabricEthEstcEp import FabricEthEstcEp
from ucsmsdk.mometa.fabric.FabricEthEstcPc import FabricEthEstcPc
from ucsmsdk.mometa.fabric.FabricEthEstcPcEp import FabricEthEstcPcEp
from ucsmsdk.mometa.fabric.FabricEthLanEp import FabricEthLanEp
from ucsmsdk.mometa.fabric.FabricEthLanPc import FabricEthLanPc
from ucsmsdk.mometa.fabric.FabricEthLanPcEp import FabricEthLanPcEp
from ucsmsdk.mometa.fabric.FabricEthTargetEp import FabricEthTargetEp
from ucsmsdk.mometa.fabric.FabricEthVlanPc import FabricEthVlanPc
from ucsmsdk.mometa.fabric.FabricEthVlanPortEp import FabricEthVlanPortEp
from ucsmsdk.mometa.fabric.FabricFcEstcEp import FabricFcEstcEp
from ucsmsdk.mometa.fabric.FabricFcSanEp import FabricFcSanEp
from ucsmsdk.mometa.fabric.FabricFcSanPc import FabricFcSanPc
from ucsmsdk.mometa.fabric.FabricFcSanPcEp import FabricFcSanPcEp
from ucsmsdk.mometa.fabric.FabricFcVsanPc import FabricFcVsanPc
from ucsmsdk.mometa.fabric.FabricFcVsanPortEp import FabricFcVsanPortEp
from ucsmsdk.mometa.fabric.FabricFcoeEstcEp import FabricFcoeEstcEp
from ucsmsdk.mometa.fabric.FabricFcoeSanEp import FabricFcoeSanEp
from ucsmsdk.mometa.fabric.FabricFcoeSanPc import FabricFcoeSanPc
from ucsmsdk.mometa.fabric.FabricFcoeSanPcEp import FabricFcoeSanPcEp
from ucsmsdk.mometa.fabric.FabricFcoeVsanPortEp import FabricFcoeVsanPortEp
from ucsmsdk.mometa.fabric.FabricSubGroup import FabricSubGroup
from ucsmsdk.mometa.fabric.FabricVlan import FabricVlan
from ucsmsdk.mometa.fabric.FabricVsan import FabricVsan
from ucsmsdk.ucscoremeta import UcsVersion

from config.ucs.object import UcsSystemConfigObject


class UcsSystemAppliancePort(UcsSystemConfigObject):
    _CONFIG_NAME = "Appliance Port"
    _CONFIG_SECTION_NAME = "appliance_ports"

    def __init__(self, parent=None, json_content=None, fabric_eth_estc_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_eth_estc_ep)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.aggr_id = None
        self.user_label = None
        self.flow_control_policy = None
        self.network_control_policy = None
        self.admin_speed = None
        self.admin_state = None
        self.priority = None
        self.pin_group = None
        self.vlan_port_mode = None
        self.appliance_vlans = []
        self.native_vlan = None
        self.ethernet_target_endpoint = []
        self.fec = None

        if self._config.load_from == "live":
            if fabric_eth_estc_ep is not None:
                self.fabric = fabric_eth_estc_ep.switch_id
                self.slot_id = fabric_eth_estc_ep.slot_id
                self.aggr_id = fabric_eth_estc_ep.aggr_port_id if int(fabric_eth_estc_ep.aggr_port_id) else None
                if self.aggr_id:
                    self.aggr_id = fabric_eth_estc_ep.port_id
                    self.port_id = fabric_eth_estc_ep.aggr_port_id
                else:
                    self.port_id = fabric_eth_estc_ep.port_id
                self.user_label = fabric_eth_estc_ep.usr_lbl
                self.flow_control_policy = fabric_eth_estc_ep.flow_ctrl_policy
                self.network_control_policy = fabric_eth_estc_ep.nw_ctrl_policy_name
                self.admin_speed = fabric_eth_estc_ep.admin_speed
                self.admin_state = fabric_eth_estc_ep.admin_state
                self.priority = fabric_eth_estc_ep.prio
                self.pin_group = fabric_eth_estc_ep.pin_group_name
                self.vlan_port_mode = fabric_eth_estc_ep.port_mode
                self.fec = fabric_eth_estc_ep.fec

                if "fabricEthTargetEp" in self._config.sdk_objects:
                    target = [target for target in self._config.sdk_objects["fabricEthTargetEp"] if "eth-estc/" +
                              self.fabric + "/phys-eth-slot-" + self.slot_id + "-port-" + self.port_id in target.dn]
                    if target:
                        if len(target) == 1:
                            self.ethernet_target_endpoint.append({})
                            self.ethernet_target_endpoint[0]["name"] = target[0].name
                            self.ethernet_target_endpoint[0]["mac_address"] = target[0].mac_address

                if "fabricEthVlanPortEp" in self._config.sdk_objects:
                    vlans = [vlan for vlan in self._config.sdk_objects["fabricEthVlanPortEp"] if "eth-estc/" +
                             self.fabric + "/phys-eth-slot-" + self.slot_id + "-port-" + self.port_id in vlan.ep_dn]
                    if vlans:
                        for vlan in vlans:
                            if vlan.is_native in ["yes", "true"]:
                                self.native_vlan = vlan.dn.split("net-")[1].split("/")[0]
                            else:
                                self.appliance_vlans.append(vlan.dn.split("net-")[1].split("/")[0])

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.ethernet_target_endpoint:
            for value in ["name", "mac_address"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id
        if self.aggr_id:
            port_name += '/' + self.aggr_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")

        parent_mo = "fabric/eth-estc/" + self.fabric.upper()

        if self.aggr_id:
            mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                 slot_id=self.slot_id)
            mo_fabric_eth_estc_ep = FabricEthEstcEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id,
                                                    port_id=self.aggr_id, port_mode=self.vlan_port_mode,
                                                    prio=self.priority,
                                                    pin_group_name=self.pin_group,
                                                    nw_ctrl_policy_name=self.network_control_policy,
                                                    flow_ctrl_policy=self.flow_control_policy,
                                                    usr_lbl=self.user_label, admin_state=self.admin_state)
            self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)

        else:
            mo_fabric_eth_estc_ep = FabricEthEstcEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                    port_id=self.port_id, port_mode=self.vlan_port_mode,
                                                    admin_speed=self.admin_speed, prio=self.priority,
                                                    pin_group_name=self.pin_group,
                                                    nw_ctrl_policy_name=self.network_control_policy,
                                                    flow_ctrl_policy=self.flow_control_policy, usr_lbl=self.user_label,
                                                    admin_state=self.admin_state, fec=self.fec)
            self._handle.add_mo(mo=mo_fabric_eth_estc_ep, modify_present=True)

        if commit:
            if self.commit(detail=port_name) != True:
                return False

        if self.ethernet_target_endpoint:
            FabricEthTargetEp(parent_mo_or_dn=mo_fabric_eth_estc_ep, name=self.ethernet_target_endpoint[0]["name"],
                              mac_address=self.ethernet_target_endpoint[0]["mac_address"])
            self._handle.add_mo(mo=mo_fabric_eth_estc_ep, modify_present=True)

            if commit:
                self.commit(detail="ethernet_target_endpoint: " + self.ethernet_target_endpoint[0]["name"])

        if self.native_vlan or self.appliance_vlans:
            if self.appliance_vlans and isinstance(self.appliance_vlans, list):
                for vlan in self.appliance_vlans:
                    mo_fabric_vlan = FabricVlan(parent_mo_or_dn="fabric/eth-estc", name=vlan)
                    FabricEthVlanPortEp(parent_mo_or_dn=mo_fabric_vlan, is_native="no", switch_id=self.fabric.upper(),
                                        port_id=self.port_id, slot_id=self.slot_id)
                    self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

                    if commit:
                        self.commit(detail="appliance_vlans: " + vlan)

            if self.native_vlan:
                mo_fabric_vlan = FabricVlan(parent_mo_or_dn="fabric/eth-estc", name=self.native_vlan)
                FabricEthVlanPortEp(parent_mo_or_dn=mo_fabric_vlan, is_native="yes", switch_id=self.fabric.upper(),
                                    port_id=self.port_id, slot_id=self.slot_id)
                self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

                if commit:
                    self.commit(detail="native_vlan: " + self.native_vlan)

        return True


class UcsSystemAppliancePortChannel(UcsSystemConfigObject):
    _CONFIG_NAME = "Appliance Port-Channel"
    _CONFIG_SECTION_NAME = "appliance_port_channels"

    def __init__(self, parent=None, json_content=None, fabric_eth_estc_pc=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_eth_estc_pc)
        self.name = None
        self.descr = None
        self.fabric = None
        self.pc_id = None
        self.lacp_policy = None
        self.flow_control_policy = None
        self.admin_speed = None
        self.admin_state = None
        self.interfaces = []
        self.protocol = None
        self.network_control_policy = None
        self.priority = None
        self.pin_group = None
        self.vlan_port_mode = None
        self.appliance_vlans = []
        self.native_vlan = None
        self.ethernet_target_endpoint = []

        if self._config.load_from == "live":
            if fabric_eth_estc_pc is not None:
                self.name = fabric_eth_estc_pc.name
                self.descr = fabric_eth_estc_pc.descr
                self.fabric = fabric_eth_estc_pc.switch_id
                self.pc_id = fabric_eth_estc_pc.port_id
                self.lacp_policy = fabric_eth_estc_pc.lacp_policy_name
                self.flow_control_policy = fabric_eth_estc_pc.flow_ctrl_policy
                self.admin_speed = fabric_eth_estc_pc.admin_speed
                self.admin_state = fabric_eth_estc_pc.admin_state
                self.protocol = fabric_eth_estc_pc.protocol
                self.priority = fabric_eth_estc_pc.prio
                self.network_control_policy = fabric_eth_estc_pc.nw_ctrl_policy_name
                self.pin_group = fabric_eth_estc_pc.pin_group_name
                self.vlan_port_mode = fabric_eth_estc_pc.port_mode

                if "fabricEthEstcPcEp" in self._config.sdk_objects:
                    interfaces = [interface for interface in self._config.sdk_objects["fabricEthEstcPcEp"]
                                  if self.fabric + "/pc-" + self.pc_id + "/" in interface.dn]
                    if interfaces:
                        for interface_pc_ep in interfaces:
                            interface = {}
                            interface["aggr_id"] = None
                            interface["slot_id"] = None
                            interface["port_id"] = None
                            interface["admin_state"] = None
                            interface["user_label"] = None

                            interface.update({"slot_id": interface_pc_ep.slot_id})
                            interface.update({"admin_state": interface_pc_ep.admin_state})
                            interface["aggr_id"] = interface_pc_ep.aggr_port_id if int(
                                interface_pc_ep.aggr_port_id) else None
                            if interface["aggr_id"]:
                                interface.update({"aggr_id": interface_pc_ep.port_id})
                                interface.update({"port_id": interface_pc_ep.aggr_port_id})
                            else:
                                interface.update({"port_id": interface_pc_ep.port_id})
                                interface.update({"user_label": interface_pc_ep.usr_lbl})
                            self.interfaces.append(interface)

                if "fabricEthTargetEp" in self._config.sdk_objects:
                    target = [target for target in self._config.sdk_objects["fabricEthTargetEp"]
                              if "eth-estc/" + self.fabric + "/pc-" + self.pc_id + "/eth-target" in target.dn]
                    if target:
                        if len(target) == 1:
                            self.ethernet_target_endpoint.append({})
                            self.ethernet_target_endpoint[0]["name"] = target[0].name
                            self.ethernet_target_endpoint[0]["mac_address"] = target[0].mac_address

                if "fabricEthVlanPc" in self._config.sdk_objects:
                    vlans = [vlan for vlan in self._config.sdk_objects["fabricEthVlanPc"]
                             if "eth-estc/" + self.fabric + "/pc-" + self.pc_id + "/" in vlan.ep_dn]
                    if vlans:
                        for vlan in vlans:
                            if vlan.is_native in ["yes", "true"]:
                                self.native_vlan = vlan.dn.split('/')[2].split('net-')[1]
                            else:
                                self.appliance_vlans.append(vlan.dn.split('/')[2].split('net-')[1])

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)
        # We need to set all values that are not present in the config file to None
        for element in self.interfaces:
            for value in ["aggr_id", "slot_id", "port_id", "admin_state", "user_label"]:
                if value not in element:
                    element[value] = None

        for element in self.ethernet_target_endpoint:
            for value in ["name", "mac_address"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name) + " - id: "
                                + self.pc_id + " on fabric " + self.fabric)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                " - id: " + self.pc_id + " on fabric " + self.fabric + ", waiting for a commit")

        # Creating Port-Channel object
        parent_mo = "fabric/eth-estc/" + self.fabric.upper()
        mo_fabric_eth_estc_pc = FabricEthEstcPc(parent_mo_or_dn=parent_mo, port_id=self.pc_id, descr=self.descr,
                                                port_mode=self.vlan_port_mode, admin_speed=self.admin_speed,
                                                name=self.name, prio=self.priority, pin_group_name=self.pin_group,
                                                nw_ctrl_policy_name=self.network_control_policy,
                                                flow_ctrl_policy=self.flow_control_policy, protocol=self.protocol,
                                                lacp_policy_name=self.lacp_policy, admin_state=self.admin_state)
        self._handle.add_mo(mo=mo_fabric_eth_estc_pc, modify_present=True)

        if commit:
            if self.commit(detail=self.pc_id) != True:
                return False

        # Adding interfaces to Port-Channel object
        if self.interfaces:
            for interface in self.interfaces:
                if interface["aggr_id"]:
                    mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=mo_fabric_eth_estc_pc,
                                                         aggr_port_id=interface["port_id"],
                                                         slot_id=interface['slot_id'])
                    FabricEthEstcPcEp(parent_mo_or_dn=mo_fabric_sub_group, port_id=interface['aggr_id'],
                                      slot_id=interface['slot_id'], admin_state=interface['admin_state'])
                    detail = interface['slot_id'] + "/" + interface['port_id'] + "/" + interface['aggr_id']

                else:
                    FabricEthEstcPcEp(parent_mo_or_dn=mo_fabric_eth_estc_pc, slot_id=interface['slot_id'],
                                      port_id=interface['port_id'], usr_lbl=interface['user_label'],
                                      admin_state=interface['admin_state'])
                    detail = interface['slot_id'] + "/" + interface['port_id']

                self._handle.add_mo(mo=mo_fabric_eth_estc_pc, modify_present=True)
                if commit:
                    self.commit(detail="interface:" + detail)

        if self.ethernet_target_endpoint:
            FabricEthTargetEp(parent_mo_or_dn=mo_fabric_eth_estc_pc, name=self.ethernet_target_endpoint[0]["name"],
                              mac_address=self.ethernet_target_endpoint[0]["mac_address"])
            self._handle.add_mo(mo=mo_fabric_eth_estc_pc, modify_present=True)

            if commit:
                self.commit(detail="ethernet_target_endpoint: " + self.ethernet_target_endpoint[0]["name"])

        if self.native_vlan or self.appliance_vlans:
            if self.appliance_vlans and isinstance(self.appliance_vlans, list):
                for vlan in self.appliance_vlans:
                    mo_fabric_vlan = FabricVlan(parent_mo_or_dn="fabric/eth-estc", name=vlan)
                    FabricEthVlanPc(parent_mo_or_dn=mo_fabric_vlan, is_native="no", switch_id=self.fabric.upper(),
                                    port_id=self.pc_id)
                    self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

                    if commit:
                        self.commit(detail="appliance_vlans: " + vlan)

            if self.native_vlan:
                mo_fabric_vlan = FabricVlan(parent_mo_or_dn="fabric/eth-estc", name=self.native_vlan)
                FabricEthVlanPc(parent_mo_or_dn=mo_fabric_vlan, is_native="yes", switch_id=self.fabric.upper(),
                                port_id=self.pc_id)
                self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

                if commit:
                    self.commit(detail="native_vlan: " + self.native_vlan)

        return True


class UcsSystemBreakoutPort(UcsSystemConfigObject):
    _CONFIG_NAME = "Breakout Port"
    _CONFIG_SECTION_NAME = "breakout_ports"
    _UCS_SDK_OBJECT_NAME = "fabricBreakout"

    def __init__(self, parent=None, json_content=None, fabric_breakout=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_breakout)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.breakout_type = None

        if self._config.load_from == "live":
            if fabric_breakout is not None:
                self.fabric = fabric_breakout.dn.split('/')[2]
                self.slot_id = fabric_breakout.slot_id
                self.port_id = fabric_breakout.port_id
                if fabric_breakout.breakout_type not in ["unknown"]:
                    self.breakout_type = fabric_breakout.breakout_type
                else:
                    # We are likely facing a 6536 FI with SAN breakout ports
                    if fabric_breakout.transport_type in ["fc"] and fabric_breakout.fc_breakout_type not in ["unknown"]:
                        self.breakout_type = fabric_breakout.fc_breakout_type

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")

        parent_mo = "fabric/Cabling/" + self.fabric.upper()
        if self.breakout_type in ["10g-4x", "25g-4x"]:
            # This is an Ethernet Breakout port
            mo_fabric_breakout = FabricBreakout(parent_mo_or_dn=parent_mo, port_id=self.port_id, slot_id=self.slot_id,
                                                transport_type="ethernet", breakout_type=self.breakout_type)
        else:
            # This is an FC Breakout port
            mo_fabric_breakout = FabricBreakout(parent_mo_or_dn=parent_mo, port_id=self.port_id, slot_id=self.slot_id,
                                                transport_type="fc", fc_breakout_type=self.breakout_type)

        self._handle.add_mo(mo=mo_fabric_breakout, modify_present=True)

        if commit:
            if self.commit(detail=port_name) != True:
                return False
        return True


class UcsSystemFcoePortChannel(UcsSystemConfigObject):
    _CONFIG_NAME = "FCoE Port Channel"
    _CONFIG_SECTION_NAME = "fcoe_port_channels"

    def __init__(self, parent=None, json_content=None, fabric_fcoe_san_pc=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_fcoe_san_pc)
        self.name = None
        self.descr = None
        self.fabric = None
        self.pc_id = None
        self.interfaces = []
        self.lacp_policy = None
        self.admin_state = None

        if self._config.load_from == "live":
            if fabric_fcoe_san_pc is not None:
                self.name = fabric_fcoe_san_pc.name
                self.descr = fabric_fcoe_san_pc.descr
                self.fabric = fabric_fcoe_san_pc.switch_id
                self.pc_id = fabric_fcoe_san_pc.port_id
                self.lacp_policy = fabric_fcoe_san_pc.lacp_policy_name
                self.admin_state = fabric_fcoe_san_pc.admin_state

                if "fabricFcoeSanPcEp" in self._config.sdk_objects:
                    interfaces = [interface for interface in self._config.sdk_objects["fabricFcoeSanPcEp"]
                                  if self.fabric + "/fcoesanpc-" + self.pc_id + "/" in interface.dn]
                    if interfaces:
                        for interface_pc_ep in interfaces:
                            interface = {}
                            interface["aggr_id"] = None
                            interface["slot_id"] = None
                            interface["port_id"] = None
                            interface["admin_state"] = None
                            interface["link_profile"] = None
                            interface["user_label"] = None

                            interface.update({"slot_id": interface_pc_ep.slot_id})
                            interface.update({"admin_state": interface_pc_ep.admin_state})
                            interface.update({"link_profile": interface_pc_ep.eth_link_profile_name})
                            interface.update({"user_label": interface_pc_ep.usr_lbl})
                            interface["aggr_id"] = interface_pc_ep.aggr_port_id if int(interface_pc_ep.aggr_port_id) \
                                else None
                            if interface["aggr_id"]:
                                interface.update({"aggr_id": interface_pc_ep.port_id})
                                interface.update({"port_id": interface_pc_ep.aggr_port_id})
                            else:
                                interface.update({"port_id": interface_pc_ep.port_id})
                            self.interfaces.append(interface)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)
        # We need to set all values that are not present in the config file to None
        for element in self.interfaces:
            for value in ["aggr_id", "slot_id", "port_id", "admin_state", "link_profile", "user_label"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name) + " - id: " +
                                self.pc_id + " on fabric " + self.fabric)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                " - id: " + self.pc_id + " on fabric " + self.fabric + ", waiting for a commit")

        parent_mo = "fabric/san/" + self.fabric.upper()
        mo_fabric_fcoe_san_pc = FabricFcoeSanPc(parent_mo_or_dn=parent_mo, port_id=self.pc_id, descr=self.descr,
                                                name=self.name, lacp_policy_name=self.lacp_policy,
                                                admin_state=self.admin_state)
        self._handle.add_mo(mo=mo_fabric_fcoe_san_pc, modify_present=True)
        if commit:
            self.commit(detail=self.pc_id)

        if self.interfaces:
            for interface in self.interfaces:
                if "aggr_id" in interface:
                    mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=mo_fabric_fcoe_san_pc,
                                                         aggr_port_id=interface["port_id"],
                                                         slot_id=interface['slot_id'])
                    FabricFcoeSanPcEp(parent_mo_or_dn=mo_fabric_sub_group, port_id=interface['aggr_id'],
                                      slot_id=interface['slot_id'], eth_link_profile_name=interface['link_profile'],
                                      usr_lbl=interface['user_label'], admin_state=interface['admin_state'])
                else:
                    FabricFcoeSanPcEp(parent_mo_or_dn=mo_fabric_fcoe_san_pc, slot_id=interface['slot_id'],
                                      port_id=interface['port_id'], eth_link_profile_name=interface['link_profile'],
                                      usr_lbl=interface['user_label'], admin_state=interface['admin_state'])

                self._handle.add_mo(mo=mo_fabric_fcoe_san_pc, modify_present=True)
                if commit:
                    self.commit(detail=self.pc_id)

        if commit:
            if self.commit(detail=self.pc_id) != True:
                return False
        return True


class UcsSystemFcoeStoragePort(UcsSystemConfigObject):
    _CONFIG_NAME = "FCoE Storage Port"
    _CONFIG_SECTION_NAME = "fcoe_storage_ports"

    def __init__(self, parent=None, json_content=None, fabric_fcoe_estc_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_fcoe_estc_ep)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.aggr_id = None
        self.user_label = None
        self.admin_state = None
        self.vsan = None
        self.vsan_fabric = None

        if self._config.load_from == "live":
            if fabric_fcoe_estc_ep is not None:
                self.fabric = fabric_fcoe_estc_ep.switch_id
                self.slot_id = fabric_fcoe_estc_ep.slot_id
                self.aggr_id = fabric_fcoe_estc_ep.aggr_port_id if int(fabric_fcoe_estc_ep.aggr_port_id) else None
                if self.aggr_id:
                    self.aggr_id = fabric_fcoe_estc_ep.port_id
                    self.port_id = fabric_fcoe_estc_ep.aggr_port_id
                else:
                    self.port_id = fabric_fcoe_estc_ep.port_id
                self.user_label = fabric_fcoe_estc_ep.usr_lbl
                self.admin_state = fabric_fcoe_estc_ep.admin_state

                if "fabricFcoeVsanPortEp" in self._config.sdk_objects:
                    vsan = [vsan for vsan in self._config.sdk_objects["fabricFcoeVsanPortEp"]
                            if self.fabric + "-slot-" + self.slot_id + "-port-" + self.port_id in vsan.dn]
                    if vsan:
                        if len(vsan) == 1:
                            if "net-" in vsan[0].dn.split('/')[2]:
                                # Then the vsan fabric is dual
                                self.vsan_fabric = "dual"
                                self.vsan = vsan[0].dn.split('/')[2].split('net-')[1]
                            elif "net-" in vsan[0].dn.split('/')[3]:
                                self.vsan_fabric = vsan[0].dn.split('/')[2]
                                self.vsan = vsan[0].dn.split('/')[3].split('net-')[1]

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id
        if self.aggr_id:
            port_name += '/' + self.aggr_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")

        parent_mo = "fabric/fc-estc/" + self.fabric.upper()

        if self.aggr_id:
            mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                 slot_id=self.slot_id)
            FabricFcoeEstcEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.aggr_id,
                             usr_lbl=self.user_label, admin_state=self.admin_state)
            self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)
        else:
            mo_fabric_fcoe_estc_ep = FabricFcoeEstcEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                      port_id=self.port_id, usr_lbl=self.user_label,
                                                      admin_state=self.admin_state)

            self._handle.add_mo(mo=mo_fabric_fcoe_estc_ep, modify_present=True)

        if self.vsan:
            if self.vsan_fabric == "dual":
                parent_mo_vsan = "fabric/fc-estc"
            else:
                parent_mo_vsan = "fabric/fc-estc/" + self.vsan_fabric.upper()
            mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo_vsan, name=self.vsan)
            if self.aggr_id:
                mo_fabric_fcoe_vsan_port_ep = FabricFcoeVsanPortEp(parent_mo_or_dn=mo_fabric_vsan, port_id=self.aggr_id,
                                                                   switch_id=self.fabric.upper(), slot_id=self.slot_id,
                                                                   aggr_port_id=self.port_id)
            else:
                mo_fabric_fcoe_vsan_port_ep = FabricFcoeVsanPortEp(parent_mo_or_dn=mo_fabric_vsan, port_id=self.port_id,
                                                                   switch_id=self.fabric.upper(), slot_id=self.slot_id)
            self._handle.add_mo(mo=mo_fabric_fcoe_vsan_port_ep, modify_present=True)

        if commit:
            if self.commit(detail=port_name) != True:
                return False
        return True


class UcsSystemFcoeUplinkPort(UcsSystemConfigObject):
    _CONFIG_NAME = "FCoE Uplink Port"
    _CONFIG_SECTION_NAME = "fcoe_uplink_ports"

    def __init__(self, parent=None, json_content=None, fabric_fcoe_san_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_fcoe_san_ep)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.aggr_id = None
        self.user_label = None
        self.link_profile = None
        self.admin_state = None
        self.admin_speed = None
        self.fec = None

        if self._config.load_from == "live":
            if fabric_fcoe_san_ep is not None:
                self.fabric = fabric_fcoe_san_ep.switch_id
                self.slot_id = fabric_fcoe_san_ep.slot_id
                self.aggr_id = fabric_fcoe_san_ep.aggr_port_id if int(fabric_fcoe_san_ep.aggr_port_id) else None
                if self.aggr_id:
                    self.aggr_id = fabric_fcoe_san_ep.port_id
                    self.port_id = fabric_fcoe_san_ep.aggr_port_id
                else:
                    self.port_id = fabric_fcoe_san_ep.port_id
                self.user_label = fabric_fcoe_san_ep.usr_lbl
                self.link_profile = fabric_fcoe_san_ep.eth_link_profile_name
                self.admin_state = fabric_fcoe_san_ep.admin_state
                self.admin_speed = fabric_fcoe_san_ep.admin_speed
                self.fec = fabric_fcoe_san_ep.fec

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id
        if self.aggr_id:
            port_name += '/' + self.aggr_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")

        parent_mo = "fabric/san/" + self.fabric.upper()

        if self.aggr_id:
            mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                 slot_id=self.slot_id)
            FabricFcoeSanEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.aggr_id,
                            usr_lbl=self.user_label, eth_link_profile_name=self.link_profile,
                            admin_state=self.admin_state)
            self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)
        else:
            mo_fabric_eth_lan_ep = FabricFcoeSanEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                   port_id=self.port_id, usr_lbl=self.user_label,
                                                   eth_link_profile_name=self.link_profile,
                                                   admin_state=self.admin_state, fec=self.fec,
                                                   admin_speed=self.admin_speed)

            self._handle.add_mo(mo=mo_fabric_eth_lan_ep, modify_present=True)

        if commit:
            if self.commit(detail=port_name) != True:
                return False
        return True


class UcsSystemLanPortChannel(UcsSystemConfigObject):
    _CONFIG_NAME = "LAN Port-Channel"
    _CONFIG_SECTION_NAME = "lan_port_channels"

    def __init__(self, parent=None, json_content=None, fabric_eth_lan_pc=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_eth_lan_pc)
        self.name = None
        self.descr = None
        self.fabric = None
        self.pc_id = None
        self.interfaces = []
        self.lacp_policy = None
        self.flow_control_policy = None
        self.admin_speed = None
        self.admin_state = None

        if self._config.load_from == "live":
            if fabric_eth_lan_pc is not None:
                self.name = fabric_eth_lan_pc.name
                self.descr = fabric_eth_lan_pc.descr
                self.fabric = fabric_eth_lan_pc.switch_id
                self.pc_id = fabric_eth_lan_pc.port_id
                self.lacp_policy = fabric_eth_lan_pc.lacp_policy_name
                self.flow_control_policy = fabric_eth_lan_pc.flow_ctrl_policy
                self.admin_speed = fabric_eth_lan_pc.admin_speed
                self.admin_state = fabric_eth_lan_pc.admin_state

                if "fabricEthLanPcEp" in self._config.sdk_objects:
                    interfaces = [interface for interface in self._config.sdk_objects["fabricEthLanPcEp"]
                                  if self.fabric + "/pc-" + self.pc_id + "/" in interface.dn]
                    if interfaces:
                        for interface_pc_ep in interfaces:
                            interface = {}
                            interface["aggr_id"] = None
                            interface["slot_id"] = None
                            interface["port_id"] = None
                            interface["admin_state"] = None
                            interface["link_profile"] = None
                            interface["user_label"] = None

                            interface.update({"slot_id": interface_pc_ep.slot_id})
                            interface.update({"admin_state": interface_pc_ep.admin_state})
                            interface.update({"link_profile": interface_pc_ep.eth_link_profile_name})
                            interface.update({"user_label": interface_pc_ep.usr_lbl})
                            if interface_pc_ep.aggr_port_id:
                                interface["aggr_id"] =\
                                    interface_pc_ep.aggr_port_id if int(interface_pc_ep.aggr_port_id) else None
                            else:
                                interface["aggr_id"] = None
                            if interface["aggr_id"]:
                                interface.update({"aggr_id": interface_pc_ep.port_id})
                                interface.update({"port_id": interface_pc_ep.aggr_port_id})
                            else:
                                interface.update({"port_id": interface_pc_ep.port_id})
                            self.interfaces.append(interface)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.interfaces:
            for value in ["aggr_id", "slot_id", "port_id", "admin_state", "link_profile", "user_label"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration with id: " + self.pc_id +
                                " on fabric " + self.fabric)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration with id: " + self.pc_id +
                                " on fabric " + self.fabric + ", waiting for a commit")

        # Creating Port-Channel object
        parent_mo = "fabric/lan/" + self.fabric.upper()
        mo_fabric_eth_lan_pc = FabricEthLanPc(parent_mo_or_dn=parent_mo, port_id=self.pc_id, descr=self.descr,
                                              name=self.name, lacp_policy_name=self.lacp_policy,
                                              flow_ctrl_policy=self.flow_control_policy, admin_speed=self.admin_speed,
                                              admin_state=self.admin_state)
        self._handle.add_mo(mo=mo_fabric_eth_lan_pc, modify_present=True)

        if commit:
            if self.commit(detail=self.pc_id) != True:
                return False

        # Adding interfaces to Port-Channel object
        if self.interfaces:
            for interface in self.interfaces:
                if interface["aggr_id"]:
                    mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=mo_fabric_eth_lan_pc,
                                                         aggr_port_id=interface["port_id"],
                                                         slot_id=interface['slot_id'])
                    FabricEthLanPcEp(parent_mo_or_dn=mo_fabric_sub_group, port_id=interface['aggr_id'],
                                     eth_link_profile_name=interface['link_profile'], usr_lbl=interface['user_label'],
                                     slot_id=interface['slot_id'], admin_state=interface['admin_state'])
                    detail = interface['slot_id'] + "/" + interface['port_id'] + "/" + interface['aggr_id']
                else:
                    FabricEthLanPcEp(parent_mo_or_dn=mo_fabric_eth_lan_pc, slot_id=interface['slot_id'],
                                     port_id=interface['port_id'], eth_link_profile_name=interface['link_profile'],
                                     usr_lbl=interface['user_label'], admin_state=interface['admin_state'])
                    detail = interface['slot_id'] + "/" + interface['port_id']

                self._handle.add_mo(mo=mo_fabric_eth_lan_pc, modify_present=True)
                if commit:
                    if self.commit(detail="interface: " + detail) != True:
                        return False

        return True


class UcsSystemLanUplinkPort(UcsSystemConfigObject):
    _CONFIG_NAME = "LAN Uplink Port"
    _CONFIG_SECTION_NAME = "lan_uplink_ports"

    def __init__(self, parent=None, json_content=None, fabric_eth_lan_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_eth_lan_ep)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.aggr_id = None
        self.user_label = None
        self.flow_control_policy = None
        self.link_profile = None
        self.admin_speed = None
        self.admin_state = None
        self.fec = None

        if self._config.load_from == "live":
            if fabric_eth_lan_ep is not None:
                self.fabric = fabric_eth_lan_ep.switch_id
                self.slot_id = fabric_eth_lan_ep.slot_id
                if fabric_eth_lan_ep.aggr_port_id:
                    self.aggr_id = fabric_eth_lan_ep.aggr_port_id if int(fabric_eth_lan_ep.aggr_port_id) else None
                else:
                    self.aggr_id = None
                if self.aggr_id:
                    self.aggr_id = fabric_eth_lan_ep.port_id
                    self.port_id = fabric_eth_lan_ep.aggr_port_id
                else:
                    self.port_id = fabric_eth_lan_ep.port_id
                self.user_label = fabric_eth_lan_ep.usr_lbl
                self.flow_control_policy = fabric_eth_lan_ep.flow_ctrl_policy
                self.link_profile = fabric_eth_lan_ep.eth_link_profile_name
                self.admin_speed = fabric_eth_lan_ep.admin_speed
                self.admin_state = fabric_eth_lan_ep.admin_state
                self.fec = fabric_eth_lan_ep.fec

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id
        if self.aggr_id:
            port_name += '/' + self.aggr_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")

        parent_mo = "fabric/lan/" + self.fabric.upper()

        if self.aggr_id:
            mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                 slot_id=self.slot_id)
            FabricEthLanEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.aggr_id,
                           usr_lbl=self.user_label, flow_ctrl_policy=self.flow_control_policy,
                           eth_link_profile_name=self.link_profile,
                           admin_state=self.admin_state)
            self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)

        else:

            mo_fabric_eth_lan_ep = FabricEthLanEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id, port_id=self.port_id,
                                                  usr_lbl=self.user_label, flow_ctrl_policy=self.flow_control_policy,
                                                  eth_link_profile_name=self.link_profile, admin_speed=self.admin_speed,
                                                  admin_state=self.admin_state, fec=self.fec)

            self._handle.add_mo(mo=mo_fabric_eth_lan_ep, modify_present=True)

        if commit:
            if self.commit(detail=port_name) != True:
                return False
        return True


class UcsSystemSanPortChannel(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Port-Channel"
    _CONFIG_SECTION_NAME = "san_port-channels"

    def __init__(self, parent=None, json_content=None, fabric_fc_san_pc=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_fc_san_pc)
        self.name = None
        self.descr = None
        self.fabric = None
        self.pc_id = None
        self.interfaces = []
        self.admin_speed = None
        self.admin_state = None
        self.vsan = None
        self.vsan_fabric = None

        if self._config.load_from == "live":
            if fabric_fc_san_pc is not None:
                self.name = fabric_fc_san_pc.name
                self.descr = fabric_fc_san_pc.descr
                self.fabric = fabric_fc_san_pc.switch_id
                self.pc_id = fabric_fc_san_pc.port_id
                self.admin_speed = fabric_fc_san_pc.admin_speed
                self.admin_state = fabric_fc_san_pc.admin_state

                if "fabricFcSanPcEp" in self._config.sdk_objects:
                    interfaces = [interface for interface in self._config.sdk_objects["fabricFcSanPcEp"]
                                  if self.fabric + "/pc-" + self.pc_id + "/" in interface.dn]
                    if interfaces:
                        for interface_pc_ep in interfaces:
                            interface = {}
                            interface["aggr_id"] = None
                            interface["slot_id"] = None
                            interface["port_id"] = None
                            interface["admin_state"] = None
                            interface["link_profile"] = None
                            interface["user_label"] = None

                            interface.update({"slot_id": interface_pc_ep.slot_id})
                            interface.update({"admin_state": interface_pc_ep.admin_state})
                            interface["aggr_id"] = interface_pc_ep.aggr_port_id if int(interface_pc_ep.aggr_port_id) \
                                else None
                            if interface["aggr_id"]:
                                interface.update({"aggr_id": interface_pc_ep.port_id})
                                interface.update({"port_id": interface_pc_ep.aggr_port_id})
                            else:
                                interface.update({"port_id": interface_pc_ep.port_id})
                                interface.update({"user_label": interface_pc_ep.usr_lbl})
                            self.interfaces.append(interface)

                if "fabricFcVsanPc" in self._config.sdk_objects:
                    vsan = [vsan for vsan in self._config.sdk_objects["fabricFcVsanPc"]
                            if self.fabric + "/pc-" + self.pc_id + "/vsan" in vsan.ep_dn]
                    if vsan:
                        if len(vsan) == 1:
                            if "net-" in vsan[0].dn.split('/')[2]:
                                # Then the vsan fabric is dual
                                self.vsan_fabric = "dual"
                                self.vsan = vsan[0].dn.split('/')[2].split('net-')[1]
                            elif "net-" in vsan[0].dn.split('/')[3]:
                                self.vsan_fabric = vsan[0].dn.split('/')[2]
                                self.vsan = vsan[0].dn.split('/')[3].split('net-')[1]

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)
        for element in self.interfaces:
            for value in ["user_label", "link_profile", "admin_state", "aggr_id", "slot_id", "port_id"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name) + " - id: " +
                                self.pc_id + " on fabric " + self.fabric)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                " - id: " + self.pc_id + " on fabric " + self.fabric + ", waiting for a commit")

        parent_mo = "fabric/san/" + self.fabric.upper()
        mo_fabric_eth_lan_pc = FabricFcSanPc(parent_mo_or_dn=parent_mo, port_id=self.pc_id, descr=self.descr,
                                             name=self.name, admin_speed=self.admin_speed, admin_state=self.admin_state)
        self._handle.add_mo(mo=mo_fabric_eth_lan_pc, modify_present=True)
        if commit:
            self.commit(detail=self.pc_id)

        # Adding interfaces to Port-Channel object
        if self.interfaces:
            for interface in self.interfaces:
                if interface["aggr_id"]:
                    mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=mo_fabric_eth_lan_pc,
                                                         aggr_port_id=interface["port_id"],
                                                         slot_id=interface['slot_id'])
                    FabricFcSanPcEp(parent_mo_or_dn=mo_fabric_sub_group, port_id=interface['aggr_id'],
                                    slot_id=interface['slot_id'], admin_state=interface['admin_state'])
                    detail = interface['slot_id'] + "/" + interface['port_id'] + "/" + interface['aggr_id']
                else:
                    FabricFcSanPcEp(parent_mo_or_dn=mo_fabric_eth_lan_pc, slot_id=interface['slot_id'],
                                    port_id=interface['port_id'], usr_lbl=interface['user_label'],
                                    admin_state=interface['admin_state'])
                    detail = interface['slot_id'] + "/" + interface['port_id']

                self._handle.add_mo(mo=mo_fabric_eth_lan_pc, modify_present=True)
                if commit:
                    self.commit(detail="interface: " + detail)

        if self.vsan:
            if not self.vsan_fabric:
                self.vsan_fabric = self.fabric
            if self.vsan_fabric == "dual":
                parent_mo_vsan = "fabric/san"
            else:
                parent_mo_vsan = "fabric/san/" + self.vsan_fabric.upper()
            mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo_vsan, name=self.vsan)
            FabricFcVsanPc(parent_mo_or_dn=mo_fabric_vsan, port_id=self.pc_id, switch_id=self.fabric.upper())
            self._handle.add_mo(mo=mo_fabric_vsan, modify_present=True)
        if commit:
            if self.commit(detail=self.pc_id) != True:
                return False
        return True


class UcsSystemSanStoragePort(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Storage Port"
    _CONFIG_SECTION_NAME = "san_storage_ports"

    def __init__(self, parent=None, json_content=None, fabric_fc_estc_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_fc_estc_ep)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.aggr_id = None
        self.fill_pattern = None
        self.user_label = None
        self.admin_state = None
        self.admin_speed = None
        self.vsan_fabric = None
        self.vsan = None

        if self._config.load_from == "live":
            if fabric_fc_estc_ep is not None:
                self.fabric = fabric_fc_estc_ep.switch_id
                self.slot_id = fabric_fc_estc_ep.slot_id
                self.aggr_id = fabric_fc_estc_ep.aggr_port_id if int(fabric_fc_estc_ep.aggr_port_id) else None
                if self.aggr_id:
                    self.aggr_id = fabric_fc_estc_ep.port_id
                    self.port_id = fabric_fc_estc_ep.aggr_port_id
                else:
                    self.port_id = fabric_fc_estc_ep.port_id
                self.user_label = fabric_fc_estc_ep.usr_lbl
                self.fill_pattern = fabric_fc_estc_ep.fill_pattern
                self.admin_state = fabric_fc_estc_ep.admin_state
                self.admin_speed = fabric_fc_estc_ep.admin_speed

                if "fabricFcVsanPortEp" in self._config.sdk_objects:
                    if self.aggr_id:
                        vsan = [vsan for vsan in self._config.sdk_objects["fabricFcVsanPortEp"]
                                if vsan.peer_dn == "sys/switch-" + self.fabric + "/slot-" + self.slot_id +
                                "/switch-fc/aggr-port-" + self.port_id + "/port-" + self.aggr_id]
                    else:
                        vsan = [vsan for vsan in self._config.sdk_objects["fabricFcVsanPortEp"]
                                if vsan.peer_dn == "sys/switch-" + self.fabric + "/slot-" + self.slot_id +
                                "/switch-fc/port-" + self.port_id]
                    if vsan:
                        if len(vsan) == 1:
                            if "net-" in vsan[0].dn.split('/')[2]:
                                # Then the vsan fabric is dual
                                self.vsan_fabric = "dual"
                                self.vsan = vsan[0].dn.split('/')[2].split('net-')[1]
                            elif "net-" in vsan[0].dn.split('/')[3]:
                                self.vsan_fabric = vsan[0].dn.split('/')[2]
                                self.vsan = vsan[0].dn.split('/')[3].split('net-')[1]

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id
        if self.aggr_id:
            port_name += '/' + self.aggr_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")

        parent_mo = "fabric/fc-estc/" + self.fabric.upper()

        if not self.is_port_member_of_san_port_channel():
            if self.aggr_id:
                mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                     slot_id=self.slot_id)
                FabricFcEstcEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.aggr_id,
                               fill_pattern=self.fill_pattern, usr_lbl=self.user_label, admin_state=self.admin_state,
                               admin_speed=self.admin_speed)
                self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)
            else:
                mo_fabric_fc_estc_ep = FabricFcEstcEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                      port_id=self.port_id, fill_pattern=self.fill_pattern,
                                                      usr_lbl=self.user_label, admin_state=self.admin_state,
                                                      admin_speed=self.admin_speed)

                self._handle.add_mo(mo=mo_fabric_fc_estc_ep, modify_present=True)

            if self.vsan:
                if self.vsan_fabric == "dual":
                    parent_mo_vsan = "fabric/fc-estc"
                else:
                    parent_mo_vsan = "fabric/fc-estc/" + self.vsan_fabric.upper()
                mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo_vsan, name=self.vsan)
                if self.aggr_id:
                    FabricFcVsanPortEp(parent_mo_or_dn=mo_fabric_vsan, port_id=self.aggr_id, aggr_port_id=self.port_id,
                                       switch_id=self.fabric.upper(), slot_id=self.slot_id)
                else:
                    FabricFcVsanPortEp(parent_mo_or_dn=mo_fabric_vsan, port_id=self.port_id,
                                       switch_id=self.fabric.upper(), slot_id=self.slot_id)
                self._handle.add_mo(mo=mo_fabric_vsan, modify_present=True)

            if commit:
                if self.commit(detail=port_name) != True:
                    return False
        return True

    def is_port_member_of_san_port_channel(self, fabric="", slot_id="", port_id="", aggr_id=""):
        """
        Check if a port is a member of a SAN port-channel. Used by push_object()

        :param fabric: <class 'str'>: Fabric of the port to check
        :param slot_id: <class 'str'>: Slot id of the port to check
        :param port_id: <class 'str'>: Port id of the port to check
        :param aggr_id: <class 'str'>: Aggr id of the port to check (for breakout ports)
        :return: True if the port is a member of a SAN port-channel, False otherwise
        """

        fabric = self.fabric if not fabric else fabric
        slot_id = self.slot_id if not slot_id else slot_id
        port_id = self.port_id if not port_id else port_id
        aggr_id = self.aggr_id if not aggr_id else port_id

        # Query on the live system
        if aggr_id:
            ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-fc/aggr-port-" + port_id +\
                    "/port-" + aggr_id
        else:
            ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-fc/port-" + port_id

        interfaces = self._device.query(mode="classid", target="fabricFcSanPcEp",
                                        filter_str="(ep_dn,'" + ep_dn + "')")

        if aggr_id:
            port_name = slot_id + "/" + port_id + "/" + aggr_id
        else:
            port_name = slot_id + "/" + port_id

        if len(interfaces) == 0:
            self.logger(level="debug", message="Port " + port_name + " of fabric " + fabric +
                                               " is not a member of a SAN port-channel")
            return False
        elif len(interfaces) == 1:
            self.logger(level="debug",
                        message="Port " + port_name + " of fabric " + fabric +
                                " is already a member of a SAN port-channel: no action will be committed")
            return True
        else:
            self.logger(level="error",
                        message="Something wrong happened while trying to identify if port " + port_name +
                                " of fabric " + fabric + " is a member of a SAN port-channel")
            return False


class UcsSystemSanUplinkPort(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Uplink Port"
    _CONFIG_SECTION_NAME = "san_uplink_ports"

    def __init__(self, parent=None, json_content=None, fabric_fc_san_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_fc_san_ep)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.aggr_id = None
        self.fill_pattern = None
        self.user_label = None
        self.admin_state = None
        self.admin_speed = None
        self.vsan_fabric = None
        self.vsan = None

        if self._config.load_from == "live":
            if fabric_fc_san_ep is not None:
                self.fabric = fabric_fc_san_ep.switch_id
                self.slot_id = fabric_fc_san_ep.slot_id
                self.aggr_id = fabric_fc_san_ep.aggr_port_id if int(fabric_fc_san_ep.aggr_port_id) else None
                if self.aggr_id:
                    self.aggr_id = fabric_fc_san_ep.port_id
                    self.port_id = fabric_fc_san_ep.aggr_port_id
                else:
                    self.port_id = fabric_fc_san_ep.port_id
                self.user_label = fabric_fc_san_ep.usr_lbl
                self.fill_pattern = fabric_fc_san_ep.fill_pattern
                self.admin_state = fabric_fc_san_ep.admin_state
                self.admin_speed = fabric_fc_san_ep.admin_speed

                if "fabricFcVsanPortEp" in self._config.sdk_objects:
                    if self.aggr_id:
                        vsan = [vsan for vsan in self._config.sdk_objects["fabricFcVsanPortEp"]
                                if vsan.peer_dn == "sys/switch-" + self.fabric + "/slot-" + self.slot_id +
                                "/switch-fc/aggr-port-" + self.port_id + "/port-" + self.aggr_id]
                    else:
                        vsan = [vsan for vsan in self._config.sdk_objects["fabricFcVsanPortEp"]
                                if vsan.peer_dn == "sys/switch-" + self.fabric + "/slot-" + self.slot_id +
                                "/switch-fc/port-" + self.port_id]
                    if vsan:
                        if len(vsan) == 1:
                            if "net-" in vsan[0].dn.split('/')[2]:
                                # Then the vsan fabric is dual
                                self.vsan_fabric = "dual"
                                self.vsan = vsan[0].dn.split('/')[2].split('net-')[1]
                            elif "net-" in vsan[0].dn.split('/')[3]:
                                self.vsan_fabric = vsan[0].dn.split('/')[2]
                                self.vsan = vsan[0].dn.split('/')[3].split('net-')[1]

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id
        if self.aggr_id:
            port_name += '/' + self.aggr_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")

        parent_mo = "fabric/san/" + self.fabric.upper()

        if not self.is_port_member_of_san_port_channel():
            if self.aggr_id:
                mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                     slot_id=self.slot_id)
                FabricFcSanEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.port_id,
                              fill_pattern=self.fill_pattern, usr_lbl=self.user_label, admin_state=self.admin_state,
                              admin_speed=self.admin_speed)
                self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)
            else:
                mo_fabric_fc_san_ep = FabricFcSanEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                    port_id=self.port_id, fill_pattern=self.fill_pattern,
                                                    usr_lbl=self.user_label, admin_state=self.admin_state,
                                                    admin_speed=self.admin_speed)
                self._handle.add_mo(mo=mo_fabric_fc_san_ep, modify_present=True)

            if self.vsan:
                if self.vsan_fabric is None:
                    parent_mo_vsan = "fabric/san/" + self.fabric.upper()
                elif self.vsan_fabric == "dual":
                    parent_mo_vsan = "fabric/san"
                else:
                    parent_mo_vsan = "fabric/san/" + self.vsan_fabric.upper()
                mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo_vsan, name=self.vsan)
                if self.aggr_id:
                    FabricFcVsanPortEp(parent_mo_or_dn=mo_fabric_vsan, port_id=self.aggr_id, aggr_port_id=self.port_id,
                                       switch_id=self.fabric.upper(), slot_id=self.slot_id)
                else:
                    FabricFcVsanPortEp(parent_mo_or_dn=mo_fabric_vsan, port_id=self.port_id,
                                       switch_id=self.fabric.upper(), slot_id=self.slot_id)
                self._handle.add_mo(mo=mo_fabric_vsan, modify_present=True)

            if commit:
                if self.commit(detail=port_name) != True:
                    return False
        return True

    def is_port_member_of_san_port_channel(self, fabric="", slot_id="", port_id="", aggr_id=""):
        """
        Check if a port is a member of a SAN port-channel. Used by push_object()

        :param fabric: <class 'str'>: Fabric of the port to check
        :param slot_id: <class 'str'>: Slot id of the port to check
        :param port_id: <class 'str'>: Port id of the port to check
        :param aggr_id: <class 'str'>: Aggr id of the port to check (for breakout ports)
        :return: True if the port is a member of a SAN port-channel, False otherwise
        """

        fabric = self.fabric if not fabric else fabric
        slot_id = self.slot_id if not slot_id else slot_id
        port_id = self.port_id if not port_id else port_id
        aggr_id = self.aggr_id if not aggr_id else port_id

        # Query on the live system
        if aggr_id:
            ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-fc/aggr-port-" + port_id +\
                    "/port-" + aggr_id
        else:
            ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-fc/port-" + port_id

        interfaces = self._device.query(mode="classid", target="fabricFcSanPcEp",
                                        filter_str="(ep_dn,'" + ep_dn + "',type='eq')")

        if aggr_id:
            port_name = slot_id + "/" + port_id + "/" + aggr_id
        else:
            port_name = slot_id + "/" + port_id

        if len(interfaces) == 0:
            self.logger(level="debug", message="Port " + port_name + " of fabric " + fabric +
                                               " is not a member of a SAN port-channel")
            return False
        elif len(interfaces) == 1:
            self.logger(level="debug",
                        message="Port " + port_name + " of fabric " + fabric +
                                " is already a member of a SAN port-channel: no action will be committed")
            return True
        else:
            self.logger(level="error",
                        message="Something wrong happened while trying to identify if port " + port_name +
                                " of fabric " + fabric + " is a member of a SAN port-channel")
            return False


class UcsSystemSanUnifiedPort(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Unified Ports"
    _CONFIG_SECTION_NAME = "san_unified_ports"
    UCS_SYSTEM_MIN_VERSION_FOR_16_UNIFIED_PORTS = "4.0(4a)"

    def __init__(self, parent=None, json_content=None, fabric=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.slot_id = None
        self.port_id_start = None
        self.port_id_end = None
        self.admin_state = None

        if self._config.load_from == "live":
            if fabric:
                self.fabric = fabric
                if "fabricFcSanPcEp" in self._config.sdk_objects:
                    san_unified_port_list = [port for port in self._config.sdk_objects["fcPIo"]
                                             if port.switch_id == self.fabric and port.unified_port == "yes"]
                    if san_unified_port_list:
                        for san_unified_port in san_unified_port_list:
                            self.slot_id = san_unified_port.slot_id
                            if san_unified_port.aggr_port_id != "0":
                                # We are facing a Unified Port that is in FC Breakout Mode
                                if not self.port_id_start:
                                    self.port_id_start = san_unified_port.aggr_port_id
                                else:
                                    if int(self.port_id_start) > int(san_unified_port.aggr_port_id):
                                        self.port_id_start = san_unified_port.aggr_port_id
                                if not self.port_id_end:
                                    self.port_id_end = san_unified_port.aggr_port_id
                                else:
                                    if int(self.port_id_end) < int(san_unified_port.aggr_port_id):
                                        self.port_id_end = san_unified_port.aggr_port_id
                            else:
                                if not self.port_id_start:
                                    self.port_id_start = san_unified_port.port_id
                                else:
                                    if int(self.port_id_start) > int(san_unified_port.port_id):
                                        self.port_id_start = san_unified_port.port_id
                                if not self.port_id_end:
                                    self.port_id_end = san_unified_port.port_id
                                else:
                                    if int(self.port_id_end) < int(san_unified_port.port_id):
                                        self.port_id_end = san_unified_port.port_id

                    else:
                        self.fabric = None
                        # In order to not push the fabric parameter alone

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " + self.slot_id +
                                '/' + self.port_id_start + " to " + self.port_id_end)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id_start + " to " + self.port_id_end +
                                ", waiting for a commit")

        # Checking if the values are valid depending on FI model
        if self._device:
            if self._device.fi_a_model == "UCS-FI-6248UP":
                self.logger("debug", "Trying to set Unified Ports on FI model " + self._device.fi_a_model)
                if self.slot_id not in ["1", "2"]:
                    self.logger("error", "Incorrect values for slot_id in fabric " + self.fabric)
                    return False
                # for base module
                if (self.slot_id == "1") and (int(self.port_id_start) % 2 == 0 or self.port_id_end != "32"
                                              or int(self.port_id_start) >= int(self.port_id_end)):
                    self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                    return False
                # for expansion module
                elif (self.slot_id == "2") and (int(self.port_id_start) % 2 == 0 or self.port_id_end != "16"
                                                or int(self.port_id_start) >= int(self.port_id_end)):
                    self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                    return False

            elif self._device.fi_a_model == "UCS-FI-6296UP":
                self.logger("debug", "Trying to set Unified Ports on FI model " + self._device.fi_a_model)
                if self.slot_id not in ["1", "2", "3", "4"]:
                    self.logger("error", "Incorrect values for slot_id in fabric " + self.fabric)
                    return False
                # for base module
                if (self.slot_id == "1") and (int(self.port_id_start) % 2 == 0 or self.port_id_end != "48"
                                              or int(self.port_id_start) >= int(self.port_id_end)):
                    self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                    return False
                # for expansion modules
                elif (self.slot_id in ["2", "3", "4"]) and (int(self.port_id_start) % 2 == 0
                                                            or self.port_id_end != "16"
                                                            or int(self.port_id_start) >= int(self.port_id_end)):
                    self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                    return False

            elif self._device.fi_a_model == "UCS-FI-6332-16UP":
                self.logger("debug", "Trying to set Unified Ports on FI model " + self._device.fi_a_model)
                if self.slot_id != "1":
                    self.logger("error", "Incorrect values for slot_id in fabric " + self.fabric)
                    return False
                if self.port_id_end not in ["6", "12", "16"] or self.port_id_start != "1"\
                        or int(self.port_id_start) >= int(self.port_id_end):
                    self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                    return False

            elif self._device.fi_a_model == "UCS-FI-6454":
                self.logger("debug", "Trying to set Unified Ports on FI model " + self._device.fi_a_model)
                if self.slot_id != "1":
                    self.logger("error", "Incorrect values for slot_id in fabric " + self.fabric)
                    return False

                # We handle the case of FI 6454 running version below 4.0(4a), which only supports 8 Unified Ports
                min_version_for_16_unified_ports = UcsVersion(self.UCS_SYSTEM_MIN_VERSION_FOR_16_UNIFIED_PORTS)
                if self._config.parent.parent.version.__le__(min_version_for_16_unified_ports):
                    self.logger(level="debug",
                                message="Running a version that supports up to 8 Unified Ports only on FI 6454")
                    if self.port_id_end not in ["4", "8"] or self.port_id_start != "1" \
                            or int(self.port_id_start) >= int(self.port_id_end):
                        self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                        return False
                else:
                    self.logger(level="debug",
                                message="Running a version that supports up to 16 Unified Ports on FI 6454")
                    if self.port_id_end not in ["4", "8", "12", "16"] or self.port_id_start != "1" \
                            or int(self.port_id_start) >= int(self.port_id_end):
                        self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                        return False

            elif self._device.fi_a_model == "UCS-FI-64108":
                self.logger("debug", "Trying to set Unified Ports on FI model " + self._device.fi_a_model)
                if self.slot_id != "1":
                    self.logger("error", "Incorrect values for slot_id in fabric " + self.fabric)
                    return False
                if self.port_id_end not in ["4", "8", "12", "16"] or self.port_id_start != "1"\
                        or int(self.port_id_start) >= int(self.port_id_end):
                    self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                    return False

            elif self._device.fi_a_model == "UCS-FI-6536":
                self.logger("debug", "Trying to set Unified Ports on FI model " + self._device.fi_a_model)
                if self.slot_id != "1":
                    self.logger("error", "Incorrect values for slot_id in fabric " + self.fabric)
                    return False
                if self.port_id_start not in ["33", "34", "35", "36"] or self.port_id_end != "36"\
                        or int(self.port_id_start) >= int(self.port_id_end):
                    self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                    return False

            elif self._device.fi_a_model == "UCS-FI-M-6324":
                self.logger("debug", "Trying to set Unified Ports on FI model " + self._device.fi_a_model)
                if self.slot_id != "1":
                    self.logger("error", "Incorrect values for slot_id in fabric " + self.fabric)
                    return False
                if self.port_id_end not in ["1", "2", "3", "4"] or self.port_id_start != "1"\
                        or int(self.port_id_start) > int(self.port_id_end):
                    self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                    return False

            elif self._device.fi_a_model == "UCSX-S9108-100G":
                self.logger("debug", "Trying to set Unified Ports on FI model " + self._device.fi_a_model)
                if self.slot_id != "1":
                    self.logger("error", "Incorrect values for slot_id in fabric " + self.fabric)
                    return False
                if self.port_id_end not in ["1", "2"] or self.port_id_start != "1"\
                        or int(self.port_id_start) > int(self.port_id_end):
                    self.logger("error", "Incorrect values for port_id start or end in fabric " + self.fabric)
                    return False

            else:
                self.logger("error", "Trying to set Unified Ports on unsupported FI model: " + self._device.fi_a_model)
                return False
        else:
            self.logger("error", "Error while checking Fabric Interconnects model")
            return False

        # Creating a list of excluded ports (FC storage & FC uplink) to avoid setting them twice
        excluded = []
        for port in (self._config.san_storage_ports + self._config.san_uplink_ports):
            if port.fabric.upper() == self.fabric.upper() and port.slot_id == self.slot_id:
                excluded.append(int(port.port_id))

        parent_mo = "fabric/san/" + self.fabric.upper()
        for port_id in range(int(self.port_id_start), int(self.port_id_end) + 1):
            if port_id not in excluded:
                # Checking if port is currently a member of a SAN Port-Channel - if so, disabling it
                san_port_channel_id = self.get_san_port_channel_id_from_port_member(port_id=str(port_id))
                if san_port_channel_id:
                    parent_mo_spc = "fabric/san/" + self.fabric.upper() + "/pc-" + san_port_channel_id
                    mo_fabric_fc_san_pc_ep = FabricFcSanPcEp(parent_mo_or_dn=parent_mo_spc, slot_id=self.slot_id,
                                                             port_id=str(port_id), admin_state="disabled")
                    self._handle.add_mo(mo_fabric_fc_san_pc_ep, modify_present=True)
                    self.logger(level="debug",
                                message="Disabled FC port " + self.slot_id + "/" + str(port_id) + " of fabric " +
                                        self.fabric + ", member of SAN Port Channel " + san_port_channel_id)
                mo_fabric_fc_san_ep = FabricFcSanEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                    port_id=str(port_id), admin_state=self.admin_state)

                self._handle.add_mo(mo=mo_fabric_fc_san_ep, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True

    def get_san_port_channel_id_from_port_member(self, fabric=None, slot_id=None, port_id=None):
        """
        Returns the SAN port-channel ID the specified port is a member of. Used by unified_port()

        :param fabric: <class 'str'>: Fabric of the port to check
        :param slot_id: <class 'str'>: Slot id of the port to check
        :param port_id: <class 'str'>: Port id of the port to check
        :return: The port channel ID if the port is a member of a SAN port-channel, False otherwise
        """
        fabric = self.fabric if not fabric else fabric
        slot_id = self.slot_id if not slot_id else slot_id
        port_id = self.port_id if not port_id else port_id

        # Query on the live system
        ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-fc/port-" + port_id
        interfaces = self._device.query(mode="classid", target="fabricFcSanPcEp", filter_str="(ep_dn,'" + ep_dn + "')")

        if interfaces:
            if len(interfaces) == 0:
                self.logger(level="debug", message="Port " + slot_id + "/" + port_id + " of fabric " + fabric +
                                                   " is not a member of a SAN port-channel")
                return False
            elif len(interfaces) == 1:
                self.logger(level="debug", message="Port " + slot_id + "/" + port_id + " of fabric " + fabric +
                                                   " is already a member of a SAN port-channel")
                return interfaces[0].dn.split("/")[3].split('-')[1]
            else:
                self.logger(level="error",
                            message="Something wrong happened while searching if port " + slot_id + "/" + port_id +
                                    " of fabric " + fabric + " is a member of a SAN port-channel or not")
                return False


class UcsSystemServerPort(UcsSystemConfigObject):
    _CONFIG_NAME = "Server Port"
    _CONFIG_SECTION_NAME = "server_ports"

    def __init__(self, parent=None, json_content=None, fabric_dce_sw_srv_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_dce_sw_srv_ep)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.aggr_id = None
        self.user_label = None
        self.admin_state = None

        if self._config.load_from == "live":
            if fabric_dce_sw_srv_ep is not None:
                self.fabric = fabric_dce_sw_srv_ep.switch_id
                self.slot_id = fabric_dce_sw_srv_ep.slot_id
                if fabric_dce_sw_srv_ep.aggr_port_id:
                    self.aggr_id = fabric_dce_sw_srv_ep.aggr_port_id if int(fabric_dce_sw_srv_ep.aggr_port_id) else None
                else:
                    self.aggr_id = None
                if self.aggr_id:
                    self.aggr_id = fabric_dce_sw_srv_ep.port_id
                    self.port_id = fabric_dce_sw_srv_ep.aggr_port_id
                else:
                    self.port_id = fabric_dce_sw_srv_ep.port_id
                self.user_label = fabric_dce_sw_srv_ep.usr_lbl
                self.admin_state = fabric_dce_sw_srv_ep.admin_state

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id
        if self.aggr_id:
            port_name += '/' + self.aggr_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")

        parent_mo = "fabric/server/sw-" + self.fabric.upper()

        if not self.is_port_member_of_server_port_channel():
            if self.aggr_id:
                mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                     slot_id=self.slot_id)
                FabricDceSwSrvEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.aggr_id,
                                 usr_lbl=self.user_label, admin_state=self.admin_state)
                self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)

            else:
                mo_fabric_dce_sw_srv_ep = FabricDceSwSrvEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                           port_id=self.port_id, usr_lbl=self.user_label,
                                                           admin_state=self.admin_state)
                self._handle.add_mo(mo=mo_fabric_dce_sw_srv_ep, modify_present=True)

            if commit:
                if self.commit(detail=port_name) != True:
                    return False

        return True

    def is_port_member_of_server_port_channel(self, fabric="", slot_id="", port_id="", aggr_id=""):
        """
        Check if a port is a member of a Server port-channel. Used by push_object()

        :param fabric: <class 'str'>: Fabric of the port to check
        :param slot_id: <class 'str'>: Slot id of the port to check
        :param port_id: <class 'str'>: Port id of the port to check
        :param aggr_id: <class 'str'>: Aggr id of the port to check (for breakout ports)
        :return: True if the port is a member of a Server port-channel, False otherwise
        """

        fabric = self.fabric if not fabric else fabric
        slot_id = self.slot_id if not slot_id else slot_id
        port_id = self.port_id if not port_id else port_id
        aggr_id = self.aggr_id if not aggr_id else port_id

        # Query on the live system
        if aggr_id:
            ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-ether/aggr-port-" + port_id +\
                    "/port-" + aggr_id
        else:
            ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-ether/port-" + port_id

        interfaces = self._device.query(mode="classid", target="fabricDceSwSrvPcEp",
                                        filter_str="(ep_dn,'" + ep_dn + "',type='eq')")
        if len(interfaces) == 0:
            if aggr_id:
                self.logger(level="debug",
                            message="Port " + slot_id + "/" + port_id + "/" + aggr_id + " of fabric " + fabric +
                                    " is not a member of a Server port-channel")
            else:
                self.logger(level="debug",
                            message="Port " + slot_id + "/" + port_id + " of fabric " + fabric +
                                    " is not a member of a Server port-channel")
            return False
        elif len(interfaces) == 1:
            if aggr_id:
                self.logger(level="debug",
                            message="Port " + slot_id + "/" + port_id + "/" + aggr_id + " of fabric " + fabric +
                                    " is already a member of a Server port-channel")
            else:
                self.logger(level="debug",
                            message="Port " + slot_id + "/" + port_id + " of fabric " + fabric +
                                    " is already a member of a Server port-channel")
            return True
        else:
            if aggr_id:
                self.logger(level="error",
                            message="Something wrong happened while trying to identify if port " + slot_id + "/"
                                    + port_id + "/" + aggr_id + " of fabric " + fabric +
                                    " is a member of a Server port-channel")
            else:
                self.logger(level="error",
                            message="Something wrong happened while trying to identify if port " + slot_id + "/"
                                    + port_id + " of fabric " + fabric + " is a member of a Server port-channel")
            return False


class UcsSystemUnifiedStoragePort(UcsSystemFcoeStoragePort, UcsSystemAppliancePort):
    _CONFIG_NAME = "Unified Storage Port"
    _CONFIG_SECTION_NAME = "unified_storage_ports"

    def __init__(self, parent=None, json_content=None, ether_pio=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=ether_pio)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.aggr_id = None
        self.user_label = None
        self.flow_control_policy = None
        self.network_control_policy = None
        self.admin_speed = None
        self.admin_state = None
        self.priority = None
        self.pin_group = None
        self.vlan_port_mode = None
        self.appliance_vlans = []
        self.native_vlan = None
        self.ethernet_target_endpoint = []
        self.vsan = None
        self.vsan_fabric = None

        if self._config.load_from == "live":
            if ether_pio is not None and ether_pio.if_role == "fcoe-nas-storage":
                self.fabric = ether_pio.switch_id
                self.slot_id = ether_pio.slot_id
                self.aggr_id = ether_pio.aggr_port_id if int(ether_pio.aggr_port_id) else None
                if self.aggr_id:
                    self.aggr_id = ether_pio.port_id
                    self.port_id = ether_pio.aggr_port_id
                else:
                    self.port_id = ether_pio.port_id

                # Appliance port
                fabric_eth_estc_ep = None
                if "fabricEthEstcEp" in self._config.sdk_objects:
                    for port in self._config.sdk_objects["fabricEthEstcEp"]:
                        if self.aggr_id and self.aggr_id == port.port_id and self.fabric == port.switch_id and \
                                self.slot_id == port.slot_id and self.port_id == port.aggr_port_id:
                            fabric_eth_estc_ep = port
                        elif self.fabric == port.switch_id and self.slot_id == port.slot_id and \
                                self.port_id == port.port_id:
                            fabric_eth_estc_ep = port

                if fabric_eth_estc_ep is not None:
                    UcsSystemAppliancePort.__init__(self, parent=parent, fabric_eth_estc_ep=fabric_eth_estc_ep)
                else:
                    self.logger(level='error', message="Impossible to find fabricEthEstcEp object corresponding to " +
                                                       "Unified Storage Port")

                # FCoE Storage Port
                fabric_fcoe_estc_ep = None
                if "fabricFcoeEstcEp" in self._config.sdk_objects:
                    for port in self._config.sdk_objects["fabricFcoeEstcEp"]:
                        if self.aggr_id and self.aggr_id == port.port_id and self.fabric == port.switch_id and \
                                self.slot_id == port.slot_id and self.port_id == port.aggr_port_id:
                            fabric_fcoe_estc_ep = port
                        elif self.fabric == port.switch_id and self.slot_id == port.slot_id and \
                                self.port_id == port.port_id:
                            fabric_fcoe_estc_ep = port

                if fabric_fcoe_estc_ep is not None:
                    UcsSystemFcoeStoragePort.__init__(self, parent=parent, fabric_fcoe_estc_ep=fabric_fcoe_estc_ep)
                else:
                    self.logger(level='error', message="Impossible to find fabricFcoeEstcEp object corresponding to " +
                                                       "Unified Storage Port")

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.ethernet_target_endpoint:
            for value in ["name", "mac_address"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id
        if self.aggr_id:
            port_name += '/' + self.aggr_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")
        is_pushed = True
        is_pushed = UcsSystemFcoeStoragePort.push_object(self=self, commit=commit) and is_pushed
        is_pushed = UcsSystemAppliancePort.push_object(self=self, commit=commit) and is_pushed

        return is_pushed


class UcsSystemUnifiedUplinkPort(UcsSystemLanUplinkPort, UcsSystemFcoeUplinkPort):
    _CONFIG_NAME = "Unified Uplink Port"
    _CONFIG_SECTION_NAME = "unified_uplink_ports"

    def __init__(self, parent=None, json_content=None, ether_pio=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=ether_pio)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.aggr_id = None
        self.user_label = None
        self.flow_control_policy = None
        self.link_profile = None
        self.admin_speed = None
        self.admin_state = None
        self.fec = None

        if self._config.load_from == "live":
            if ether_pio is not None and ether_pio.if_role == "network-fcoe-uplink":
                self.fabric = ether_pio.switch_id
                self.slot_id = ether_pio.slot_id
                self.aggr_id = ether_pio.aggr_port_id if int(ether_pio.aggr_port_id) else None
                if self.aggr_id:
                    self.aggr_id = ether_pio.port_id
                    self.port_id = ether_pio.aggr_port_id
                else:
                    self.port_id = ether_pio.port_id
            else:
                return None

            # Lan Uplink port
            fabric_eth_lan_ep = None
            if "fabricEthLanEp" in self._config.sdk_objects:
                for port in self._config.sdk_objects["fabricEthLanEp"]:
                    if self.aggr_id and self.aggr_id == port.port_id and self.fabric == port.switch_id \
                            and self.slot_id == port.slot_id and self.port_id == port.aggr_port_id:
                        fabric_eth_lan_ep = port
                    elif self.fabric == port.switch_id and self.slot_id == port.slot_id \
                            and self.port_id == port.port_id:
                        fabric_eth_lan_ep = port

            if fabric_eth_lan_ep is not None:
                UcsSystemLanUplinkPort.__init__(self, parent=parent, fabric_eth_lan_ep=fabric_eth_lan_ep)
            else:
                # Trying to see if LAN Uplink port is part of a LAN Port-Channel
                fabric_eth_lan_pc_ep = None
                if "fabricEthLanPcEp" in self._config.sdk_objects:
                    for port in self._config.sdk_objects["fabricEthLanPcEp"]:
                        if self.aggr_id and self.aggr_id == port.port_id and self.fabric == port.switch_id \
                                and self.slot_id == port.slot_id and self.port_id == port.aggr_port_id:
                            fabric_eth_lan_pc_ep = port
                        elif self.fabric == port.switch_id and self.slot_id == port.slot_id \
                                and self.port_id == port.port_id:
                            fabric_eth_lan_pc_ep = port

                if fabric_eth_lan_pc_ep is None:
                    # We only warn if we have found neither a corresponding fabricEthLanEp nor a fabricEthLanPcEp
                    self.logger(level="error", message="Impossible to find fabricEthLanEp")

                # Otherwise we simply ignore the port if it is part of a LAN Port-Channel, since its extra attributes
                # will be fetched in the appropriate Port-Channel section

            # FCoE Uplink Port
            fabric_fcoe_san_ep = None
            if "fabricFcoeSanEp" in self._config.sdk_objects:
                for port in self._config.sdk_objects["fabricFcoeSanEp"]:
                    if self.aggr_id and self.aggr_id == port.port_id and self.fabric == port.switch_id \
                            and self.slot_id == port.slot_id and self.port_id == port.aggr_port_id:
                        fabric_fcoe_san_ep = port
                    elif self.fabric == port.switch_id and self.slot_id == port.slot_id \
                            and self.port_id == port.port_id:
                        fabric_fcoe_san_ep = port

            if fabric_fcoe_san_ep is not None:
                UcsSystemFcoeUplinkPort.__init__(self, parent=parent, fabric_fcoe_san_ep=fabric_fcoe_san_ep)
            else:
                # Trying to see if FCoE Uplink port is part of a FCoE Port-Channel
                fabric_fcoe_san_pc_ep = None
                if "fabricFcoeSanPcEp" in self._config.sdk_objects:
                    for port in self._config.sdk_objects["fabricFcoeSanPcEp"]:
                        if self.aggr_id and self.aggr_id == port.port_id and self.fabric == port.switch_id \
                                and self.slot_id == port.slot_id and self.port_id == port.aggr_port_id:
                            fabric_fcoe_san_pc_ep = port
                        elif self.fabric == port.switch_id and self.slot_id == port.slot_id \
                                and self.port_id == port.port_id:
                            fabric_fcoe_san_pc_ep = port

                if fabric_fcoe_san_pc_ep is None:
                    # We only warn if we have found neither a corresponding fabricFcoeSanEp nor a fabricFcoeSanPcEp
                    self.logger(level="error", message="Impossible to find fabricFcoeSanEp")

                # Otherwise we simply ignore the port if it is part of a FCoE Port-Channel, since its extra attributes
                # will be fetched in the appropriate Port-Channel section

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        port_name = self.fabric + "/" + self.slot_id + '/' + self.port_id
        if self.aggr_id:
            port_name += '/' + self.aggr_id

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + port_name)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + port_name +
                                ", waiting for a commit")

        is_pushed = True
        is_pushed = UcsSystemFcoeUplinkPort.push_object(self=self, commit=commit) and is_pushed
        is_pushed = UcsSystemLanUplinkPort.push_object(self=self, commit=commit) and is_pushed

        return is_pushed
