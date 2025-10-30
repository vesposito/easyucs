# coding: utf-8
# !/usr/bin/env python

""" san.py: Easy UCS Deployment Tool """

from ucsmsdk.mometa.fabric.FabricEthMonDestEp import FabricEthMonDestEp
from ucsmsdk.mometa.fabric.FabricFcEndpoint import FabricFcEndpoint
from ucsmsdk.mometa.fabric.FabricFcMon import FabricFcMon
from ucsmsdk.mometa.fabric.FabricFcMonSrcEp import FabricFcMonSrcEp
from ucsmsdk.mometa.fabric.FabricFcUserZone import FabricFcUserZone
from ucsmsdk.mometa.fabric.FabricFcZoneProfile import FabricFcZoneProfile
from ucsmsdk.mometa.fabric.FabricSanPinGroup import FabricSanPinGroup
from ucsmsdk.mometa.fabric.FabricSanPinTarget import FabricSanPinTarget
from ucsmsdk.mometa.fabric.FabricSubGroup import FabricSubGroup
from ucsmsdk.mometa.fabric.FabricVsan import FabricVsan
from ucsmsdk.mometa.fcpool.FcpoolBlock import FcpoolBlock
from ucsmsdk.mometa.fcpool.FcpoolInitiators import FcpoolInitiators
from ucsmsdk.mometa.fcpool.FcpoolOui import FcpoolOui
from ucsmsdk.mometa.fcpool.FcpoolOuis import FcpoolOuis
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

from config.ucs.object import UcsSystemConfigObject
from config.ucs.ucsm.lan import UcsSystemQosPolicy
from config.ucs.ucsm.servers import UcsSystemFibreChannelAdapterPolicy, UcsSystemThresholdPolicy


