# coding: utf-8
# !/usr/bin/env python

""" port.py: Easy UCS Deployment Tool """

from inventory.intersight.object import IntersightInventoryObject
from inventory.intersight.transceiver import IntersightTransceiver


class IntersightPort(IntersightInventoryObject):
    def __init__(self, parent=None, port=None):
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=port)
        self.peer = None
        self.type = None

    def _get_peer_port(self):
        peer = None
        # Fetching peer info
        peer_interface_list = self.get_inventory_objects_from_ref(ref=self._object.acknowledged_peer_interface)
        if len(peer_interface_list) == 1:
            if peer_interface_list[0].object_type == "ether.PhysicalPort":
                # This is a port connected to an FI
                if peer_interface_list[0].aggregate_port_id:
                    peer = {
                        "switch": peer_interface_list[0].switch_id,
                        "aggr_port": peer_interface_list[0].aggregate_port_id,
                        "port": peer_interface_list[0].port_id,
                        "slot": peer_interface_list[0].slot_id
                    }
                else:
                    peer = {
                        "switch": peer_interface_list[0].switch_id,
                        "aggr_port": None,
                        "port": peer_interface_list[0].port_id,
                        "slot": peer_interface_list[0].slot_id
                    }
            elif peer_interface_list[0].object_type in ["ether.HostPort", "ether.NetworkPort"]:
                # This is a port connected to a chassis / FEX
                equipment_io_card_list = self.get_inventory_objects_from_ref(
                    ref=peer_interface_list[0].equipment_io_card_base)
                if len(equipment_io_card_list) == 1 and \
                        equipment_io_card_list[0].object_type == "equipment.IoCard":
                    # This is a port connected to a chassis.
                    # We also need to fetch the "equipment.Chassis" object to find its ID
                    compute_chassis_list = self.get_inventory_objects_from_ref(
                        ref=equipment_io_card_list[0].equipment_chassis)
                    if len(compute_chassis_list) == 1:
                        peer = {
                            "chassis": compute_chassis_list[0].chassis_id,
                            "port": peer_interface_list[0].port_id,
                            "slot": peer_interface_list[0].slot_id,
                            "switch": peer_interface_list[0].switch_id
                        }
                elif len(equipment_io_card_list) == 1 and \
                        equipment_io_card_list[0].object_type == "equipment.Fex":
                    # This is a port connected to a FEX
                    peer = {
                        "fex": equipment_io_card_list[0].module_id,
                        "port": peer_interface_list[0].port_id,
                        "slot": peer_interface_list[0].slot_id,
                        "switch": peer_interface_list[0].switch_id
                    }
            elif peer_interface_list[0].object_type == "adapter.ExtEthInterface":
                # This is a port connected to a rack server (adapter)
                # We need to fetch the "adapter.Unit" object to find its ID
                adapter_unit_list = self.get_inventory_objects_from_ref(ref=peer_interface_list[0].adapter_unit)
                if len(adapter_unit_list) == 1:
                    # We also need to fetch the "compute.RackUnit" object to find its ID
                    compute_rack_unit_list = self.get_inventory_objects_from_ref(
                        ref=adapter_unit_list[0].compute_rack_unit)
                    if len(compute_rack_unit_list) == 1:
                        peer = {
                            "rack": compute_rack_unit_list[0].server_id,
                            "port": peer_interface_list[0].ext_eth_interface_id,
                            "slot": adapter_unit_list[0].adapter_id
                        }
                    else:
                        self.logger(level="error", message="No compute.RackUnit found for port")

        return peer

    def _get_transceivers(self):
        if self._inventory.load_from == "live":
            transceiver_list = []
            for transceiver in self._inventory.sdk_objects.get("equipment_transceiver", []):
                if transceiver.ether_host_port:
                    if transceiver.ether_host_port.moid == self._object.moid and \
                            transceiver.presence not in ["no"] and transceiver.status not in ["removed"]:
                        transceiver_list.append(IntersightTransceiver(self, transceiver))
                elif transceiver.ether_physical_port:
                    if transceiver.ether_physical_port.moid == self._object.moid and \
                            transceiver.presence not in ["no"] and transceiver.status not in ["removed"]:
                        transceiver_list.append(IntersightTransceiver(self, transceiver))
                elif transceiver.fc_physical_port:
                    if transceiver.fc_physical_port.moid == self._object.moid and \
                            transceiver.presence not in ["no"] and transceiver.status not in ["removed"]:
                        transceiver_list.append(IntersightTransceiver(self, transceiver))
            return transceiver_list
        elif self._inventory.load_from == "file" and "transceivers" in self._object:
            return [IntersightTransceiver(self, transceiver) for transceiver in self._object["transceivers"]]
        else:
            return []


