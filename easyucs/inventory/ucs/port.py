# coding: utf-8
# !/usr/bin/env python

""" port.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject
from easyucs.inventory.ucs.neighbor import UcsSystemLanNeighborEntry, UcsSystemSanNeighborEntry
from easyucs.inventory.ucs.transceiver import UcsImcTransceiver, UcsSystemTransceiver


class UcsPort(GenericUcsInventoryObject):
    def __init__(self, parent=None, port=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=port)

        self.transport = None

        self.transceivers = self._get_transceivers()

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

    def _get_transceivers(self):
        return []


class UcsAdaptorPort(UcsPort):
    _UCS_SDK_OBJECT_NAME = "adaptorExtEthIf"

    def __init__(self, parent=None, adaptor_ext_eth_if=None):
        UcsPort.__init__(self, parent=parent, port=adaptor_ext_eth_if)

        self.link_state = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="link_state")
        self.port_id = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="port_id")
        self.if_type = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="if_type")
        self.mac = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="mac")

        if self._inventory.load_from == "live":
            self.transport = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="transport")
            if self.transport == "":
                self.transport = None
        elif self._inventory.load_from == "file":
            if "transport" in adaptor_ext_eth_if:
                self.transport = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="transport")


class UcsSystemAdaptorPort(UcsAdaptorPort, UcsSystemInventoryObject):
    def __init__(self, parent=None, adaptor_ext_eth_if=None):
        UcsAdaptorPort.__init__(self, parent=parent, adaptor_ext_eth_if=adaptor_ext_eth_if)

        self.role = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="if_role",
                                       attribute_secondary_name="role")
        self.slot_id = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="slot_id")
        self.switch_id = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="switch_id")
        self.transport = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="transport")
        self.type = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="type")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_ext_eth_if)

        self.aggr_port_id = None
        self.is_breakout = False
        self.is_port_channel_member = False
        self.pc_id = None
        self.peer = None
        if self._inventory.load_from == "live":
            self._peer_dn = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="peer_dn")
            self.peer = self._get_peer_port()

            if adaptor_ext_eth_if.aggr_port_id is not None:
                if adaptor_ext_eth_if.aggr_port_id != '0':
                    self.aggr_port_id = adaptor_ext_eth_if.aggr_port_id
                    self.is_breakout = True

            if adaptor_ext_eth_if.ep_dn != "":
                self.is_port_channel_member = True
                self.pc_id = adaptor_ext_eth_if.ep_dn.split("/")[4].split("-")[1]

        elif self._inventory.load_from == "file":
            for attribute in ["aggr_port_id", "is_breakout", "is_port_channel_member", "pc_id", "peer"]:
                setattr(self, attribute, None)
                if attribute in adaptor_ext_eth_if:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if,
                                                                attribute_name=attribute))

    def _get_transceivers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemTransceiver,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "transceivers" in self._ucs_sdk_object:
            return [UcsSystemTransceiver(self, transceiver) for transceiver in
                    self._ucs_sdk_object["transceivers"]]
        else:
            return []


class UcsSystemIomPort(UcsPort, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "etherSwitchIntFIo"

    def __init__(self, parent=None, ether_switch_int_f_io=None):
        UcsPort.__init__(self, parent=parent, port=ether_switch_int_f_io)

        self.chassis_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="chassis_id")
        self.port_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="port_id")
        self.oper_state = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="oper_state")
        self.role = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="if_role",
                                       attribute_secondary_name="role")
        self.slot_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="slot_id")
        self.switch_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="switch_id")
        self.transport = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="transport")
        self.type = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="type")
        self.xcvr_type = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="xcvr_type")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ether_switch_int_f_io)

        self.aggr_port_id = None
        self.is_breakout = False
        self.is_port_channel_member = False
        self.pc_id = None
        self.peer = None
        if self._inventory.load_from == "live":
            self._peer_dn = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="peer_dn")
            self.peer = self._get_peer_port()

            if ether_switch_int_f_io.aggr_port_id is not None:
                if ether_switch_int_f_io.aggr_port_id != '0':
                    self.aggr_port_id = ether_switch_int_f_io.aggr_port_id
                    self.is_breakout = True

            if ether_switch_int_f_io.ep_dn != "":
                self.is_port_channel_member = True
                self.pc_id = ether_switch_int_f_io.ep_dn.split("/")[4].split("-")[1]

        elif self._inventory.load_from == "file":
            for attribute in ["aggr_port_id", "is_breakout", "is_port_channel_member", "pc_id", "peer"]:
                setattr(self, attribute, None)
                if attribute in ether_switch_int_f_io:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=ether_switch_int_f_io,
                                                                attribute_name=attribute))

    def _get_transceivers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemTransceiver,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "transceivers" in self._ucs_sdk_object:
            return [UcsSystemTransceiver(self, transceiver) for transceiver in
                    self._ucs_sdk_object["transceivers"]]
        else:
            return []


class UcsSystemFexFabricPort(UcsPort, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "etherSwitchIntFIo"

    def __init__(self, parent=None, ether_switch_int_f_io=None):
        UcsPort.__init__(self, parent=parent, port=ether_switch_int_f_io)

        self.chassis_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="chassis_id")
        self.port_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="port_id")
        self.oper_state = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="oper_state")
        self.role = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="if_role",
                                       attribute_secondary_name="role")
        self.slot_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="slot_id")
        self.switch_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="switch_id")
        self.transport = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="transport")
        self.type = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="type")
        self.xcvr_type = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="xcvr_type")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ether_switch_int_f_io)

        self.aggr_port_id = None
        self.is_breakout = False
        self.is_port_channel_member = False
        self.pc_id = None
        self.peer = None
        if self._inventory.load_from == "live":
            self._peer_dn = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="peer_dn")
            self.peer = self._get_peer_port()

            if ether_switch_int_f_io.aggr_port_id is not None:
                if ether_switch_int_f_io.aggr_port_id != '0':
                    self.aggr_port_id = ether_switch_int_f_io.aggr_port_id
                    self.is_breakout = True

            if ether_switch_int_f_io.ep_dn != "":
                self.is_port_channel_member = True
                self.pc_id = ether_switch_int_f_io.ep_dn.split("/")[4].split("-")[1]

        elif self._inventory.load_from == "file":
            for attribute in ["aggr_port_id", "is_breakout", "is_port_channel_member", "pc_id", "peer"]:
                setattr(self, attribute, None)
                if attribute in ether_switch_int_f_io:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=ether_switch_int_f_io,
                                                                attribute_name=attribute))

    def _get_transceivers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemTransceiver,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "transceivers" in self._ucs_sdk_object:
            return [UcsSystemTransceiver(self, transceiver) for transceiver in
                    self._ucs_sdk_object["transceivers"]]
        else:
            return []


class UcsSystemFexHostPort(UcsPort, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "etherServerIntFIo"

    def __init__(self, parent=None, ether_server_int_f_io=None):
        UcsPort.__init__(self, parent=parent, port=ether_server_int_f_io)

        self.admin_speed = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="admin_speed")
        self.chassis_id = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="chassis_id")
        self.oper_state = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="oper_state")
        self.port_id = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="port_id")
        self.role = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="if_role",
                                       attribute_secondary_name="role")
        self.slot_id = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="slot_id")
        self.switch_id = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="switch_id")
        self.transport = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="transport")
        self.type = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="type")
        self.xcvr_type = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="xcvr_type")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ether_server_int_f_io)

        self.aggr_port_id = None
        self.is_breakout = False
        self.is_port_channel_member = False
        self.pc_id = None
        self.peer = None
        if self._inventory.load_from == "live":
            self._peer_dn = self.get_attribute(ucs_sdk_object=ether_server_int_f_io, attribute_name="peer_dn")
            self.peer = self._get_peer_port()

            if ether_server_int_f_io.aggr_port_id is not None:
                if ether_server_int_f_io.aggr_port_id != '0':
                    self.aggr_port_id = ether_server_int_f_io.aggr_port_id
                    self.is_breakout = True

            if ether_server_int_f_io.ep_dn != "":
                self.is_port_channel_member = True
                self.pc_id = ether_server_int_f_io.ep_dn.split("/")[4].split("-")[1]

        elif self._inventory.load_from == "file":
            for attribute in ["aggr_port_id", "is_breakout", "is_port_channel_member", "pc_id", "peer"]:
                setattr(self, attribute, None)
                if attribute in ether_server_int_f_io:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=ether_server_int_f_io,
                                                                attribute_name=attribute))


class UcsSystemFiPort(UcsPort):
    def __init__(self, parent=None, port=None):
        UcsPort.__init__(self, parent=parent, port=port)

        self.is_breakout_xcvr = self.get_attribute(ucs_sdk_object=port, attribute_name="is_breakout_xcvr")
        self.is_port_channel_member = self.get_attribute(ucs_sdk_object=port, attribute_name="is_port_channel_member")
        self.mode = self.get_attribute(ucs_sdk_object=port, attribute_name="mode")
        self.oper_speed = self.get_attribute(ucs_sdk_object=port, attribute_name="oper_speed")
        self.port_id = self.get_attribute(ucs_sdk_object=port, attribute_name="port_id")
        self.role = self.get_attribute(ucs_sdk_object=port, attribute_name="if_role", attribute_secondary_name="role")
        self.slot_id = self.get_attribute(ucs_sdk_object=port, attribute_name="slot_id")
        self.switch_id = self.get_attribute(ucs_sdk_object=port, attribute_name="switch_id")
        self.transport = self.get_attribute(ucs_sdk_object=port, attribute_name="transport")
        self.type = self.get_attribute(ucs_sdk_object=port, attribute_name="type")
        self.xcvr_type = self.get_attribute(ucs_sdk_object=port, attribute_name="xcvr_type")

        if self.is_breakout_xcvr in ["no", "false"]:
            self.is_breakout_xcvr = False
        elif self.is_breakout_xcvr in ["yes", "true"]:
            self.is_breakout_xcvr = True

        if self.is_port_channel_member in ["no", "false"]:
            self.is_port_channel_member = False
        elif self.is_port_channel_member in ["yes", "true"]:
            self.is_port_channel_member = True

        self.neighbor_entries = self._get_neighbor_entries()

        self.aggr_port_id = None
        self.pc_id = None
        if self._inventory.load_from == "live":
            self.is_breakout = False

            if port.aggr_port_id is not None:
                if port.aggr_port_id != '0':
                    self.aggr_port_id = port.aggr_port_id
                    self.is_breakout = True

            if self.is_port_channel_member:
                self.pc_id = port.ep_dn.split("pc-")[1].split("/")[0]

        elif self._inventory.load_from == "file":
            for attribute in ["aggr_port_id", "is_breakout", "pc_id"]:
                setattr(self, attribute, None)
                if attribute in port:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=port, attribute_name=attribute))

    def _get_neighbor_entries(self):
            return []

    def _get_transceivers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemTransceiver,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "transceivers" in self._ucs_sdk_object:
            return [UcsSystemTransceiver(self, transceiver) for transceiver in
                    self._ucs_sdk_object["transceivers"]]
        else:
            return []


class UcsSystemFiEthPort(UcsSystemFiPort, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "etherPIo"

    def __init__(self, parent=None, ether_pio=None):
        UcsSystemFiPort.__init__(self, parent=parent, port=ether_pio)

        self.mac = self.get_attribute(ucs_sdk_object=ether_pio, attribute_name="mac")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ether_pio)

        self.peer = None
        if self._inventory.load_from == "live":
            self._peer_dn = self.get_attribute(ucs_sdk_object=ether_pio, attribute_name="peer_dn")
            self.peer = self._get_peer_port()
        elif self._inventory.load_from == "file":
            if "peer" in ether_pio:
                self.peer = ether_pio["peer"]

    def _get_neighbor_entries(self):
        if self._inventory.load_from == "live":
            network_lan_neighbor_entry_list = []
            network_lldp_neighbor_entry_list = []
            ucs_system_lan_neighbor_entry_list = []

            if "networkLanNeighborEntry" in self._inventory.sdk_objects:
                if self._inventory.sdk_objects["networkLanNeighborEntry"] is not None:
                    # We filter out SDK objects that are not under this Dn
                    network_lan_neighbor_entry_list = [network_lan_neighbor_entry for network_lan_neighbor_entry in
                                                       self._inventory.sdk_objects["networkLanNeighborEntry"] if
                                                       self.dn == network_lan_neighbor_entry.fi_port_dn]
            if "networkLldpNeighborEntry" in self._inventory.sdk_objects:
                if self._inventory.sdk_objects["networkLldpNeighborEntry"] is not None:
                    # We filter out SDK objects that are not under this Dn
                    network_lldp_neighbor_entry_list = [network_lldp_neighbor_entry for network_lldp_neighbor_entry in
                                                        self._inventory.sdk_objects["networkLldpNeighborEntry"] if
                                                        self.dn == network_lldp_neighbor_entry.fi_port_dn]

            if len(network_lan_neighbor_entry_list) != 0 and len(network_lldp_neighbor_entry_list) != 0:
                # We have both CDP and LLDP neighbors entries
                for network_lan_neighbor_entry in network_lan_neighbor_entry_list:
                    for network_lldp_neighbor_entry in network_lldp_neighbor_entry_list:
                        if network_lldp_neighbor_entry.fi_port_dn == network_lan_neighbor_entry.fi_port_dn:
                            ucs_system_lan_neighbor_entry_list.append(
                                UcsSystemLanNeighborEntry(parent=self,
                                                          network_lan_neighbor_entry=network_lan_neighbor_entry,
                                                          network_lldp_neighbor_entry=network_lldp_neighbor_entry))

            if len(network_lan_neighbor_entry_list) == 0 and len(network_lldp_neighbor_entry_list) != 0:
                # We have LLDP neighbors only
                for network_lldp_neighbor_entry in network_lldp_neighbor_entry_list:
                    ucs_system_lan_neighbor_entry_list.append(
                        UcsSystemLanNeighborEntry(parent=self,
                                                  network_lan_neighbor_entry=None,
                                                  network_lldp_neighbor_entry=network_lldp_neighbor_entry))

            if len(network_lan_neighbor_entry_list) != 0 and len(network_lldp_neighbor_entry_list) == 0:
                # We have CDP neighbors only
                for network_lan_neighbor_entry in network_lan_neighbor_entry_list:
                    ucs_system_lan_neighbor_entry_list.append(
                        UcsSystemLanNeighborEntry(parent=self,
                                                  network_lan_neighbor_entry=network_lan_neighbor_entry,
                                                  network_lldp_neighbor_entry=None))

            return ucs_system_lan_neighbor_entry_list

        elif self._inventory.load_from == "file" and "neighbor_entries" in self._ucs_sdk_object:
            return [UcsSystemLanNeighborEntry(self, neighbor_entry) for neighbor_entry in
                    self._ucs_sdk_object["neighbor_entries"]]
        else:
            return []


class UcsSystemFiFcPort(UcsSystemFiPort, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "fcPIo"

    def __init__(self, parent=None, fc_pio=None):
        UcsSystemFiPort.__init__(self, parent=parent, port=fc_pio)

        self.max_speed = self.get_attribute(ucs_sdk_object=fc_pio, attribute_name="max_speed")
        self.wwn = self.get_attribute(ucs_sdk_object=fc_pio, attribute_name="wwn")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=fc_pio)

    def _get_neighbor_entries(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemSanNeighborEntry,
                                                                  parent=self)

        elif self._inventory.load_from == "file" and "neighbor_entries" in self._ucs_sdk_object:
            return [UcsSystemSanNeighborEntry(self, neighbor_entry) for neighbor_entry in
                    self._ucs_sdk_object["neighbor_entries"]]
        else:
            return []


class UcsSystemSiocPort(UcsPort, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "etherSwitchIntFIo"

    def __init__(self, parent=None, ether_switch_int_f_io=None):
        UcsPort.__init__(self, parent=parent, port=ether_switch_int_f_io)

        self.chassis_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="chassis_id")
        self.port_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="port_id")
        self.role = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="if_role",
                                       attribute_secondary_name="role")
        self.slot_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="slot_id")
        self.switch_id = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="switch_id")
        self.transport = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="transport")
        self.type = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="type")
        self.xcvr_type = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="xcvr_type")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ether_switch_int_f_io)

        self.aggr_port_id = None
        self.is_breakout = False
        self.is_port_channel_member = False
        self.pc_id = None
        self.peer = None
        if self._inventory.load_from == "live":
            self._peer_dn = self.get_attribute(ucs_sdk_object=ether_switch_int_f_io, attribute_name="peer_dn")
            self.peer = self._get_peer_port()

            if ether_switch_int_f_io.aggr_port_id is not None:
                if ether_switch_int_f_io.aggr_port_id != '0':
                    self.aggr_port_id = ether_switch_int_f_io.aggr_port_id
                    self.is_breakout = True

            if ether_switch_int_f_io.ep_dn != "":
                self.is_port_channel_member = True
                self.pc_id = ether_switch_int_f_io.ep_dn.split("/")[4].split("-")[1]

            # This is needed to determine if S3260 is in breakout mode or in 40G native mode, as aggr_id is not set
            if "shared-io-module/fabric-pc" in ether_switch_int_f_io.ep_dn:
                self.is_breakout = True

        elif self._inventory.load_from == "file":
            for attribute in ["aggr_port_id", "is_breakout", "is_port_channel_member", "pc_id", "peer"]:
                setattr(self, attribute, None)
                if attribute in ether_switch_int_f_io:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=ether_switch_int_f_io,
                                                                attribute_name=attribute))

    def _get_transceivers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemTransceiver,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "transceivers" in self._ucs_sdk_object:
            return [UcsSystemTransceiver(self, transceiver) for transceiver in
                    self._ucs_sdk_object["transceivers"]]
        else:
            return []


class UcsImcAdaptorPort(UcsAdaptorPort, UcsImcInventoryObject):
    def __init__(self, parent=None, adaptor_ext_eth_if=None):
        UcsAdaptorPort.__init__(self, parent=parent, adaptor_ext_eth_if=adaptor_ext_eth_if)

        self.admin_speed = self.get_attribute(ucs_sdk_object=adaptor_ext_eth_if, attribute_name="admin_speed")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_ext_eth_if)

    def _get_transceivers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcTransceiver,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "transceivers" in self._ucs_sdk_object:
            return [UcsImcTransceiver(self, transceiver) for transceiver in self._ucs_sdk_object["transceivers"]]
        else:
            return []


class UcsImcNetworkAdapterPort(UcsPort, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "networkAdapterEthIf"

    def __init__(self, parent=None, network_adapter_eth_if=None):
        UcsPort.__init__(self, parent=parent, port=network_adapter_eth_if)

        self.mac = self.get_attribute(ucs_sdk_object=network_adapter_eth_if, attribute_name="mac")
        self.port_id = self.get_attribute(ucs_sdk_object=network_adapter_eth_if, attribute_name="id",
                                          attribute_secondary_name="port_id")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=network_adapter_eth_if)
