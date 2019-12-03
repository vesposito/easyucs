# coding: utf-8
# !/usr/bin/env python

""" mgmt.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsMgmtInterface(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "mgmtIf"

    def __init__(self, parent=None, mgmt_if=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=mgmt_if)

        self.default_gw = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="ext_gw",
                                             attribute_secondary_name="default_gw")
        self.id = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="id")
        self.ip = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="ext_ip", attribute_secondary_name="ip")
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
        self.switch_id = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="switch_id")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=mgmt_if)

        self.peer = None
        if self._inventory.load_from == "live":
            self._peer_dn = self.get_attribute(ucs_sdk_object=mgmt_if, attribute_name="peer_dn")
            self.peer = self._get_peer_port()
        elif self._inventory.load_from == "file":
            if "peer" in mgmt_if:
                self.peer = mgmt_if["peer"]


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