class IntersightAdaptorPort(IntersightPort):
    def __init__(self, parent=None, adaptor_ext_eth_if=None):
        IntersightPort.__init__(self, parent=parent, port=adaptor_ext_eth_if)

        self.aggr_port_id = None
        self.if_type = self.get_attribute(attribute_name="interface_type", attribute_secondary_name="if_type")
        self.is_breakout = False
        self.mac = self.get_attribute(attribute_name="mac_address", attribute_secondary_name="mac")
        self.port_id = self.get_attribute(attribute_name="ext_eth_interface_id", attribute_secondary_name="port_id")
        self.switch_id = self.get_attribute(attribute_name="switch_id")

        if self._inventory.load_from == "live":
            self.peer = self._get_peer_port()

        elif self._inventory.load_from == "file":
            for attribute in ["peer"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))


class IntersightFexFabricPort(IntersightPort):
    def __init__(self, parent=None, port=None):
        IntersightPort.__init__(self, parent=parent, port=port)

        self.aggr_port_id = None
        self.is_breakout = False
        self.oper_state = self.get_attribute(attribute_name="oper_state")
        self.port_id = self.get_attribute(attribute_name="port_id")
        self.role = "Uplink"  # We use this to color ports during draw operation
        self.slot_id = self.get_attribute(attribute_name="slot_id")
        self.switch_id = None
        self.type = "lan"

        self.transceivers = self._get_transceivers()

        if self._inventory.load_from == "live":
            self.switch_id = self._parent.switch_id
            self.peer = self._get_peer_port()

        elif self._inventory.load_from == "file":
            for attribute in ["peer", "switch_id"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))


class IntersightFexHostPort(IntersightPort):
    def __init__(self, parent=None, port=None):
        IntersightPort.__init__(self, parent=parent, port=port)

        self.aggr_port_id = None
        self.is_breakout = False
        self.oper_state = self.get_attribute(attribute_name="oper_state")
        self.port_id = self.get_attribute(attribute_name="port_id")
        self.role = "Server"  # We use this to color ports during draw operation
        self.slot_id = self.get_attribute(attribute_name="slot_id")
        self.switch_id = None
        self.type = "lan"

        self.transceivers = self._get_transceivers()

        if self._inventory.load_from == "live":
            self.switch_id = self._parent.switch_id
            self.peer = self._get_peer_port()

        elif self._inventory.load_from == "file":
            for attribute in ["peer", "switch_id"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))


class IntersightFiPort(IntersightPort):
    def __init__(self, parent=None, port=None):
        IntersightPort.__init__(self, parent=parent, port=port)

        self.aggr_port_id = self.get_attribute(attribute_name="aggregate_port_id",
                                               attribute_secondary_name="aggr_port_id")
        self.mode = self.get_attribute(attribute_name="mode")
        self.oper_speed = self.get_attribute(attribute_name="oper_speed")
        self.port_id = self.get_attribute(attribute_name="port_id")
        self.role = self.get_attribute(attribute_name="role")
        self.slot_id = self.get_attribute(attribute_name="slot_id")
        self.switch_id = None

        self.transceivers = self._get_transceivers()

        if self._inventory.load_from == "live":
            # We clean up empty aggr_port_id values
            if self.aggr_port_id == 0:
                self.aggr_port_id = None
                self.is_breakout = False
            else:
                self.is_breakout = True

            self.switch_id = self._parent.id

        elif self._inventory.load_from == "file":
            for attribute in ["is_breakout", "switch_id"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))


class IntersightFiEthPort(IntersightFiPort):
    def __init__(self, parent=None, ether_physical_port=None):
        IntersightFiPort.__init__(self, parent=parent, port=ether_physical_port)

        self.mac = self.get_attribute(attribute_name="mac_address", attribute_secondary_name="mac")
        self.transport = "ether"
        self.type = "lan"

        if self._inventory.load_from == "live":
            self.peer = self._get_peer_port()

        elif self._inventory.load_from == "file":
            for attribute in ["peer"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))


class IntersightFiFcPort(IntersightFiPort):
    def __init__(self, parent=None, fc_physical_port=None):
        IntersightFiPort.__init__(self, parent=parent, port=fc_physical_port)

        self.max_speed = self.get_attribute(attribute_name="max_speed")
        self.transport = "fc"
        self.type = "san"
        self.wwn = self.get_attribute(attribute_name="wwn")


class IntersightIomPort(IntersightPort):
    def __init__(self, parent=None, port=None):
        IntersightPort.__init__(self, parent=parent, port=port)

        self.aggr_port_id = None
        self.chassis_id = None
        self.is_breakout = False
        self.port_id = self.get_attribute(attribute_name="port_id")
        self.role = "Uplink"  # We use this to color ports during draw operation
        self.slot_id = self.get_attribute(attribute_name="slot_id")
        self.switch_id = None
        self.type = "lan"

        self.transceivers = self._get_transceivers()

        if self._inventory.load_from == "live":
            self.chassis_id = self._parent._parent.id
            self.switch_id = self._parent.switch_id
            self.peer = self._get_peer_port()

        elif self._inventory.load_from == "file":
            for attribute in ["chassis_id", "peer", "switch_id"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
