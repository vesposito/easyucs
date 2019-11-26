# coding: utf-8
# !/usr/bin/env python

""" neighbor.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.inventory.object import UcsSystemInventoryObject
from easyucs.draw.ucs.neighbor import UcsSystemDrawNeighbor


class UcsSystemNeighborEntry(UcsSystemInventoryObject):
    def __init__(self, parent=None, neighbor_entry=None):
        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=neighbor_entry)


class UcsSystemLanNeighbor(UcsSystemInventoryObject):
    def __init__(self, parent=None, ucs_system_lan_neighbor_entry=None, ucs_system_fi_eth_port=None, group_number=None):
        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ucs_system_lan_neighbor_entry)

        self.device_type = ucs_system_lan_neighbor_entry.device_type
        self.group_number = group_number
        self.ip_v4_mgmt_address = ucs_system_lan_neighbor_entry.ip_v4_mgmt_address
        self.model = ucs_system_lan_neighbor_entry.model
        self.system_name = ucs_system_lan_neighbor_entry.system_name

        self.peer_ports = [ucs_system_fi_eth_port]

    def _generate_draw(self):
        self._draw = UcsSystemDrawNeighbor(parent=self, parent_draw=None)


class UcsSystemLanNeighborEntry(UcsSystemNeighborEntry):
    def __init__(self, parent=None, network_lan_neighbor_entry=None, network_lldp_neighbor_entry=None):
        self.device_type = "unknown"
        self.is_aci_leaf = False
        self.is_nexus = False
        self.model = None
        self.serial = None
        self.system_desc = None

        if network_lan_neighbor_entry is not None:
            UcsSystemNeighborEntry.__init__(self, parent=parent, neighbor_entry=network_lan_neighbor_entry)
        elif network_lldp_neighbor_entry is not None:
            UcsSystemNeighborEntry.__init__(self, parent=parent, neighbor_entry=network_lldp_neighbor_entry)
        else:
            UcsSystemNeighborEntry.__init__(self, parent=parent, neighbor_entry=None)

        if network_lan_neighbor_entry is not None:
            self.cdp_capabilities = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                       attribute_name="capabilities",
                                                       attribute_secondary_name="cdp_capabilities")
            self.cdp_ip_v4_address = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                        attribute_name="ip_v4_address",
                                                        attribute_secondary_name="cdp_ip_v4_address")
            self.cdp_ip_v4_mgmt_address = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                             attribute_name="ip_v4_mgmt_address",
                                                             attribute_secondary_name="cdp_ip_v4_mgmt_address")
            self.cdp_native_vlan = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                      attribute_name="native_vlan",
                                                      attribute_secondary_name="cdp_native_vlan")
            self.cdp_remote_interface = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                           attribute_name="remote_interface",
                                                           attribute_secondary_name="cdp_remote_interface")
            self.cdp_system_name = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                      attribute_name="system_name",
                                                      attribute_secondary_name="cdp_system_name")
            self.device_id = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                attribute_name="device_id")
            self.model = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry, attribute_name="platform",
                                            attribute_secondary_name="model")
            self.serial = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry, attribute_name="serial_number",
                                             attribute_secondary_name="serial")

        if network_lldp_neighbor_entry is not None:
            self.chassis_id = self.get_attribute(ucs_sdk_object=network_lldp_neighbor_entry,
                                                 attribute_name="chassis_id")
            self.lldp_capabilities = self.get_attribute(ucs_sdk_object=network_lldp_neighbor_entry,
                                                        attribute_name="capabilities",
                                                        attribute_secondary_name="lldp_capabilities")
            self.lldp_enabled_capabilities = self.get_attribute(ucs_sdk_object=network_lldp_neighbor_entry,
                                                                attribute_name="enabled_capabilities",
                                                                attribute_secondary_name="lldp_enabled_capabilities")
            self.lldp_ip_v4_mgmt_address = self.get_attribute(ucs_sdk_object=network_lldp_neighbor_entry,
                                                              attribute_name="ip_v4_mgmt_address",
                                                              attribute_secondary_name="lldp_ip_v4_mgmt_address")
            self.lldp_native_vlan = self.get_attribute(ucs_sdk_object=network_lldp_neighbor_entry,
                                                       attribute_name="native_vlan",
                                                       attribute_secondary_name="lldp_native_vlan")
            self.lldp_system_name = self.get_attribute(ucs_sdk_object=network_lldp_neighbor_entry,
                                                       attribute_name="system_name",
                                                       attribute_secondary_name="lldp_system_name")
            self.lldp_remote_interface = self.get_attribute(ucs_sdk_object=network_lldp_neighbor_entry,
                                                            attribute_name="remote_interface",
                                                            attribute_secondary_name="lldp_remote_interface")
            self.remote_interface_desc = self.get_attribute(ucs_sdk_object=network_lldp_neighbor_entry,
                                                            attribute_name="remote_if_desc",
                                                            attribute_secondary_name="remote_interface_desc")
            self.system_desc = self.get_attribute(ucs_sdk_object=network_lldp_neighbor_entry,
                                                  attribute_name="system_desc")

        if self._inventory.load_from == "live":
            if self.model is not None and self.model != '':
                if any(x in self.model for x in ["N3K-", "N5K-", "N6K-", "N7K-", "N77-", "N9K-"]):
                    self.is_nexus = True
            else:
                self.model = None

            if self.system_desc is not None and self.system_desc != '':
                if "Cisco NX-OS" in self.system_desc:
                    self.is_nexus = True
                if "topology/pod-" in self.system_desc:
                    self.is_aci_leaf = True
                    self.is_nexus = True

            if hasattr(self, 'cdp_capabilities'):
                cdp_capabilities_list = self.cdp_capabilities.split(", ")
                if "Switch" in cdp_capabilities_list:
                    if "Router" in cdp_capabilities_list:
                        if self.is_nexus:
                            if self.is_aci_leaf:
                                self.device_type = "aci_leaf"
                            else:
                                self.device_type = "l3_nexus"
                        else:
                            self.device_type = "l3_switch"
                    else:
                        if self.is_nexus:
                            self.device_type = "l2_nexus"
                        else:
                            self.device_type = "switch"
                elif "Router" in cdp_capabilities_list:
                    self.device_type = "router"

            elif hasattr(self, 'lldp_capabilities'):
                if "," in self.lldp_capabilities:
                    lldp_capabilities_list = self.lldp_capabilities.split(", ")
                else:
                    # Sometimes LLDP capabilities are not separated by a comma but simply appended as a string
                    lldp_capabilities_list = self.lldp_capabilities
                if "B" in lldp_capabilities_list:
                    if "R" in lldp_capabilities_list:
                        if self.is_nexus:
                            if self.is_aci_leaf:
                                self.device_type = "aci_leaf"
                            else:
                                self.device_type = "l3_nexus"
                        else:
                            self.device_type = "l3_switch"
                    else:
                        if self.is_nexus:
                            self.device_type = "l2_nexus"
                        else:
                            self.device_type = "switch"
                elif "D" in lldp_capabilities_list:
                    self.device_type = "router"

            if hasattr(self, 'cdp_ip_v4_mgmt_address'):
                self.ip_v4_mgmt_address = self.cdp_ip_v4_mgmt_address
            elif hasattr(self, 'lldp_ip_v4_mgmt_address'):
                self.ip_v4_mgmt_address = self.lldp_ip_v4_mgmt_address
            else:
                self.ip_v4_mgmt_address = None

            if hasattr(self, 'cdp_native_vlan'):
                self.native_vlan = self.cdp_native_vlan
            elif hasattr(self, 'lldp_native_vlan'):
                self.native_vlan = self.lldp_native_vlan
            else:
                self.native_vlan = None

            if hasattr(self, 'cdp_remote_interface'):
                self.remote_interface = self.cdp_remote_interface
            elif hasattr(self, 'lldp_remote_interface'):
                self.remote_interface = self.lldp_remote_interface
            else:
                self.remote_interface = None

            if hasattr(self, 'cdp_system_name'):
                self.system_name = self.cdp_system_name
            elif hasattr(self, 'lldp_system_name'):
                self.system_name = self.lldp_system_name
            else:
                self.system_name = None

        elif self._inventory.load_from == "file":
            # Since we are loading from file, we don't have 2 distinct set of attributes (for CDP and LLDP), but rather
            # a single JSON content containing all attributes.
            # We need this JSON content to be sent using the first parameter (network_lan_neighbor_entry)
            if network_lan_neighbor_entry is not None:
                self.is_aci_leaf = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                        attribute_name="is_aci_leaf")
                self.chassis_id = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                     attribute_name="chassis_id")
                self.device_type = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                      attribute_name="device_type")
                self.ip_v4_mgmt_address = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                             attribute_name="ip_v4_mgmt_address")
                self.is_nexus = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry, attribute_name="is_nexus")
                self.lldp_capabilities = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                            attribute_name="lldp_capabilities")
                self.lldp_enabled_capabilities = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                                    attribute_name="lldp_enabled_capabilities")
                self.lldp_ip_v4_mgmt_address = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                                  attribute_name="lldp_ip_v4_mgmt_address")
                self.lldp_native_vlan = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                           attribute_name="lldp_native_vlan")
                self.lldp_system_name = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                           attribute_name="lldp_system_name")
                self.lldp_remote_interface = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                                attribute_name="lldp_remote_interface")
                self.native_vlan = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                      attribute_name="native_vlan")
                self.remote_interface = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                           attribute_name="remote_interface")
                self.remote_interface_desc = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                                attribute_name="remote_interface_desc")
                self.system_desc = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                      attribute_name="system_desc")
                self.system_name = self.get_attribute(ucs_sdk_object=network_lan_neighbor_entry,
                                                      attribute_name="system_name")


class UcsSystemSanNeighbor(UcsSystemInventoryObject):
    def __init__(self, parent=None, ucs_system_san_neighbor_entry=None, ucs_system_fi_fc_port=None):
        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ucs_system_san_neighbor_entry)

        self.fabric_mgmt_addr = ucs_system_san_neighbor_entry.fabric_mgmt_addr
        self.fabric_nwwn = ucs_system_san_neighbor_entry.fabric_nwwn

        self.device_type = "fc_switch"

        self.peer_ports = [ucs_system_fi_fc_port]

    def _generate_draw(self):
        self._draw = UcsSystemDrawNeighbor(parent=self, parent_draw=None)


class UcsSystemSanNeighborEntry(UcsSystemNeighborEntry):
    _UCS_SDK_OBJECT_NAME = "networkSanNeighborEntry"

    def __init__(self, parent=None, network_san_neighbor_entry=None):
        UcsSystemNeighborEntry.__init__(self, parent=parent, neighbor_entry=network_san_neighbor_entry)

        self.fabric_mgmt_addr = self.get_attribute(ucs_sdk_object=network_san_neighbor_entry,
                                                   attribute_name="fabric_mgmt_addr")
        self.fabric_nwwn = self.get_attribute(ucs_sdk_object=network_san_neighbor_entry, attribute_name="fabric_nwwn")
        self.fabric_pwwn = self.get_attribute(ucs_sdk_object=network_san_neighbor_entry, attribute_name="fabric_pwwn")
