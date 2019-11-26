# coding: utf-8
# !/usr/bin/env python

""" san.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

from ucsmsdk.mometa.fabric.FabricFcEndpoint import FabricFcEndpoint
from ucsmsdk.mometa.fabric.FabricFcEstcEp import FabricFcEstcEp
from ucsmsdk.mometa.fabric.FabricFcSanEp import FabricFcSanEp
from ucsmsdk.mometa.fabric.FabricFcSanPc import FabricFcSanPc
from ucsmsdk.mometa.fabric.FabricFcSanPcEp import FabricFcSanPcEp
from ucsmsdk.mometa.fabric.FabricFcUserZone import FabricFcUserZone
from ucsmsdk.mometa.fabric.FabricFcVsanPc import FabricFcVsanPc
from ucsmsdk.mometa.fabric.FabricFcVsanPortEp import FabricFcVsanPortEp
from ucsmsdk.mometa.fabric.FabricFcZoneProfile import FabricFcZoneProfile
from ucsmsdk.mometa.fabric.FabricFcoeEstcEp import FabricFcoeEstcEp
from ucsmsdk.mometa.fabric.FabricFcoeSanEp import FabricFcoeSanEp
from ucsmsdk.mometa.fabric.FabricFcoeSanPc import FabricFcoeSanPc
from ucsmsdk.mometa.fabric.FabricFcoeSanPcEp import FabricFcoeSanPcEp
from ucsmsdk.mometa.fabric.FabricFcoeVsanPortEp import FabricFcoeVsanPortEp
from ucsmsdk.mometa.fabric.FabricSanPinGroup import FabricSanPinGroup
from ucsmsdk.mometa.fabric.FabricSanPinTarget import FabricSanPinTarget
from ucsmsdk.mometa.fabric.FabricSubGroup import FabricSubGroup
from ucsmsdk.mometa.fabric.FabricVsan import FabricVsan
from ucsmsdk.mometa.fcpool.FcpoolBlock import FcpoolBlock
from ucsmsdk.mometa.fcpool.FcpoolInitiators import FcpoolInitiators
from ucsmsdk.mometa.iqnpool.IqnpoolBlock import IqnpoolBlock
from ucsmsdk.mometa.iqnpool.IqnpoolPool import IqnpoolPool
from ucsmsdk.mometa.storage.StorageConnectionPolicy import StorageConnectionPolicy
from ucsmsdk.mometa.storage.StorageFcTargetEp import StorageFcTargetEp
from ucsmsdk.mometa.storage.StorageIniGroup import StorageIniGroup
from ucsmsdk.mometa.storage.StorageInitiator import StorageInitiator
from ucsmsdk.mometa.storage.StorageVsanRef import StorageVsanRef
from ucsmsdk.mometa.vnic.VnicFc import VnicFc
from ucsmsdk.mometa.vnic.VnicFcGroupDef import VnicFcGroupDef
from ucsmsdk.mometa.vnic.VnicFcIf import VnicFcIf
from ucsmsdk.mometa.vnic.VnicFcNode import VnicFcNode
from ucsmsdk.mometa.vnic.VnicSanConnPolicy import VnicSanConnPolicy
from ucsmsdk.mometa.vnic.VnicSanConnTempl import VnicSanConnTempl
from ucsmsdk.mometa.vnic.VnicVhbaBehPolicy import VnicVhbaBehPolicy

from easyucs.config.object import UcsSystemConfigObject


class UcsSystemFcoeUplinkPort(UcsSystemConfigObject):
    _CONFIG_NAME = "FCoE Uplink Port"

    def __init__(self, parent=None, json_content=None, fabric_fcoe_san_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " + self.slot_id +
                                '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id + ", waiting for a commit")

        parent_mo = "fabric/san/" + self.fabric.upper()
        if self.aggr_id:
            mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                 slot_id=self.slot_id)
            FabricFcoeSanEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.aggr_id,
                            usr_lbl=self.user_label,
                            eth_link_profile_name=self.link_profile, admin_state=self.admin_state)
            self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)
        else:
            mo_fabric_eth_lan_ep = FabricFcoeSanEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                   port_id=self.port_id,
                                                   usr_lbl=self.user_label, eth_link_profile_name=self.link_profile,
                                                   admin_state=self.admin_state, fec=self.fec,
                                                   admin_speed=self.admin_speed)

            self._handle.add_mo(mo=mo_fabric_eth_lan_ep, modify_present=True)

        if commit:
            if self.commit(detail=self.fabric + " " + self.slot_id + '/' + self.port_id) != True:
                return False
        return True


class UcsSystemFcoeStoragePort(UcsSystemConfigObject):
    _CONFIG_NAME = "FCoE Storage Port"

    def __init__(self, parent=None, json_content=None, fabric_fcoe_estc_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " + self.slot_id +
                                '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id + ", waiting for a commit")

        parent_mo = "fabric/fc-estc/" + self.fabric.upper()
        if self.aggr_id:
            mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=parent_mo, aggr_port_id=self.port_id,
                                                 slot_id=self.slot_id)
            FabricFcoeEstcEp(parent_mo_or_dn=mo_fabric_sub_group, slot_id=self.slot_id, port_id=self.aggr_id,
                             usr_lbl=self.user_label, admin_state=self.admin_state)
            self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)
        else:
            mo_fabric_eth_lan_ep = FabricFcoeEstcEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id,
                                                    port_id=self.port_id, usr_lbl=self.user_label,
                                                    admin_state=self.admin_state)

            self._handle.add_mo(mo=mo_fabric_eth_lan_ep, modify_present=True)
        if commit:
            if self.commit() != True:
                return False

        if self.vsan:
            if self.vsan_fabric == "dual":
                parent_mo_vsan = "fabric/fc-estc"
            else:
                parent_mo_vsan = "fabric/fc-estc/" + self.vsan_fabric.upper()
            mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo_vsan, name=self.vsan)
            mo_fabric_fcoe_vsan_port_ep = FabricFcoeVsanPortEp(parent_mo_or_dn=mo_fabric_vsan, port_id=self.port_id,
                                                               switch_id=self.fabric.upper(), slot_id=self.slot_id)
            self._handle.add_mo(mo=mo_fabric_fcoe_vsan_port_ep, modify_present=True)

        if commit:
            if self.commit(detail=self.fabric + " " + self.slot_id + '/' + self.port_id) != True:
                return False
        return True


class UcsSystemSanPortChannel(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Port-Channel"

    def __init__(self, parent=None, json_content=None, fabric_fc_san_pc=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
                                del interface["aggr_id"]
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
                for element in self.interfaces:
                    for value in ["user_label", "link_profile", "admin_state", "aggr_id", "slot_id", "port_id"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

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

        if self.interfaces:
            for interface in self.interfaces:
                if interface["aggr_id"]:
                    mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=mo_fabric_eth_lan_pc,
                                                         aggr_port_id=interface["port_id"],
                                                         slot_id=interface['slot_id'])
                    FabricFcSanPcEp(parent_mo_or_dn=mo_fabric_sub_group, port_id=interface['aggr_id'],
                                    slot_id=interface['slot_id'], admin_state=interface['admin_state'])
                else:
                    FabricFcSanPcEp(parent_mo_or_dn=mo_fabric_eth_lan_pc, slot_id=interface['slot_id'],
                                    port_id=interface['port_id'], usr_lbl=interface['user_label'],
                                    admin_state=interface['admin_state'])

                self._handle.add_mo(mo=mo_fabric_eth_lan_pc, modify_present=True)
                if commit:
                    self.commit(detail=self.pc_id)

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


class UcsSystemFcoePortChannel(UcsSystemConfigObject):
    _CONFIG_NAME = "FCoE Port Channel"

    def __init__(self, parent=None, json_content=None, fabric_fcoe_san_pc=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
                            interface["aggr_id"] = interface_pc_ep.aggr_port_id if int(interface_pc_ep.aggr_port_id) \
                                else None
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

        self.clean_object()

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
                                      slot_id=interface['slot_id'], admin_state=interface['admin_state'])
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


class UcsSystemSanUplinkPort(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Uplink Port"

    def __init__(self, parent=None, json_content=None, fabric_fc_san_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
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
                self.port_id = fabric_fc_san_ep.port_id
                self.user_label = fabric_fc_san_ep.usr_lbl
                self.fill_pattern = fabric_fc_san_ep.fill_pattern
                self.admin_state = fabric_fc_san_ep.admin_state
                self.admin_speed = fabric_fc_san_ep.admin_speed

                if "fabricFcVsanPortEp" in self._config.sdk_objects:
                    vsan = [vsan for vsan in self._config.sdk_objects["fabricFcVsanPortEp"]
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
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " + self.slot_id +
                                '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                                self.slot_id + '/' + self.port_id + ", waiting for a commit")

        parent_mo = "fabric/san/" + self.fabric.upper()

        if not self.is_port_member_of_san_port_channel():
            mo_fabric_fc_san_ep = FabricFcSanEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id, port_id=self.port_id,
                                                fill_pattern=self.fill_pattern, usr_lbl=self.user_label,
                                                admin_state=self.admin_state, admin_speed=self.admin_speed)
            self._handle.add_mo(mo=mo_fabric_fc_san_ep, modify_present=True)

            if self.vsan:
                if self.vsan_fabric is None:
                    parent_mo_vsan = "fabric/san/" + self.fabric.upper()
                elif self.vsan_fabric == "dual":
                    parent_mo_vsan = "fabric/san"
                else:
                    parent_mo_vsan = "fabric/san/" + self.vsan_fabric.upper()
                mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo_vsan, name=self.vsan)
                FabricFcVsanPortEp(parent_mo_or_dn=mo_fabric_vsan, port_id=self.port_id,
                                   switch_id=self.fabric.upper(), slot_id=self.slot_id)
                self._handle.add_mo(mo=mo_fabric_vsan, modify_present=True)

            if commit:
                if self.commit(detail=self.fabric + " " + self.slot_id + '/' + self.port_id) != True:
                    return False
        return True

    def is_port_member_of_san_port_channel(self, fabric="", slot_id="", port_id=""):
        """
        Check if a port is a member of a San port-channel. Used by push_object()

        :param fabric: <class 'str'>: Fabric of the port to check
        :param slot_id: <class 'str'>: Slot id of the port to check
        :param port_id: <class 'str'>: Port id of the port to check
        :return: True if the port is a member of a SAN port-channel, False otherwise
        """

        fabric = self.fabric if not fabric else fabric
        slot_id = self.slot_id if not slot_id else slot_id
        port_id = self.port_id if not port_id else port_id

        # Query on the live system
        ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-fc/port-" + port_id

        interfaces = self._device.query(mode="classid", target="fabricFcSanPcEp",
                                        filter_str="(ep_dn,'" + ep_dn + "',type='eq')")
        if len(interfaces) == 0:
            self.logger(level="debug", message="Port " + slot_id + "/" + port_id + " of fabric " + fabric +
                                               " is not a member of a SAN port-channel")
            return False
        elif len(interfaces) == 1:
            self.logger(level="debug",
                        message="Port " + slot_id + "/" + port_id + " of fabric " + fabric +
                                " is already a member of a SAN port-channel: no action will be committed")
            return True
        else:
            self.logger(level="error",
                        message="Something wrong happened while trying to identify if port " + slot_id + "/"
                                + port_id + " of fabric " + fabric + " is a member of a SAN port-channel")
            return False


class UcsSystemSanStoragePort(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Storage Port"

    def __init__(self, parent=None, json_content=None, fabric_fc_estc_ep=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.slot_id = None
        self.port_id = None
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
                self.port_id = fabric_fc_estc_ep.port_id
                self.user_label = fabric_fc_estc_ep.usr_lbl
                self.fill_pattern = fabric_fc_estc_ep.fill_pattern
                self.admin_state = fabric_fc_estc_ep.admin_state
                self.admin_speed = fabric_fc_estc_ep.admin_speed

                if "fabricFcVsanPortEp" in self._config.sdk_objects:
                    vsan = [vsan for vsan in self._config.sdk_objects["fabricFcVsanPortEp"]
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
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.fabric + " " + self.slot_id +
                                '/' + self.port_id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.fabric + " " +
                        self.slot_id + '/' + self.port_id + ", waiting for a commit")

        parent_mo = "fabric/fc-estc/" + self.fabric.upper()

        if not self.is_port_member_of_san_port_channel():
            mo_fabric_fc_estc_ep = FabricFcEstcEp(parent_mo_or_dn=parent_mo, slot_id=self.slot_id, port_id=self.port_id,
                                                  fill_pattern=self.fill_pattern, usr_lbl=self.user_label,
                                                  admin_state=self.admin_state, admin_speed=self.admin_speed)
            self._handle.add_mo(mo=mo_fabric_fc_estc_ep, modify_present=True)

            if self.vsan:
                if self.vsan_fabric == "dual":
                    parent_mo_vsan = "fabric/fc-estc"
                else:
                    parent_mo_vsan = "fabric/fc-estc/" + self.vsan_fabric.upper()
                mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo_vsan, name=self.vsan)
                FabricFcVsanPortEp(parent_mo_or_dn=mo_fabric_vsan, port_id=self.port_id,
                                   switch_id=self.fabric.upper(), slot_id=self.slot_id)
                self._handle.add_mo(mo=mo_fabric_vsan, modify_present=True)

            if commit:
                if self.commit(detail=self.fabric + " " + self.slot_id + '/' + self.port_id) != True:
                    return False
        return True

    def is_port_member_of_san_port_channel(self, fabric="", slot_id="", port_id=""):
        """
        Check if a port is a member of a San port-channel. Used by push_object()

        :param fabric: <class 'str'>: Fabric of the port to check
        :param slot_id: <class 'str'>: Slot id of the port to check
        :param port_id: <class 'str'>: Port id of the port to check
        :return: True if the port is a member of a SAN port-channel, False otherwise
        """

        fabric = self.fabric if not fabric else fabric
        slot_id = self.slot_id if not slot_id else slot_id
        port_id = self.port_id if not port_id else port_id

        # Query on the live system
        ep_dn = "sys/switch-" + fabric.upper() + "/slot-" + slot_id + "/switch-fc/port-" + port_id

        interfaces = self._device.query(mode="classid", target="fabricFcSanPcEp", filter_str="(ep_dn,'" + ep_dn + "')")

        if len(interfaces) == 0:
            self.logger(level="debug", message="Port " + slot_id + "/" + port_id + " of fabric " + fabric +
                                               " is not a member of a SAN port-channel")
            return False
        elif len(interfaces) == 1:
            self.logger(level="debug",
                        message="Port " + slot_id + "/" + port_id + " of fabric " + fabric +
                                " is already a member of a SAN port-channel: no action will be committed")
            return True
        else:
            self.logger(level="error",
                        message="Something wrong happened while trying to identify if port " + slot_id + "/"
                                + port_id + " of fabric " + fabric + " is a member of a SAN port-channel")
            return False


class UcsSystemVsan(UcsSystemConfigObject):
    _CONFIG_NAME = "VSAN"

    def __init__(self, parent=None, json_content=None, fabric_vsan=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.fcoe_vlan_id = None
        self.id = None
        self.name = None
        self.zoning = None

        if self._config.load_from == "live":
            if fabric_vsan is not None:
                self.fcoe_vlan_id = fabric_vsan.fcoe_vlan
                self.id = fabric_vsan.id
                self.name = fabric_vsan.name
                self.zoning = fabric_vsan.zoning_state

                if fabric_vsan.switch_id not in ["NONE", "dual"]:
                    self.fabric = fabric_vsan.switch_id
                else:
                    self.fabric = "dual"

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.name + ' (' + self.id + ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')' + ", waiting for a commit")

        parent_mo = "fabric/san"
        if self.fabric is not None and self.fabric not in ["NONE", "dual"]:
            parent_mo = "fabric/san/" + self.fabric

        mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo, name=self.name, id=self.id,
                                    zoning_state=self.zoning, fcoe_vlan=self.fcoe_vlan_id)

        self._handle.add_mo(mo=mo_fabric_vsan, modify_present=True)
        if commit:
            if self.commit(detail=self.name + " (" + self.id + ")") != True:
                return False
        return True


class UcsSystemStorageVsan(UcsSystemConfigObject):
    _CONFIG_NAME = "Storage VSAN"

    def __init__(self, parent=None, json_content=None, fabric_vsan=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.fcoe_vlan_id = None
        self.id = None
        self.name = None
        self.zoning = None

        if self._config.load_from == "live":
            if fabric_vsan is not None:
                self.fcoe_vlan_id = fabric_vsan.fcoe_vlan
                self.id = fabric_vsan.id
                self.name = fabric_vsan.name
                self.zoning = fabric_vsan.zoning_state

                if fabric_vsan.switch_id not in ["NONE", "dual"]:
                    self.fabric = fabric_vsan.switch_id
                else:
                    self.fabric = "dual"

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.name + ' (' + self.id + ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')' + ", waiting for a commit")

        parent_mo = "fabric/fc-estc"
        if self.fabric is not None and self.fabric not in ["NONE", "dual"]:
            parent_mo = "fabric/fc-estc/" + self.fabric

        mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo, name=self.name, id=self.id,
                                    zoning_state=self.zoning, fcoe_vlan=self.fcoe_vlan_id)

        self._handle.add_mo(mo=mo_fabric_vsan, modify_present=True)
        if commit:
            if self.commit(detail=self.name + " (" + self.id + ")") != True:
                return False
        return True


class UcsSystemSanPinGroup(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Pin Group"

    def __init__(self, parent=None, json_content=None, fabric_san_pin_group=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.interfaces = []

        if self._config.load_from == "live":
            if fabric_san_pin_group is not None:
                self.descr = fabric_san_pin_group.descr
                self.name = fabric_san_pin_group.name

                if "fabricSanPinTarget" in self._config.sdk_objects:
                    interfaces = [interface for interface in self._config.sdk_objects["fabricSanPinTarget"]
                                  if "san-pin-group-" + self.name + "/" in interface.dn]
                    if interfaces:
                        for interface_ep_pc in interfaces:
                            interface = {}
                            interface["fcoe"] = "no"
                            interface["fabric"] = interface_ep_pc.fabric_id
                            if "fcoesan" in interface_ep_pc.ep_dn:
                                interface["fcoe"] = "yes"

                            if "phys" in interface_ep_pc.ep_dn:
                                # We are facing a physical interface (not a port-channel)
                                interface["aggr_id"] = None
                                interface["slot_id"] = None
                                interface["port_id"] = None
                                if "aggr-port" in interface_ep_pc.ep_dn:
                                    if "fcoesan" in interface_ep_pc.ep_dn:
                                        interface.update({"port_id": interface_ep_pc.ep_dn.split('/')[4].split('-')[5]})
                                        interface.update({"aggr_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[4]})
                                        interface.update({"slot_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[1]})
                                    else:
                                        # We should never end up here, since breakout is only for FCoE ports
                                        # Left code in case breakout is supported for FC ports in the future
                                        interface.update({"port_id": interface_ep_pc.ep_dn.split('/')[4].split('-')[4]})
                                        interface.update({"aggr_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[4]})
                                        interface.update({"slot_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[1]})
                                else:
                                    if "fcoesan" in interface_ep_pc.ep_dn:
                                        interface.update({"port_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[5]})
                                        interface.update({"slot_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[3]})
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
                    for value in ["aggr_id", "slot_id", "port_id", "fabric", "fcoe", "pc_id"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "fabric/san"

        mo_fabric_san_pin_group = FabricSanPinGroup(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        self._handle.add_mo(mo=mo_fabric_san_pin_group, modify_present=True)
        if commit:
            self.commit()

        if self.interfaces:
            for interface in self.interfaces:
                if ("port_id" in interface) & ("pc_id" in interface):
                    self.logger(level="error", message="You must choose between (port_id & slot_id) or pc_id for an " +
                                                       "interface in SAN Pin Group : " + str(self.name))
                else:
                    # Normal behaviour
                    if "pc_id" in interface:
                        if interface['fcoe'] == "yes":
                            interface_dn = parent_mo + "/" + interface['fabric'] + "/fcoesanpc-" + interface['pc_id']
                        else:
                            interface_dn = parent_mo + "/" + interface['fabric'] + "/pc-" + interface['pc_id']
                        FabricSanPinTarget(parent_mo_or_dn=mo_fabric_san_pin_group, ep_dn=interface_dn,
                                           fabric_id=interface['fabric'])
                    elif ("port_id" in interface) & ("slot_id" in interface):
                        if "aggr_id" in interface:
                            if interface['fcoe'] == "yes":
                                interface_dn = parent_mo + "/" + interface['fabric'] + "/slot-" + interface['slot_id']\
                                               + "-aggr-port-" + interface['aggr_id'] + "/phys-fcoesanep-slot-" + \
                                               interface['slot_id'] + "-port-" + interface['port_id']
                            else:
                                interface_dn = parent_mo + "/" + interface['fabric'] + "/slot-" + interface['slot_id']\
                                               + "-aggr-port-" + interface['aggr_id'] + "/phys-slot-" + \
                                               interface['slot_id'] + "-port-" + interface['port_id']
                        else:
                            if interface['fcoe'] == "yes":
                                interface_dn = parent_mo + "/" + interface['fabric'] + "/phys-fcoesanep-slot-" + \
                                               interface['slot_id'] + "-port-" + interface['port_id']
                            else:
                                interface_dn = parent_mo + "/" + interface['fabric'] + "/phys-slot-" + \
                                               interface['slot_id'] + "-port-" + interface['port_id']
                        FabricSanPinTarget(parent_mo_or_dn=mo_fabric_san_pin_group, ep_dn=interface_dn,
                                           fabric_id=interface['fabric'])
                    self._handle.add_mo(mo=mo_fabric_san_pin_group, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemSanUnifiedPort(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Unified Ports"

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
                if self.port_id_end not in ["4", "8"] or self.port_id_start != "1"\
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

            else:
                self.logger("error", "Trying to set Unified Ports on unsupported FI model " + self._device.fi_a_model)
                return False
        else:
            self.logger("error", "Error while checking FI's model")
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


class UcsSystemWwpnPool(UcsSystemConfigObject):
    _CONFIG_NAME = "WWPN Pool"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwpnpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.order = None
        self.wwpn_blocks = []

        if self._config.load_from == "live":
            if wwpnpool_pool is not None:
                self.name = wwpnpool_pool.name
                self.descr = wwpnpool_pool.descr
                self.order = wwpnpool_pool.assignment_order

                if "fcpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["fcpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/wwn-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                self.wwpn_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.wwpn_blocks:
                    for value in ["to", "from", "size"]:
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

        mo_fc_pool_init = FcpoolInitiators(parent_mo_or_dn=parent_mo, descr=self.descr, assignment_order=self.order,
                                           name=self.name, purpose="port-wwn-assignment")
        if self.wwpn_blocks:
            for block in self.wwpn_blocks:
                if block["to"]:
                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=block["to"], r_from=block["from"])
                elif block["size"]:
                    wwpn_pool_to = block["from"]
                    # Convert from hexa to int
                    wwpn_pool_to = int(wwpn_pool_to.replace(":", ""), 16)
                    for i in range(int(block["size"]) - 1):
                        wwpn_pool_to = wwpn_pool_to + 1
                    # Convert to hexa
                    wwpn_pool_to = hex(wwpn_pool_to).split("0x")[1]
                    if len(wwpn_pool_to) != 16:
                        # Add the missing 0 to get 16 letters in the string. We lost some 0 during the conversion
                        wwpn_pool_to = "0" * (16-len(wwpn_pool_to)) + wwpn_pool_to
                    wwpn_pool_to = wwpn_pool_to[0:2] + ":" + wwpn_pool_to[2:4] + ":" + wwpn_pool_to[4:6] + ":" + \
                                   wwpn_pool_to[6:8] + ":" + wwpn_pool_to[8:10] + ":" + wwpn_pool_to[10:12] + ":" + \
                                   wwpn_pool_to[12:14] + ":" + wwpn_pool_to[14:16]
                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=wwpn_pool_to,
                                r_from=block["from"])

        self._handle.add_mo(mo=mo_fc_pool_init, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        

class UcsSystemWwnnPool(UcsSystemConfigObject):
    _CONFIG_NAME = "WWNN Pool"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwnnpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.order = None
        self.wwnn_blocks = []

        if self._config.load_from == "live":
            if wwnnpool_pool is not None:
                self.name = wwnnpool_pool.name
                self.descr = wwnnpool_pool.descr
                self.order = wwnnpool_pool.assignment_order

                if "fcpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["fcpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/wwn-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                self.wwnn_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.wwnn_blocks:
                    for value in ["to", "from", "size"]:
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

        mo_fc_pool_init = FcpoolInitiators(parent_mo_or_dn=parent_mo,
                                           descr=self.descr,
                                           assignment_order=self.order,
                                           name=self.name,
                                           purpose="node-wwn-assignment"
                                           )
        if self.wwnn_blocks:
            for block in self.wwnn_blocks:
                if block["to"]:
                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=block["to"], r_from=block["from"])
                elif block["size"]:
                    wwnn_pool_to = block["from"]
                    # Convert from hexa to int
                    wwnn_pool_to = int(wwnn_pool_to.replace(":", ""), 16)
                    for i in range(int(block["size"]) - 1):
                        wwnn_pool_to = wwnn_pool_to + 1
                    # Convert to hexa
                    wwnn_pool_to = hex(wwnn_pool_to).split("0x")[1]
                    if len(wwnn_pool_to) != 16:
                        # Add the missing 0 to get 16 letters in the string. We lost some 0 during the conversion
                        wwnn_pool_to = "0" * (16-len(wwnn_pool_to)) + wwnn_pool_to
                    wwnn_pool_to = wwnn_pool_to[0:2] + ":" + wwnn_pool_to[2:4] + ":" + wwnn_pool_to[4:6] + ":" + \
                                   wwnn_pool_to[6:8] + ":" + wwnn_pool_to[8:10] + ":" + wwnn_pool_to[10:12] + ":" + \
                                   wwnn_pool_to[12:14] + ":" + wwnn_pool_to[14:16]

                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=wwnn_pool_to,
                                r_from=block["from"])

        self._handle.add_mo(mo=mo_fc_pool_init, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        

class UcsSystemWwxnPool(UcsSystemConfigObject):
    _CONFIG_NAME = "WWxN Pool"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwxnpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.max_ports_per_node = None
        self.order = None
        self.wwxn_blocks = []

        if self._config.load_from == "live":
            if wwxnpool_pool is not None:
                self.name = wwxnpool_pool.name
                self.descr = wwxnpool_pool.descr
                self.max_ports_per_node = wwxnpool_pool.max_ports_per_node.split("upto")[1]
                self.order = wwxnpool_pool.assignment_order

                if "fcpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["fcpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/wwn-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                self.wwxn_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.wwxn_blocks:
                    for value in ["to", "from", "size"]:
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

        max_ports_per_node = None
        if self.max_ports_per_node:
            max_ports_per_node = "upto" + self.max_ports_per_node

        mo_fc_pool_init = FcpoolInitiators(parent_mo_or_dn=parent_mo,
                                           descr=self.descr,
                                           assignment_order=self.order,
                                           name=self.name,
                                           max_ports_per_node=max_ports_per_node,
                                           purpose="node-and-port-wwn-assignment"
                                           )
        if self.wwxn_blocks:
            for block in self.wwxn_blocks:
                if block["to"]:
                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=block["to"], r_from=block["from"])
                elif block["size"]:
                    wwxn_pool_to = block["from"]
                    # Convert from hexa to int
                    wwxn_pool_to = int(wwxn_pool_to.replace(":", ""), 16)
                    for i in range(int(block["size"]) - 1):
                        wwxn_pool_to = wwxn_pool_to + 1
                    # Convert to hexa
                    wwxn_pool_to = hex(wwxn_pool_to).split("0x")[1]
                    if len(wwxn_pool_to) != 16:
                        # Add the missing 0 to get 16 letters in the string. We lost some 0 during the conversion
                        wwxn_pool_to = "0" * (16-len(wwxn_pool_to)) + wwxn_pool_to
                    wwxn_pool_to = wwxn_pool_to[0:2] + ":" + wwxn_pool_to[2:4] + ":" + wwxn_pool_to[4:6] + ":" + \
                                   wwxn_pool_to[6:8] + ":" + wwxn_pool_to[8:10] + ":" + wwxn_pool_to[10:12] + ":" + \
                                   wwxn_pool_to[12:14] + ":" + wwxn_pool_to[14:16]
                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=wwxn_pool_to,
                                r_from=block["from"])

        self._handle.add_mo(mo=mo_fc_pool_init, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemVhbaTemplate(UcsSystemConfigObject):
    _CONFIG_NAME = "vHBA Template"
    _UCS_SDK_OBJECT_NAME = "vnicSanConnTempl"

    def __init__(self, parent=None, json_content=None, vhba_san_conn_templ=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.fabric = None
        self.descr = None
        self.redundancy_type = None
        self.peer_redundancy_template = None
        self.template_type = None
        self.qos_policy = None
        self.pin_group = None
        self.max_data_field_size = None
        self.vsan = None
        self.wwpn_pool = None
        self.stats_threshold_policy = None

        if self._config.load_from == "live":
            if vhba_san_conn_templ is not None:
                self.name = vhba_san_conn_templ.name
                self.fabric = vhba_san_conn_templ.switch_id
                self.descr = vhba_san_conn_templ.descr
                self.redundancy_type = vhba_san_conn_templ.redundancy_pair_type
                self.peer_redundancy_template = vhba_san_conn_templ.peer_redundancy_templ_name
                self.template_type = vhba_san_conn_templ.templ_type
                self.qos_policy = vhba_san_conn_templ.qos_policy_name
                self.pin_group = vhba_san_conn_templ.pin_to_group_name
                self.max_data_field_size = vhba_san_conn_templ.max_data_field_size
                self.wwpn_pool = vhba_san_conn_templ.ident_pool_name
                self.stats_threshold_policy = vhba_san_conn_templ.stats_policy_name

                if "vnicFcIf" in self._config.sdk_objects and not self.vsan:
                    if self._parent._dn:
                        vsans = [vlan for vlan in self._config.sdk_objects["vnicFcIf"] if
                                 self._parent._dn + "/san-conn-templ-" + self.name + "/" in vlan.dn]
                        if len(vsans) == 1:
                            self.vsan = vsans[0].name
                        else:
                            self.logger(level="error",
                                        message="Only one VSAN can be found in a " + self._CONFIG_NAME + " :" + str(
                                            self.name))

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

        redundancy_pair_type = "none" if self.redundancy_type == "no-redundancy" else self.redundancy_type
        mo_vnic_san_conn_temp = VnicSanConnTempl(parent_mo_or_dn=parent_mo, switch_id=self.fabric.upper(),
                                                 name=self.name, descr=self.descr,
                                                 redundancy_pair_type=redundancy_pair_type,
                                                 qos_policy_name=self.qos_policy,
                                                 peer_redundancy_templ_name=self.peer_redundancy_template,
                                                 templ_type=self.template_type, ident_pool_name=self.wwpn_pool,
                                                 max_data_field_size=self.max_data_field_size,
                                                 pin_to_group_name=self.pin_group,
                                                 stats_policy_name=self.stats_threshold_policy)
        if self.vsan:
            VnicFcIf(parent_mo_or_dn=mo_vnic_san_conn_temp, name=self.vsan)

        self._handle.add_mo(mo=mo_vnic_san_conn_temp, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemDefaultVhbaBehavior(UcsSystemConfigObject):
    _CONFIG_NAME = "Default vHBA Behavior"
    _UCS_SDK_OBJECT_NAME = "vnicVhbaBehPolicy"

    def __init__(self, parent=None, json_content=None, vnic_vhba_beh_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.action = None
        self.vhba_template = None

        if self._config.load_from == "live":
            if vnic_vhba_beh_policy is not None:
                self.action = vnic_vhba_beh_policy.action
                self.vhba_template = vnic_vhba_beh_policy.nw_templ_name

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

        mo_vnic_vhba_beh_policy = VnicVhbaBehPolicy(parent_mo_or_dn=parent_mo, action=self.action,
                                                    nw_templ_name=self.vhba_template)

        self._handle.add_mo(mo=mo_vnic_vhba_beh_policy, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemFcZoneProfile(UcsSystemConfigObject):
    _CONFIG_NAME = "FC Zone Profile"

    def __init__(self, parent=None, json_content=None, fabric_fc_zone_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.fc_zoning = None
        self.fc_user_zones = []

        if self._config.load_from == "live":
            if fabric_fc_zone_profile is not None:
                self.name = fabric_fc_zone_profile.name
                self.descr = fabric_fc_zone_profile.descr
                self.fc_zoning = fabric_fc_zone_profile.admin_state

                if "fabricFcUserZone" in self._config.sdk_objects:
                    for user_zone in self._config.sdk_objects["fabricFcUserZone"]:
                        if fabric_fc_zone_profile.dn in user_zone.dn:
                            fc_user_zone = {}
                            fc_user_zone.update({"name": user_zone.name})
                            fc_user_zone.update({"path": user_zone.path})

                            if "storageVsanRef" in self._config.sdk_objects:
                                for vsan_ref in self._config.sdk_objects["storageVsanRef"]:
                                    if user_zone.dn in vsan_ref.dn:
                                        fc_user_zone.update({"vsan": vsan_ref.name})
                            if "fabricFcEndpoint" in self._config.sdk_objects:
                                fc_user_zone.update({"wwpns": []})
                                for fc_endpoint in self._config.sdk_objects["fabricFcEndpoint"]:
                                    if user_zone.dn in fc_endpoint.dn:
                                        fc_user_zone["wwpns"].append(fc_endpoint.wwpn)

                            self.fc_user_zones.append(fc_user_zone)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.fc_user_zones:
                    for value in ["name", "path", "vsan", "wwpns"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name)
                                + ", waiting for a commit")

        parent_mo = "fabric/fc-estc"
        mo_fabric_eth_lan_ep = FabricFcZoneProfile(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr,
                                                   admin_state=self.fc_zoning)
        for fc_user_zone in self.fc_user_zones:
            mo_user_zone = FabricFcUserZone(parent_mo_or_dn=mo_fabric_eth_lan_ep, name=fc_user_zone["name"],
                                            path=fc_user_zone["path"])
            StorageVsanRef(parent_mo_or_dn=mo_user_zone, name=fc_user_zone["vsan"])
            if fc_user_zone["wwpns"]:
                for wwpn in fc_user_zone["wwpns"]:
                    FabricFcEndpoint(parent_mo_or_dn=mo_user_zone, wwpn=wwpn)

        self._handle.add_mo(mo=mo_fabric_eth_lan_ep, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemSanConnectivityPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Connectivity Policy"
    _UCS_SDK_OBJECT_NAME = "vnicSanConnPolicy"

    def __init__(self, parent=None, json_content=None, vnic_san_conn_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.wwnn_pool = None
        self.vhbas = []
        self.vhba_initiator_groups = []

        if self._config.load_from == "live":
            if vnic_san_conn_policy is not None:
                self.name = vnic_san_conn_policy.name
                self.descr = vnic_san_conn_policy.descr

                if "vnicFcNode" in self._parent._config.sdk_objects:
                    for vnic_fc in self._config.sdk_objects["vnicFcNode"]:
                        if self._parent._dn:
                            if self._parent._dn + "/san-conn-pol-" + self.name + '/' in vnic_fc.dn:
                                self.wwnn_pool = vnic_fc.ident_pool_name

                if "vnicFc" in self._parent._config.sdk_objects:
                    for vnic_fc in self._config.sdk_objects["vnicFc"]:
                        if self._parent._dn:
                            if self._parent._dn + "/san-conn-pol-" + self.name + '/' in vnic_fc.dn:
                                vhba = {}
                                vhba.update({"name": vnic_fc.name})
                                vhba.update({"adapter_policy": vnic_fc.adaptor_profile_name})
                                vhba.update({"order": vnic_fc.order})
                                if vnic_fc.nw_templ_name:
                                    vhba.update({"template": vnic_fc.nw_templ_name})
                                else:
                                    vhba.update({"fabric": vnic_fc.switch_id})
                                    vhba.update({"wwpn_pool": vnic_fc.ident_pool_name})
                                    vhba.update({"pin_group": vnic_fc.pin_to_group_name})
                                    vhba.update({"persistent_binding": vnic_fc.pers_bind})
                                    vhba.update({"max_data_field_size": vnic_fc.max_data_field_size})
                                    vhba.update({"qos_policy": vnic_fc.qos_policy_name})
                                    vhba.update({"stats_threshold_policy": vnic_fc.stats_policy_name})

                                    if "vnicFcIf" in self._parent._config.sdk_objects:
                                        for conn_policy in self._config.sdk_objects["vnicFcIf"]:
                                            if self._parent._dn + "/san-conn-pol-" + self.name + '/fc-' + vhba['name'] \
                                                    + '/' in conn_policy.dn:
                                                vhba.update({"vsan": conn_policy.name})

                                self.vhbas.append(vhba)

                if "storageIniGroup" in self._parent._config.sdk_objects:
                    for ini_group in self._config.sdk_objects["storageIniGroup"]:
                        if self._parent._dn:
                            if self._parent._dn + "/san-conn-pol-" + self.name + '/' in ini_group.dn:
                                group = {}
                                group.update({"name": ini_group.name})
                                group.update({"descr": ini_group.descr})
                                if "vnicFcGroupDef" in self._parent._config.sdk_objects:
                                    for fc_group in self._config.sdk_objects["vnicFcGroupDef"]:
                                        if self._parent._dn + "/san-conn-pol-" + self.name + '/grp-' + group['name'] + \
                                                '/fc' in fc_group.dn:
                                            group.update(
                                                {"storage_connection_policy": fc_group.storage_conn_policy_name})
                                if "storageInitiator" in self._parent._config.sdk_objects:
                                    group.update({"initiators": []})
                                    for init in self._config.sdk_objects["storageInitiator"]:
                                        if self._parent._dn + "/san-conn-pol-" + self.name + '/grp-' + group['name'] + \
                                                '/' in init.dn:
                                            group['initiators'].append(init.name)

                                self.vhba_initiator_groups.append(group)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.vhbas:
                    for value in ["adapter_policy", "template", "template", "fabric",
                                  "name", "order", "wwpn_pool", "persistent_binding",
                                  "max_data_field_size", "qos_policy", "vsan", "pin_group", "stats_threshold_policy"]:
                        if value not in element:
                            element[value] = None

                for element in self.vhba_initiator_groups:
                    for value in ["storage_connection_policy", "initiators", "name", "descr"]:
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

        mo_vnic_san_conn_policy = VnicSanConnPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        if self.wwnn_pool:
            VnicFcNode(parent_mo_or_dn=mo_vnic_san_conn_policy, ident_pool_name=self.wwnn_pool)
        self._handle.add_mo(mo=mo_vnic_san_conn_policy, modify_present=True)
        if self.commit(detail=self.name) != True:
            return False

        if self.vhbas:
            for vhba in self.vhbas:
                if vhba['template']:
                    mo_vnic_fc = VnicFc(parent_mo_or_dn=mo_vnic_san_conn_policy,
                                        adaptor_profile_name=vhba['adapter_policy'],
                                        nw_templ_name=vhba['template'], name=vhba['name'],
                                        order=vhba['order'])

                    self._handle.add_mo(mo=mo_vnic_fc, modify_present=True)
                    if commit:
                        if self.commit(detail=vhba['name']) != True:
                            continue
                else:
                    if vhba['fabric']:
                        vhba['fabric'] = vhba['fabric'].upper()
                    mo_vnic_fc = VnicFc(parent_mo_or_dn=mo_vnic_san_conn_policy, name=vhba['name'], order=vhba['order'],
                                        switch_id=vhba['fabric'],
                                        ident_pool_name=vhba['wwpn_pool'], pers_bind=vhba['persistent_binding'],
                                        max_data_field_size=vhba['max_data_field_size'],
                                        adaptor_profile_name=vhba['adapter_policy'], qos_policy_name=vhba['qos_policy'],
                                        pin_to_group_name=vhba["pin_group"],
                                        stats_policy_name=vhba["stats_threshold_policy"])

                    # Adding the vsan
                    if 'vsan' in vhba:
                        mo_vnic_ether_if = VnicFcIf(parent_mo_or_dn=mo_vnic_fc, name=vhba['vsan'])
                        self._handle.add_mo(mo_vnic_ether_if, modify_present=True)

                    self._handle.add_mo(mo=mo_vnic_fc, modify_present=True)
                    if commit:
                        if self.commit(detail=vhba['name']) != True:
                            continue

        if self.vhba_initiator_groups:
            for initiator in self.vhba_initiator_groups:
                mo_ini_group = StorageIniGroup(parent_mo_or_dn=mo_vnic_san_conn_policy,
                                               name=initiator['name'],
                                               descr=initiator['descr'])
                if initiator['storage_connection_policy']:
                    VnicFcGroupDef(parent_mo_or_dn=mo_ini_group,
                                   storage_conn_policy_name=initiator['storage_connection_policy'])
                if initiator['initiators']:
                    for sto_initiator in initiator['initiators']:
                        StorageInitiator(parent_mo_or_dn=mo_ini_group, name=sto_initiator)

                self._handle.add_mo(mo=mo_ini_group, modify_present=True)
                if commit:
                    if self.commit(detail=initiator['name']) != True:
                        return False

        # if commit:
        #   if self.commit(detail=self.name):
        #      return False
        return True


class UcsSystemStorageConnectionPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Storage Connection Policy"
    _UCS_SDK_OBJECT_NAME = "storageConnectionPolicy"

    def __init__(self, parent=None, json_content=None, storage_connection_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.zoning_type = None
        self.fc_target_endpoints = []

        if self._config.load_from == "live":
            if storage_connection_policy is not None:
                self.name = storage_connection_policy.name
                self.descr = storage_connection_policy.descr
                self.zoning_type = storage_connection_policy.zoning_type
                if self.zoning_type == "simt":
                    self.zoning_type = "single_initiator_multiple_targets"
                elif self.zoning_type == "sist":
                    self.zoning_type = "single_initiator_single_target"

                if "storageFcTargetEp" in self._parent._config.sdk_objects:
                    for fc_target in self._config.sdk_objects["storageFcTargetEp"]:
                        if self._parent._dn:
                            if self._parent._dn + "/storage-connpolicy-" + self.name + '/' in fc_target.dn:
                                target = {}
                                target.update({"wwpn": fc_target.targetwwpn})
                                target.update({"descr": fc_target.descr})
                                target.update({"path": fc_target.path})

                                if "storageVsanRef" in self._parent._config.sdk_objects:
                                    for vsan in self._config.sdk_objects["storageVsanRef"]:
                                        if self._parent._dn + "/storage-connpolicy-" + self.name + '/fc-target-ep-' + \
                                                target["wwpn"] + '/' in vsan.dn:
                                            target.update({"vsan": vsan.name})

                                self.fc_target_endpoints.append(target)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.fc_target_endpoints:
                    for value in ["wwpn", "descr", "path", "vsan"]:
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

        zoning_type = self.zoning_type
        if zoning_type == "single_initiator_multiple_targets":
            zoning_type = "simt"
        if zoning_type == "single_initiator_single_target":
            zoning_type = "sist"

        mo_storage_connection_policy = StorageConnectionPolicy(parent_mo_or_dn=parent_mo, name=self.name,
                                                               descr=self.descr, zoning_type=zoning_type)
        self._handle.add_mo(mo=mo_storage_connection_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.fc_target_endpoints:
            for target in self.fc_target_endpoints:
                mo_storage_fc_target_ep = StorageFcTargetEp(parent_mo_or_dn=mo_storage_connection_policy,
                                                            targetwwpn=target["wwpn"], descr=target["descr"],
                                                            path=target["path"])
                # Adding the VSAN
                if 'vsan' in target:
                    StorageVsanRef(parent_mo_or_dn=mo_storage_fc_target_ep, name=target['vsan'])

                self._handle.add_mo(mo=mo_storage_connection_policy, modify_present=True)
                if commit:
                    if self.commit(detail=target['wwpn']) != True:
                        continue

        return True


class UcsSystemIqnSuffixPool(UcsSystemConfigObject):
    _CONFIG_NAME = "IQN Suffix Pool"
    _UCS_SDK_OBJECT_NAME = "iqnpoolPool"

    def __init__(self, parent=None, json_content=None, iqnpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.order = None
        self.prefix = None
        self.iqn_blocks = []

        if self._config.load_from == "live":
            if iqnpool_pool is not None:
                self.name = iqnpool_pool.name
                self.descr = iqnpool_pool.descr
                self.order = iqnpool_pool.assignment_order
                self.prefix = iqnpool_pool.prefix

                if "iqnpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["iqnpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/iqn-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                block.update({"suffix": pool_block.suffix})
                                self.iqn_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.iqn_blocks:
                    for value in ["to", "from", "size", "suffix"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

        if not self.prefix:
            # We need to add an exception after clean_object() because the
            # IQN Suffix pool can have no prefix even if prefix is required (e.g. default)
            self.prefix = ''

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

        mo_iqn_pool_init = IqnpoolPool(parent_mo_or_dn=parent_mo, descr=self.descr, assignment_order=self.order,
                                       name=self.name, prefix=self.prefix)
        if self.iqn_blocks:
            for block in self.iqn_blocks:
                if block["to"]:
                    IqnpoolBlock(parent_mo_or_dn=mo_iqn_pool_init, to=block["to"], r_from=block["from"],
                                 suffix=block["suffix"])
                elif block["size"]:
                    iqn_pool_to = int(block["from"])
                    for i in range(int(block["size"]) - 1):
                        iqn_pool_to = iqn_pool_to + 1
                    iqn_pool_to = str(iqn_pool_to)
                    IqnpoolBlock(parent_mo_or_dn=mo_iqn_pool_init, to=iqn_pool_to, r_from=block["from"],
                                 suffix=block["suffix"])

        self._handle.add_mo(mo=mo_iqn_pool_init, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
