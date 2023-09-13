# coding: utf-8
# !/usr/bin/env python

""" mgmt.py: Easy UCS Deployment Tool """

from inventory.ucs.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsMgmtInterface(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "mgmtIf"

    def __init__(self, parent=None, mgmt_if=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=mgmt_if)

        self.ipv4_default_gw = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="ext_gw",
                                                  attribute_secondary_name="ipv4_default_gw")
        self.id = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="id")
        self.ipv4 = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="ext_ip", attribute_secondary_name="ipv4")
        self.mac = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="mac")
        self.mask = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="ext_mask",
                                       attribute_secondary_name="mask")

    def _get_peer_port(self):
        if hasattr(self, "_peer_dn"):
            if self._peer_dn:
                peer_dn = self._peer_dn.split('/')

                if peer_dn[1].startswith("switch-"):
                    # Retrieve switch port details
                    if peer_dn[4].startswith("aggr"):
                        peer = {
                            "switch": peer_dn[1].split('-')[-1],
                            "slot": int(peer_dn[2].split('-')[-1]),
                            "aggr_port": int(peer_dn[4].split('-')[-1]),
                            "port": int(peer_dn[5].split('-')[-1])
                        }
                    else:
                        peer = {
                            "switch": peer_dn[1].split('-')[-1],
                            "slot": int(peer_dn[2].split('-')[-1]),
                            "aggr_port": None,
                            "port": int(peer_dn[4].split('-')[-1])
                        }
                    return peer

                elif peer_dn[1].startswith("chassis-"):
                    # Retrieve chassis port details
                    if peer_dn[3] == "shared-io-module":
                        peer = {
                            "chassis": int(peer_dn[1].split('-')[-1]),
                            "slot": int(peer_dn[2].split('-')[-1]),
                            "aggr_port": None,
                            "port": int(peer_dn[5].split('-')[-1])
                        }
                    elif peer_dn[4].startswith("aggr"):
                        peer = {
                            "chassis": int(peer_dn[1].split('-')[-1]),
                            "slot": int(peer_dn[2].split('-')[-1]),
                            "aggr_port": int(peer_dn[4].split('-')[-1]),
                            "port": int(peer_dn[5].split('-')[-1])
                        }
                    else:
                        peer = {
                            "chassis": int(peer_dn[1].split('-')[-1]),
                            "slot": int(peer_dn[2].split('-')[-1]),
                            "aggr_port": None,
                            "port": int(peer_dn[4].split('-')[-1])
                        }
                    return peer

                elif peer_dn[1].startswith("rack-unit-") and peer_dn[2] != "mgmt":  # TODO Simple version -> to complete
                    peer = {
                        "rack": int(peer_dn[1].split('-')[-1]),
                        "slot": int(peer_dn[2].split('-')[-1]),
                        "aggr_port": None,
                        "port": int(peer_dn[3].split('-')[-1])
                    }
                    return peer

                elif peer_dn[1].startswith("fex"):  # TODO Simple version -> to complete
                    # Retrieve FEX port details
                    peer = {
                        "fex": int(peer_dn[1].split('-')[-1]),
                        "slot": int(peer_dn[2].split('-')[-1]),
                        "aggr_port": None,
                        "port": int(peer_dn[4].split('-')[-1])
                    }
                    return peer
        return None


