# coding: utf-8
# !/usr/bin/env python

""" lan.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

import time

from netaddr import EUI, IPAddress

from ucsmsdk.mometa.dpsec.DpsecMac import DpsecMac
from ucsmsdk.mometa.epqos.EpqosDefinition import EpqosDefinition
from ucsmsdk.mometa.epqos.EpqosEgress import EpqosEgress
from ucsmsdk.mometa.fabric.FabricBreakout import FabricBreakout
from ucsmsdk.mometa.fabric.FabricDceSwSrvEp import FabricDceSwSrvEp
from ucsmsdk.mometa.fabric.FabricEthEstcEp import FabricEthEstcEp
from ucsmsdk.mometa.fabric.FabricEthEstcPc import FabricEthEstcPc
from ucsmsdk.mometa.fabric.FabricEthEstcPcEp import FabricEthEstcPcEp
from ucsmsdk.mometa.fabric.FabricEthLanEp import FabricEthLanEp
from ucsmsdk.mometa.fabric.FabricEthLanPc import FabricEthLanPc
from ucsmsdk.mometa.fabric.FabricEthLanPcEp import FabricEthLanPcEp
from ucsmsdk.mometa.fabric.FabricEthLinkProfile import FabricEthLinkProfile
from ucsmsdk.mometa.fabric.FabricEthTargetEp import FabricEthTargetEp
from ucsmsdk.mometa.fabric.FabricEthVlanPc import FabricEthVlanPc
from ucsmsdk.mometa.fabric.FabricEthVlanPortEp import FabricEthVlanPortEp
from ucsmsdk.mometa.fabric.FabricLacpPolicy import FabricLacpPolicy
from ucsmsdk.mometa.fabric.FabricLanPinGroup import FabricLanPinGroup
from ucsmsdk.mometa.fabric.FabricLanPinTarget import FabricLanPinTarget
from ucsmsdk.mometa.fabric.FabricMulticastPolicy import FabricMulticastPolicy
from ucsmsdk.mometa.fabric.FabricNetGroup import FabricNetGroup
from ucsmsdk.mometa.fabric.FabricNetGroupRef import FabricNetGroupRef
from ucsmsdk.mometa.fabric.FabricPooledVlan import FabricPooledVlan
from ucsmsdk.mometa.fabric.FabricSubGroup import FabricSubGroup
from ucsmsdk.mometa.fabric.FabricUdldLinkPolicy import FabricUdldLinkPolicy
from ucsmsdk.mometa.fabric.FabricUdldPolicy import FabricUdldPolicy
from ucsmsdk.mometa.fabric.FabricVlan import FabricVlan
from ucsmsdk.mometa.fabric.FabricVlanGroupReq import FabricVlanGroupReq
from ucsmsdk.mometa.fabric.FabricVlanReq import FabricVlanReq
from ucsmsdk.mometa.firmware.FirmwareAck import FirmwareAck
from ucsmsdk.mometa.flowctrl.FlowctrlItem import FlowctrlItem
from ucsmsdk.mometa.ippool.IppoolBlock import IppoolBlock
from ucsmsdk.mometa.ippool.IppoolIpV6Block import IppoolIpV6Block
from ucsmsdk.mometa.ippool.IppoolPool import IppoolPool
from ucsmsdk.mometa.macpool.MacpoolBlock import MacpoolBlock
from ucsmsdk.mometa.macpool.MacpoolPool import MacpoolPool
from ucsmsdk.mometa.nwctrl.NwctrlDefinition import NwctrlDefinition
from ucsmsdk.mometa.qosclass.QosclassEthBE import QosclassEthBE
from ucsmsdk.mometa.qosclass.QosclassEthClassified import QosclassEthClassified
from ucsmsdk.mometa.qosclass.QosclassFc import QosclassFc
from ucsmsdk.mometa.qosclass.QosclassSlowDrain import QosclassSlowDrain
from ucsmsdk.mometa.vnic.VnicDynamicConPolicy import VnicDynamicConPolicy
from ucsmsdk.mometa.vnic.VnicDynamicConPolicyRef import VnicDynamicConPolicyRef
from ucsmsdk.mometa.vnic.VnicEther import VnicEther
from ucsmsdk.mometa.vnic.VnicEtherIf import VnicEtherIf
from ucsmsdk.mometa.vnic.VnicIScsiLCP import VnicIScsiLCP
from ucsmsdk.mometa.vnic.VnicLanConnPolicy import VnicLanConnPolicy
from ucsmsdk.mometa.vnic.VnicLanConnTempl import VnicLanConnTempl
from ucsmsdk.mometa.vnic.VnicUsnicConPolicyRef import VnicUsnicConPolicyRef
from ucsmsdk.mometa.vnic.VnicVlan import VnicVlan
from ucsmsdk.mometa.vnic.VnicVmqConPolicyRef import VnicVmqConPolicyRef
from ucsmsdk.mometa.vnic.VnicVnicBehPolicy import VnicVnicBehPolicy

from easyucs import common
from easyucs.config.object import UcsSystemConfigObject
from easyucs.config.ucs.san import UcsSystemFcoeStoragePort, UcsSystemFcoeUplinkPort


class UcsSystemLanUplinkPort(UcsSystemConfigObject):
    _CONFIG_NAME = "LAN Uplink Port"

    def __init__(self, parent=None, json_content=None, fabric_eth_lan_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
        if commit:
            if self.aggr_id:
                self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + "/" +
                                    self.slot_id + '/' + self.port_id + "/" + self.aggr_id)
            else:
                self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                    self.slot_id + '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id + ", waiting for a commit")
        parent_mo = "fabric/lan/" + self.fabric.upper()

        if self.aggr_id:
            mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                 slot_id=self.slot_id)
            FabricEthLanEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.aggr_id,
                           usr_lbl=self.user_label, flow_ctrl_policy=self.flow_control_policy,
                           eth_link_profile_name=self.link_profile,
                           admin_state=self.admin_state)
            self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)

            if commit:
                if self.commit(detail=self.fabric + "/" + self.slot_id + '/' + self.port_id + '/' + self.aggr_id) != True:
                    return False
        else:

            mo_fabric_eth_lan_ep = FabricEthLanEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id, port_id=self.port_id,
                                                  usr_lbl=self.user_label, flow_ctrl_policy=self.flow_control_policy,
                                                  eth_link_profile_name=self.link_profile, admin_speed=self.admin_speed,
                                                  admin_state=self.admin_state, fec=self.fec)

            self._handle.add_mo(mo=mo_fabric_eth_lan_ep, modify_present=True)

            if commit:
                if self.commit(detail=self.fabric + "/" + self.slot_id + '/' + self.port_id) != True:
                    return False
        return True


class UcsSystemAppliancePort(UcsSystemConfigObject):
    _CONFIG_NAME = "Appliance Port"

    def __init__(self, parent=None, json_content=None, fabric_eth_estc_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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

                # We need to set all values that are not present in the config file to None
                for element in self.ethernet_target_endpoint:
                    for value in ["name", "mac_address"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " + self.slot_id +
                                '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id + ", waiting for a commit")

        parent_mo = "fabric/eth-estc/" + self.fabric.upper()

        if self.aggr_id:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + "/" + self.slot_id +
                                '/' + self.port_id + '/' + self.aggr_id)
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

            if commit:
                if self.commit(detail=self.fabric + "/" + self.slot_id + '/' + self.port_id + '/' + self.aggr_id) != True:
                    return False

        else:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + "/" + self.slot_id +
                                '/' + self.port_id)
            mo_fabric_eth_estc_ep = FabricEthEstcEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                    port_id=self.port_id, port_mode=self.vlan_port_mode,
                                                    admin_speed=self.admin_speed, prio=self.priority,
                                                    pin_group_name=self.pin_group,
                                                    nw_ctrl_policy_name=self.network_control_policy,
                                                    flow_ctrl_policy=self.flow_control_policy, usr_lbl=self.user_label,
                                                    admin_state=self.admin_state, fec=self.fec)
            self._handle.add_mo(mo=mo_fabric_eth_estc_ep, modify_present=True)

            if commit:
                if self.commit(detail=self.fabric + "/" + self.slot_id + '/' + self.port_id) != True:
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


class UcsSystemServerPort(UcsSystemConfigObject):
    _CONFIG_NAME = "Server Port"

    def __init__(self, parent=None, json_content=None, fabric_dce_sw_srv_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
        if commit:
            if self.aggr_id:
                self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                    self.slot_id + '/' + self.port_id + '/' + self.aggr_id)
            else:
                self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                    self.slot_id + '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id + ", waiting for a commit")

        parent_mo = "fabric/server/sw-" + self.fabric.upper()

        if not self.is_port_member_of_server_port_channel():
            if self.aggr_id:
                mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                     slot_id=self.slot_id)
                FabricDceSwSrvEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.aggr_id,
                                 usr_lbl=self.user_label, admin_state=self.admin_state)
                self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)

                if commit:
                    if self.commit(
                            detail=self.fabric + "/" + self.slot_id + '/' + self.port_id + "/" + self.aggr_id) != True:
                        return False

            else:
                mo_fabric_dce_sw_srv_ep = FabricDceSwSrvEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                           port_id=self.port_id, usr_lbl=self.user_label,
                                                           admin_state=self.admin_state)
                self._handle.add_mo(mo=mo_fabric_dce_sw_srv_ep, modify_present=True)

                if commit:
                    if self.commit(detail=self.fabric + "/" + self.slot_id + '/' + self.port_id) != True:
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
            ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-ether/aggr-port-" + aggr_id +\
                    "/port-" + port_id
        else:
            ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-ether/port-" + port_id

        interfaces = self._device.query(mode="classid", target="fabricDceSwSrvPcEp",
                                        filter_str="(ep_dn,'" + ep_dn + "',type='eq')")
        if len(interfaces) == 0:
            if aggr_id:
                self.logger(level="debug",
                            message="Port " + slot_id + "/" + aggr_id + "/" + port_id + " of fabric " + fabric +
                                    " is not a member of a Server port-channel")
            else:
                self.logger(level="debug",
                            message="Port " + slot_id + "/" + port_id + " of fabric " + fabric +
                                    " is not a member of a Server port-channel")
            return False
        elif len(interfaces) == 1:
            if aggr_id:
                self.logger(level="debug",
                            message="Port " + slot_id + "/" + aggr_id + "/" + port_id + " of fabric " + fabric +
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


class UcsSystemLanPortChannel(UcsSystemConfigObject):
    _CONFIG_NAME = "LAN Port-Channel"

    def __init__(self, parent=None, json_content=None, fabric_eth_lan_pc=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
                                interface.update({"link_profile": interface_pc_ep.eth_link_profile_name})
                                interface.update({"user_label": interface_pc_ep.usr_lbl})
                                del interface["aggr_id"]
                            self.interfaces.append(interface)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.interfaces:
                    for value in ["aggr_id", "slot_id", "port_id", "admin_state", "link_profile", "user_label"]:
                        if value not in element:
                            element[value] = None
        self.clean_object()

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


class UcsSystemAppliancePortChannel(UcsSystemConfigObject):
    _CONFIG_NAME = "Appliance Port-Channel"

    def __init__(self, parent=None, json_content=None, fabric_eth_estc_pc=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
                                del interface["aggr_id"]
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

                # We need to set all values that are not present in the config file to None
                for element in self.interfaces:
                    for value in ["aggr_id", "slot_id", "port_id", "admin_state", "user_label"]:
                        if value not in element:
                            element[value] = None

                for element in self.ethernet_target_endpoint:
                    for value in ["name", "mac_address"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

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
                if "aggr_id" in interface:
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


class UcsSystemApplianceVlan(UcsSystemConfigObject):
    _CONFIG_NAME = "Appliance VLAN"
    _UCS_SDK_OBJECT_NAME = "fabricVlan"

    def __init__(self, parent=None, json_content=None, fabric_vlan=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.native_vlan = None
        self.primary_vlan_name = None
        self.sharing_type = None
        self.id = None
        self.name = None
        self.org_permissions = []

        # Range purpose
        self.id_from = None
        self.id_to = None
        self.prefix = None

        if self._config.load_from == "live":
            if fabric_vlan is not None:
                self.id = fabric_vlan.id
                self.name = fabric_vlan.name

                if fabric_vlan.switch_id not in ["NONE", "dual"]:
                    self.fabric = fabric_vlan.switch_id
                if fabric_vlan.default_net in ["true", "yes"]:
                    self.native_vlan = "yes"
                if fabric_vlan.sharing != "none":
                    self.sharing_type = fabric_vlan.sharing
                    if self.sharing_type in ["community", "isolated"]:
                        self.primary_vlan_name = fabric_vlan.pub_nw_name

                if "fabricVlanReq" in self._config.sdk_objects:
                    for vlan_req in self._config.sdk_objects["fabricVlanReq"]:
                        if vlan_req.name == self.name:
                            org_dn = vlan_req.dn.split("/vlan-req-")[0]
                            self.org_permissions.append(org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.name + ' (' +
                                self.id + ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')' + ", waiting for a commit")

        parent_mo = "fabric/eth-estc"
        if self.fabric is not None and self.fabric not in ["NONE", "dual"]:
            parent_mo = "fabric/eth-estc/" + self.fabric

        mo_fabric_vlan = FabricVlan(parent_mo_or_dn=parent_mo, sharing=self.sharing_type, name=self.name,
                                    id=self.id, default_net=self.native_vlan, pub_nw_name=self.primary_vlan_name)
        self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                mo_fabric_vlan_req = FabricVlanReq(parent_mo_or_dn=complete_org_path, name=self.name)
                self._handle.add_mo(mo=mo_fabric_vlan_req, modify_present=True)

        if commit:
            if self.commit(detail=self.name + " (" + self.id + ")") != True:
                return False

        return True


class UcsSystemVlan(UcsSystemConfigObject):
    _CONFIG_NAME = "VLAN"
    _UCS_SDK_OBJECT_NAME = "fabricVlan"

    def __init__(self, parent=None, json_content=None, fabric_vlan=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.multicast_policy_name = None
        self.native_vlan = None
        self.primary_vlan_name = None
        self.sharing_type = None
        self.id = None
        self.name = None
        self.org_permissions = []

        # Range purpose
        self.id_from = None
        self.id_to = None
        self.prefix = None

        if self._config.load_from == "live":
            if fabric_vlan is not None:
                self.id = fabric_vlan.id
                self.name = fabric_vlan.name

                if fabric_vlan.switch_id not in ["NONE", "dual"]:
                    self.fabric = fabric_vlan.switch_id
                if fabric_vlan.mcast_policy_name != "":
                    self.multicast_policy_name = fabric_vlan.mcast_policy_name
                if fabric_vlan.default_net in ["true", "yes"]:
                    self.native_vlan = "yes"
                if fabric_vlan.sharing != "none":
                    self.sharing_type = fabric_vlan.sharing
                    if self.sharing_type in ["community", "isolated"]:
                        self.primary_vlan_name = fabric_vlan.pub_nw_name

                if "fabricVlanReq" in self._config.sdk_objects:
                    for vlan_req in self._config.sdk_objects["fabricVlanReq"]:
                        if vlan_req.name == self.name:
                            org_dn = vlan_req.dn.split("/vlan-req-")[0]
                            self.org_permissions.append(org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')' + ", waiting for a commit")

        parent_mo = "fabric/lan"
        if self.fabric is not None and self.fabric not in ["NONE", "dual"]:
            parent_mo = "fabric/lan/" + self.fabric

        mo_fabric_vlan = FabricVlan(parent_mo_or_dn=parent_mo, sharing=self.sharing_type, name=self.name,
                                    id=self.id, mcast_policy_name=self.multicast_policy_name,
                                    default_net=self.native_vlan, pub_nw_name=self.primary_vlan_name)
        self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                mo_fabric_vlan_req = FabricVlanReq(parent_mo_or_dn=complete_org_path, name=self.name)
                self._handle.add_mo(mo=mo_fabric_vlan_req, modify_present=True)

        if commit:
            if self.commit(detail=self.name + " (" + self.id + ")") != True:
                return False

        return True


class UcsSystemLanPinGroup(UcsSystemConfigObject):
    _CONFIG_NAME = "LAN Pin Group"

    def __init__(self, parent=None, json_content=None, fabric_lan_pin_group=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.interfaces = []

        if self._config.load_from == "live":
            if fabric_lan_pin_group is not None:
                self.descr = fabric_lan_pin_group.descr
                self.name = fabric_lan_pin_group.name

                if "fabricLanPinTarget" in self._config.sdk_objects:
                    interfaces = [interface for interface in self._config.sdk_objects["fabricLanPinTarget"]
                                  if "lan-pin-group-" + self.name + "/" in interface.dn]
                    if interfaces:
                        for interface_ep_pc in interfaces:
                            interface = {}
                            interface["fabric"] = interface_ep_pc.fabric_id

                            if "phys" in interface_ep_pc.ep_dn:
                                # We are facing a physical interface (not a port-channel)
                                interface["aggr_id"] = None
                                interface["slot_id"] = None
                                interface["port_id"] = None
                                if "aggr-port" in interface_ep_pc.ep_dn:
                                    interface.update({"port_id": interface_ep_pc.ep_dn.split('/')[4].split('-')[4]})
                                    interface.update({"aggr_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[4]})
                                    interface.update({"slot_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[1]})
                                else:
                                    interface.update({"port_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[4]})
                                    interface.update({"slot_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[2]})
                            elif "pc" in interface_ep_pc.ep_dn:
                                # We are facing a port-channel interface
                                interface["pc_id"] = None
                                interface.update({"pc_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[1]})
                            self.interfaces.append(interface)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.interfaces:
                    for value in ["aggr_id", "slot_id", "port_id", "fabric", "pc_id"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "fabric/lan"

        mo_fabric_lan_pin_group = FabricLanPinGroup(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        self._handle.add_mo(mo=mo_fabric_lan_pin_group, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.interfaces:
            for interface in self.interfaces:
                if interface["port_id"] and interface["pc_id"]:
                    self.logger(level="error", message="You can only choose a port_id & port_id or pc_id for an " +
                                                       "interface in LAN Pin Group : " + str(self.name))
                else:
                    # Normal behaviour
                    if interface["pc_id"]:
                        interface_dn = parent_mo + "/" + interface['fabric'] + "/pc-" + interface['pc_id']
                        detail = interface['fabric'] + "/pc-" + interface['pc_id']

                    elif interface["port_id"] and interface["slot_id"]:
                        if interface["aggr_id"]:
                            # FIXME: usage of aggr_id as port identifier or sub-interface identifier ???
                            interface_dn = parent_mo + "/" + interface['fabric'] + "/slot-" + interface['slot_id'] +\
                                           "-aggr-port-" + interface['aggr_id'] + "/phys-slot-" + interface['slot_id']\
                                           + "-port-" + interface['port_id']
                            detail = interface['fabric'] + "/" + interface['slot_id'] + "/" + interface['port_id'] +\
                                     "/" + interface['aggr_id']
                        else:
                            interface_dn = parent_mo + "/" + interface['fabric'] + "/phys-slot-" + interface['slot_id']\
                                           + "-port-" + interface['port_id']
                            detail = interface['fabric'] + "/" + interface['slot_id'] + "/" + interface['port_id']

                    FabricLanPinTarget(parent_mo_or_dn=mo_fabric_lan_pin_group, ep_dn=interface_dn,
                                       fabric_id=interface['fabric'])
                    self._handle.add_mo(mo=mo_fabric_lan_pin_group, modify_present=True)

                    if commit:
                        self.commit(detail="interface:" + detail)

        return True


class UcsSystemVlanGroup(UcsSystemConfigObject):
    _CONFIG_NAME = "VLAN Group"
    _UCS_SDK_OBJECT_NAME = "fabricNetGroup"

    def __init__(self, parent=None, json_content=None, fabric_net_group=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.vlans = []
        self.native_vlan = None
        self.lan_uplink_ports = []
        self.lan_port_channels = []
        self.org_permissions = []

        if self._config.load_from == "live":
            if fabric_net_group is not None:
                self.name = fabric_net_group.name
                self.native_vlan = fabric_net_group.native_net

                if "fabricPooledVlan" in self._config.sdk_objects:
                    vlans = [vlan for vlan in self._config.sdk_objects["fabricPooledVlan"]
                             if "fabric/lan/net-group-" + self.name in vlan.dn]
                    if vlans:
                        for vlan in vlans:
                            if vlan.name != self.native_vlan:
                                self.vlans.append(vlan.name)

                if "fabricEthVlanPortEp" in self._config.sdk_objects:
                    interfaces = [lan_uplink_port for lan_uplink_port in self._config.sdk_objects["fabricEthVlanPortEp"]
                                  if "fabric/lan/net-group-" + self.name + "/" in lan_uplink_port.dn]
                    if interfaces:
                        for eth_vlan_port_ep in interfaces:
                            lan_uplink_port = {}
                            lan_uplink_port["aggr_id"] = None
                            lan_uplink_port["slot_id"] = None
                            lan_uplink_port["port_id"] = None
                            lan_uplink_port["fabric"] = None

                            lan_uplink_port.update({"fabric": eth_vlan_port_ep.switch_id})
                            lan_uplink_port.update({"slot_id": eth_vlan_port_ep.slot_id})
                            lan_uplink_port["aggr_id"] = eth_vlan_port_ep.aggr_port_id if \
                                int(eth_vlan_port_ep.aggr_port_id) else None
                            if lan_uplink_port["aggr_id"]:
                                lan_uplink_port.update({"aggr_id": eth_vlan_port_ep.port_id})
                                lan_uplink_port.update({"port_id": eth_vlan_port_ep.aggr_port_id})
                            else:
                                lan_uplink_port.update({"port_id": eth_vlan_port_ep.port_id})
                                del lan_uplink_port["aggr_id"]
                            self.lan_uplink_ports.append(lan_uplink_port)

                if "fabricEthVlanPc" in self._config.sdk_objects:
                    port_channels = [port_channel for port_channel in self._config.sdk_objects["fabricEthVlanPc"]
                                     if "fabric/lan/net-group-" + self.name + "/pc" in port_channel.dn]
                    if port_channels:
                        for eth_vlan_pc in port_channels:
                            port_channel = {}
                            port_channel["pc_id"] = None
                            port_channel["fabric"] = None

                            port_channel.update({"pc_id": eth_vlan_pc.port_id})
                            port_channel.update({"fabric": eth_vlan_pc.switch_id})
                            self.lan_port_channels.append(port_channel)

                if "fabricVlanGroupReq" in self._config.sdk_objects:
                    for vlangroup_req in self._config.sdk_objects["fabricVlanGroupReq"]:
                        if vlangroup_req.name == self.name:
                            org_dn = vlangroup_req.dn.split("/vlan-group-req-")[0]
                            self.org_permissions.append(org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.lan_uplink_ports:
                    for value in ["aggr_id", "slot_id", "port_id", "fabric"]:
                        if value not in element:
                            element[value] = None

                for element in self.lan_port_channels:
                    for value in ["pc_id", "fabric"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "fabric/lan"
        mo_fabric_net_group = FabricNetGroup(parent_mo_or_dn=parent_mo, native_net=self.native_vlan, name=self.name)
        self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.vlans:
            for vlan in self.vlans:
                FabricPooledVlan(parent_mo_or_dn=mo_fabric_net_group, name=vlan)
                self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

                if commit:
                    self.commit(detail="vlan: " + vlan)

        if self.native_vlan:
            FabricPooledVlan(parent_mo_or_dn=mo_fabric_net_group, name=self.native_vlan)
            self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

            if commit:
                self.commit(detail="native_vlan: " + self.native_vlan)

        if self.lan_uplink_ports:
            for port in self.lan_uplink_ports:
                if port["fabric"]:
                    port["fabric"] = port["fabric"].upper()
                if "aggr_id" in port:
                    mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=mo_fabric_net_group,
                                                         aggr_port_id=port["port_id"], slot_id=port["slot_id"])
                    FabricEthVlanPortEp(parent_mo_or_dn=mo_fabric_sub_group, port_id=port["aggr_id"],
                                        slot_id=port["slot_id"], switch_id=port["fabric"])
                    detail = port["fabric"] + "/" + port["slot_id"] + "/" + port["port_id"] + "/" + port["aggr_id"]
                else:
                    FabricEthVlanPortEp(parent_mo_or_dn=mo_fabric_net_group, port_id=port["port_id"],
                                        slot_id=port["slot_id"], switch_id=port["fabric"])
                    detail = port["fabric"] + "/" + port["slot_id"] + "/" + port["port_id"]
                self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

                if commit:
                    self.commit(detail="lan_uplink_port: " + detail)

        if self.lan_port_channels:
            for port_channel in self.lan_port_channels:
                if port_channel["fabric"]:
                    port_channel["fabric"] = port_channel["fabric"].upper()
                FabricEthVlanPc(parent_mo_or_dn=mo_fabric_net_group, port_id=port_channel["pc_id"],
                                switch_id=port_channel["fabric"])
                self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

                if commit:
                    self.commit(detail="lan_port_channel: " + port["fabric"] + "/pc-" + port["pc_id"])

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                mo_fabric_ng_req = FabricVlanGroupReq(parent_mo_or_dn=complete_org_path, name=self.name)
                self._handle.add_mo(mo=mo_fabric_ng_req, modify_present=True)

                if commit:
                    self.commit(detail="Org permission: " + organization)

        return True


class UcsSystemQosSystemClass(UcsSystemConfigObject):
    _CONFIG_NAME = "QoS System Class"

    def __init__(self, parent=None, json_content=None, qos_class=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.priority = None
        self.state = None
        self.cos = None
        self.packet_drop = None
        self.weight = None
        self.mtu = None
        self.multicast_optimized = None

        if self._config.load_from == "live":
            if qos_class is not None:
                self.priority = qos_class.priority
                self.weight = qos_class.weight
                if self.priority not in ["fibre channel", "fibre-channel", "fibre_channel", "fc"]:
                    self.multicast_optimized = qos_class.multicast_optimize
                self.state = qos_class.admin_state
                self.packet_drop = qos_class.drop
                if self.packet_drop == "drop":
                    self.packet_drop = "enabled"
                if self.packet_drop == "no-drop":
                    self.packet_drop = "disabled"
                self.mtu = qos_class.mtu
                self.cos = qos_class.cos

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " " + self.priority)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " " + self.priority +
                                ", waiting for a commit")

        parent_mo = "fabric/lan/classes"

        if self.multicast_optimized == "enabled":
            self.multicast_optimized = "true"
        if self.multicast_optimized == "disabled":
            self.multicast_optimized = "false"
        if self.packet_drop == "enabled":
            self.packet_drop = "drop"
        if self.packet_drop == "disabled":
            self.packet_drop = "no-drop"

        if self.priority in ["best effort", "best-effort", "best_effort"]:
            mo_qos = QosclassEthBE(parent_mo_or_dn=parent_mo, weight=self.weight,
                                   multicast_optimize=self.multicast_optimized, mtu=self.mtu)

        elif self.priority in ["fibre channel", "fibre-channel", "fibre_channel", "fc"]:
            mo_qos = QosclassFc(parent_mo_or_dn=parent_mo, weight=self.weight, cos=self.cos)

        else:
            mo_qos = QosclassEthClassified(parent_mo_or_dn=parent_mo, priority=self.priority, drop=self.packet_drop,
                                           admin_state=self.state, weight=self.weight,
                                           multicast_optimize=self.multicast_optimized, cos=self.cos, mtu=self.mtu)

        self._handle.add_mo(mo=mo_qos, modify_present=True)
        if commit:
            if self.commit(detail=self.priority) != True:
                return False
        else:
            return True

        # Handle Reboot if any
        if self._device.fi_a_model == "UCS-FI-6332-16UP":

            mo_fabric_lan_classes_fsm = self._device.query(mode="dn", target="fabric/lan/classes/fsm")
            mo_fabric_lan_classes_fsm_wait_user_ack = \
                self._device.query(mode="dn", target="fabric/lan/classes/fsm/stage-configGlobalQoSWaitForUserAck")

            need_reboot = False

            # if "waiting for user acknowledge" or "waiting for peer reboot"
            if mo_fabric_lan_classes_fsm_wait_user_ack.stage_status == "inProgress" \
                    or mo_fabric_lan_classes_fsm.rmt_err_descr == "Wait for peer reboot":
                need_reboot = True

            if self._device.sys_mode == "cluster" and need_reboot:
                # Peer FI rebooting
                if mo_fabric_lan_classes_fsm.rmt_err_descr == "Wait for peer reboot":
                    self.logger(message="Please wait up to 720 seconds while the secondary " +
                                        "Fabric Interconnect is rebooting")
                    if not self._device.wait_for_fsm_status(
                            ucs_sdk_object_dn="fabric/lan/classes/fsm/stage-configGlobalQoSSetPeer", status="success",
                            timeout=720, attribute="stage_status"):
                        self.logger(level="error",
                                    message="Timeout exceeded while waiting for FSM state of QOS System Class " +
                                            "to reach UserAck state")
                        return False

                # Sending the user-ack
                self.logger(message="Secondary Fabric Interconnect is back, sending user-acknowledgement")
                mo_ack = FirmwareAck(parent_mo_or_dn="sys/fw-system", admin_state="trigger-immediate")
                self._handle.add_mo(mo=mo_ack, modify_present=True)
                if self.commit(detail="User-acknowledgement") != True:
                    return False

                # Handling reboot of primary FI
                self.logger(message="Caution: The system will reboot in a few seconds!")
                self.logger(message="Waiting up to 720 seconds for the primary FI to come back")
                time.sleep(240)
                if not common.check_web_page(device=self._device, url="https://" + self._device.target,
                                             str_match="Cisco", timeout=480):
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False

                # Need to reconnect
                if not self._device.connect():
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False
                self.logger(message="Reconnected to UCS system: " + self._device.name + " running version: "
                                    + self._device.version.version)

            if self._device.sys_mode == "stand-alone" and need_reboot:
                # Sending the user-ack
                self.logger(message="Sending user-acknowledgement")
                mo_ack = FirmwareAck(parent_mo_or_dn="sys/fw-system", admin_state="trigger-immediate")
                self._handle.add_mo(mo=mo_ack, modify_present=True)
                if self.commit(detail="User-acknowledgement") != True:
                    return False

                # Handling reboot of the FI
                self.logger(message="Caution: The system will reboot in a few seconds!")
                self.logger(message="Waiting up to 720 seconds for the FI to come back")
                time.sleep(240)
                if not common.check_web_page(device=self._device, url="https://" + self._device.target,
                                             str_match="Cisco", timeout=480):
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False

                # Need to reconnect
                if not self._device.connect():
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False
                self.logger(message="Reconnected to UCS system: " + self._device.name + " running version: "
                                    + self._device.version.version)
        return True


class UcsSystemSlowDrainTimers(UcsSystemConfigObject):
    _CONFIG_NAME = "Slow Drain Timers"
    _UCS_SDK_OBJECT_NAME = "qosclassSlowDrain"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)

        self.fcoe_port = None
        self.core_fcoe_port = None
        self.edge_fcoe_port = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "qosclassSlowDrain" in self._config.sdk_objects:
                qosclass_slow_drain = [policy for policy in self._config.sdk_objects["qosclassSlowDrain"]]
                if len(qosclass_slow_drain):
                    self.fcoe_port = qosclass_slow_drain[0].eth_admin_state
                    self.core_fcoe_port = qosclass_slow_drain[0].core_port_timer
                    self.edge_fcoe_port = qosclass_slow_drain[0].edge_port_timer

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        mo_qos_class_slow_drain = QosclassSlowDrain(parent_mo_or_dn="fabric/lan/classes",
                                                    eth_admin_state=self.fcoe_port,
                                                    core_port_timer=self.core_fcoe_port,
                                                    edge_port_timer=self.edge_fcoe_port)
        self._handle.add_mo(mo=mo_qos_class_slow_drain, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemUnifiedStoragePort(UcsSystemFcoeStoragePort, UcsSystemAppliancePort):
    _CONFIG_NAME = "Unified Storage Port"

    def __init__(self, parent=None, json_content=None, ether_pio=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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

                # We need to set all values that are not present in the config file to None
                for element in self.ethernet_target_endpoint:
                    for value in ["name", "mac_address"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " + self.slot_id +
                                '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id + ", waiting for a commit")

        UcsSystemFcoeStoragePort.push_object(self=self, commit=commit)
        UcsSystemAppliancePort.push_object(self=self, commit=commit)

        return True


class UcsSystemUnifiedUplinkPort(UcsSystemLanUplinkPort, UcsSystemFcoeUplinkPort):
    _CONFIG_NAME = "Unified Uplink Port"

    def __init__(self, parent=None, json_content=None, ether_pio=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
            if "fabricEthLanEp" in self._config.sdk_objects:
                fabric_eth_lan_ep = None
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
                self.logger('error', "Impossible to find fabricEthLanEp")

            # FCoE Uplink Port
            if "fabricFcoeSanEp" in self._config.sdk_objects:
                fabric_fcoe_san_ep = None
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
                self.logger('error', "Impossible to find fabricFcoeSanEp")

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " + self.slot_id +
                                '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id + ", waiting for a commit")

        UcsSystemFcoeUplinkPort.push_object(self=self, commit=commit)
        UcsSystemLanUplinkPort.push_object(self=self, commit=commit)

        return True


class UcsSystemBreakoutPort(UcsSystemConfigObject):
    _CONFIG_NAME = "Breakout Port"
    _UCS_SDK_OBJECT_NAME = "fabricBreakout"

    def __init__(self, parent=None, json_content=None, fabric_breakout=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
        self.breakout_type = None

        if self._config.load_from == "live":
            if fabric_breakout is not None:
                self.fabric = fabric_breakout.dn.split('/')[2]
                self.slot_id = fabric_breakout.slot_id
                self.port_id = fabric_breakout.port_id
                self.breakout_type = fabric_breakout.breakout_type

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " + self.slot_id +
                                '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id + ", waiting for a commit")

        parent_mo = "fabric/Cabling/" + self.fabric.upper()
        mo_fabric_breakout = FabricBreakout(parent_mo_or_dn=parent_mo, port_id=self.port_id, slot_id=self.slot_id,
                                            breakout_type=self.breakout_type)

        self._handle.add_mo(mo=mo_fabric_breakout, modify_present=True)

        if commit:
            if self.commit(detail=self.fabric + " " + self.slot_id + '/' + self.port_id) != True:
                return False
        return True


class UcsSystemIpPool(UcsSystemConfigObject):
    _CONFIG_NAME = "IP Pool"
    _UCS_SDK_OBJECT_NAME = "ippoolPool"

    def __init__(self, parent=None, json_content=None, ippool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.order = None
        self.ip_blocks = []
        self.ipv6_blocks = []

        if self._config.load_from == "live":
            if ippool_pool is not None:
                self.name = ippool_pool.name
                self.descr = ippool_pool.descr
                self.order = ippool_pool.assignment_order

                if "ippoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["ippoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ip-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"gateway": pool_block.def_gw})
                                block.update({"primary_dns": pool_block.prim_dns})
                                block.update({"secondary_dns": pool_block.sec_dns})
                                block.update({"netmask": pool_block.subnet})
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                self.ip_blocks.append(block)

                if "ippoolIpV6Block" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["ippoolIpV6Block"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ip-pool-" + self.name + "/v6block-" in pool_block.dn:
                                block = {}
                                block.update({"gateway": pool_block.def_gw})
                                block.update({"primary_dns": pool_block.prim_dns})
                                block.update({"secondary_dns": pool_block.sec_dns})
                                block.update({"prefix": pool_block.prefix})
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                self.ipv6_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.ip_blocks:
                    for value in ["gateway", "primary_dns", "secondary_dns", "netmask", "to", "from", "size"]:
                        if value not in element:
                            element[value] = None

                for element in self.ipv6_blocks:
                    for value in ["gateway", "primary_dns", "secondary_dns", "prefix", "to", "from", "size"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_ippool_pool = IppoolPool(parent_mo_or_dn=parent_mo,
                                    descr=self.descr,
                                    assignment_order=self.order,
                                    name=self.name)
        self._handle.add_mo(mo=mo_ippool_pool, modify_present=True)
        if commit:
            if self.commit() != True:
                return False

        if self.ip_blocks:
            for block in self.ip_blocks:
                mo_ip_pool_block = None
                if block["to"]:
                    mo_ip_pool_block = IppoolBlock(parent_mo_or_dn=mo_ippool_pool, to=block["to"], r_from=block["from"],
                                                   def_gw=block["gateway"], prim_dns=block["primary_dns"],
                                                   sec_dns=block["secondary_dns"], subnet=block["netmask"])
                elif block["size"]:
                    ip_pool_to = block["from"]
                    for i in range(int(block["size"])-1):
                        ip_pool_to = IPAddress(ip_pool_to) + 1
                    block["to"] = str(ip_pool_to)
                    mo_ip_pool_block = IppoolBlock(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                   r_from=block["from"],
                                                   def_gw=block["gateway"], prim_dns=block["primary_dns"],
                                                   sec_dns=block["secondary_dns"], subnet=block["netmask"])
                if mo_ip_pool_block:
                    self._handle.add_mo(mo=mo_ip_pool_block, modify_present=True)
                    if commit:
                        err = self.commit(show=False)
                        if err != True:
                            # We handle this specific error
                            if "Create-only and naming props cannot be modified after creation, class=ippoolBlock" \
                                    in err.error_descr:
                                self.logger(level="warning",
                                            message="The ip pool block from " + block["from"] + " to " + block["to"] +
                                                    " in " + str(self.name) + " can't be modified. " +
                                                    "Deleting and adding it again with the new values.")

                                # We need to delete the range
                                mo_ip_pool_block = IppoolBlock(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                               r_from=block["from"])
                                self._handle.remove_mo(mo_ip_pool_block)
                                if self.commit() != True:
                                    continue
                                # Then we need to add the range again
                                mo_ip_pool_block = IppoolBlock(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                               r_from=block["from"],
                                                               def_gw=block["gateway"], prim_dns=block["primary_dns"],
                                                               sec_dns=block["secondary_dns"], subnet=block["netmask"])
                                self._handle.add_mo(mo=mo_ip_pool_block, modify_present=True)
                                if self.commit() != True:
                                    self.logger(level="error", message="Adding ip pool blocks: aborted")
                                    return False

                            else:
                                # The print value of commit is True so we log the error if it is not the expected error
                                self.logger(level="error", message="Error in configuring " +
                                                                   self._CONFIG_NAME + ": " + err.error_descr)
                            return False

        if self.ipv6_blocks:
            for block in self.ipv6_blocks:
                mo_ip_pool_block = None
                if block["to"]:
                    mo_ip_pool_block = IppoolIpV6Block(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                       r_from=block["from"], def_gw=block["gateway"],
                                                       prim_dns=block["primary_dns"], sec_dns=block["secondary_dns"],
                                                       prefix=block["prefix"])
                elif block["size"]:
                    ip_pool_to = block["from"]
                    for i in range(int(block["size"])-1):
                        ip_pool_to = IPAddress(ip_pool_to) + 1
                    block["to"] = str(ip_pool_to)
                    mo_ip_pool_block = IppoolIpV6Block(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                       r_from=block["from"], def_gw=block["gateway"],
                                                       prim_dns=block["primary_dns"], sec_dns=block["secondary_dns"],
                                                       prefix=block["prefix"])
                if mo_ip_pool_block:
                    self._handle.add_mo(mo=mo_ip_pool_block, modify_present=True)
                    if commit:
                        err = self.commit(show=False)
                        if err != True:
                            # We handle this specific error
                            if "Create-only and naming props cannot be modified after creation, class=ippoolIpV6Block" \
                                    in err.error_descr:
                                self.logger(level="warning",
                                            message="The IPv6 pool block from " + block["from"] + " to " + block["to"]
                                                    + " in " + str(self.name) + " can't be modified." +
                                                    "Deleting and adding it again with the new values.")

                                # We need to delete the range
                                mo_ip_pool_block = IppoolIpV6Block(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                                   r_from=block["from"])
                                self._handle.remove_mo(mo_ip_pool_block)
                                if self.commit() != True:
                                    continue
                                # Then we need to add the range again
                                mo_ip_pool_block = IppoolIpV6Block(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                                   r_from=block["from"], def_gw=block["gateway"],
                                                                   prim_dns=block["primary_dns"],
                                                                   sec_dns=block["secondary_dns"],
                                                                   prefix=block["prefix"])
                                self._handle.add_mo(mo=mo_ip_pool_block, modify_present=True)
                                if self.commit() != True:
                                    self.logger(level="error", message="Adding IPv6 pool blocks: aborted")
                                    return False

                            else:
                                # The print value of commit is True so we log the error if it is not the expected error
                                self.logger(level="error", message="Error in configuring " +
                                                                   self._CONFIG_NAME + ": " + err.error_descr)
                            return False

        return True


class UcsSystemMacPool(UcsSystemConfigObject):
    _CONFIG_NAME = "MAC Pool"
    _UCS_SDK_OBJECT_NAME = "macpoolPool"

    def __init__(self, parent=None, json_content=None, macpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.order = None
        self.mac_blocks = []

        if self._config.load_from == "live":
            if macpool_pool is not None:
                self.name = macpool_pool.name
                self.descr = macpool_pool.descr
                self.order = macpool_pool.assignment_order

                if "macpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["macpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/mac-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                self.mac_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.mac_blocks:
                    for value in ["to",
                                  "from",
                                  "size"
                                  ]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_macpool_pool = MacpoolPool(parent_mo_or_dn=parent_mo,
                                      descr=self.descr,
                                      assignment_order=self.order,
                                      name=self.name)
        if self.mac_blocks:
            for block in self.mac_blocks:
                if block["to"]:
                    MacpoolBlock(parent_mo_or_dn=mo_macpool_pool, to=block["to"],
                                 r_from=block["from"])
                elif block["size"]:
                    mac_pool_to = EUI(block["from"])
                    for i in range(int(block["size"])-1):
                        mac_pool_to = EUI(int(mac_pool_to)+1)
                    mac_pool_to = str(mac_pool_to).replace("-", ":")
                    MacpoolBlock(parent_mo_or_dn=mo_macpool_pool, to=mac_pool_to,
                                 r_from=block["from"])

        self._handle.add_mo(mo=mo_macpool_pool, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemVnicTemplate(UcsSystemConfigObject):
    _CONFIG_NAME = "vNIC Template"
    _UCS_SDK_OBJECT_NAME = "vnicLanConnTempl"

    def __init__(self, parent=None, json_content=None, vnic_lan_conn_templ=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.fabric = None
        self.descr = None
        self.redundancy_type = None
        self.peer_redundancy_template = None
        self.qos_policy = None
        self.cdn_source = None
        self.cdn_name = None
        self.target = []
        self.mtu = None
        self.mac_pool = None
        self.template_type = None
        self.pin_group = None
        self.stats_threshold_policy = None
        self.network_control_policy = None
        self.connection_policy = None
        self.connection_policy_name = None
        self.vlan_native = None
        self.vlans = []
        self.vlan_groups = []

        if self._config.load_from == "live":
            if vnic_lan_conn_templ is not None:
                self.name = vnic_lan_conn_templ.name
                self.fabric = vnic_lan_conn_templ.switch_id
                self.descr = vnic_lan_conn_templ.descr
                self.redundancy_type = vnic_lan_conn_templ.redundancy_pair_type
                self.peer_redundancy_template = vnic_lan_conn_templ.peer_redundancy_templ_name
                self.qos_policy = vnic_lan_conn_templ.qos_policy_name
                self.cdn_source = vnic_lan_conn_templ.cdn_source
                self.cdn_name = vnic_lan_conn_templ.admin_cdn_name
                self.target = vnic_lan_conn_templ.target.split(',')
                self.mtu = vnic_lan_conn_templ.mtu
                self.mac_pool = vnic_lan_conn_templ.ident_pool_name
                self.template_type = vnic_lan_conn_templ.templ_type
                self.pin_group = vnic_lan_conn_templ.pin_to_group_name
                self.stats_threshold_policy = vnic_lan_conn_templ.stats_policy_name
                self.network_control_policy = vnic_lan_conn_templ.nw_ctrl_policy_name

                # Looking for the connection_policy
                if "vnicDynamicConPolicyRef" in self._parent._config.sdk_objects and not self.connection_policy:
                    for policy in self._config.sdk_objects["vnicDynamicConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ" + self.name in policy.dn:
                                self.connection_policy = "dynamic-vnic"
                                self.connection_policy_name = policy.con_policy_name
                if "vnicUsnicConPolicyRef" in self._parent._config.sdk_objects and not self.connection_policy:
                    for policy in self._config.sdk_objects["vnicUsnicConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ" + self.name in policy.dn:
                                self.connection_policy = "usNIC"
                                self.connection_policy_name = policy.con_policy_name
                if "vnicVmqConPolicyRef" in self._parent._config.sdk_objects and not self.connection_policy:
                    for policy in self._config.sdk_objects["vnicVmqConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ" + self.name in policy.dn:
                                self.connection_policy = "VMQ"
                                self.connection_policy_name = policy.con_policy_name

                if "vnicEtherIf" in self._config.sdk_objects:
                    if self._parent._dn:
                        vlans = [vlan for vlan in self._config.sdk_objects["vnicEtherIf"] if
                                 self._parent._dn + "/lan-conn-templ-" + self.name + "/" in vlan.dn]
                        if vlans:
                            for vlan in vlans:
                                if vlan.default_net in ["yes", "true"]:
                                    self.vlan_native = vlan.name
                                else:
                                    self.vlans.append(vlan.name)
                if "fabricNetGroupRef" in self._config.sdk_objects:
                    if self._parent._dn:
                        vlans = [vlan for vlan in self._config.sdk_objects["fabricNetGroupRef"] if
                                 self._parent._dn + "/lan-conn-templ-" + self.name + "/" in vlan.dn]
                        if vlans:
                            for vlan in vlans:
                                self.vlan_groups.append(vlan.name)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        target = None
        if self.target:
            if self.target.__class__.__name__ == "list":
                target = ','.join(self.target)
            # Target can be "adaptor" in the SDK but written "adapter" in the GUI
            target = target.replace("adapter", "adaptor")

        redundancy_pair_type = "none" if self.redundancy_type == "no-redundancy" else self.redundancy_type
        mo_vnic_lan_conn_temp = VnicLanConnTempl(parent_mo_or_dn=parent_mo, switch_id=self.fabric.upper(),
                                                 name=self.name, descr=self.descr, target=target,
                                                 cdn_source=self.cdn_source,
                                                 nw_ctrl_policy_name=self.network_control_policy,
                                                 admin_cdn_name=self.cdn_name,
                                                 redundancy_pair_type=redundancy_pair_type,
                                                 qos_policy_name=self.qos_policy,
                                                 peer_redundancy_templ_name=self.peer_redundancy_template,
                                                 templ_type=self.template_type, mtu=self.mtu,
                                                 ident_pool_name=self.mac_pool,
                                                 pin_to_group_name=self.pin_group,
                                                 stats_policy_name=self.stats_threshold_policy)

        if self.connection_policy:
            if self.connection_policy == "dynamic_vnic" or self.connection_policy == "dynamic-vnic":
                VnicDynamicConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                        con_policy_name=self.connection_policy_name)
            elif self.connection_policy == "usNIC" or self.connection_policy == "usnic":
                VnicUsnicConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                      con_policy_name=self.connection_policy_name)
            elif self.connection_policy == "VMQ" or self.connection_policy == "vmq":
                VnicVmqConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                    con_policy_name=self.connection_policy_name)

        # self._handle.add_mo(mo=mo_vnic_lan_conn_temp, modify_present=True)
        # if commit:
        #     if self.commit(detail=self.name) != True:
        #         return False

        if self.vlans:
            for vlan in self.vlans:
                if vlan == self.vlan_native:
                    # Avoid an issue when the native VLAN is written in the VLANS section and VLAN Native parameter
                    continue
                VnicEtherIf(parent_mo_or_dn=mo_vnic_lan_conn_temp, name=vlan, default_net="no")
        if self.vlan_native:
            VnicEtherIf(parent_mo_or_dn=mo_vnic_lan_conn_temp, name=self.vlan_native, default_net="yes")
        if self.vlan_groups:
            for vlan in self.vlan_groups:
                FabricNetGroupRef(parent_mo_or_dn=mo_vnic_lan_conn_temp, name=vlan)

        self._handle.add_mo(mo=mo_vnic_lan_conn_temp, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemQosPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "QoS Policy"
    _UCS_SDK_OBJECT_NAME = "epqosDefinition"

    def __init__(self, parent=None, json_content=None, epqos_definition=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.rate = None
        self.priority = None
        self.burst = None
        self.host_control = None

        if self._config.load_from == "live":
            if epqos_definition is not None:
                self.name = epqos_definition.name
                self.descr = epqos_definition.descr
                if "epqosEgress" in self._config.sdk_objects:
                    if self._parent._dn:
                        epqos_egress = [egress for egress in self._config.sdk_objects["epqosEgress"]
                                        if self._parent._dn + "/ep-qos-" + self.name + "/" in egress.dn]
                        if len(epqos_egress) == 1:
                            self.rate = epqos_egress[0].rate
                            self.priority = epqos_egress[0].prio
                            self.burst = epqos_egress[0].burst
                            self.host_control = epqos_egress[0].host_control

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + self.policy_name)
            return False

        mo_epqos_definition = EpqosDefinition(parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name)
        EpqosEgress(parent_mo_or_dn=mo_epqos_definition, rate=self.rate, prio=self.priority, burst=self.burst, name="",
                    host_control=self.host_control)

        self._handle.add_mo(mo=mo_epqos_definition, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemUdldLinkPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "UDLD Link Policy"

    def __init__(self, parent=None, json_content=None, fabric_udld_link_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.mode = None
        self.admin_state = None

        if self._config.load_from == "live":
            if fabric_udld_link_policy is not None:
                self.name = fabric_udld_link_policy.name
                self.mode = fabric_udld_link_policy.mode
                self.admin_state = fabric_udld_link_policy.admin_state

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "fabric/lan"
        mo_fabric_udld_link_policy = FabricUdldLinkPolicy(parent_mo_or_dn=parent_mo, mode=self.mode,
                                                          admin_state=self.admin_state, name=self.name)

        self._handle.add_mo(mo=mo_fabric_udld_link_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemLinkProfile(UcsSystemConfigObject):
    _CONFIG_NAME = "Link Profile"

    def __init__(self, parent=None, json_content=None, fabric_eth_link_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.udld_link_policy = None

        if self._config.load_from == "live":
            if fabric_eth_link_profile is not None:
                self.name = fabric_eth_link_profile.name
                self.udld_link_policy = fabric_eth_link_profile.udld_link_policy_name

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "fabric/lan"
        mo_fabric_eth_link_profile = FabricEthLinkProfile(parent_mo_or_dn=parent_mo,
                                                          udld_link_policy_name=self.udld_link_policy,
                                                          name=self.name)

        self._handle.add_mo(mo=mo_fabric_eth_link_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemApplianceNetworkControlPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Appliance Network Control Policy"

    def __init__(self, parent=None, json_content=None, nwctrl_definition=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.cdp_admin_state = None
        self.action_on_uplink_fail = None
        self.mac_register_mode = None
        self.descr = None
        self.mac_security_forge = None

        if self._config.load_from == "live":
            if nwctrl_definition is not None:
                self.name = nwctrl_definition.name
                self.cdp_admin_state = nwctrl_definition.cdp
                self.action_on_uplink_fail = nwctrl_definition.uplink_fail_action
                self.mac_register_mode = nwctrl_definition.mac_register_mode
                self.descr = nwctrl_definition.descr

                if "dpsecMac" in self._config.sdk_objects:
                    for dpsec_mac in self._config.sdk_objects["dpsecMac"]:
                        if "fabric/eth-estc/nwctrl-" + self.name in dpsec_mac.dn:
                            self.mac_security_forge = dpsec_mac.forge

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "fabric/eth-estc"
        mo_nwctrl_definition = NwctrlDefinition(parent_mo_or_dn=parent_mo, cdp=self.cdp_admin_state,
                                                name=self.name, uplink_fail_action=self.action_on_uplink_fail,
                                                mac_register_mode=self.mac_register_mode, descr=self.descr)
        DpsecMac(parent_mo_or_dn=mo_nwctrl_definition, descr=self.descr, name="", forge=self.mac_security_forge)

        self._handle.add_mo(mo=mo_nwctrl_definition, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemNetworkControlPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Network Control Policy"
    _UCS_SDK_OBJECT_NAME = "nwctrlDefinition"

    def __init__(self, parent=None, json_content=None, nwctrl_definition=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.cdp_admin_state = None
        self.action_on_uplink_fail = None
        self.mac_register_mode = None
        self.descr = None
        self.lldp_receive = None
        self.lldp_transmit = None
        self.mac_security_forge = None

        if self._config.load_from == "live":
            if nwctrl_definition is not None:
                self.name = nwctrl_definition.name
                self.cdp_admin_state = nwctrl_definition.cdp
                self.action_on_uplink_fail = nwctrl_definition.uplink_fail_action
                self.mac_register_mode = nwctrl_definition.mac_register_mode
                self.descr = nwctrl_definition.descr
                self.lldp_receive = nwctrl_definition.lldp_receive
                self.lldp_transmit = nwctrl_definition.lldp_transmit

                if "dpsecMac" in self._parent._config.sdk_objects:
                    for dpsec_mac in self._config.sdk_objects["dpsecMac"]:
                        if self._parent._dn + "/nwctrl-" + self.name in dpsec_mac.dn:
                            self.mac_security_forge = dpsec_mac.forge

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_nwctrl_definition = NwctrlDefinition(parent_mo_or_dn=parent_mo, cdp=self.cdp_admin_state,
                                                lldp_receive=self.lldp_receive, name=self.name,
                                                uplink_fail_action=self.action_on_uplink_fail,
                                                lldp_transmit=self.lldp_transmit, descr=self.descr,
                                                mac_register_mode=self.mac_register_mode)
        DpsecMac(parent_mo_or_dn=mo_nwctrl_definition, descr=self.descr, name="", forge=self.mac_security_forge)

        self._handle.add_mo(mo=mo_nwctrl_definition, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemDefaultVnicBehavior(UcsSystemConfigObject):
    _CONFIG_NAME = "Default vNIC Behavior"
    _UCS_SDK_OBJECT_NAME = "vnicVnicBehPolicy"

    def __init__(self, parent=None, json_content=None, vnic_vnic_beh_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.action = None
        self.vnic_template = None

        if self._config.load_from == "live":
            if vnic_vnic_beh_policy is not None:
                self.action = vnic_vnic_beh_policy.action
                self.vnic_template = vnic_vnic_beh_policy.nw_templ_name

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error", message="Impossible to find the parent dn of " + self._CONFIG_NAME)
            return False

        mo_vnic_vnic_beh_policy = VnicVnicBehPolicy(parent_mo_or_dn=parent_mo, action=self.action,
                                                    nw_templ_name=self.vnic_template)

        self._handle.add_mo(mo=mo_vnic_vnic_beh_policy, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemFlowControlPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Flow Control Policy"
    _UCS_SDK_OBJECT_NAME = "flowctrlItem"
    # Note: This policy is in orgs in UCS Manager but does not use orgs in its DN.

    def __init__(self, parent=None, json_content=None, flowctrl_item=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.priority = None
        self.receive = None
        self.send = None

        if self._config.load_from == "live":
            if flowctrl_item is not None:
                self.name = flowctrl_item.name
                self.priority = flowctrl_item.prio
                self.receive = flowctrl_item.rcv
                self.send = flowctrl_item.snd

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "fabric/lan/flowctrl"
        mo_flowctrl_item = FlowctrlItem(parent_mo_or_dn=parent_mo, name=self.name, snd=self.send,
                                        rcv=self.receive, prio=self.priority)

        self._handle.add_mo(mo=mo_flowctrl_item, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemMulticastPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Multicast Policy"
    _UCS_SDK_OBJECT_NAME = "fabricMulticastPolicy"

    def __init__(self, parent=None, json_content=None, fabric_multicast_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.igmp_snooping_state = None
        self.igmp_snooping_querier_state = None
        self.fi_a_querier_ip_address = None
        self.fi_b_querier_ip_address = None

        if self._config.load_from == "live":
            if fabric_multicast_policy is not None:
                self.name = fabric_multicast_policy.name
                self.descr = fabric_multicast_policy.descr
                self.igmp_snooping_state = fabric_multicast_policy.snooping_state
                self.igmp_snooping_querier_state = fabric_multicast_policy.querier_state

                if self.igmp_snooping_querier_state == "enabled":
                    self.fi_a_querier_ip_address = fabric_multicast_policy.querier_ip_addr
                    self.fi_b_querier_ip_address = fabric_multicast_policy.querier_ip_addr_peer

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_fabric_multicast_policy = FabricMulticastPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr,
                                                           querier_state=self.igmp_snooping_querier_state,
                                                           snooping_state=self.igmp_snooping_state,
                                                           querier_ip_addr_peer=self.fi_b_querier_ip_address,
                                                           querier_ip_addr=self.fi_a_querier_ip_address)

        self._handle.add_mo(mo=mo_fabric_multicast_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemLinkProtocolPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Link Protocol Policy"
    _UCS_SDK_OBJECT_NAME = "fabricUdldPolicy"

    def __init__(self, parent=None, json_content=None, fabric_udld_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.message_interval = None
        self.recovery_action = None

        if self._config.load_from == "live":
            if fabric_udld_policy is not None:
                self.message_interval = fabric_udld_policy.msg_interval
                self.recovery_action = fabric_udld_policy.recovery_action

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error", message="Impossible to find the parent dn of " + self._CONFIG_NAME)
            return False

        mo_fabric_udld_policy = FabricUdldPolicy(parent_mo_or_dn=parent_mo, msg_interval=self.message_interval,
                                                 recovery_action=self.recovery_action)
        self._handle.add_mo(mo=mo_fabric_udld_policy, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemLacpPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "LACP Policy"
    _UCS_SDK_OBJECT_NAME = "fabricLacpPolicy"

    def __init__(self, parent=None, json_content=None, fabric_lacp_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.suspend_individual = None
        self.lacp_rate = None

        if self._config.load_from == "live":
            if fabric_lacp_policy is not None:
                self.name = fabric_lacp_policy.name
                self.descr = fabric_lacp_policy.descr
                self.suspend_individual = fabric_lacp_policy.suspend_individual
                self.lacp_rate = fabric_lacp_policy.fast_timer

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_fabric_lacp_policy = FabricLacpPolicy(parent_mo_or_dn=parent_mo, suspend_individual=self.suspend_individual,
                                                 fast_timer=self.lacp_rate, name=self.name)
        self._handle.add_mo(mo=mo_fabric_lacp_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemLanConnectivityPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "LAN Connectivity Policy"
    _UCS_SDK_OBJECT_NAME = "vnicLanConnPolicy"

    def __init__(self, parent=None, json_content=None, vnic_lan_conn_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.vnics = []
        self.iscsi_vnics = []

        if self._config.load_from == "live":
            if vnic_lan_conn_policy is not None:
                self.name = vnic_lan_conn_policy.name
                self.descr = vnic_lan_conn_policy.descr

                if "vnicEther" in self._parent._config.sdk_objects:
                    for vnic_ether in self._config.sdk_objects["vnicEther"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-pol-" + self.name in vnic_ether.dn:
                                vnic = {}
                                vnic.update({"name": vnic_ether.name})
                                vnic.update({"adapter_policy": vnic_ether.adaptor_profile_name})
                                vnic.update({"order": vnic_ether.order})
                                if vnic_ether.nw_templ_name:
                                    vnic.update({"template": vnic_ether.nw_templ_name})
                                else:
                                    vnic.update({"fabric": vnic_ether.switch_id})
                                    vnic.update({"mac_address_pool": vnic_ether.ident_pool_name})
                                    if not vnic_ether.ident_pool_name and vnic_ether.addr == "derived":
                                        vnic.update({"mac_address": "hardware-default"})
                                    vnic.update({"mtu": vnic_ether.mtu})
                                    vnic.update({"qos_policy": vnic_ether.qos_policy_name})
                                    vnic.update({"network_control_policy": vnic_ether.nw_ctrl_policy_name})
                                    vnic.update({"cdn_source": vnic_ether.cdn_source})
                                    vnic.update({"cdn_name": vnic_ether.admin_cdn_name})
                                    vnic.update({"pin_group": vnic_ether.pin_to_group_name})

                                    vnic.update({"connection_policy_name": None})
                                    if "vnicDynamicConPolicyRef" in self._parent._config.sdk_objects:
                                        for conn_policy in self._config.sdk_objects["vnicDynamicConPolicyRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update({"connection_policy": "dynamic-vnic"})
                                                vnic.update({"connection_policy_name": conn_policy.con_policy_name})
                                    if "vnicUsnicConPolicyRef" in self._parent._config.sdk_objects \
                                            and not vnic['connection_policy_name']:
                                        for conn_policy in self._config.sdk_objects["vnicUsnicConPolicyRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update({"connection_policy": "usnic"})
                                                vnic.update({"connection_policy_name": conn_policy.con_policy_name})
                                    if "vnicVmqConPolicyRef" in self._parent._config.sdk_objects \
                                            and not vnic['connection_policy_name']:
                                        for conn_policy in self._config.sdk_objects["vnicVmqConPolicyRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update({"connection_policy": "vmq"})
                                                vnic.update({"connection_policy_name": conn_policy.con_policy_name})

                                    if "vnicEtherIf" in self._parent._config.sdk_objects:
                                        vnic.update({"vlans": []})
                                        for conn_policy in self._config.sdk_objects["vnicEtherIf"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                if conn_policy.default_net == "yes":
                                                    vnic.update({"vlan_native": conn_policy.name})
                                                else:
                                                    vnic['vlans'].append(conn_policy.name)

                                self.vnics.append(vnic)

                if "vnicIScsiLCP" in self._parent._config.sdk_objects:
                    for vnic_iscsi_lcp in self._config.sdk_objects["vnicIScsiLCP"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-pol-" + self.name in vnic_iscsi_lcp.dn:
                                vnic = {}
                                vnic.update({"name": vnic_iscsi_lcp.name})
                                vnic.update({"overlay_vnic": vnic_iscsi_lcp.vnic_name})
                                vnic.update({"iscsi_adapter_policy": vnic_iscsi_lcp.adaptor_profile_name})
                                vnic.update({"mac_address_pool": vnic_iscsi_lcp.ident_pool_name})
                                if "vnicVlan" in self._parent._config.sdk_objects:
                                    for vnicvlan in self._config.sdk_objects["vnicVlan"]:
                                        if self._parent._dn + "/lan-conn-pol-" + self.name + '/iscsi-' + \
                                                vnic['name'] + '/' in vnicvlan.dn:
                                            vnic.update({"vlan": vnicvlan.vlan_name})
                                self.iscsi_vnics.append(vnic)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.vnics:
                    for value in ["vlans", "connection_policy", "connection_policy_name", "template", "adapter_policy",
                                  "name", "cdn_source", "cdn_name", "order", "fabric",
                                  "mac_address_pool", "mtu", "qos_policy", "network_control_policy",
                                  "vlan_native", "pin_group", "mac_address"]:
                        if value not in element:
                            element[value] = None
                for element in self.iscsi_vnics:
                    for value in ["vlan", "mac_address_pool", "overlay_vnic", "name", "iscsi_adapter_policy"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_vnic_lan_conn_policy = VnicLanConnPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        self._handle.add_mo(mo=mo_vnic_lan_conn_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.vnics:
            for vnic in self.vnics:
                if vnic['template']:
                    mo_vnic_ether = VnicEther(parent_mo_or_dn=mo_vnic_lan_conn_policy,
                                              adaptor_profile_name=vnic['adapter_policy'],
                                              nw_templ_name=vnic['template'],
                                              name=vnic['name'],
                                              order=vnic['order'])
                    self._handle.add_mo(mo=mo_vnic_ether, modify_present=True)
                    # We need to commit the interface first and then add the vlan and connection policy to it
                    if commit:
                        if self.commit(detail=vnic['name'] + " on " + str(self.name)) != True:
                            # We can use continue because the commit buffer is discard if it's an SDK error exception
                            continue
                else:
                    if vnic['fabric']:
                        vnic['fabric'] = vnic['fabric'].upper()
                    mac_address_pool = vnic["mac_address_pool"]
                    mac_address = vnic["mac_address"]
                    if mac_address == "hardware-default":
                        mac_address_pool = ""
                        mac_address = "derived"
                    mo_vnic_ether = VnicEther(parent_mo_or_dn=mo_vnic_lan_conn_policy,
                                              name=vnic['name'], mtu=vnic['mtu'],
                                              adaptor_profile_name=vnic['adapter_policy'],
                                              order=vnic['order'], switch_id=vnic['fabric'],
                                              ident_pool_name=mac_address_pool,
                                              addr=mac_address,
                                              qos_policy_name=vnic['qos_policy'],
                                              nw_ctrl_policy_name=vnic['network_control_policy'],
                                              cdn_source=vnic['cdn_source'],
                                              admin_cdn_name=vnic['cdn_name'],
                                              pin_to_group_name=vnic['pin_group'])
                    self._handle.add_mo(mo=mo_vnic_ether, modify_present=True)
                    # We need to commit the interface first and then add the vlan and connection policy to it
                    if commit:
                        if self.commit(detail=vnic['name'] + " on " + str(self.name)) != True:
                            # We can use continue because the commit buffer is discard if it's an SDK error exception
                            continue

                    # Creating connection_policy
                    if vnic["connection_policy"] and vnic["connection_policy_name"]:
                        connection_policy = vnic['connection_policy']
                        connection_policy_name = vnic['connection_policy_name']
                        if connection_policy == "dynamic-vnic":
                            # connection_policy = "SRIOV-VMFEX"
                            VnicDynamicConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                                    con_policy_name=connection_policy_name)
                        elif connection_policy == "usNIC" or connection_policy == "usnic":
                            # connection_policy = "SRIOV-USNIC"
                            VnicUsnicConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                                  con_policy_name=connection_policy_name)
                        elif connection_policy == "VMQ" or connection_policy == "vmq":
                            # connection_policy = "VMQ"
                            VnicVmqConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                                con_policy_name=connection_policy_name)

                    # Adding the vlans
                    if vnic['vlan_native']:
                        mo_vnic_ether_if = VnicEtherIf(parent_mo_or_dn=mo_vnic_ether,
                                                       name=vnic['vlan_native'],
                                                       default_net="yes")
                        self._handle.add_mo(mo_vnic_ether_if, modify_present=True)
                    if vnic['vlans']:
                        for vlan in vnic['vlans']:
                            mo_vnic_ether_if = VnicEtherIf(parent_mo_or_dn=mo_vnic_ether,
                                                           name=vlan,
                                                           default_net="no")
                            self._handle.add_mo(mo_vnic_ether_if, modify_present=True)

                self._handle.add_mo(mo=mo_vnic_ether, modify_present=True)

            for iscsi_vnic in self.iscsi_vnics:
                mo_vnic_iscsi_lcp = VnicIScsiLCP(parent_mo_or_dn=mo_vnic_lan_conn_policy,
                                                 adaptor_profile_name=iscsi_vnic["iscsi_adapter_policy"],
                                                 ident_pool_name=iscsi_vnic["mac_address_pool"],
                                                 name=iscsi_vnic["name"],
                                                 vnic_name=iscsi_vnic["overlay_vnic"])
                VnicVlan(parent_mo_or_dn=mo_vnic_iscsi_lcp, name="", vlan_name=iscsi_vnic["vlan"])

                self._handle.add_mo(mo=mo_vnic_iscsi_lcp, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True

class UcsSystemDynamicVnicConnectionPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Dynamic vNIC Connection Policy"
    _UCS_SDK_OBJECT_NAME = "vnicDynamicConPolicy"

    def __init__(self, parent=None, json_content=None, vnic_dynamic_con_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.number_dynamic_vnics = None
        self.adapter_policy = None
        self.protection = None

        if self._config.load_from == "live":
            if vnic_dynamic_con_policy is not None:
                self.name = vnic_dynamic_con_policy.name
                self.descr = vnic_dynamic_con_policy.descr
                self.number_dynamic_vnics = vnic_dynamic_con_policy.dynamic_eth
                self.adapter_policy = vnic_dynamic_con_policy.adaptor_profile_name
                self.protection = vnic_dynamic_con_policy.protection

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + self.name)
            return False

        mo_vnic_dynamic_con_policy = VnicDynamicConPolicy(parent_mo_or_dn=parent_mo,
                                                          descr=self.descr,
                                                          name=self.name,
                                                          dynamic_eth=self.number_dynamic_vnics,
                                                          adaptor_profile_name=self.adapter_policy,
                                                          protection=self.protection)

        self._handle.add_mo(mo=mo_vnic_dynamic_con_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
