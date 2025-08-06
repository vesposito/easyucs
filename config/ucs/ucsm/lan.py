# coding: utf-8
# !/usr/bin/env python

""" lan.py: Easy UCS Deployment Tool """

import time

from netaddr import EUI, IPAddress

from ucsmsdk.mometa.dpsec.DpsecMac import DpsecMac
from ucsmsdk.mometa.epqos.EpqosDefinition import EpqosDefinition
from ucsmsdk.mometa.epqos.EpqosEgress import EpqosEgress
from ucsmsdk.mometa.fabric.FabricEthLanFlowMonitoring import FabricEthLanFlowMonitoring
from ucsmsdk.mometa.fabric.FabricEthLinkProfile import FabricEthLinkProfile
from ucsmsdk.mometa.fabric.FabricEthMon import FabricEthMon
from ucsmsdk.mometa.fabric.FabricEthMonDestEp import FabricEthMonDestEp
from ucsmsdk.mometa.fabric.FabricEthMonSrcEp import FabricEthMonSrcEp
from ucsmsdk.mometa.fabric.FabricFcMonSrcEp import FabricFcMonSrcEp
from ucsmsdk.mometa.fabric.FabricEthVlanPc import FabricEthVlanPc
from ucsmsdk.mometa.fabric.FabricEthVlanPortEp import FabricEthVlanPortEp
from ucsmsdk.mometa.fabric.FabricFlowMonDefinition import FabricFlowMonDefinition
from ucsmsdk.mometa.fabric.FabricFlowMonExporterProfile import FabricFlowMonExporterProfile
from ucsmsdk.mometa.fabric.FabricLacpPolicy import FabricLacpPolicy
from ucsmsdk.mometa.fabric.FabricLanPinGroup import FabricLanPinGroup
from ucsmsdk.mometa.fabric.FabricLanPinTarget import FabricLanPinTarget
from ucsmsdk.mometa.fabric.FabricLifeTime import FabricLifeTime
from ucsmsdk.mometa.fabric.FabricMacSec import FabricMacSec
from ucsmsdk.mometa.fabric.FabricMacSecEapol import FabricMacSecEapol
from ucsmsdk.mometa.fabric.FabricMacSecIfConfig import FabricMacSecIfConfig
from ucsmsdk.mometa.fabric.FabricMacSecKey import FabricMacSecKey
from ucsmsdk.mometa.fabric.FabricMacSecKeyChain import FabricMacSecKeyChain
from ucsmsdk.mometa.fabric.FabricMacSecPolicy import FabricMacSecPolicy
from ucsmsdk.mometa.fabric.FabricMonOriginIP import FabricMonOriginIP
from ucsmsdk.mometa.fabric.FabricMonOriginSVI import FabricMonOriginSVI
from ucsmsdk.mometa.fabric.FabricMulticastPolicy import FabricMulticastPolicy
from ucsmsdk.mometa.fabric.FabricNetflowCollector import FabricNetflowCollector
from ucsmsdk.mometa.fabric.FabricNetflowIPv4Addr import FabricNetflowIPv4Addr
from ucsmsdk.mometa.fabric.FabricNetflowMonExporter import FabricNetflowMonExporter
from ucsmsdk.mometa.fabric.FabricNetflowMonExporterRef import FabricNetflowMonExporterRef
from ucsmsdk.mometa.fabric.FabricNetflowMonitor import FabricNetflowMonitor
from ucsmsdk.mometa.fabric.FabricNetflowMonitorRef import FabricNetflowMonitorRef
from ucsmsdk.mometa.fabric.FabricNetflowMonSession import FabricNetflowMonSession
from ucsmsdk.mometa.fabric.FabricNetflowMonSrcEp import FabricNetflowMonSrcEp
from ucsmsdk.mometa.fabric.FabricNetflowTimeoutPolicy import FabricNetflowTimeoutPolicy
from ucsmsdk.mometa.fabric.FabricNetGroup import FabricNetGroup
from ucsmsdk.mometa.fabric.FabricNetGroupRef import FabricNetGroupRef
from ucsmsdk.mometa.fabric.FabricPooledVlan import FabricPooledVlan
from ucsmsdk.mometa.fabric.FabricRemoteConfig import FabricRemoteConfig
from ucsmsdk.mometa.fabric.FabricSubGroup import FabricSubGroup
from ucsmsdk.mometa.fabric.FabricUdldLinkPolicy import FabricUdldLinkPolicy
from ucsmsdk.mometa.fabric.FabricUdldPolicy import FabricUdldPolicy
from ucsmsdk.mometa.fabric.FabricVlan import FabricVlan
from ucsmsdk.mometa.fabric.FabricVlanGroupReq import FabricVlanGroupReq
from ucsmsdk.mometa.fabric.FabricVlanReq import FabricVlanReq
from ucsmsdk.mometa.firmware.FirmwareAck import FirmwareAck
from ucsmsdk.mometa.flowctrl.FlowctrlItem import FlowctrlItem
from ucsmsdk.mometa.ip.IpIpV4StaticTargetAddr import IpIpV4StaticTargetAddr
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
from ucsmsdk.mometa.vnic.VnicDynamicCon import VnicDynamicCon
from ucsmsdk.mometa.vnic.VnicDynamicConPolicy import VnicDynamicConPolicy
from ucsmsdk.mometa.vnic.VnicDynamicConPolicyRef import VnicDynamicConPolicyRef
from ucsmsdk.mometa.vnic.VnicEther import VnicEther
from ucsmsdk.mometa.vnic.VnicEtherIf import VnicEtherIf
from ucsmsdk.mometa.vnic.VnicIScsiLCP import VnicIScsiLCP
from ucsmsdk.mometa.vnic.VnicLanConnPolicy import VnicLanConnPolicy
from ucsmsdk.mometa.vnic.VnicLanConnTempl import VnicLanConnTempl
from ucsmsdk.mometa.vnic.VnicSriovHpnConPolicy import VnicSriovHpnConPolicy
from ucsmsdk.mometa.vnic.VnicSriovHpnConPolicyRef import VnicSriovHpnConPolicyRef
from ucsmsdk.mometa.vnic.VnicUsnicConPolicy import VnicUsnicConPolicy
from ucsmsdk.mometa.vnic.VnicUsnicConPolicyRef import VnicUsnicConPolicyRef
from ucsmsdk.mometa.vnic.VnicVlan import VnicVlan
from ucsmsdk.mometa.vnic.VnicVmqConPolicy import VnicVmqConPolicy
from ucsmsdk.mometa.vnic.VnicVmqConPolicyRef import VnicVmqConPolicyRef
from ucsmsdk.mometa.vnic.VnicVnicBehPolicy import VnicVnicBehPolicy

import common
from config.ucs.object import UcsSystemConfigObject
from config.ucs.ucsm.servers import UcsSystemEthernetAdapterPolicy, UcsSystemThresholdPolicy