class UcsSystemMgmtInterface(UcsMgmtInterface, UcsSystemInventoryObject):
    def __init__(self, parent=None, mgmt_if=None):
        UcsMgmtInterface.__init__(self, parent=parent, mgmt_if=mgmt_if)

        self.internal_ip = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="ip",
                                              attribute_secondary_name="internal_ip")
        self.internal_mask = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="mask",
                                                attribute_secondary_name="internal_mask")
        self.switch_id = None
        if self._device.metadata.device_type not in ["ucsc"]:
            # The following attribute is not supported in UCS Central
            self.switch_id = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="switch_id")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=mgmt_if)

        self.ipv4_mode = None
        self.ipv4_pool_name = None
        self.peer = None
        self.type = "outband"
        if self._inventory.load_from == "live":
            self._get_outband_mgmt_ip_mode()
            self._peer_dn = None
            if self._device.metadata.device_type not in ["ucsc"]:
                # The following attribute is not supported in UCS Central
                self._peer_dn = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="peer_dn")
            self.peer = self._get_peer_port()
        elif self._inventory.load_from == "file":
            if "peer" in mgmt_if:
                self.peer = mgmt_if["peer"]
            if "ipv4_mode" in mgmt_if:
                self.ipv4_mode = mgmt_if["ipv4_mode"]
            if "ipv4_pool_name" in mgmt_if:
                self.ipv4_pool_name = mgmt_if["ipv4_pool_name"]

    def _get_outband_mgmt_ip_mode(self):
        # We check if we already have fetched the list of vnicIpV4StaticAddr objects
        if self._inventory.sdk_objects["vnicIpV4StaticAddr"] is not None:
            vnic_ipv4_static_addr_list = [vnic_ipv4_static_addr for vnic_ipv4_static_addr in
                                          self._inventory.sdk_objects["vnicIpV4StaticAddr"]
                                          if self._parent.dn + "/mgmt/ipv4-static-addr" in vnic_ipv4_static_addr.dn]

            # We fetch the vnicIpV4StaticAddr details if there is one and only one object in the list
            if len(vnic_ipv4_static_addr_list) == 1:
                self.ipv4_mode = "static"
                return True

        # We check if we already have fetched the list of vnicIpV4PooledAddr objects
        if self._inventory.sdk_objects["vnicIpV4PooledAddr"] is not None:
            vnic_ipv4_pooled_addr_list = [vnic_ipv4_pooled_addr for vnic_ipv4_pooled_addr in
                                          self._inventory.sdk_objects["vnicIpV4PooledAddr"]
                                          if self._parent.dn + "/mgmt/ipv4-pooled-addr" in vnic_ipv4_pooled_addr.dn]

            # We fetch the vnicIpV4PooledAddr details if there is one and only one object in the list
            if len(vnic_ipv4_pooled_addr_list) == 1:
                self.ipv4_mode = "pool"
                self.ipv4_pool_name = vnic_ipv4_pooled_addr_list[0].name
                return True

        return False