class UcsSystemVsan(UcsSystemConfigObject):
    _CONFIG_NAME = "VSAN"
    _CONFIG_SECTION_NAME = "vsans"
    _UCS_SDK_OBJECT_NAME = "fabricVsan"

    def __init__(self, parent=None, json_content=None, fabric_vsan=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_vsan)
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
    _CONFIG_SECTION_NAME = "storage_vsans"
    _UCS_SDK_OBJECT_NAME = "fabricVsan"

    def __init__(self, parent=None, json_content=None, fabric_vsan=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_vsan)
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
    _CONFIG_SECTION_NAME = "san_pin_groups"
    _UCS_SDK_OBJECT_NAME = "fabricSanPinGroup"

    def __init__(self, parent=None, json_content=None, fabric_san_pin_group=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_san_pin_group)
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
                                        interface.update({"port_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[4]})
                                        interface.update({"aggr_id": interface_ep_pc.ep_dn.split('/')[4].split('-')[5]})
                                        interface.update({"slot_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[1]})
                                    else:
                                        # We should never end up here, since breakout is only for FCoE ports
                                        # Left code in case breakout is supported for FC ports in the future
                                        interface.update({"port_id": interface_ep_pc.ep_dn.split('/')[3].split('-')[4]})
                                        interface.update({"aggr_id": interface_ep_pc.ep_dn.split('/')[4].split('-')[4]})
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

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.interfaces:
            for value in ["aggr_id", "slot_id", "port_id", "fabric", "fcoe", "pc_id"]:
                if value not in element:
                    element[value] = None

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
                if (interface["port_id"] is not None) & (interface["pc_id"] is not None):
                    self.logger(level="error", message="You must choose between (port_id & slot_id) or pc_id for an " +
                                                       "interface in SAN Pin Group : " + str(self.name))
                else:
                    # Normal behaviour
                    if interface["pc_id"] is not None:
                        if interface['fcoe'] == "yes":
                            interface_dn = parent_mo + "/" + interface['fabric'] + "/fcoesanpc-" + interface['pc_id']
                        else:
                            interface_dn = parent_mo + "/" + interface['fabric'] + "/pc-" + interface['pc_id']
                        FabricSanPinTarget(parent_mo_or_dn=mo_fabric_san_pin_group, ep_dn=interface_dn,
                                           fabric_id=interface['fabric'])
                    elif (interface["port_id"] is not None) & (interface["slot_id"] is not None):
                        if interface["aggr_id"] is not None:
                            if interface['fcoe'] == "yes":
                                interface_dn = parent_mo + "/" + interface['fabric'] + "/slot-" + interface['slot_id']\
                                    + "-aggr-port-" + interface['port_id'] + "/phys-fcoesanep-slot-" + \
                                    interface['slot_id'] + "-port-" + interface['aggr_id']
                            else:
                                interface_dn = parent_mo + "/" + interface['fabric'] + "/slot-" + interface['slot_id']\
                                    + "-aggr-port-" + interface['port_id'] + "/phys-slot-" + \
                                    interface['slot_id'] + "-port-" + interface['aggr_id']
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


class UcsSystemWwpnPool(UcsSystemConfigObject):
    _CONFIG_NAME = "WWPN Pool"
    _CONFIG_SECTION_NAME = "wwpn_pools"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwpnpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=wwpnpool_pool)
        self.descr = None
        self.name = None
        self.order = None
        self.wwpn_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if wwpnpool_pool is not None:
                self.name = wwpnpool_pool.name
                self.descr = wwpnpool_pool.descr
                self.order = wwpnpool_pool.assignment_order
                self.operational_state = {
                    "size": wwpnpool_pool.size,
                    "assigned": wwpnpool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.wwpn_blocks:
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
    _CONFIG_SECTION_NAME = "wwnn_pools"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwnnpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=wwnnpool_pool)
        self.descr = None
        self.name = None
        self.order = None
        self.wwnn_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if wwnnpool_pool is not None:
                self.name = wwnnpool_pool.name
                self.descr = wwnnpool_pool.descr
                self.order = wwnnpool_pool.assignment_order
                self.operational_state = {
                    "size": wwnnpool_pool.size,
                    "assigned": wwnnpool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)
        for element in self.wwnn_blocks:
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
    _CONFIG_SECTION_NAME = "wwxn_pools"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwxnpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=wwxnpool_pool)
        self.descr = None
        self.name = None
        self.max_ports_per_node = None
        self.order = None
        self.wwxn_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if wwxnpool_pool is not None:
                self.name = wwxnpool_pool.name
                self.descr = wwxnpool_pool.descr
                self.max_ports_per_node = wwxnpool_pool.max_ports_per_node.split("upto")[1]
                self.order = wwxnpool_pool.assignment_order
                self.operational_state = {
                    "size": wwxnpool_pool.size,
                    "assigned": wwxnpool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.wwxn_blocks:
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


class UcsSystemOuiPool(UcsSystemConfigObject):
    _CONFIG_NAME = "OUI Pools"
    _CONFIG_SECTION_NAME = "oui_pools"
    _UCS_SDK_OBJECT_NAME = "fcpoolOuis"

    def __init__(self, parent=None, json_content=None, fcpool_ouis=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fcpool_ouis)
        self.name = None
        self.fabric = None
        self.ouis = []
        if self._config.load_from == "live":
            self.name = fcpool_ouis.name
            if "fcpoolOui" in self._config.sdk_objects:
                for fcpool_oui in self._config.sdk_objects["fcpoolOui"]:
                    if (fcpool_oui.dn.startswith("sys/switch-" + fcpool_oui.switch_id + "/oui-pool-" + fcpool_ouis.name)
                            and fcpool_ouis.dn.startswith("sys/switch-" + fcpool_oui.switch_id)):
                        self.fabric = fcpool_oui.switch_id
                        self.ouis.append(fcpool_oui.oui)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: ")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration, waiting for a commit")

        fcpool_ouis_parent_mo = f"sys/switch-{self.fabric}"
        mo_fcpool_ouis = FcpoolOuis(parent_mo_or_dn=fcpool_ouis_parent_mo, name=self.name)

        self._handle.add_mo(mo=mo_fcpool_ouis, modify_present=True)

        for oui in self.ouis:
            mo_fcpool_oui = FcpoolOui(parent_mo_or_dn=fcpool_ouis_parent_mo + "/oui-pool-" + self.name, oui=oui)
            self._handle.add_mo(mo=mo_fcpool_oui, modify_present=True)

        if commit:
            if self.commit(detail=f"{self.name}-{self.fabric}") != True:
                return False
        return True


class UcsSystemDefaultVhbaBehavior(UcsSystemConfigObject):
    _CONFIG_NAME = "Default vHBA Behavior"
    _CONFIG_SECTION_NAME = "default_vhba_behavior"
    _UCS_SDK_OBJECT_NAME = "vnicVhbaBehPolicy"

    def __init__(self, parent=None, json_content=None, vnic_vhba_beh_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_vhba_beh_policy)
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
    _CONFIG_SECTION_NAME = "fc_zone_profiles"

    def __init__(self, parent=None, json_content=None, fabric_fc_zone_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_fc_zone_profile)
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

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.fc_user_zones:
            for value in ["name", "path", "vsan", "wwpns"]:
                if value not in element:
                    element[value] = None

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


class UcsSystemSanTrafficMonitoringSession(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Traffic Monitoring Session"
    _CONFIG_SECTION_NAME = "san_traffic_monitoring_sessions"
    _UCS_SDK_OBJECT_NAME = "fabricFcMon"

    def __init__(self, parent=None, json_content=None, fabric_fc_mon=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_fc_mon)
        self.admin_state = None
        self.admin_speed = None
        self.destination = []
        self.fabric = None
        self.name = None
        self.sources = []
        self.span_control_packets = None
        if self._config.load_from == "live":
            if fabric_fc_mon is not None:
                self.admin_state = fabric_fc_mon.admin_state
                self.fabric = fabric_fc_mon.id
                self.name = fabric_fc_mon.name
                self.span_control_packets = fabric_fc_mon.span_ctrl_pkts
                directions = {}
                uplink_port_type_list = ["uplink-port", "storage"]
                port_channel_type_list = ["port-channel"]

                if "fabricEthMonDestEp" in self._config.sdk_objects:
                    # Based on fabric ID and session name, fetching the destination details of a monitoring session
                    for fabric_eth_mon_dest_ep in self._config.sdk_objects["fabricEthMonDestEp"]:
                        fabric = fabric_eth_mon_dest_ep.switch_id
                        name = fabric_eth_mon_dest_ep.dn.split("/")[3].replace("fc-mon-", "")
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

                # To get direction field of all sources in a monitoring session
                if "fabricEthMonSrcEp" in self._config.sdk_objects:
                    for src_ep_obj in self._config.sdk_objects["fabricEthMonSrcEp"]:
                        directions[src_ep_obj.dn] = src_ep_obj.direction
                if "fabricFcMonSrcEp" in self._config.sdk_objects:
                    for src_ep_obj in self._config.sdk_objects["fabricFcMonSrcEp"]:
                        directions[src_ep_obj.dn] = src_ep_obj.direction

                # Fetching details of all types of sources in monitoring session
                if "fabricFcMonSrcRef" in self._config.sdk_objects:
                    # Based on the source type fetching all the required fields
                    for fabric_fc_mon_src_ref in self._config.sdk_objects["fabricFcMonSrcRef"]:
                        source_type = fabric_fc_mon_src_ref.source_type
                        source_dn = fabric_fc_mon_src_ref.source_dn.split("/")
                        monitoring_session_name = source_dn[-1].replace("mon-src-", "")
                        fabric = fabric_fc_mon_src_ref.dn.split("/")[2]
                        if self.fabric == fabric and self.name == monitoring_session_name:
                            source_dict = {"source_type": source_type}
                            if fabric_fc_mon_src_ref.source_dn in directions:
                                source_dict["direction"] = directions[fabric_fc_mon_src_ref.source_dn]
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
                            elif source_type == "vsan":
                                if fabric_fc_mon_src_ref.source_dn.startswith("fabric/san/"):
                                    source_dict["vsan"] = source_dn[-2].split("net-")[-1]
                                elif fabric_fc_mon_src_ref.source_dn.startswith("fabric/fc-estc/"):
                                    source_dict["storage_vsan"] = source_dn[-2].split("net-")[-1]
                                if fabric_fc_mon_src_ref.source_dn.startswith("fabric/san/" + self.fabric):
                                    source_dict["fabric"] = self.fabric
                                elif fabric_fc_mon_src_ref.source_dn.startswith("fabric/fc-estc/" + self.fabric):
                                    source_dict["fabric"] = self.fabric
                                else:
                                    source_dict["fabric"] = "dual"
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
                          "slot_id", "source_type", "storage_vsan", "vhba", "vsan"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "fabric/sanmon/" + self.fabric
        mo_fabric_fc_mon = FabricFcMon(name=self.name, parent_mo_or_dn=parent_mo, admin_state=self.admin_state,
                                       span_ctrl_pkts=self.span_control_packets, id=self.fabric)
        self._handle.add_mo(mo=mo_fabric_fc_mon, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.destination:
            if self.destination[0].get("aggr_id"):
                mo_fabric_sub_group = FabricSubGroup(parent_mo_or_dn=mo_fabric_fc_mon,
                                                     slot_id=self.destination[0].get("slot_id"),
                                                     aggr_port_id=self.destination[0].get("port_id"))
                FabricEthMonDestEp(parent_mo_or_dn=mo_fabric_sub_group, admin_speed=self.admin_speed,
                                   slot_id=self.destination[0].get("slot_id"),
                                   port_id=self.destination[0].get("aggr_id"))
                dst_descr = self.destination[0].get("slot_id") + "/" + self.destination[0].get("port_id") + "/" + \
                            self.destination[0].get("aggr_id")
                self._handle.add_mo(mo=mo_fabric_sub_group, modify_present=True)
            else:
                mo_fabric_eth_mon_dest_ep = FabricEthMonDestEp(parent_mo_or_dn=mo_fabric_fc_mon,
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
                    parent_dn = ""
                    src_descr = ""
                    if source["source_type"] == "uplink-port":
                        # For SAN Uplink Port source type
                        parent_dn += "fabric/san/" + self.fabric
                        if source["aggr_id"]:
                            parent_dn += ("/slot-" + source["slot_id"] + "-aggr-port-" + source["port_id"] +
                                          "/phys-slot-" + source["slot_id"] + "-port-" + source["aggr_id"])
                            src_descr = source["slot_id"] + "/" + source["port_id"] + "/" + source["aggr_id"]
                        else:
                            parent_dn += "/phys-slot-" + source["slot_id"] + "-port-" + source["port_id"]
                            src_descr = source["slot_id"] + "/" + source["port_id"]
                    elif source["source_type"] == "port-channel":
                        # For SAN Port-Channel source type
                        parent_dn += "fabric/san/" + self.fabric + "/pc-" + source["pc_id"]
                        src_descr = source["pc_id"]
                    elif source["source_type"] == "storage":
                        # For FC Storage Port source type
                        parent_dn += "fabric/fc-estc/" + self.fabric
                        if source["aggr_id"]:
                            parent_dn += ("/slot-" + source["slot_id"] + "-aggr-port-" + source["port_id"] +
                                          "/phys-fc-slot-" + source["slot_id"] + "-port-" + source["aggr_id"])
                            src_descr = source["slot_id"] + "/" + source["port_id"] + "/" + source["aggr_id"]
                        else:
                            parent_dn += "/phys-fc-slot-" + source["slot_id"] + "-port-" + source["port_id"]
                            src_descr = source["slot_id"] + "/" + source["port_id"]
                    elif source["source_type"] == "vsan":
                        # For VSAN source type
                        if source["vsan"]:
                            # Regular VSAN
                            if source["fabric"] == "dual":
                                parent_dn += "fabric/san/net-" + source["vsan"]
                                src_descr = source["vsan"]
                            else:
                                parent_dn += "fabric/san/" + source["fabric"] + "/net-" + source["vsan"]
                                src_descr = source["fabric"] + "/" + source["vsan"]
                        elif source["storage_vsan"]:
                            # Storage VSAN
                            if source["fabric"] == "dual":
                                parent_dn += "fabric/fc-estc/net-" + source["storage_vsan"]
                                src_descr = source["storage_vsan"] + " (storage)"
                            else:
                                parent_dn += "fabric/fc-estc/" + source["fabric"] + "/net-" + source["storage_vsan"]
                                src_descr = source["fabric"] + "/" + source["storage_vsan"] + " (storage)"
                    elif source["source_type"] == "vhba":
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


class UcsSystemStorageConnectionPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Storage Connection Policy"
    _CONFIG_SECTION_NAME = "storage_connection_policies"
    _UCS_SDK_OBJECT_NAME = "storageConnectionPolicy"

    def __init__(self, parent=None, json_content=None, storage_connection_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=storage_connection_policy)
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
                                            break

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

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.fc_target_endpoints:
            for value in ["wwpn", "descr", "path", "vsan"]:
                if value not in element:
                    element[value] = None

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


class UcsSystemIqnPool(UcsSystemConfigObject):
    _CONFIG_NAME = "IQN Pool"
    _CONFIG_SECTION_NAME = "iqn_pools"
    _UCS_SDK_OBJECT_NAME = "iqnpoolPool"

    def __init__(self, parent=None, json_content=None, iqnpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=iqnpool_pool)
        self.descr = None
        self.name = None
        self.order = None
        self.prefix = None
        self.iqn_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if iqnpool_pool is not None:
                self.name = iqnpool_pool.name
                self.descr = iqnpool_pool.descr
                self.order = iqnpool_pool.assignment_order
                self.prefix = iqnpool_pool.prefix
                self.operational_state = {
                    "size": iqnpool_pool.size,
                    "assigned": iqnpool_pool.assigned
                }

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

        self.clean_object()

        if not self.prefix:
            # We need to add an exception after clean_object() because the
            # IQN Pool can have no prefix even if prefix is required (e.g. default)
            self.prefix = ''

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)
        for element in self.iqn_blocks:
            for value in ["to", "from", "size", "suffix"]:
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


class UcsSystemVhbaTemplate(UcsSystemConfigObject):
    _CONFIG_NAME = "vHBA Template"
    _CONFIG_SECTION_NAME = "vhba_templates"
    _UCS_SDK_OBJECT_NAME = "vnicSanConnTempl"
    _POLICY_MAPPING_TABLE = {
        "adapter_policy": UcsSystemFibreChannelAdapterPolicy,
        "pin_group": UcsSystemSanPinGroup,
        "qos_policy": UcsSystemQosPolicy,
        "stats_threshold_policy": UcsSystemThresholdPolicy,
        "wwpn_pool": UcsSystemWwpnPool
    }

    def __init__(self, parent=None, json_content=None, vhba_san_conn_templ=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vhba_san_conn_templ)
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
        self.operational_state = {}

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
                        elif len(vsans) == 0:
                            self.logger(level="error",
                                        message=f"Missing at least one VSAN in {self._CONFIG_NAME}: {str(self.name)}")
                        else:
                            self.logger(level="error",
                                        message=f"More than one VSAN can be found in {self._CONFIG_NAME}: "
                                                f"{str(self.name)}")

                # Fetching the operational state of the referenced policies
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vhba_san_conn_templ.oper_peer_redundancy_templ_name,
                        separator="/san-conn-templ-",
                        policy_name="peer_redundancy_template"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vhba_san_conn_templ.oper_qos_policy_name,
                        separator="/ep-qos-",
                        policy_name="qos_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vhba_san_conn_templ.oper_stats_policy_name,
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

        for policy in ["peer_redundancy_template", "qos_policy", "stats_threshold_policy"]:
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


class UcsSystemSanConnectivityPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "SAN Connectivity Policy"
    _CONFIG_SECTION_NAME = "san_connectivity_policies"
    _UCS_SDK_OBJECT_NAME = "vnicSanConnPolicy"
    _POLICY_MAPPING_TABLE = {
        "wwnn_pool": UcsSystemWwnnPool,
        "vhbas": [
            {
                "adapter_policy": UcsSystemFibreChannelAdapterPolicy,
                "pin_group": UcsSystemSanPinGroup,
                "qos_policy": UcsSystemQosPolicy,
                "stats_threshold_policy": UcsSystemThresholdPolicy,
                "vhba_template": UcsSystemVhbaTemplate,
                "wwpn_pool": UcsSystemWwpnPool
            }
        ]
    }

    def __init__(self, parent=None, json_content=None, vnic_san_conn_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_san_conn_policy)
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
                                break

                if "vnicFc" in self._parent._config.sdk_objects:
                    for vnic_fc in self._config.sdk_objects["vnicFc"]:
                        if self._parent._dn:
                            if self._parent._dn + "/san-conn-pol-" + self.name + '/' in vnic_fc.dn:
                                vhba = {"_object_type": "vhbas"}
                                vhba.update({"name": vnic_fc.name})
                                vhba.update({"adapter_policy": vnic_fc.adaptor_profile_name})
                                vhba.update({"order": vnic_fc.order})
                                if vnic_fc.nw_templ_name:
                                    vhba.update({"vhba_template": vnic_fc.nw_templ_name})
                                else:
                                    vhba.update({"fabric": vnic_fc.switch_id})
                                    vhba.update({"wwpn_pool": vnic_fc.ident_pool_name})
                                    vhba.update({"pin_group": vnic_fc.pin_to_group_name})
                                    vhba.update({"persistent_binding": vnic_fc.pers_bind})
                                    vhba.update({"max_data_field_size": vnic_fc.max_data_field_size})
                                    vhba.update({"qos_policy": vnic_fc.qos_policy_name})
                                    vhba.update({"stats_threshold_policy": vnic_fc.stats_policy_name})

                                    if vhba["persistent_binding"] == "1":
                                        vhba["persistent_binding"] = "enabled"

                                    if "vnicFcIf" in self._parent._config.sdk_objects:
                                        for conn_policy in self._config.sdk_objects["vnicFcIf"]:
                                            if self._parent._dn + "/san-conn-pol-" + self.name + '/fc-' + vhba['name'] \
                                                    + '/' in conn_policy.dn:
                                                vhba.update({"vsan": conn_policy.name})
                                                break

                                # Fetching the operational state of the referenced policies
                                oper_state = {}
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_fc.oper_adaptor_profile_name,
                                        separator="/fc-profile-",
                                        policy_name="adapter_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_fc.oper_pin_to_group_name,
                                        separator="/san-pin-group-",
                                        policy_name="pin_group"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_fc.oper_qos_policy_name,
                                        separator="/ep-qos-",
                                        policy_name="qos_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_fc.oper_stats_policy_name,
                                        separator="/thr-policy-",
                                        policy_name="stats_threshold_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_fc.oper_nw_templ_name,
                                        separator="/san-conn-templ-",
                                        policy_name="vhba_template"
                                    )
                                )

                                vhba['operational_state'] = oper_state

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
                                            break
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

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.vhbas:
            for value in ["adapter_policy", "vhba_template", "fabric", "name", "order", "wwpn_pool",
                          "persistent_binding", "max_data_field_size", "qos_policy", "vsan", "pin_group",
                          "stats_threshold_policy", "operational_state"]:
                if value not in element:
                    element[value] = None

            if element["operational_state"]:
                for policy in ["adapter_policy", "pin_group", "qos_policy", "stats_threshold_policy",
                               "vhba_template", "wwpn_pool"]:
                    if policy not in element["operational_state"]:
                        element["operational_state"][policy] = None
                    elif element["operational_state"][policy]:
                        for value in ["name", "org"]:
                            if value not in element["operational_state"][policy]:
                                element["operational_state"][policy][value] = None

            # Flagging this as a vHBA
            element["_object_type"] = "vhbas"

        for element in self.vhba_initiator_groups:
            for value in ["storage_connection_policy", "initiators", "name", "descr"]:
                if value not in element:
                    element[value] = None

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
                if vhba['vhba_template']:
                    mo_vnic_fc = VnicFc(parent_mo_or_dn=mo_vnic_san_conn_policy,
                                        adaptor_profile_name=vhba['adapter_policy'],
                                        nw_templ_name=vhba['vhba_template'], name=vhba['name'],
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