class UcsSystemApplianceVlan(UcsSystemConfigObject):
    _CONFIG_NAME = "Appliance VLAN"
    _CONFIG_SECTION_NAME = "appliance_vlans"
    _UCS_SDK_OBJECT_NAME = "fabricVlan"

    def __init__(self, parent=None, json_content=None, fabric_vlan=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_vlan)
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
                    if not part.startswith("org-"):
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
    _CONFIG_SECTION_NAME = "vlans"
    _UCS_SDK_OBJECT_NAME = "fabricVlan"

    def __init__(self, parent=None, json_content=None, fabric_vlan=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_vlan)
        self.fabric = None
        self.multicast_policy_name = None
        self.native_vlan = None
        self.primary_vlan_name = None
        self.sharing_type = None
        self.id = None
        self.name = None
        self.lan_uplink_ports = []
        self.lan_port_channels = []
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

                if "fabricEthVlanPortEp" in self._config.sdk_objects:
                    interfaces = [lan_uplink_port for lan_uplink_port in self._config.sdk_objects["fabricEthVlanPortEp"]
                                  if "fabric/lan/net-" + self.name + "/" in lan_uplink_port.dn]
                    if interfaces:
                        for eth_vlan_port_ep in interfaces:
                            lan_uplink_port = {}
                            lan_uplink_port["aggr_id"] = None
                            lan_uplink_port["slot_id"] = None
                            lan_uplink_port["port_id"] = None
                            lan_uplink_port["fabric"] = None
                            lan_uplink_port["native_vlan"] = None

                            lan_uplink_port.update({"fabric": eth_vlan_port_ep.switch_id})
                            lan_uplink_port.update({"slot_id": eth_vlan_port_ep.slot_id})
                            lan_uplink_port["aggr_id"] = eth_vlan_port_ep.aggr_port_id if \
                                int(eth_vlan_port_ep.aggr_port_id) else None
                            if lan_uplink_port["aggr_id"]:
                                lan_uplink_port.update({"aggr_id": eth_vlan_port_ep.port_id})
                                lan_uplink_port.update({"port_id": eth_vlan_port_ep.aggr_port_id})
                            else:
                                lan_uplink_port.update({"port_id": eth_vlan_port_ep.port_id})
                            lan_uplink_port.update({"native_vlan": eth_vlan_port_ep.is_native})
                            self.lan_uplink_ports.append(lan_uplink_port)

                if "fabricEthVlanPc" in self._config.sdk_objects:
                    port_channels = [port_channel for port_channel in self._config.sdk_objects["fabricEthVlanPc"]
                                     if "fabric/lan/net-" + self.name + "/pc" in port_channel.dn]
                    if port_channels:
                        for eth_vlan_pc in port_channels:
                            port_channel = {}
                            port_channel["pc_id"] = None
                            port_channel["fabric"] = None
                            port_channel["native_vlan"] = None

                            port_channel.update({"pc_id": eth_vlan_pc.port_id})
                            port_channel.update({"fabric": eth_vlan_pc.switch_id})
                            port_channel.update({"native_vlan": eth_vlan_pc.is_native})
                            self.lan_port_channels.append(port_channel)

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

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.lan_uplink_ports:
            for value in ["aggr_id", "slot_id", "port_id", "fabric", "native_vlan"]:
                if value not in element:
                    element[value] = None

        for element in self.lan_port_channels:
            for value in ["pc_id", "fabric", "native_vlan"]:
                if value not in element:
                    element[value] = None

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

        if self.lan_uplink_ports:
            for port in self.lan_uplink_ports:
                if port["fabric"]:
                    port["fabric"] = port["fabric"].upper()
                if port["aggr_id"]:
                    mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=mo_fabric_vlan,
                                                         aggr_port_id=port["port_id"], slot_id=port["slot_id"])
                    FabricEthVlanPortEp(parent_mo_or_dn=mo_fabric_sub_group, port_id=port["aggr_id"],
                                        slot_id=port["slot_id"], switch_id=port["fabric"],
                                        is_native=port["native_vlan"])
                else:
                    FabricEthVlanPortEp(parent_mo_or_dn=mo_fabric_vlan, port_id=port["port_id"],
                                        slot_id=port["slot_id"], switch_id=port["fabric"],
                                        is_native=port["native_vlan"])
                self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

        if self.lan_port_channels:
            for port_channel in self.lan_port_channels:
                if port_channel["fabric"]:
                    port_channel["fabric"] = port_channel["fabric"].upper()
                FabricEthVlanPc(parent_mo_or_dn=mo_fabric_vlan, port_id=port_channel["pc_id"],
                                switch_id=port_channel["fabric"], is_native=port_channel["native_vlan"])
                self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if not part.startswith("org-"):
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
    _CONFIG_SECTION_NAME = "lan_pin_groups"
    _UCS_SDK_OBJECT_NAME = "fabricLanPinGroup"

    def __init__(self, parent=None, json_content=None, fabric_lan_pin_group=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_lan_pin_group)
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
                                    interface.update({"port_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[4]})
                                    interface.update({"aggr_id": interface_ep_pc.ep_dn.split('/')[4].split('-')[4]})
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

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.interfaces:
            for value in ["aggr_id", "slot_id", "port_id", "fabric", "pc_id"]:
                if value not in element:
                    element[value] = None

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
                if (interface["port_id"] is not None) and (interface["pc_id"] is not None):
                    self.logger(level="error", message="You can only choose a port_id & port_id or pc_id for an " +
                                                       "interface in LAN Pin Group : " + str(self.name))
                else:
                    # Normal behaviour
                    interface_dn = None
                    detail = ""
                    if interface["pc_id"] is not None:
                        interface_dn = parent_mo + "/" + interface['fabric'] + "/pc-" + interface['pc_id']
                        detail = interface['fabric'] + "/pc-" + interface['pc_id']

                    elif (interface["port_id"] is not None) and (interface["slot_id"] is not None):
                        if interface["aggr_id"] is not None:
                            # FIXME: usage of aggr_id as port identifier or sub-interface identifier ???
                            interface_dn = parent_mo + "/" + interface['fabric'] + "/slot-" + interface['slot_id'] +\
                                "-aggr-port-" + interface['port_id'] + "/phys-slot-" + interface['slot_id']\
                                + "-port-" + interface['aggr_id']
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
                        self.commit(detail="interface: " + detail)

        return True


class UcsSystemVlanGroup(UcsSystemConfigObject):
    _CONFIG_NAME = "VLAN Group"
    _CONFIG_SECTION_NAME = "vlan_groups"
    _UCS_SDK_OBJECT_NAME = "fabricNetGroup"

    def __init__(self, parent=None, json_content=None, fabric_net_group=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_net_group)
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
                             if "fabric/lan/net-group-" + self.name + "/" in vlan.dn]
                    if vlans:
                        for vlan in vlans:
                            if vlan.name != self.native_vlan:
                                if vlan.config_issues in ["named-vlan-unresolved"]:
                                    self.logger(level="warning",
                                                message="Unable to resolve referenced VLAN '" + str(vlan.name) +
                                                        "' from VLAN Group '" + self.name + "'")
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


        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.lan_uplink_ports:
            for value in ["aggr_id", "slot_id", "port_id", "fabric"]:
                if value not in element:
                    element[value] = None

        for element in self.lan_port_channels:
            for value in ["pc_id", "fabric"]:
                if value not in element:
                    element[value] = None

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
                if port["aggr_id"]:
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
                    self.commit(detail="lan_port_channel: " + port_channel["fabric"] + "/pc-" + port_channel["pc_id"])

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if not part.startswith("org-"):
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
    _CONFIG_SECTION_NAME = "qos_system_class"

    def __init__(self, parent=None, json_content=None, qos_class=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=qos_class)
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
    _CONFIG_SECTION_NAME = "slow_drain_timers"
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


class UcsSystemIpPool(UcsSystemConfigObject):
    _CONFIG_NAME = "IP Pool"
    _CONFIG_SECTION_NAME = "ip_pools"
    _UCS_SDK_OBJECT_NAME = "ippoolPool"

    def __init__(self, parent=None, json_content=None, ippool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=ippool_pool)
        self.descr = None
        self.name = None
        self.order = None
        self.ip_blocks = []
        self.ipv6_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if ippool_pool is not None:
                self.name = ippool_pool.name
                self.descr = ippool_pool.descr
                self.order = ippool_pool.assignment_order
                self.operational_state = {
                    "size": ippool_pool.size,
                    "assigned": ippool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.ip_blocks:
            for value in ["gateway", "primary_dns", "secondary_dns", "netmask", "to", "from", "size"]:
                if value not in element:
                    element[value] = None

        for element in self.ipv6_blocks:
            for value in ["gateway", "primary_dns", "secondary_dns", "prefix", "to", "from", "size"]:
                if value not in element:
                    element[value] = None

        for value in ["assigned", "size"]:
            if value not in self.operational_state:
                self.operational_state[value] = None

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
                                # The print value of commit is True, so we log the error if it is not the expected error
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
                                # The print value of commit is True, so we log the error if it is not the expected error
                                self.logger(level="error", message="Error in configuring " +
                                                                   self._CONFIG_NAME + ": " + err.error_descr)
                            return False

        return True


class UcsSystemMacPool(UcsSystemConfigObject):
    _CONFIG_NAME = "MAC Pool"
    _CONFIG_SECTION_NAME = "mac_pools"
    _UCS_SDK_OBJECT_NAME = "macpoolPool"

    def __init__(self, parent=None, json_content=None, macpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=macpool_pool)
        self.descr = None
        self.name = None
        self.order = None
        self.mac_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if macpool_pool is not None:
                self.name = macpool_pool.name
                self.descr = macpool_pool.descr
                self.order = macpool_pool.assignment_order
                self.operational_state = {
                    "size": macpool_pool.size,
                    "assigned": macpool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.mac_blocks:
            for value in ["to", "from", "size"]:
                if value not in element:
                    element[value] = None

        for value in ["assigned", "size"]:
            if value not in self.operational_state:
                self.operational_state[value] = None

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


class UcsSystemQosPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "QoS Policy"
    _CONFIG_SECTION_NAME = "qos_policies"
    _UCS_SDK_OBJECT_NAME = "epqosDefinition"

    def __init__(self, parent=None, json_content=None, epqos_definition=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=epqos_definition)
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
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + self.name)
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
    _CONFIG_SECTION_NAME = "udld_link_policies"
    _UCS_SDK_OBJECT_NAME = "fabricUdldLinkPolicy"

    def __init__(self, parent=None, json_content=None, fabric_udld_link_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_udld_link_policy)
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
    _CONFIG_SECTION_NAME = "link_profiles"
    _UCS_SDK_OBJECT_NAME = "fabricEthLinkProfile"

    def __init__(self, parent=None, json_content=None, fabric_eth_link_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_eth_link_profile)
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


class UcsSystemGenericNetworkControlPolicy(UcsSystemConfigObject):
    _UCS_SDK_OBJECT_NAME = "nwctrlDefinition"

    def __init__(self, parent=None, json_content=None, nwctrl_definition=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=nwctrl_definition)
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

                # This check is for Network Control Policy
                if self._parent.__class__.__name__ == "UcsSystemOrg":
                    if "dpsecMac" in self._parent._config.sdk_objects:
                        for dpsec_mac in self._config.sdk_objects["dpsecMac"]:
                            if self._parent._dn + "/nwctrl-" + self.name + "/" in dpsec_mac.dn:
                                self.mac_security_forge = dpsec_mac.forge
                                break

                # This check is for Appliance Network Control Policy
                elif "dpsecMac" in self._config.sdk_objects:
                    for dpsec_mac in self._config.sdk_objects["dpsecMac"]:
                        if "fabric/eth-estc/nwctrl-" + self.name in dpsec_mac.dn:
                            self.mac_security_forge = dpsec_mac.forge
                            break

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

        if self._parent.__class__.__name__ != "UcsSystemOrg":
            # This is for Appliance Network Control Policy
            parent_mo = "fabric/eth-estc"
        elif hasattr(self._parent, '_dn'):
            # This is for Network Control Policy
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


class UcsSystemApplianceNetworkControlPolicy(UcsSystemGenericNetworkControlPolicy):
    _CONFIG_NAME = "Appliance Network Control Policy"
    _CONFIG_SECTION_NAME = "appliance_network_control_policies"


class UcsSystemNetworkControlPolicy(UcsSystemGenericNetworkControlPolicy):
    _CONFIG_NAME = "Network Control Policy"
    _CONFIG_SECTION_NAME = "network_control_policies"


class UcsSystemDefaultVnicBehavior(UcsSystemConfigObject):
    _CONFIG_NAME = "Default vNIC Behavior"
    _CONFIG_SECTION_NAME = "default_vnic_behavior"
    _UCS_SDK_OBJECT_NAME = "vnicVnicBehPolicy"

    def __init__(self, parent=None, json_content=None, vnic_vnic_beh_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_vnic_beh_policy)
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
    _CONFIG_SECTION_NAME = "flow_control_policies"
    _UCS_SDK_OBJECT_NAME = "flowctrlItem"
    # Note: This policy is in orgs in UCS Manager but does not use orgs in its DN.

    def __init__(self, parent=None, json_content=None, flowctrl_item=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=flowctrl_item)
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
    _CONFIG_SECTION_NAME = "multicast_policies"
    _UCS_SDK_OBJECT_NAME = "fabricMulticastPolicy"

    def __init__(self, parent=None, json_content=None, fabric_multicast_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_multicast_policy)
        self.name = None
        self.descr = None
        self.igmp_snooping_state = None
        self.igmp_snooping_querier_state = None
        self.igmp_source_ip_proxy_state = None
        self.fi_a_querier_ip_address = None
        self.fi_b_querier_ip_address = None

        if self._config.load_from == "live":
            if fabric_multicast_policy is not None:
                self.name = fabric_multicast_policy.name
                self.descr = fabric_multicast_policy.descr
                self.igmp_snooping_state = fabric_multicast_policy.snooping_state
                self.igmp_snooping_querier_state = fabric_multicast_policy.querier_state
                self.igmp_source_ip_proxy_state = fabric_multicast_policy.source_ip_proxy_state

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
                                                           source_ip_proxy_state=self.igmp_source_ip_proxy_state,
                                                           querier_ip_addr_peer=self.fi_b_querier_ip_address,
                                                           querier_ip_addr=self.fi_a_querier_ip_address)

        self._handle.add_mo(mo=mo_fabric_multicast_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemLinkProtocolPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Link Protocol Policy"
    _CONFIG_SECTION_NAME = "link_protocol_policy"
    _UCS_SDK_OBJECT_NAME = "fabricUdldPolicy"

    def __init__(self, parent=None, json_content=None, fabric_udld_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_udld_policy)
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
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
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
    _CONFIG_SECTION_NAME = "lacp_policies"
    _UCS_SDK_OBJECT_NAME = "fabricLacpPolicy"

    def __init__(self, parent=None, json_content=None, fabric_lacp_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_lacp_policy)
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


class UcsSystemLanTrafficMonitoringSession(UcsSystemConfigObject):
    _CONFIG_NAME = "LAN Traffic Monitoring Session"
    _CONFIG_SECTION_NAME = "lan_traffic_monitoring_sessions"
    _UCS_SDK_OBJECT_NAME = "fabricEthMon"

    def __init__(self, parent=None, json_content=None, fabric_eth_mon=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_eth_mon)
        self.admin_state = None
        self.admin_speed = None
        self.destination = []
        self.destination_ip = None
        self.enable_packet_truncation = None
        self.erspan_id = None
        self.fabric = None
        self.ip_dscp = None
        self.ip_ttl = None
        self.maximum_transmission_unit = None
        self.name = None
        self.session_type = None
        self.sources = []
        self.span_control_packets = None
        if self._config.load_from == "live":
            if fabric_eth_mon is not None:
                self.admin_state = fabric_eth_mon.admin_state
                self.fabric = fabric_eth_mon.id
                self.name = fabric_eth_mon.name
                self.session_type = fabric_eth_mon.session_type
                self.span_control_packets = fabric_eth_mon.span_ctrl_pkts

                if self.session_type == "erspan-source":
                    # This is an ERSPAN session
                    if "fabricRemoteConfig" in self._config.sdk_objects:
                        for fabric_remote_config in self._config.sdk_objects["fabricRemoteConfig"]:
                            if fabric_eth_mon.dn + "/" in fabric_remote_config.dn:
                                self.destination_ip = fabric_remote_config.dest_ip
                                self.enable_packet_truncation = fabric_remote_config.is_mtu
                                self.erspan_id = fabric_remote_config.erspan_id
                                self.ip_dscp = fabric_remote_config.ip_dscp
                                self.ip_ttl = fabric_remote_config.ip_ttl
                                self.maximum_transmission_unit = fabric_remote_config.mtu
                                break
                else:
                    # This is a local SPAN session
                    if "fabricEthMonDestEp" in self._config.sdk_objects:
                        # Based on fabric ID and session name, fetching the destination details of a monitoring session
                        for fabric_eth_mon_dest_ep in self._config.sdk_objects["fabricEthMonDestEp"]:
                            fabric = fabric_eth_mon_dest_ep.switch_id
                            name = fabric_eth_mon_dest_ep.dn.split("/")[3].replace("eth-mon-", "")
                            if self.fabric == fabric and self.name == name:
                                self.admin_speed = fabric_eth_mon_dest_ep.admin_speed
                                destination = {"slot_id": fabric_eth_mon_dest_ep.slot_id}
                                if fabric_eth_mon_dest_ep.aggr_port_id not in ["", "0"]:
                                    destination.update({"aggr_id": fabric_eth_mon_dest_ep.port_id})
                                    destination.update({"port_id": fabric_eth_mon_dest_ep.aggr_port_id})
                                else:
                                    destination.update({"aggr_id": None})
                                    destination.update({"port_id": fabric_eth_mon_dest_ep.port_id})
                                self.destination.append(destination)
                                break

                directions = {}
                uplink_port_type_list = ["uplink-port", "fcoeuplink-port", "storage", "nas-port"]
                port_channel_type_list = ["port-channel", "fcoeuplink-portchannel"]

                # To get direction field of all sources in a monitoring session
                if "fabricEthMonSrcEp" in self._config.sdk_objects:
                    for src_ep_obj in self._config.sdk_objects["fabricEthMonSrcEp"]:
                        directions[src_ep_obj.dn] = src_ep_obj.direction
                if "fabricFcMonSrcEp" in self._config.sdk_objects:
                    for src_ep_obj in self._config.sdk_objects["fabricFcMonSrcEp"]:
                        directions[src_ep_obj.dn] = src_ep_obj.direction

                # Fetching details of all types of sources in monitoring session
                # ToDo: Include support for vm-vnic source
                if "fabricEthMonSrcRef" in self._config.sdk_objects:
                    # Based on the source type fetching all the required fields
                    for fabric_eth_mon_src_ref in self._config.sdk_objects["fabricEthMonSrcRef"]:
                        source_type = fabric_eth_mon_src_ref.source_type
                        source_dn = fabric_eth_mon_src_ref.source_dn.split("/")
                        monitoring_session_name = source_dn[-1].replace("mon-src-", "")
                        fabric = fabric_eth_mon_src_ref.dn.split("/")[2]
                        if self.fabric == fabric and self.name == monitoring_session_name:
                            source_dict = {"source_type": source_type}
                            if fabric_eth_mon_src_ref.source_dn in directions:
                                source_dict["direction"] = directions[fabric_eth_mon_src_ref.source_dn]
                            if source_type in uplink_port_type_list:
                                if "-aggr-port-" in source_dn[3]:
                                    source_dict["slot_id"] = source_dn[-2].split("-slot-")[1].split("-port-")[0]
                                    source_dict["aggr_id"] = source_dn[-2].split("-slot-")[1].split("-port-")[1]
                                    source_dict["port_id"] = source_dn[-3].split("-aggr-port-")[1]
                                else:
                                    source_dict["slot_id"] = source_dn[-2].split("-slot-")[1].split("-port-")[0]
                                    source_dict["port_id"] = source_dn[-2].split("-slot-")[1].split("-port-")[1]
                            elif source_type in port_channel_type_list:
                                source_dict["pc_id"] = source_dn[-2].split("pc-")[-1]
                            elif source_type == "vlan":
                                source_dict["vlan"] = source_dn[-2].split("net-")[-1]
                                if fabric_eth_mon_src_ref.source_dn.startswith("fabric/lan/" + self.fabric):
                                    source_dict["fabric"] = self.fabric
                                else:
                                    source_dict["fabric"] = "dual"
                            elif source_type == "vnic":
                                source_dict["org"] = "/".join([i.replace("org-", "", 1) for i in source_dn])
                                source_dict["service_profile"] = source_dn[-3].replace("ls-", "")
                                source_dict["vnic"] = source_dn[-2].replace("ether-", "")
                            elif source_type == "vhba":
                                source_dict["org"] = "/".join(
                                    [i.replace("org-", "") for i in source_dn if i.startswith("org-")])
                                source_dict["service_profile"] = source_dn[-3].replace("ls-", "")
                                source_dict["vhba"] = source_dn[-2].replace("fc-", "")
                            self.sources.append(source_dict)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.destination:
            for value in ["aggr_id", "port_id", "slot_id"]:
                if value not in element:
                    element[value] = None

        for element in self.sources:
            for value in ["aggr_id", "direction", "fabric", "org", "pc_id", "port_id", "service_profile",
                          "slot_id", "source_type", "vhba", "vlan", "vnic"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "fabric/lanmon/" + self.fabric
        mo_fabric_eth_mon = FabricEthMon(name=self.name, parent_mo_or_dn=parent_mo, admin_state=self.admin_state,
                                         span_ctrl_pkts=self.span_control_packets, id=self.fabric,
                                         session_type=self.session_type)
        self._handle.add_mo(mo=mo_fabric_eth_mon, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.session_type == "erspan-source":
            mo_fabric_remote_config = FabricRemoteConfig(parent_mo_or_dn=mo_fabric_eth_mon, dest_ip=self.destination_ip,
                                                         is_mtu=self.enable_packet_truncation, erspan_id=self.erspan_id,
                                                         ip_dscp=self.ip_dscp, ip_ttl=self.ip_ttl,
                                                         mtu=self.maximum_transmission_unit)
            self._handle.add_mo(mo=mo_fabric_remote_config, modify_present=True)
            if commit:
                if self.commit(detail="ERSPAN Source Configuration") != True:
                    return False

        if self.destination:
            if self.destination[0].get("aggr_id"):
                mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=mo_fabric_eth_mon,
                                                     slot_id=self.destination[0].get("slot_id"),
                                                     aggr_port_id=self.destination[0].get("port_id"))
                FabricEthMonDestEp(parent_mo_or_dn=mo_fabric_sub_group, admin_speed=self.admin_speed,
                                   slot_id=self.destination[0].get("slot_id"),
                                   port_id=self.destination[0].get("aggr_id"))
                dst_descr = self.destination[0].get("slot_id") + "/" + self.destination[0].get("port_id") + "/" + \
                            self.destination[0].get("aggr_id")
                self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)
            else:
                mo_fabric_eth_mon_dest_ep = FabricEthMonDestEp(parent_mo_or_dn=mo_fabric_eth_mon,
                                                               admin_speed=self.admin_speed,
                                                               slot_id=self.destination[0].get("slot_id"),
                                                               port_id=self.destination[0].get("port_id"))
                dst_descr = self.destination[0].get("slot_id") + "/" + self.destination[0].get("port_id")

                self._handle.add_mo(mo=mo_fabric_eth_mon_dest_ep, modify_present=True)
            if commit:
                if self.commit(detail="Destination Port " + dst_descr) != True:
                    return False

        source_status_failed = False
        if self.sources:
            for source in self.sources:
                if "direction" in source:
                    if source["source_type"] != "vhba":
                        parent_dn = ""
                        src_descr = ""
                        if source["source_type"] == "uplink-port":
                            # For LAN Uplink Port source type
                            parent_dn += "fabric/lan/" + self.fabric
                            if source["aggr_id"]:
                                parent_dn += ("/slot-" + source["slot_id"] + "-aggr-port-" + source["port_id"] +
                                              "/phys-slot-" + source["slot_id"] + "-port-" + source["aggr_id"])
                                src_descr = source["slot_id"] + "/" + source["port_id"] + "/" + source["aggr_id"]
                            else:
                                parent_dn += "/phys-slot-" + source["slot_id"] + "-port-" + source["port_id"]
                                src_descr = source["slot_id"] + "/" + source["port_id"]
                        elif source["source_type"] == "port-channel":
                            # For LAN Port-Channel source type
                            parent_dn += "fabric/lan/" + self.fabric + "/pc-" + source["pc_id"]
                            src_descr = source["pc_id"]
                        elif source["source_type"] == "nas-port":
                            # For Appliance Port source type
                            parent_dn += "fabric/eth-estc/" + self.fabric
                            if source["aggr_id"]:
                                parent_dn += ("/slot-" + source["slot_id"] + "-aggr-port-" + source["port_id"] +
                                              "/phys-eth-slot-" + source["slot_id"] + "-port-" + source["aggr_id"])
                                src_descr = source["slot_id"] + "/" + source["port_id"] + "/" + source["aggr_id"]
                            else:
                                parent_dn += "/phys-eth-slot-" + source["slot_id"] + "-port-" + source["port_id"]
                                src_descr = source["slot_id"] + "/" + source["port_id"]
                        elif source["source_type"] == "fcoeuplink-port":
                            # For FCoE Uplink Port source type
                            parent_dn += "fabric/san/" + self.fabric
                            if source["aggr_id"]:
                                parent_dn += ("/slot-" + source["slot_id"] + "-aggr-port-" + source["port_id"] +
                                              "/phys-fcoesanep-slot-" + source["slot_id"] + "-port-" +
                                              source["aggr_id"])
                                src_descr = source["slot_id"] + "/" + source["port_id"] + "/" + source["aggr_id"]
                            else:
                                parent_dn += "/phys-fcoesanep-slot-" + source["slot_id"] + "-port-" + source["port_id"]
                                src_descr = source["slot_id"] + "/" + source["port_id"]
                        elif source["source_type"] == "fcoeuplink-portchannel":
                            # For FCoE Port-Channel source type
                            parent_dn += "fabric/san/" + self.fabric + "/fcoesanpc-" + source["pc_id"]
                            src_descr = source["pc_id"]
                        elif source["source_type"] == "storage":
                            # For FCoE Storage Port source type
                            parent_dn += "fabric/fc-estc/" + self.fabric
                            if source["aggr_id"]:
                                parent_dn += ("/slot-" + source["slot_id"] + "-aggr-port-" + source["port_id"] +
                                              "/phys-fcoe-slot-" + source["slot_id"] + "-port-" + source["aggr_id"])
                                src_descr = source["slot_id"] + "/" + source["port_id"] + "/" + source["aggr_id"]
                            else:
                                parent_dn += "/phys-fcoe-slot-" + source["slot_id"] + "-port-" + source["port_id"]
                                src_descr = source["slot_id"] + "/" + source["port_id"]
                        elif source["source_type"] == "vlan":
                            # For VLAN source type
                            if source["fabric"] == "dual":
                                parent_dn += "fabric/lan/net-" + source["vlan"]
                                src_descr = source["vlan"]
                            else:
                                parent_dn += "fabric/lan/" + source["fabric"] + "/net-" + source["vlan"]
                                src_descr = source["fabric"] + "/" + source["vlan"]
                        elif source["source_type"] == "vnic":
                            # For vNIC source type
                            parent_dn += '/'.join([org.replace("", "org-", 1) for org in source["org"].split("/")])
                            parent_dn += "/ls-" + source["service_profile"] + "/ether-" + source["vnic"]
                            src_descr = source["org"] + "/" + source["service_profile"] + " - " + source["vnic"]

                        mo_fabric_eth_mon_src_ep = FabricEthMonSrcEp(parent_mo_or_dn=parent_dn, name=self.name,
                                                                     direction=source["direction"])
                        self._handle.add_mo(mo=mo_fabric_eth_mon_src_ep, modify_present=True)
                    else:
                        # For vHBA source type
                        parent_dn = '/'.join([org.replace("", "org-", 1) for org in source["org"].split("/")])
                        parent_dn += "/ls-" + source["service_profile"] + "/fc-" + source["vhba"]
                        src_descr = source["org"] + "/" + source["service_profile"] + " - " + source["vhba"]

                        mo_fabric_fc_mon_src_ep = FabricFcMonSrcEp(parent_mo_or_dn=parent_dn, name=self.name,
                                                                   direction=source["direction"])
                        self._handle.add_mo(mo=mo_fabric_fc_mon_src_ep, modify_present=True)
                    if commit:
                        if self.commit(detail="Source " + source["source_type"] + " " + src_descr) != True:
                            source_status_failed = True
        if source_status_failed:
            return False


class UcsSystemTrafficMonitoringConfiguration(UcsSystemConfigObject):
    _CONFIG_NAME = "Traffic Monitoring Configuration"
    _CONFIG_SECTION_NAME = "traffic_monitoring_configuration"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.origin_interfaces_ip = []
        self.origin_interface_source_vlan = None

        if self._config.load_from == "live":
            if "fabricMonOriginSVI" in self._config.sdk_objects:
                if self._config.sdk_objects["fabricMonOriginSVI"]:
                    self.origin_interface_source_vlan = self._config.sdk_objects["fabricMonOriginSVI"][0].source_vlan

            if "fabricMonOriginIP" in self._config.sdk_objects:
                if self._config.sdk_objects["fabricMonOriginIP"]:
                    for fabric_mon_origin_ip in self._config.sdk_objects["fabricMonOriginIP"]:
                        origin_interface_ip = {
                            "fabric": fabric_mon_origin_ip.fabric_id,
                            "source_ip": fabric_mon_origin_ip.addr,
                            "default_gateway": fabric_mon_origin_ip.def_gw,
                            "subnet_mask": fabric_mon_origin_ip.subnet
                        }
                        self.origin_interfaces_ip.append(origin_interface_ip)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.origin_interfaces_ip:
                    for value in ["default_gateway", "fabric", "source_ip", "subnet_mask"]:
                        if value not in element:
                            element[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        mo_erspan = "fabric/remote-traffic-mon"
        mo_fabric_mon_origin_svi = FabricMonOriginSVI(parent_mo_or_dn=mo_erspan,
                                                      source_vlan=self.origin_interface_source_vlan)
        if self.origin_interfaces_ip:
            for origin_interface_ip in self.origin_interfaces_ip:
                FabricMonOriginIP(parent_mo_or_dn=mo_fabric_mon_origin_svi, fabric_id=origin_interface_ip["fabric"],
                                  addr=origin_interface_ip["source_ip"], def_gw=origin_interface_ip["default_gateway"],
                                  subnet=origin_interface_ip["subnet_mask"])

        self._handle.add_mo(mo_fabric_mon_origin_svi, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemDynamicVnicConnectionPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Dynamic vNIC Connection Policy"
    _CONFIG_SECTION_NAME = "dynamic_vnic_connection_policies"
    _UCS_SDK_OBJECT_NAME = "vnicDynamicConPolicy"
    _UCS_SDK_SPECIFIC_OBJECT_NAME = "vnicDynamicCon"

    def __init__(self, parent=None, json_content=None, vnic_dynamic_con_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_dynamic_con_policy)
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

                if self._parent._dn:
                    if self._parent.__class__.__name__ == "UcsSystemServiceProfile":
                        # We are in presence of a Specific Dynamic vNIC Connection Policy under a Service Profile object
                        self.name = None

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        detail = str(self.name)
        if self._parent.__class__.__name__ == "UcsSystemServiceProfile":
            # We are in presence of a Specific Dynamic vNIC Connection Policy under a Service Profile object
            detail = "Service Profile " + str(self._parent.name)
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + detail)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + detail +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + self.name)
            return False

        if self._parent.__class__.__name__ == "UcsSystemServiceProfile":
            # We are in presence of a Specific Dynamic vNIC Connection Policy under a Service Profile object
            mo_vnic_dynamic_con_policy = VnicDynamicCon(
                parent_mo_or_dn=parent_mo, descr=self.descr, dynamic_eth=self.number_dynamic_vnics,
                adaptor_profile_name=self.adapter_policy, protection=self.protection
            )
        else:
            # We are in presence of a regular Dynamic vNIC Connection Policy under an Org object
            mo_vnic_dynamic_con_policy = VnicDynamicConPolicy(
                parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name, dynamic_eth=self.number_dynamic_vnics,
                adaptor_profile_name=self.adapter_policy, protection=self.protection
            )

        self._handle.add_mo(mo=mo_vnic_dynamic_con_policy, modify_present=True)
        if commit:
            detail = str(self.name)
            if self._parent.__class__.__name__ == "UcsSystemServiceProfile":
                # We are in presence of a Specific Dynamic vNIC Connection Policy under a Service Profile object
                detail = "Service Profile " + str(self._parent.name)
            if self.commit(detail=detail) != True:
                return False
        return True


class UcsSystemUsnicConnectionPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "usNIC Connection Policy"
    _CONFIG_SECTION_NAME = "usnic_connection_policies"
    _UCS_SDK_OBJECT_NAME = "vnicUsnicConPolicy"

    def __init__(self, parent=None, json_content=None, vnic_usnic_con_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_usnic_con_policy)
        self.name = None
        self.descr = None
        self.number_of_usnics = None
        self.adapter_policy = None

        if self._config.load_from == "live":
            if vnic_usnic_con_policy is not None:
                self.name = vnic_usnic_con_policy.name
                self.descr = vnic_usnic_con_policy.descr
                self.number_of_usnics = vnic_usnic_con_policy.usnic_count
                self.adapter_policy = vnic_usnic_con_policy.adaptor_profile_name

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

        mo_vnic_usnic_con_policy = VnicUsnicConPolicy(parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name,
                                                      usnic_count=self.number_of_usnics,
                                                      adaptor_profile_name=self.adapter_policy)

        self._handle.add_mo(mo=mo_vnic_usnic_con_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemVmqConnectionPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "VMQ Connection Policy"
    _CONFIG_SECTION_NAME = "vmq_connection_policies"
    _UCS_SDK_OBJECT_NAME = "vnicVmqConPolicy"

    def __init__(self, parent=None, json_content=None, vnic_vmq_con_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_vmq_con_policy)
        self.name = None
        self.descr = None
        self.multi_queue = None
        self.number_of_sub_vnics = None
        self.number_of_vmqs = None
        self.number_of_interrupts = None
        self.adapter_policy = None

        if self._config.load_from == "live":
            if vnic_vmq_con_policy is not None:
                self.name = vnic_vmq_con_policy.name
                self.descr = vnic_vmq_con_policy.descr
                self.multi_queue = vnic_vmq_con_policy.multi_queue
                if self.multi_queue in ["disabled"]:
                    self.number_of_vmqs = vnic_vmq_con_policy.vmq_count
                    self.number_of_interrupts = vnic_vmq_con_policy.intr_count
                elif self.multi_queue in ["enabled"]:
                    self.adapter_policy = vnic_vmq_con_policy.adaptor_profile_name
                    self.number_of_sub_vnics = vnic_vmq_con_policy.vmmq_sub_vnics

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

        mo_vnic_vmq_con_policy = VnicVmqConPolicy(parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name,
                                                  multi_queue=self.multi_queue,
                                                  adaptor_profile_name=self.adapter_policy,
                                                  intr_count=self.number_of_interrupts,
                                                  vmmq_sub_vnics=self.number_of_sub_vnics,
                                                  vmq_count=self.number_of_vmqs)

        self._handle.add_mo(mo=mo_vnic_vmq_con_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemSriovHpnConnectionPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "SRIOV HPN Connection Policy"
    _CONFIG_SECTION_NAME = "sriov_hpn_connection_policies"
    _UCS_SDK_OBJECT_NAME = "vnicSriovHpnConPolicy"

    def __init__(self, parent=None, json_content=None, vnic_sriov_hpn_con_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_sriov_hpn_con_policy)
        self.name = None
        self.descr = None
        self.number_of_sriov_hpn_vnics = None
        self.transmit_queues = None
        self.receive_queues = None
        self.completion_queues = None
        self.interrupt_count = None

        if self._config.load_from == "live":
            if vnic_sriov_hpn_con_policy is not None:
                self.name = vnic_sriov_hpn_con_policy.name
                self.descr = vnic_sriov_hpn_con_policy.descr
                self.number_of_sriov_hpn_vnics = vnic_sriov_hpn_con_policy.sriovhpn_count
                self.transmit_queues = vnic_sriov_hpn_con_policy.transmit_queue_count
                self.receive_queues = vnic_sriov_hpn_con_policy.receive_queue_count
                self.completion_queues = vnic_sriov_hpn_con_policy.completion_queue_count
                self.interrupt_count = vnic_sriov_hpn_con_policy.interrupt_count

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

        mo_vnic_sriov_hpn_con_policy = VnicSriovHpnConPolicy(parent_mo_or_dn=parent_mo, descr=self.descr,
                                                             name=self.name,
                                                             sriovhpn_count=self.number_of_sriov_hpn_vnics,
                                                             transmit_queue_count=self.transmit_queues,
                                                             receive_queue_count=self.receive_queues,
                                                             completion_queue_count=self.completion_queues,
                                                             interrupt_count=self.interrupt_count)

        self._handle.add_mo(mo=mo_vnic_sriov_hpn_con_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemNetflowMonitoring(UcsSystemConfigObject):
    _CONFIG_NAME = "NetFlow Monitoring"
    _CONFIG_SECTION_NAME = "netflow_monitoring"
    _UCS_SDK_OBJECT_NAME = "fabricEthLanFlowMonitoring"

    def __init__(self, parent=None, json_content=None, fabric_eth_lan_flow_monitoring=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_eth_lan_flow_monitoring)
        self.admin_state = None
        self.flow_record_definitions = []
        self.flow_exporters = []
        self.flow_collectors = []
        self.flow_exporter_profiles = []
        self.flow_monitors = []
        self.flow_timeout_policies = []
        self.flow_monitor_sessions= []
        if self._config.load_from == "live":
            if fabric_eth_lan_flow_monitoring is not None:
                self.admin_state = fabric_eth_lan_flow_monitoring.admin_state
            
            if "fabricFlowMonDefinition" in self._config.sdk_objects:
                for fabric_flow_mon_definition in self._config.sdk_objects["fabricFlowMonDefinition"]:
                    flow_record_definition = {}
                    flow_record_definition.update({"name": fabric_flow_mon_definition.name,
                                                  "descr": fabric_flow_mon_definition.descr,
                                                  "record_type": fabric_flow_mon_definition.record_type})
                    if fabric_flow_mon_definition.ipv4keys:
                        ipv4_keys = []
                        ipv4_key_list = fabric_flow_mon_definition.ipv4keys.split(",")
                        for ipv4_key in ipv4_key_list:
                            ipv4_keys.append(ipv4_key)
                        flow_record_definition.update({"key_type": fabric_flow_mon_definition.key_type, 
                                                        "ipv4keys": ipv4_keys})
                    elif fabric_flow_mon_definition.ipv6keys:
                        ipv6_keys = []
                        ipv6_key_list = fabric_flow_mon_definition.ipv6keys.split(",")
                        for ipv6_key in ipv6_key_list:
                            ipv6_keys.append(ipv6_key)
                        flow_record_definition.update({"key_type": fabric_flow_mon_definition.key_type, 
                                                       "ipv6keys": ipv6_keys})
                    elif fabric_flow_mon_definition.l2keys:
                        l2_keys = []
                        l2_key_list = fabric_flow_mon_definition.l2keys.split(",")
                        for l2_key in l2_key_list:
                            l2_keys.append(l2_key)
                        flow_record_definition.update({"key_type": fabric_flow_mon_definition.key_type, 
                                                        "l2keys": l2_keys})
                    if fabric_flow_mon_definition.nonkeys:
                        non_keys = []
                        non_key_list = fabric_flow_mon_definition.nonkeys.split(",")
                        for non_key in non_key_list:
                            non_keys.append(non_key)
                        flow_record_definition.update({"nonkeys": non_keys})
                    self.flow_record_definitions.append(flow_record_definition)

            if "fabricNetflowMonExporter" in self._config.sdk_objects:
                for fabric_netflow_mon_exporter in self._config.sdk_objects["fabricNetflowMonExporter"]:
                    flow_exporter = {}
                    flow_exporter.update({
                        "name": fabric_netflow_mon_exporter.name,
                        "descr": fabric_netflow_mon_exporter.descr,
                        "dscp": fabric_netflow_mon_exporter.dscp,
                        "exporter_profile": fabric_netflow_mon_exporter.flow_exp_profile,
                        "flow_collector": fabric_netflow_mon_exporter.flow_mon_collector,
                        "template_data_timeout": fabric_netflow_mon_exporter.template_data_timeout,
                        "option_exporter_stats_timeout": fabric_netflow_mon_exporter.exporter_stats_timeout,
                        "option_interface_table_timeout": fabric_netflow_mon_exporter.interface_table_timeout,
                        "version": fabric_netflow_mon_exporter.version
                    })
                    self.flow_exporters.append(flow_exporter) 

            if "fabricNetflowCollector" in self._config.sdk_objects:
                for fabric_netflow_collector in self._config.sdk_objects["fabricNetflowCollector"]:
                    flow_collector = {}
                    flow_collector.update({
                        "name": fabric_netflow_collector.name,
                        "descr": fabric_netflow_collector.descr,
                        "port": fabric_netflow_collector.port,
                        "vlan": fabric_netflow_collector.source_vlan
                    })
                    if "ipIpV4StaticTargetAddr" in self._config.sdk_objects:
                        for ip_ipv4_static_target_addr in self._config.sdk_objects["ipIpV4StaticTargetAddr"]:
                            if fabric_netflow_collector.dn + "/" in ip_ipv4_static_target_addr.dn:
                                flow_collector.update({
                                    "collector_ip": ip_ipv4_static_target_addr.addr,
                                    "exporter_gateway_ip": ip_ipv4_static_target_addr.def_gw
                                })
                    self.flow_collectors.append(flow_collector) 

            if "fabricFlowMonExporterProfile" in self._config.sdk_objects:
                for fabric_flow_mon_exporter_profile in self._config.sdk_objects["fabricFlowMonExporterProfile"]:
                    flow_exporter_profile = {}
                    flow_exporter_profile.update({
                        "name": fabric_flow_mon_exporter_profile.name,
                        "descr": fabric_flow_mon_exporter_profile.descr
                    })
                    if "vnicEtherIf" in self._config.sdk_objects:
                        exporter_interfaces = []
                        for vnic_ether_if in self._config.sdk_objects["vnicEtherIf"]:
                            if fabric_flow_mon_exporter_profile.dn in vnic_ether_if.dn:
                                exporter_interface = {}
                                exporter_interface.update({"vlan": vnic_ether_if.name})
                                if "fabricNetflowIPv4Addr" in self._config.sdk_objects:
                                    for fabric_netflow_ipv4_addr in self._config.sdk_objects["fabricNetflowIPv4Addr"]:
                                        if vnic_ether_if.dn + "/" in fabric_netflow_ipv4_addr.dn:
                                            if fabric_netflow_ipv4_addr.fabric_id == "A":
                                                exporter_interface.update({
                                                    "fabric_a": {
                                                        "source_ip": fabric_netflow_ipv4_addr.addr,
                                                        "subnet_mask": fabric_netflow_ipv4_addr.subnet
                                                    }
                                                })
                                            elif fabric_netflow_ipv4_addr.fabric_id == "B":
                                                exporter_interface.update({
                                                    "fabric_b": {
                                                        "source_ip": fabric_netflow_ipv4_addr.addr,
                                                        "subnet_mask": fabric_netflow_ipv4_addr.subnet
                                                    }
                                                })
                                    exporter_interfaces.append(exporter_interface)
                        flow_exporter_profile.update({"exporter_interfaces": exporter_interfaces})

                    self.flow_exporter_profiles.append(flow_exporter_profile)   

            if "fabricNetflowMonitor" in self._config.sdk_objects:
                for fabric_netflow_monitor in self._config.sdk_objects["fabricNetflowMonitor"]:
                    flow_monitor = {}
                    flow_monitor.update({
                        "name": fabric_netflow_monitor.name,
                        "descr": fabric_netflow_monitor.descr,
                        "flow_definition": fabric_netflow_monitor.flow_mon_record_def,
                        "flow_timeout_policy": fabric_netflow_monitor.flow_timeout_policy
                    })
                    if "fabricNetflowMonExporterRef" in self._config.sdk_objects:
                        exporters = []
                        for fabric_netflow_exporter_ref in self._config.sdk_objects["fabricNetflowMonExporterRef"]:
                            if fabric_netflow_monitor.dn + "/" in fabric_netflow_exporter_ref.dn:
                                exporters.append(fabric_netflow_exporter_ref.nf_mon_exporter_name)
                        flow_monitor.update({"flow_exporters": exporters})
                    self.flow_monitors.append(flow_monitor)

            if "fabricNetflowTimeoutPolicy" in self._config.sdk_objects:
                for fabric_netflow_timeout_policy in self._config.sdk_objects["fabricNetflowTimeoutPolicy"]:
                    flow_timeout_policy = {}
                    flow_timeout_policy.update({
                        "name": fabric_netflow_timeout_policy.name,
                        "descr": fabric_netflow_timeout_policy.descr,
                        "active_timeout": fabric_netflow_timeout_policy.active_timeout,
                        "inactive_timeout": fabric_netflow_timeout_policy.inactive_timeout
                    })
                    self.flow_timeout_policies.append(flow_timeout_policy)
            
            if "fabricNetflowMonSession" in self._config.sdk_objects:
                for fabric_netflow_mon_session in self._config.sdk_objects["fabricNetflowMonSession"]:
                    flow_monitor_session = {}
                    flow_monitor_session.update({
                        "name": fabric_netflow_mon_session.name,
                        "descr": fabric_netflow_mon_session.descr
                    })
                    if "fabricNetflowMonitorRef" in self._config.sdk_objects:
                        flow_monitors = []
                        for fabric_netflow_monitor_ref in self._config.sdk_objects["fabricNetflowMonitorRef"]:
                            if fabric_netflow_mon_session.dn + "/" in fabric_netflow_monitor_ref.dn:
                                flow_monitor = {}
                                flow_monitor.update({
                                    "direction": fabric_netflow_monitor_ref.direction,
                                    "name": fabric_netflow_monitor_ref.nf_monitor_name,
                                })
                                flow_monitors.append(flow_monitor)
                        flow_monitor_session.update({
                            "flow_monitors": flow_monitors
                        })
                        if "fabricNetflowMonSrcRef" in self._config.sdk_objects:
                            sources=[]
                            for fabric_netflow_mon_src_ref in self._config.sdk_objects["fabricNetflowMonSrcRef"]:
                                if fabric_netflow_mon_session.dn + "/" in fabric_netflow_mon_src_ref.dn:
                                    source={}
                                    source_dn = fabric_netflow_mon_src_ref.source_dn.split("/")
                                    source_type = fabric_netflow_mon_src_ref.source_type
                                    if source_type == "vnic":
                                        source.update({
                                            "source_type": source_type,
                                            "vnic": source_dn[2].replace("ether-", ""),
                                            "service_profile": source_dn[1].replace("ls-", ""),
                                            "org": "/".join([i.replace("org-", "", 1) for i in source_dn])
                                        })
                                        sources.append(source)
                                    if source_type == "port-profile":
                                        source={}
                                        source.update({
                                            "source_type": source_type,
                                            "port_profile": source_dn[3].replace("vnic-", "")
                                        })
                                        sources.append(source)
                            flow_monitor_session.update({
                                "sources": sources
                            })
                    self.flow_monitor_sessions.append(flow_monitor_session)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()
    
    def clean_object(self): 
        UcsSystemConfigObject.clean_object(self)

        for record_definition in self.flow_record_definitions:
            for value in ["descr", "ipv4keys", "ipv6keys", "key_type", "l2keys", "name", "nonkeys", "record_type"]:
                if value not in record_definition:
                    record_definition[value] = None

        for exporter in self.flow_exporters:
            for value in ["descr", "dscp", "exporter_profile", "flow_collector", "name", "option_exporter_stats_timeout",
                           "option_interface_table_timeout", "template_data_timeout", "version"]:
                if value not in exporter:
                    exporter[value] = None
        
        for collector in self.flow_collectors:
            for value in ["collector_ip", "descr", "exporter_gateway_ip", "name", "port", "vlan"]:
                if value not in collector:
                    collector[value] = None

        for exporter_profile in self.flow_exporter_profiles:
            for value in ["descr", "exporter_interfaces", "name"]:
                if value not in exporter_profile:
                    exporter_profile[value] = None

            if exporter_profile["exporter_interfaces"]:
                for interface in exporter_profile["exporter_interfaces"]:
                    if "vlan" not in interface:
                        interface["vlan"] = None
                    for value in ["fabric_a", "fabric_b"]:
                        if value not in interface:
                            interface[value] = None
                        elif interface[value]:
                            for sub_value in ["source_ip", "subnet_mask"]:
                                if sub_value not in interface[value]:
                                    interface[value][sub_value] = None

        for monitor in self.flow_monitors:
            for value in ["descr", "flow_definition", "flow_exporters", "flow_timeout_policy", "name"]:
                if value not in monitor:
                    monitor[value] = None

        for timeout_policy in self.flow_timeout_policies:
            for value in ["active_timeout", "descr", "inactive_timeout", "name"]:
                if value not in timeout_policy:
                    timeout_policy[value] = None
        
        for monitor_session in self.flow_monitor_sessions:
            for value in ["descr", "flow_monitors", "name", "sources"]:
                if value not in monitor_session:
                    monitor_session[value] = None
            
            if monitor_session["flow_monitors"]:
                for monitor in monitor_session["flow_monitors"]:
                    for value in ["direction", "name"]:
                        if value not in monitor:
                            monitor[value] = None

            if monitor_session["sources"]:
                for source in monitor_session["sources"]:
                    for value in ["org", "service_profile", "source_type", "vnic", "port_profile"]:
                        if value not in source:
                            source[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "fabric/lanmon"
        mo_fabric_eth_lan_flow_monitoring = FabricEthLanFlowMonitoring(parent_mo_or_dn=parent_mo,
                                                                       admin_state=self.admin_state)
        self._handle.add_mo(mo=mo_fabric_eth_lan_flow_monitoring, modify_present=True)
        if commit:
            if self.commit(detail="Admin State") != True:
                return False

        if self.flow_record_definitions:
            for record_definition in self.flow_record_definitions:
                if record_definition["record_type"] != "system-defined":
                    mo_fabric_flow_mon_definition = FabricFlowMonDefinition(parent_mo_or_dn=mo_fabric_eth_lan_flow_monitoring,
                                                                            name=record_definition["name"],
                                                                            descr=record_definition["descr"],
                                                                            key_type=record_definition["key_type"],
                                                                            ipv4keys=",".join(record_definition["ipv4keys"]) if record_definition["ipv4keys"] else None,
                                                                            ipv6keys=",".join(record_definition["ipv6keys"]) if record_definition["ipv6keys"] else None,
                                                                            l2keys=",".join(record_definition["l2keys"]) if record_definition["l2keys"] else None,
                                                                            nonkeys=",".join(record_definition["nonkeys"] if record_definition["nonkeys"] else None)
                                                                            )
                    self._handle.add_mo(mo=mo_fabric_flow_mon_definition, modify_present=True)
                    if commit:
                        if self.commit(detail="Flow Record Definition - '" + record_definition["name"] + "'") != True:
                            return False

        if self.flow_exporter_profiles:
            for exporter_profile in self.flow_exporter_profiles:
                mo_fabric_flow_mon_exporter_profile = FabricFlowMonExporterProfile(parent_mo_or_dn=mo_fabric_eth_lan_flow_monitoring,
                                                                    name=exporter_profile["name"],
                                                                    descr=exporter_profile["descr"]
                                                                    )
                for interface in exporter_profile["exporter_interfaces"]:
                    mo_vnic_ether_if = VnicEtherIf(parent_mo_or_dn=mo_fabric_flow_mon_exporter_profile, name=interface["vlan"])
                    for fabric_id in ["A", "B"]:
                        fabric = interface[f"fabric_{fabric_id.lower()}"]
                        if fabric is not None:
                            FabricNetflowIPv4Addr(parent_mo_or_dn=mo_vnic_ether_if, addr=fabric["source_ip"], subnet=fabric["subnet_mask"], fabric_id=fabric_id)
                    self._handle.add_mo(mo=mo_vnic_ether_if, modify_present=True)
                    if commit:
                        if self.commit(detail="Flow Exporter Profile - '" + exporter_profile["name"] + "'") != True:
                            return False
                        
        if self.flow_collectors:
            for collector in self.flow_collectors:
                mo_fabric_netflow_collector = FabricNetflowCollector(parent_mo_or_dn=mo_fabric_eth_lan_flow_monitoring,
                                                                    name=collector["name"],
                                                                    descr=collector["descr"],
                                                                    source_vlan=collector["vlan"],
                                                                    port=collector["port"]
                                                                    )
                IpIpV4StaticTargetAddr(parent_mo_or_dn=mo_fabric_netflow_collector, addr=collector["collector_ip"],
                                       def_gw=collector["exporter_gateway_ip"])
                self._handle.add_mo(mo=mo_fabric_netflow_collector, modify_present=True)
                if commit:
                    if self.commit(detail="Flow Collector - '" + collector["name"] + "'") != True:
                        return False
        
        if self.flow_exporters:
            for exporter in self.flow_exporters:
                mo_fabric_netflow_mon_exporter = FabricNetflowMonExporter(parent_mo_or_dn=mo_fabric_eth_lan_flow_monitoring,
                                                                          name=exporter["name"],
                                                                          descr=exporter["descr"],
                                                                          dscp=exporter["dscp"],
                                                                          flow_exp_profile=exporter["exporter_profile"],
                                                                          flow_mon_collector=exporter["flow_collector"],
                                                                          exporter_stats_timeout=exporter["option_exporter_stats_timeout"],
                                                                          interface_table_timeout=exporter["option_interface_table_timeout"],
                                                                          template_data_timeout=exporter["template_data_timeout"]
                                                                        )
                self._handle.add_mo(mo=mo_fabric_netflow_mon_exporter, modify_present=True)
                if commit:
                    if self.commit(detail="Flow Exporter - '" + exporter["name"] + "'") != True:
                        return False
        
        if self.flow_monitors:
            for monitor in self.flow_monitors:
                mo_fabric_netflow_monitor = FabricNetflowMonitor(parent_mo_or_dn=mo_fabric_eth_lan_flow_monitoring,
                                                                          name=monitor["name"],
                                                                          descr=monitor["descr"],
                                                                          flow_mon_record_def=monitor["flow_definition"],
                                                                          flow_timeout_policy=monitor["flow_timeout_policy"]
                                                                )
                if monitor["flow_exporters"]:
                    for flow_exporter in monitor["flow_exporters"]:
                        FabricNetflowMonExporterRef(parent_mo_or_dn=mo_fabric_netflow_monitor, nf_mon_exporter_name=flow_exporter)
                self._handle.add_mo(mo=mo_fabric_netflow_monitor, modify_present=True)
                if commit:
                    if self.commit(detail="Flow Monitor - '" + monitor["name"] + "'") != True:
                        return False
        
        if self.flow_timeout_policies:
            # Only 'descr' of the pre-defined 'default' flow timeout policy can be pushed.
            mo_fabric_netflow_timeout_policy = FabricNetflowTimeoutPolicy(parent_mo_or_dn=mo_fabric_eth_lan_flow_monitoring,
                                                                          name="default",
                                                                          descr=self.flow_timeout_policies[0]["descr"])
            self._handle.add_mo(mo=mo_fabric_netflow_timeout_policy, modify_present=True)
            if commit:
                if self.commit(detail="Flow Timeout Policy - 'default'") != True:
                    return False
            

        if self.flow_monitor_sessions:
            for monitor_session in self.flow_monitor_sessions:
                mo_fabric_netflow_mon_session = FabricNetflowMonSession(parent_mo_or_dn=mo_fabric_eth_lan_flow_monitoring,
                                                                        name=monitor_session["name"],
                                                                        descr=monitor_session["descr"]
                                                                        )
                if monitor_session["flow_monitors"]:
                    for flow_monitor in monitor_session["flow_monitors"]:
                        if flow_monitor.get("direction") is not None:
                            FabricNetflowMonitorRef(parent_mo_or_dn=mo_fabric_netflow_mon_session, nf_monitor_name=flow_monitor["name"],
                                                    direction=flow_monitor["direction"])
                self._handle.add_mo(mo=mo_fabric_netflow_mon_session, modify_present=True)
                if commit:
                    if self.commit(detail="Flow Monitor Session - '" + monitor_session["name"] + "'") != True:
                        return False
                if monitor_session["sources"]:
                    source_failed = False
                    for source in monitor_session["sources"]:
                        src_descr = ""
                        if source["source_type"] == "vnic":
                            dn_splitted = source["org"].split("/")
                            ls_index = dn_splitted.index(next(path for path in dn_splitted if path.startswith("ls-")))
                            parent_dn = "/".join([f"org-{path}" if i < ls_index else path for i, path in enumerate(dn_splitted[:-1])])
                            src_descr = source["org"] + "/" + source["service_profile"] + " - " + source["vnic"]
                            mo_fabric_netflow_mon_src_ep = FabricNetflowMonSrcEp(parent_mo_or_dn=parent_dn, name=monitor_session["name"])
                            self._handle.add_mo(mo=mo_fabric_netflow_mon_src_ep, modify_present=True)
                        elif source["source_type"] == "port-profile":
                            mo_fabric_netflow_mon_src_ep = FabricNetflowMonSrcEp(parent_mo_or_dn="fabric/lan/profiles/vnic-" + source["port_profile"],
                                                                                 name=monitor_session["name"])
                            self._handle.add_mo(mo=mo_fabric_netflow_mon_src_ep, modify_present=True)
                        if commit:
                            if self.commit(detail="Source " + source["source_type"] + " " + src_descr) != True:
                                source_failed = True
                    if source_failed:
                        return False

        return True


class UcsSystemVnicTemplate(UcsSystemConfigObject):
    _CONFIG_NAME = "vNIC Template"
    _CONFIG_SECTION_NAME = "vnic_templates"
    _UCS_SDK_OBJECT_NAME = "vnicLanConnTempl"
    _POLICY_MAPPING_TABLE = {
        "mac_address_pool": UcsSystemMacPool,
        "network_control_policy": UcsSystemNetworkControlPolicy,
        "pin_group": UcsSystemLanPinGroup,
        "qos_policy": UcsSystemQosPolicy,
        "sriov_hpn_connection_policy": UcsSystemSriovHpnConnectionPolicy,
        "stats_threshold_policy": UcsSystemThresholdPolicy,
        "usnic_connection_policy": UcsSystemUsnicConnectionPolicy,
        "vmq_connection_policy": UcsSystemVmqConnectionPolicy,
    }

    def __init__(self, parent=None, json_content=None, vnic_lan_conn_templ=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_lan_conn_templ)
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
        self.mac_address_pool = None
        self.template_type = None
        self.pin_group = None
        self.q_in_q = None
        self.etherchannel_pinning = None
        self.dynamic_vnic_connection_policy = None
        self.stats_threshold_policy = None
        self.sriov_hpn_connection_policy = None
        self.network_control_policy = None
        self.usnic_connection_policy = None
        self.vmq_connection_policy = None
        self.vlan_native = None
        self.vlan_q_in_q = None
        self.vlans = []
        self.vlan_groups = []
        self.operational_state = {}

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
                self.mac_address_pool = vnic_lan_conn_templ.ident_pool_name
                self.template_type = vnic_lan_conn_templ.templ_type
                self.pin_group = vnic_lan_conn_templ.pin_to_group_name
                self.stats_threshold_policy = vnic_lan_conn_templ.stats_policy_name
                self.network_control_policy = vnic_lan_conn_templ.nw_ctrl_policy_name
                self.q_in_q = vnic_lan_conn_templ.q_in_q
                self.etherchannel_pinning = vnic_lan_conn_templ.ether_channel_pinning

                # Looking for the connection_policy
                if "vnicDynamicConPolicyRef" in self._parent._config.sdk_objects and \
                        not self.dynamic_vnic_connection_policy:
                    for policy in self._config.sdk_objects["vnicDynamicConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ-" + self.name + "/" in policy.dn:
                                self.dynamic_vnic_connection_policy = policy.con_policy_name
                                self.operational_state.update(
                                    self.get_operational_state(
                                        policy_dn=policy.oper_con_policy_name,
                                        separator="/dynamic-con-",
                                        policy_name="dynamic_vnic_connection_policy"
                                    )
                                )
                                break
                if "vnicUsnicConPolicyRef" in self._parent._config.sdk_objects and not self.usnic_connection_policy:
                    for policy in self._config.sdk_objects["vnicUsnicConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ-" + self.name + "/" in policy.dn:
                                self.usnic_connection_policy = policy.con_policy_name
                                self.operational_state.update(
                                    self.get_operational_state(
                                        policy_dn=policy.oper_con_policy_name,
                                        separator="/usnic-con-",
                                        policy_name="usnic_connection_policy"
                                    )
                                )
                                break
                if "vnicVmqConPolicyRef" in self._parent._config.sdk_objects and not self.vmq_connection_policy:
                    for policy in self._config.sdk_objects["vnicVmqConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ-" + self.name + "/" in policy.dn:
                                self.vmq_connection_policy = policy.con_policy_name
                                self.operational_state.update(
                                    self.get_operational_state(
                                        policy_dn=policy.oper_con_policy_name,
                                        separator="/vmq-con-",
                                        policy_name="vmq_connection_policy"
                                    )
                                )
                                break
                if "vnicSriovHpnConPolicyRef" in self._parent._config.sdk_objects and \
                        not self.sriov_hpn_connection_policy:
                    for policy in self._config.sdk_objects["vnicSriovHpnConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ-" + self.name + "/" in policy.dn:
                                self.sriov_hpn_connection_policy = policy.con_policy_name
                                self.operational_state.update(
                                    self.get_operational_state(
                                        policy_dn=policy.oper_con_policy_name,
                                        separator="/sriov-hpn-con-",
                                        policy_name="sriov_hpn_connection_policy"
                                    )
                                )
                                break

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
                                if vlan.is_qin_q_vlan in ["yes", "true"]:
                                    self.vlan_q_in_q = vlan.name
                if "fabricNetGroupRef" in self._config.sdk_objects:
                    if self._parent._dn:
                        vlans = [vlan for vlan in self._config.sdk_objects["fabricNetGroupRef"] if
                                 self._parent._dn + "/lan-conn-templ-" + self.name + "/" in vlan.dn]
                        if vlans:
                            for vlan in vlans:
                                self.vlan_groups.append(vlan.name)

                # Fetching the operational state of the referenced policies
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vnic_lan_conn_templ.oper_nw_ctrl_policy_name,
                        separator="/nwctrl-",
                        policy_name="network_control_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vnic_lan_conn_templ.oper_peer_redundancy_templ_name,
                        separator="/lan-conn-templ-",
                        policy_name="peer_redundancy_template"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vnic_lan_conn_templ.oper_qos_policy_name,
                        separator="/ep-qos-",
                        policy_name="qos_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vnic_lan_conn_templ.oper_stats_policy_name,
                        separator="/thr-policy-",
                        policy_name="stats_threshold_policy"
                    )
                )

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for policy in ["dynamic_vnic_connection_policy", "mac_address_pool", "network_control_policy",
                       "peer_redundancy_template", "qos_policy", "sriov_hpn_connection_policy",
                       "stats_threshold_policy", "usnic_connection_policy", "vmq_connection_policy"]:
            if policy not in self.operational_state:
                self.operational_state[policy] = None
            elif self.operational_state[policy]:
                for value in ["name", "org"]:
                    if value not in self.operational_state[policy]:
                        self.operational_state[policy][value] = None

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
                                                 q_in_q=self.q_in_q,
                                                 ether_channel_pinning=self.etherchannel_pinning,
                                                 redundancy_pair_type=redundancy_pair_type,
                                                 qos_policy_name=self.qos_policy,
                                                 peer_redundancy_templ_name=self.peer_redundancy_template,
                                                 templ_type=self.template_type, mtu=self.mtu,
                                                 ident_pool_name=self.mac_address_pool,
                                                 pin_to_group_name=self.pin_group,
                                                 stats_policy_name=self.stats_threshold_policy)

        if self.dynamic_vnic_connection_policy:
            VnicDynamicConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                    con_policy_name=self.dynamic_vnic_connection_policy)
        if self.usnic_connection_policy:
            VnicUsnicConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                  con_policy_name=self.usnic_connection_policy)
        if self.vmq_connection_policy:
            VnicVmqConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                con_policy_name=self.vmq_connection_policy)
        if self.sriov_hpn_connection_policy:
            VnicSriovHpnConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                     con_policy_name=self.sriov_hpn_connection_policy)

        # self._handle.add_mo(mo=mo_vnic_lan_conn_temp, modify_present=True)
        # if commit:
        #     if self.commit(detail=self.name) != True:
        #         return False

        if self.vlans:
            for vlan in self.vlans:
                if vlan == self.vlan_native:
                    # Avoid an issue when the native VLAN is written in the VLANS section and VLAN Native parameter
                    continue
                if self.vlan_q_in_q == vlan:
                    vnic_q_in_q = "yes"
                else:
                    vnic_q_in_q = "no"
                VnicEtherIf(parent_mo_or_dn=mo_vnic_lan_conn_temp, name=vlan, default_net="no",
                            is_qin_q_vlan=vnic_q_in_q)
        if self.vlan_native:
            if self.vlan_q_in_q == self.vlan_native:
                vnic_q_in_q = "yes"
            else:
                vnic_q_in_q = "no"
            VnicEtherIf(parent_mo_or_dn=mo_vnic_lan_conn_temp, name=self.vlan_native, default_net="yes",
                        is_qin_q_vlan=vnic_q_in_q)
        if self.vlan_groups:
            for vlan in self.vlan_groups:
                FabricNetGroupRef(parent_mo_or_dn=mo_vnic_lan_conn_temp, name=vlan)

        self._handle.add_mo(mo=mo_vnic_lan_conn_temp, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemLanConnectivityPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "LAN Connectivity Policy"
    _CONFIG_SECTION_NAME = "lan_connectivity_policies"
    _UCS_SDK_OBJECT_NAME = "vnicLanConnPolicy"
    _POLICY_MAPPING_TABLE = {
        "vnics": [
            {
                "adapter_policy": UcsSystemEthernetAdapterPolicy,
                "mac_address_pool": UcsSystemMacPool,
                "network_control_policy": UcsSystemNetworkControlPolicy,
                "pin_group": UcsSystemLanPinGroup,
                "qos_policy": UcsSystemQosPolicy,
                "sriov_hpn_connection_policy": UcsSystemSriovHpnConnectionPolicy,
                "stats_threshold_policy": UcsSystemThresholdPolicy,
                "usnic_connection_policy": UcsSystemUsnicConnectionPolicy,
                "vmq_connection_policy": UcsSystemVmqConnectionPolicy,
                "vnic_template": UcsSystemVnicTemplate
            }
        ]
    }

    def __init__(self, parent=None, json_content=None, vnic_lan_conn_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_lan_conn_policy)
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
                            if self._parent._dn + "/lan-conn-pol-" + self.name + "/" in vnic_ether.dn:
                                oper_state = {}
                                vnic = {"_object_type": "vnics"}
                                vnic.update({"name": vnic_ether.name})
                                vnic.update({"adapter_policy": vnic_ether.adaptor_profile_name})
                                vnic.update({"order": vnic_ether.order})

                                if vnic_ether.nw_templ_name:
                                    vnic.update({"vnic_template": vnic_ether.nw_templ_name})
                                    vnic.update({"redundancy_pair": vnic_ether.redundancy_pair_type})
                                else:
                                    vnic.update({"fabric": vnic_ether.switch_id})
                                    vnic.update({"q_in_q": vnic_ether.q_in_q})
                                    vnic.update({"etherchannel_pinning": vnic_ether.ether_channel_pinning})
                                    vnic.update({"mac_address_pool": vnic_ether.ident_pool_name})
                                    if not vnic_ether.ident_pool_name and vnic_ether.addr == "derived":
                                        vnic.update({"mac_address": "hardware-default"})
                                    vnic.update({"mtu": vnic_ether.mtu})
                                    vnic.update({"qos_policy": vnic_ether.qos_policy_name})
                                    vnic.update({"network_control_policy": vnic_ether.nw_ctrl_policy_name})
                                    vnic.update({"cdn_source": vnic_ether.cdn_source})
                                    vnic.update({"cdn_name": vnic_ether.admin_cdn_name})
                                    vnic.update({"pin_group": vnic_ether.pin_to_group_name})
                                    vnic.update({"stats_threshold_policy": vnic_ether.stats_policy_name})

                                    vnic.update({"dynamic_vnic_connection_policy": None})
                                    vnic.update({"usnic_connection_policy": None})
                                    vnic.update({"vmq_connection_policy": None})
                                    vnic.update({"sriov_hpn_connection_policy": None})
                                    if "vnicDynamicConPolicyRef" in self._parent._config.sdk_objects:
                                        for conn_policy in self._config.sdk_objects["vnicDynamicConPolicyRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update(
                                                    {"dynamic_vnic_connection_policy": conn_policy.con_policy_name})
                                                # Added the operational state of connection policy for manual type
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=conn_policy.oper_con_policy_name,
                                                        separator="/dynamic-con-",
                                                        policy_name="dynamic_vnic_connection_policy"
                                                    )
                                                )
                                                break
                                    if "vnicUsnicConPolicyRef" in self._parent._config.sdk_objects \
                                            and not vnic['usnic_connection_policy']:
                                        for conn_policy in self._config.sdk_objects["vnicUsnicConPolicyRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update({"usnic_connection_policy": conn_policy.con_policy_name})
                                                # Added the operational state of connection policy for manual type
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=conn_policy.oper_con_policy_name,
                                                        separator="/usnic-con-",
                                                        policy_name="usnic_connection_policy"
                                                    )
                                                )
                                                break
                                    if "vnicVmqConPolicyRef" in self._parent._config.sdk_objects \
                                            and not vnic['vmq_connection_policy']:
                                        for conn_policy in self._config.sdk_objects["vnicVmqConPolicyRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update({"vmq_connection_policy": conn_policy.con_policy_name})
                                                # Added the operational state of connection policy for manual type
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=conn_policy.oper_con_policy_name,
                                                        separator="/vmq-con-",
                                                        policy_name="vmq_connection_policy"
                                                    )
                                                )
                                                break
                                    if "vnicSriovHpnConPolicyRef" in self._parent._config.sdk_objects \
                                            and not vnic['sriov_hpn_connection_policy']:
                                        for conn_policy in self._config.sdk_objects["vnicSriovHpnConPolicyRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update(
                                                    {"sriov_hpn_connection_policy": conn_policy.con_policy_name})
                                                # Added the operational state of connection policy for manual type
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=conn_policy.oper_con_policy_name,
                                                        separator="/sriov-hpn-con-",
                                                        policy_name="sriov_hpn_connection_policy"
                                                    )
                                                )
                                                break

                                    if "vnicEtherIf" in self._parent._config.sdk_objects:
                                        vnic.update({"vlans": []})
                                        for vnic_ether_if in self._config.sdk_objects["vnicEtherIf"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in vnic_ether_if.dn:
                                                if vnic_ether_if.default_net == "yes":
                                                    vnic.update({"vlan_native": vnic_ether_if.name})
                                                else:
                                                    vnic['vlans'].append(vnic_ether_if.name)
                                                if vnic_ether_if.is_qin_q_vlan in ["yes", "true"]:
                                                    vnic.update({"vlan_q_in_q": vnic_ether_if.name})

                                    if "fabricNetGroupRef" in self._parent._config.sdk_objects:
                                        vnic.update({"vlan_groups": []})
                                        for fabric_net_group_ref in self._config.sdk_objects["fabricNetGroupRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in fabric_net_group_ref.dn:
                                                vnic['vlan_groups'].append(fabric_net_group_ref.name)

                                # Fetching the operational state of the referenced policies
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_adaptor_profile_name,
                                        separator="/eth-profile-",
                                        policy_name="adapter_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_nw_ctrl_policy_name,
                                        separator="/nwctrl-",
                                        policy_name="network_control_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_pin_to_group_name,
                                        separator="/lan-pin-group-",
                                        policy_name="pin_group"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_qos_policy_name,
                                        separator="/ep-qos-",
                                        policy_name="qos_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_stats_policy_name,
                                        separator="/thr-policy-",
                                        policy_name="stats_threshold_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_nw_templ_name,
                                        separator="/lan-conn-templ-",
                                        policy_name="vnic_template"
                                    )
                                )

                                vnic['operational_state'] = oper_state

                                self.vnics.append(vnic)

                if "vnicIScsiLCP" in self._parent._config.sdk_objects:
                    for vnic_iscsi_lcp in self._config.sdk_objects["vnicIScsiLCP"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-pol-" + self.name + "/" in vnic_iscsi_lcp.dn:
                                oper_state = {}
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
                                            break
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_iscsi_lcp.oper_adaptor_profile_name,
                                        separator="/iscsi-profile-",
                                        policy_name="iscsi_adapter_policy"
                                    )
                                )
                                vnic['operational_state'] = oper_state

                                self.iscsi_vnics.append(vnic)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)


        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.vnics:
            for value in ["adapter_policy", "cdn_name", "cdn_source", "dynamic_vnic_connection_policy",
                          "etherchannel_pinning", "fabric", "mac_address", "mac_address_pool", "mtu", "name",
                          "network_control_policy", "order", "operational_state", "pin_group", "q_in_q", "qos_policy",
                          "redundancy_pair", "sriov_hpn_connection_policy", "stats_threshold_policy",
                          "usnic_connection_policy", "vlans", "vlan_groups", "vlan_native", "vlan_q_in_q",
                          "vmq_connection_policy", "vnic_template"]:
                if value not in element:
                    element[value] = None

            if element["operational_state"]:
                for policy in ["adapter_policy", "mac_address_pool", "network_control_policy", "pin_group",
                               "qos_policy", "stats_threshold_policy", "vnic_template"]:
                    if policy not in element["operational_state"]:
                        element["operational_state"][policy] = None
                    elif element["operational_state"][policy]:
                        for value in ["name", "org"]:
                            if value not in element["operational_state"][policy]:
                                element["operational_state"][policy][value] = None

            # Flagging this as a vNIC
            element["_object_type"] = "vnics"

        for element in self.iscsi_vnics:
            for value in ["vlan", "mac_address_pool", "overlay_vnic", "name", "iscsi_adapter_policy",
                          "operational_state"]:
                if value not in element:
                    element[value] = None

            if element["operational_state"]:
                for policy in ["iscsi_adapter_policy"]:
                    if policy not in element["operational_state"]:
                        element["operational_state"][policy] = None
                    elif element["operational_state"][policy]:
                        for value in ["name", "org"]:
                            if value not in element["operational_state"][policy]:
                                element["operational_state"][policy][value] = None

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
                if vnic['vnic_template']:
                    # TODO: Handle initial-template pushing
                    mo_vnic_ether = VnicEther(parent_mo_or_dn=mo_vnic_lan_conn_policy,
                                              adaptor_profile_name=vnic['adapter_policy'],
                                              nw_templ_name=vnic['vnic_template'],
                                              # redundancy_pair_type=vnic['redundancy_pair'],
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
                                              q_in_q=vnic['q_in_q'],
                                              ether_channel_pinning=vnic['etherchannel_pinning'],
                                              ident_pool_name=mac_address_pool,
                                              addr=mac_address,
                                              qos_policy_name=vnic['qos_policy'],
                                              nw_ctrl_policy_name=vnic['network_control_policy'],
                                              cdn_source=vnic['cdn_source'],
                                              admin_cdn_name=vnic['cdn_name'],
                                              pin_to_group_name=vnic['pin_group'],
                                              stats_policy_name=vnic["stats_threshold_policy"])
                    self._handle.add_mo(mo=mo_vnic_ether, modify_present=True)
                    # We need to commit the interface first and then add the vlan and connection policy to it
                    if commit:
                        if self.commit(detail=vnic['name'] + " on " + str(self.name)) != True:
                            # We can use continue because the commit buffer is discard if it's an SDK error exception
                            continue

                    # Creating connection_policy
                    if vnic["dynamic_vnic_connection_policy"]:
                        # connection_policy = "SRIOV-VMFEX"
                        VnicDynamicConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                                con_policy_name=vnic["dynamic_vnic_connection_policy"])
                    elif vnic["sriov_hpn_connection_policy"]:
                        # connection_policy = "SRIOV-HPN"
                        VnicSriovHpnConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                                 con_policy_name=vnic["sriov_hpn_connection_policy"])
                    elif vnic["usnic_connection_policy"]:
                        # connection_policy = "SRIOV-USNIC"
                        VnicUsnicConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                              con_policy_name=vnic["usnic_connection_policy"])
                    elif vnic["vmq_connection_policy"]:
                        # connection_policy = "VMQ"
                        VnicVmqConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                            con_policy_name=vnic["vmq_connection_policy"])

                    # Adding the vlans
                    if vnic['vlan_native']:
                        if vnic['vlan_q_in_q'] == vnic['vlan_native']:
                            vnic_q_in_q = "yes"
                        else:
                            vnic_q_in_q = "no"
                        mo_vnic_ether_if = VnicEtherIf(parent_mo_or_dn=mo_vnic_ether,
                                                       name=vnic['vlan_native'],
                                                       default_net="yes",
                                                       is_qin_q_vlan=vnic_q_in_q)
                        self._handle.add_mo(mo_vnic_ether_if, modify_present=True)
                    if vnic['vlans']:
                        for vlan in vnic['vlans']:
                            if vnic['vlan_q_in_q'] == vlan:
                                vnic_q_in_q = "yes"
                            else:
                                vnic_q_in_q = "no"
                            mo_vnic_ether_if = VnicEtherIf(parent_mo_or_dn=mo_vnic_ether,
                                                           name=vlan,
                                                           default_net="no",
                                                           is_qin_q_vlan=vnic_q_in_q)
                            self._handle.add_mo(mo_vnic_ether_if, modify_present=True)

                    # Adding the vlan groups
                    if vnic['vlan_groups']:
                        for vlan_group in vnic['vlan_groups']:
                            mo_fabric_net_group_ref = FabricNetGroupRef(parent_mo_or_dn=mo_vnic_ether,
                                                                        name=vlan_group)
                            self._handle.add_mo(mo_fabric_net_group_ref, modify_present=True)

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