class UcsSystemMgmtInterfaceInband(UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "mgmtInterface"

    def __init__(self, parent=None, mgmt_interface=None):
        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=mgmt_interface)
        self.ipv4_mode = self.get_attribute(ucs_sdk_object=mgmt_interface, attribute_name="ip_v4_state",
                                            attribute_secondary_name="ipv4_mode")
        self.ipv6_mode = self.get_attribute(ucs_sdk_object=mgmt_interface, attribute_name="ip_v6_state",
                                            attribute_secondary_name="ipv6_mode")

        self.id = None
        self.ipv4 = None
        self.ipv6 = None
        self.ipv4_default_gw = None
        self.ipv6_default_gw = None
        self.ipv4_pool_name = None
        self.ipv6_pool_name = None
        self.mask = None
        self.network_name = None
        self.network_vlan_id = None
        self.peer = None
        self.prefix = None
        self.type = "inband"
        if self._inventory.load_from == "live":
            self._get_inband_mgmt_vlan()
            self._get_inband_mgmt_ip_addr()
        elif self._inventory.load_from == "file":
            for attribute in ["ipv4", "ipv6", "ipv4_default_gw", "ipv6_default_gw", "ipv4_pool_name", "ipv6_pool_name",
                              "mask", "network_name", "network_vlan_id", "prefix"]:
                setattr(self, attribute, None)
                if attribute in mgmt_interface:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=mgmt_interface,
                                                                attribute_name=attribute))

    def _get_inband_mgmt_ip_addr(self):
        found = False
        # We check if we already have fetched the list of vnicIpV4StaticAddr objects
        if self._inventory.sdk_objects["vnicIpV4StaticAddr"] is not None:
            vnic_ipv4_static_addr_list = [vnic_ipv4_static_addr for vnic_ipv4_static_addr in
                                          self._inventory.sdk_objects["vnicIpV4StaticAddr"]
                                          if self._parent.dn + "/mgmt/iface-in-band/network/ipv4-static-addr" in
                                          vnic_ipv4_static_addr.dn]

            # We fetch the vnicIpV4StaticAddr details if there is one and only one object in the list
            if len(vnic_ipv4_static_addr_list) == 1:
                self.ipv4_default_gw = vnic_ipv4_static_addr_list[0].def_gw
                self.ipv4 = vnic_ipv4_static_addr_list[0].addr
                self.ipv4_mode = "static"
                self.mask = vnic_ipv4_static_addr_list[0].subnet
                found = True

        # We check if we already have fetched the list of vnicIpV6StaticAddr objects
        if self._inventory.sdk_objects["vnicIpV6StaticAddr"] is not None:
            vnic_ipv6_static_addr_list = [vnic_ipv6_static_addr for vnic_ipv6_static_addr in
                                          self._inventory.sdk_objects["vnicIpV6StaticAddr"]
                                          if self._parent.dn + "/mgmt/iface-in-band/network/ipv6-static-addr" in
                                          vnic_ipv6_static_addr.dn]

            # We fetch the vnicIpV6StaticAddr details if there is one and only one object in the list
            if len(vnic_ipv6_static_addr_list) == 1:
                self.ipv6_default_gw = vnic_ipv6_static_addr_list[0].def_gw
                self.ipv6 = vnic_ipv6_static_addr_list[0].addr
                self.ipv6_mode = "static"
                self.prefix = vnic_ipv6_static_addr_list[0].prefix
                found = True

        # We check if we already have fetched the list of vnicIpV4MgmtPooledAddr objects
        if self._inventory.sdk_objects["vnicIpV4MgmtPooledAddr"] is not None:
            vnic_ipv4_mgmt_pooled_addr_list = [vnic_ipv4_mgmt_pooled_addr for vnic_ipv4_mgmt_pooled_addr in
                                               self._inventory.sdk_objects["vnicIpV4MgmtPooledAddr"]
                                               if self._parent.dn + "/mgmt/iface-in-band/network/ipv4-pooled-addr" in
                                               vnic_ipv4_mgmt_pooled_addr.dn]

            # We fetch the vnicIpV4MgmtPooledAddr details if there is one and only one object in the list
            if len(vnic_ipv4_mgmt_pooled_addr_list) == 1:
                self.ipv4_default_gw = vnic_ipv4_mgmt_pooled_addr_list[0].def_gw
                self.ipv4 = vnic_ipv4_mgmt_pooled_addr_list[0].addr
                self.ipv4_mode = "pool"
                self.ipv4_pool_name = vnic_ipv4_mgmt_pooled_addr_list[0].name
                self.mask = vnic_ipv4_mgmt_pooled_addr_list[0].subnet
                found = True

        # We check if we already have fetched the list of vnicIpV6MgmtPooledAddr objects
        if self._inventory.sdk_objects["vnicIpV6MgmtPooledAddr"] is not None:
            vnic_ipv6_mgmt_pooled_addr_list = [vnic_ipv6_mgmt_pooled_addr for vnic_ipv6_mgmt_pooled_addr in
                                               self._inventory.sdk_objects["vnicIpV6MgmtPooledAddr"]
                                               if
                                               self._parent.dn + "/mgmt/iface-in-band/network/ipv6-pooled-addr" in
                                               vnic_ipv6_mgmt_pooled_addr.dn]

            # We fetch the vnicIpV6MgmtPooledAddr details if there is one and only one object in the list
            if len(vnic_ipv6_mgmt_pooled_addr_list) == 1:
                self.ipv6_default_gw = vnic_ipv6_mgmt_pooled_addr_list[0].def_gw
                self.ipv6 = vnic_ipv6_mgmt_pooled_addr_list[0].addr
                self.ipv6_mode = "pool"
                self.ipv6_pool_name = vnic_ipv6_mgmt_pooled_addr_list[0].name
                self.prefix = vnic_ipv6_mgmt_pooled_addr_list[0].prefix
                found = True

        if found:
            return True
        return False

    def _get_inband_mgmt_vlan(self):
        # We check if we already have fetched the list of mgmtVnet objects
        if self._inventory.sdk_objects["mgmtVnet"] is not None:
            mgmt_vnet_list = [mgmt_vnet for mgmt_vnet in self._inventory.sdk_objects["mgmtVnet"]
                              if self._parent.dn + "/mgmt/iface-in-band/network" in mgmt_vnet.dn]

            # We fetch the mgmtVnet details if there is one and only one object in the list
            if len(mgmt_vnet_list) == 1:
                self.network_name = mgmt_vnet_list[0].name
                self.network_vlan_id = mgmt_vnet_list[0].id
                return True

        return False


class UcsImcMgmtInterface(UcsMgmtInterface, UcsImcInventoryObject):
    def __init__(self, parent=None, mgmt_if=None):
        UcsMgmtInterface.__init__(self, parent=parent, mgmt_if=mgmt_if)

        self.admin_duplex = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="admin_duplex")
        self.admin_net_speed = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="admin_net_speed")
        self.auto_neg = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="auto_neg")
        self.dhcp_enable = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="dhcp_enable")
        self.dns_preferred = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="dns_preferred")
        self.dns_alternate = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="dns_alternate")
        self.hostname = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="hostname")
        self.nic_mode = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="nic_mode")
        self.nic_redundancy = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="nic_redundancy")
        self.oper_duplex = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="oper_duplex")
        self.oper_net_speed = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="oper_net_speed")
        self.vic_slot = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="vic_slot")
        self.vlan_enable = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="vlan_enable")
        self.vlan_id = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="vlan_id")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=mgmt_if)
