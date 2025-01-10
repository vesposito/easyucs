# coding: utf-8
# !/usr/bin/env python

""" domain.py: Easy UCS Deployment Tool """
from inventory.intersight.chassis import IntersightChassis
from inventory.intersight.fabric import IntersightFex, IntersightFi
from inventory.intersight.object import IntersightInventoryObject
from inventory.intersight.rack import IntersightComputeRackUnit


class IntersightImmDomain(IntersightInventoryObject):
    def __init__(self, parent=None, asset_device_registration=None):
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=asset_device_registration)

        self.chassis = []
        self.fabric_extenders = []
        self.fabric_interconnects = []
        self.name = None
        self.rack_units = []

        if self._inventory.load_from == "live":
            if self._object.device_hostname:
                self.name = self._object.device_hostname[0]

            # We need to find the "equipment.Chassis" objects that belong to this IMM domain
            for equipment_chassis in self._inventory.sdk_objects.get("equipment_chassis", []):
                if equipment_chassis.registered_device.moid == asset_device_registration.moid:
                    self.chassis.append(IntersightChassis(parent=self, equipment_chassis=equipment_chassis))

            # We sort the list of chassis to return objects in an appropriate order
            self.chassis = sorted(self.chassis, key=lambda x: x.id if getattr(x, "id", None) else 0)

            # We need to find the "compute.RackUnit" objects that belong to this IMM domain
            for compute_rack_unit in self._inventory.sdk_objects.get("compute_rack_unit", []):
                parent_asset_device_registration = self.get_inventory_objects_from_ref(
                    ref=compute_rack_unit.registered_device)
                if len(parent_asset_device_registration) == 1:
                    if parent_asset_device_registration[0].parent_connection:
                        if parent_asset_device_registration[0].parent_connection.moid == \
                                asset_device_registration.moid:
                            self.rack_units.append(
                                IntersightComputeRackUnit(parent=self, compute_rack_unit=compute_rack_unit))

            # We sort the list of rack units to return objects in an appropriate order
            self.rack_units = sorted(self.rack_units, key=lambda x: x.id if getattr(x, "id", None) else 0)

            # We need to find the "network.Element" objects that belong to this IMM domain
            for network_element in self._inventory.sdk_objects.get("network_element", []):
                if network_element.registered_device.moid == asset_device_registration.moid:
                    self.fabric_interconnects.append(IntersightFi(parent=self, network_element=network_element))

            # We sort the list of FIs to return objects in an appropriate order
            self.fabric_interconnects = sorted(self.fabric_interconnects,
                                               key=lambda x: x.id if getattr(x, "id", None) else 0)

            # Finally, we need to find the "equipment.Fex" objects that belong to this IMM domain
            for equipment_fex in self._inventory.sdk_objects.get("equipment_fex", []):
                if equipment_fex.registered_device.moid == asset_device_registration.moid:
                    self.fabric_extenders.append(IntersightFex(parent=self, equipment_fex=equipment_fex))

            # We sort the list of FEXs to return objects in an appropriate order
            self.fabric_extenders = sorted(self.fabric_extenders, key=lambda x: x.id if getattr(x, "id", None) else 0)

        elif self._inventory.load_from == "file":
            if "chassis" in self._object:
                for chassis in self._object["chassis"]:
                    self.chassis.append(IntersightChassis(parent=self, equipment_chassis=chassis))
            if "fabric_extenders" in self._object:
                for fex in self._object["fabric_extenders"]:
                    self.fabric_extenders.append(IntersightFex(parent=self, equipment_fex=fex))
            if "fabric_interconnects" in self._object:
                for fi in self._object["fabric_interconnects"]:
                    self.fabric_interconnects.append(IntersightFi(parent=self, network_element=fi))
            if "rack_units" in self._object:
                for rack in self._object["rack_units"]:
                    self.rack_units.append(IntersightComputeRackUnit(parent=self, compute_rack_unit=rack))
            for attribute in ["name"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))


class IntersightUcsmDomain(IntersightInventoryObject):
    def __init__(self, parent=None, top_system=None):
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=top_system)

        self.ipv4_address = self.get_attribute(attribute_name="ipv4_address")
        self.ipv6_address = self.get_attribute(attribute_name="ipv6_address")
        self.name = self.get_attribute(attribute_name="name")

        self.chassis = []
        self.fabric_extenders = []
        self.fabric_interconnects = self._get_fabric_interconnects()
        self.rack_units = self._get_rack_units()

        if self._inventory.load_from == "live":
            # We need to find the "equipment.Chassis" objects that belong to this UCSM domain
            for equipment_chassis in self._inventory.sdk_objects.get("equipment_chassis", []):
                if equipment_chassis.registered_device.moid == top_system.registered_device.moid:
                    self.chassis.append(IntersightChassis(parent=self, equipment_chassis=equipment_chassis))

            # We sort the list of chassis to return objects in an appropriate order
            self.chassis = sorted(self.chassis, key=lambda x: x.id if getattr(x, "id", None) else 0)

        elif self._inventory.load_from == "file":
            if "chassis" in self._object:
                for chassis in self._object["chassis"]:
                    self.chassis.append(IntersightChassis(parent=self, equipment_chassis=chassis))
            for attribute in []:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_fabric_interconnects(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.network_elements, object_class=IntersightFi,
                                                       parent=self)
        elif self._inventory.load_from == "file" and "fabric_interconnects" in self._object:
            return [IntersightFi(self, fi) for fi in self._object["fabric_interconnects"]]
        else:
            return []

    def _get_rack_units(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.compute_rack_units,
                                                       object_class=IntersightComputeRackUnit, parent=self)
        elif self._inventory.load_from == "file" and "rack_units" in self._object:
            return [IntersightComputeRackUnit(self, rack) for rack in self._object["rack_units"]]
        else:
            return []