class UcsSystemMacSec(UcsSystemConfigObject):
    _CONFIG_NAME = "MACsec"
    _CONFIG_SECTION_NAME = "macsec"
    _UCS_SDK_OBJECT_NAME = "fabricMacSec"

    def __init__(self, parent=None, json_content=None, fabric_mac_sec=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_mac_sec)
        self.admin_state = None
        self.keychain = None
        self.policies = None
        self.eapol = None
        self.interface_configuration = None
        if self._config.load_from == "live":
            if fabric_mac_sec is not None:
                self.admin_state = fabric_mac_sec.admin_state

            if "fabricMacSecKeyChain" in self._config.sdk_objects:
                macsec_keychains = []
                for keychain in self._config.sdk_objects["fabricMacSecKeyChain"]:
                    if fabric_mac_sec.dn+"/macsec-keychain-"+keychain.name == keychain.dn:
                        keychain_dict = {
                            "name": keychain.name
                        }
                        if "fabricMacSecKey" in self._config.sdk_objects:
                            keys = []
                            for key in self._config.sdk_objects["fabricMacSecKey"]:
                                if fabric_mac_sec.dn + "/macsec-keychain-" + keychain.name + "/macsec-key-" + key.key_id == key.dn:
                                    key_dict = {
                                        "key_id": key.key_id,
                                        "encrypt_type": key.encrypt_type,
                                        "cryptographic_algorithm": key.cryptographic_algorithm
                                    }
                                    if key.key_hex_string:
                                        key_dict["key_hex_string"] = key.key_hex_string
                                    if "fabricLifeTime" in self._config.sdk_objects:
                                        life_time = []
                                        for lifetime in self._config.sdk_objects["fabricLifeTime"]:
                                            if fabric_mac_sec.dn + "/macsec-keychain-" + keychain.name + "/macsec-key-" + key.key_id + "/lifetime" == lifetime.dn:
                                                lifetime_dict = {
                                                    "start_date_time": lifetime.start_date_time,
                                                    "timezone": lifetime.timezone,
                                                    "infinite_lifetime": lifetime.infinite
                                                }
                                                if lifetime.infinite != "enabled":
                                                    lifetime_dict["duration"] = lifetime.duration
                                                    lifetime_dict["end_date_time"] = lifetime.end_date_time
                                                life_time.append(lifetime_dict)
                                        key_dict["lifetime"] = life_time

                                    keys.append(key_dict)
                            keychain_dict["keys"] = keys

                        macsec_keychains.append(keychain_dict)
                self.keychain = macsec_keychains

            if "fabricMacSecPolicy" in self._config.sdk_objects:
                macsec_policies = []
                for policy in self._config.sdk_objects["fabricMacSecPolicy"]:
                    if fabric_mac_sec.dn+"/macsec-policy-"+policy.name == policy.dn:
                        macsec_policy = {
                            "name": policy.name,
                            "descr": policy.descr,
                            "cipher_suite": policy.cipher_suite,
                            "conf_offset": policy.conf_offset,
                            "include_icv_param": policy.include_icv_param,
                            "security_policy": policy.security_policy,
                            "key_server_priority": policy.key_server_priority,
                            "replay_window_size": policy.replay_window_size
                        }
                        if policy.sak_expiry_time != "0":
                            macsec_policy["sak_expiry_time"] = policy.sak_expiry_time

                        macsec_policies.append(macsec_policy)
                self.policies = macsec_policies

            if "fabricMacSecEapol" in self._config.sdk_objects:
                macsec_eapol = []
                for eapol in self._config.sdk_objects["fabricMacSecEapol"]:
                    if fabric_mac_sec.dn + "/macsec-eapol-" + eapol.name == eapol.dn:
                        eapol_dict = {
                            "name": eapol.name,
                            "descr": eapol.descr,
                            "ether_type": hex(int(eapol.ether_type)),
                            "mac_address": eapol.mac_address
                        }
                        macsec_eapol.append(eapol_dict)
                self.eapol = macsec_eapol

            if "fabricMacSecIfConfig" in self._config.sdk_objects:
                macsec_if_config = []
                for if_config in self._config.sdk_objects["fabricMacSecIfConfig"]:
                    if fabric_mac_sec.dn + "/macsec-intf-conf-" + if_config.name == if_config.dn:
                        config = {
                            "name": if_config.name,
                            "macsec_eapol_name": if_config.mac_sec_eapol_name,
                            "macsec_fallback_keychain_name": if_config.mac_sec_fallback_key_chain_name,
                            "macsec_keychain_name": if_config.mac_sec_key_chain_name,
                            "macsec_policy_name": if_config.mac_sec_policy_name
                        }
                        macsec_if_config.append(config)
                self.interface_configuration = macsec_if_config

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        if self.policies:
            for element in self.policies:
                for value in ["name", "descr", "cipher_suite", "key_server_priority", "security_policy",
                              "replay_window_size", "sak_expiry_time", "include_icv_param"]:
                    if value not in element:
                        element[value] = None
        if self.eapol:
            for element in self.eapol:
                for value in ["name", "descr", "mac_address", "ether_type"]:
                    if value not in element:
                        element[value] = None
        if self.interface_configuration:
            for element in self.interface_configuration:
                for value in ["name", "macsec_eapol_name", "macsec_fallback_keychain_name", "macsec_keychain_name",
                              "macsec_policy_name"]:
                    if value not in element:
                        element[value] = None
        if self.keychain:
            for element in self.keychain:
                for value in ["name", "keys"]:
                    if value not in element:
                        element[value] = None

                if element["keys"]:
                    for key in element["keys"]:
                        for value in ["cryptographic_algorithm", "encrypt_type", "key_hex_string", "key_id",
                                      "lifetime"]:
                            if value not in key:
                                key[value] = None

                        if key["lifetime"]:
                            for lifetime in key["lifetime"]:
                                for value in ["duration", "end_date_time", "infinite_lifetime", "start_date_time",
                                              "timezone"]:
                                    if value not in lifetime:
                                        lifetime[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "fabric/lan"
        mo_fabric_mac_sec = FabricMacSec(parent_mo_or_dn=parent_mo, admin_state=self.admin_state)
        self._handle.add_mo(mo=mo_fabric_mac_sec, modify_present=True)

        if self.policies:
            for policy in self.policies:

                mo_fabric_mac_sec_policy = FabricMacSecPolicy(parent_mo_or_dn=mo_fabric_mac_sec,
                                                              name=policy["name"],
                                                              descr=policy["descr"],
                                                              cipher_suite=policy["cipher_suite"],
                                                              conf_offset=policy["conf_offset"],
                                                              include_icv_param=policy["include_icv_param"],
                                                              key_server_priority=policy["key_server_priority"],
                                                              replay_window_size=policy["replay_window_size"],
                                                              sak_expiry_time=policy["sak_expiry_time"],
                                                              security_policy=policy["security_policy"]
                                                              )
                self._handle.add_mo(mo=mo_fabric_mac_sec_policy, modify_present=True)

        if self.eapol:
            for eapol in self.eapol:
                mo_fabric_mac_sec_eapol = FabricMacSecEapol(parent_mo_or_dn=mo_fabric_mac_sec,
                                                            ether_type=str(int(eapol["ether_type"], 16)),
                                                            mac_address=eapol["mac_address"],
                                                            name=eapol["name"],
                                                            descr=eapol["descr"]
                                                            )
                self._handle.add_mo(mo=mo_fabric_mac_sec_eapol, modify_present=True)

        if self.interface_configuration:
            for intf_config in self.interface_configuration:
                mo_fabric_mac_sec_intf_config = FabricMacSecIfConfig(
                    parent_mo_or_dn=mo_fabric_mac_sec,
                    mac_sec_eapol_name=intf_config["macsec_eapol_name"],
                    mac_sec_fallback_key_chain_name=intf_config["macsec_fallback_keychain_name"],
                    mac_sec_key_chain_name=intf_config["macsec_keychain_name"],
                    mac_sec_policy_name=intf_config["macsec_policy_name"],
                    name=intf_config["name"]
                )
                self._handle.add_mo(mo=mo_fabric_mac_sec_intf_config, modify_present=True)

        if self.keychain:
            for keychain in self.keychain:
                mo_fabric_mac_sec_keychain = FabricMacSecKeyChain(parent_mo_or_dn=mo_fabric_mac_sec,
                                                                  name=keychain["name"])
                if keychain.get("keys"):
                    for keys in keychain["keys"]:
                        mo_fabric_mac_sec_key = FabricMacSecKey(
                            parent_mo_or_dn=mo_fabric_mac_sec_keychain,
                            key_id=keys["key_id"],
                            key_hex_string=keys["key_hex_string"],
                            encrypt_type=keys["encrypt_type"],
                            cryptographic_algorithm=keys["cryptographic_algorithm"]
                        )
                        self._handle.add_mo(mo=mo_fabric_mac_sec_key, modify_present=True)

                        if keys.get("lifetime"):
                            for lifetime in keys["lifetime"]:
                                mo_fabric_mac_sec_key_lifetime = FabricLifeTime(
                                    parent_mo_or_dn=mo_fabric_mac_sec_key,
                                    duration=lifetime["duration"],
                                    start_date_time=lifetime["start_date_time"],
                                    end_date_time=lifetime["end_date_time"],
                                    timezone=lifetime["timezone"],
                                    infinite=lifetime["infinite_lifetime"]
                                )
                                self._handle.add_mo(mo=mo_fabric_mac_sec_key_lifetime, modify_present=True)
                self._handle.add_mo(mo=mo_fabric_mac_sec_keychain, modify_present=True)

        if commit:
            if self.commit(detail="Admin State") != True:
                return False

        return True
