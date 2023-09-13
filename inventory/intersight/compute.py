# coding: utf-8
# !/usr/bin/env python

""" compute.py: Easy UCS Deployment Tool """

from inventory.intersight.object import IntersightInventoryObject
from inventory.intersight.psu import IntersightPsu


class IntersightComputeRackUnit(IntersightInventoryObject):
    def __init__(self, parent=None, compute_rack_unit=None):
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=compute_rack_unit)

        self.model = self.get_attribute(attribute_name="model")
        self.power_supplies = self._get_power_supplies()

        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
            self.name = self._get_compute_rack_unit_name()

        elif self._inventory.load_from == "file":
            for attribute in ["locator_led_status", "name"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_compute_rack_unit_name(self):
        # In case this ComputeRackUnit is not part of a UCS Domain, we want to fetch its name
        if self._object.platform_type not in ["IMC"]:
            return None

        top_system_moid = self._object.top_system.moid

        if "top_system" in self._inventory.sdk_objects:
            for top_system in self._inventory.sdk_objects["top_system"]:
                if top_system.moid == top_system_moid:
                    return top_system.name

        return None

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.psus, object_class=IntersightPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._object:
            return [IntersightPsu(self, psu) for psu in self._object["power_supplies"]]
        else:
            return []
