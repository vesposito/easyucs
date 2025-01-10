# coding: utf-8
# !/usr/bin/env python

""" memory.py: Easy UCS Deployment Tool """
from inventory.generic.memory import GenericMemoryArray, GenericMemoryUnit
from inventory.intersight.object import IntersightInventoryObject


class IntersightMemoryArray(GenericMemoryArray, IntersightInventoryObject):
    def __init__(self, parent=None, memory_array=None):
        GenericMemoryArray.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=memory_array)

        self.capacity_current = self.get_attribute(attribute_name="current_capacity",
                                                   attribute_secondary_name="capacity_current", attribute_type="int")
        self.capacity_max = self.get_attribute(attribute_name="max_capacity",
                                               attribute_secondary_name="capacity_max", attribute_type="int")
        self.id = self.get_attribute(attribute_name="array_id", attribute_secondary_name="id")
        self.revision = self.get_attribute(attribute_name="revision")
        self.slots_max = self.get_attribute(attribute_name="max_devices", attribute_secondary_name="slots_max",
                                            attribute_type="int")

        self.memory_units = self._get_memory_units()

        if self._inventory.load_from == "live":
            self.slots_populated = len(self.memory_units)

            if not self.capacity_max:
                # We use the catalog to get the value if it is missing from the API
                self._get_max_capacity()

        elif self._inventory.load_from == "file":
            for attribute in ["slots_populated"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_memory_units(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.units, object_class=IntersightMemoryUnit,
                                                       parent=self)
        elif self._inventory.load_from == "file" and "memory_units" in self._object:
            return [IntersightMemoryUnit(self, memory_unit) for memory_unit in self._object["memory_units"]]
        else:
            return []


class IntersightMemoryUnit(GenericMemoryUnit, IntersightInventoryObject):
    def __init__(self, parent=None, memory_unit=None):
        GenericMemoryUnit.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=memory_unit)

        self.capacity = self.get_attribute(attribute_name="capacity", attribute_type="int")
        self.clock = self.get_attribute(attribute_name="clock", attribute_type="int")
        self.form_factor = self.get_attribute(attribute_name="form_factor")
        self.id = self.get_attribute(attribute_name="memory_id", attribute_secondary_name="id")
        self.latency = self.get_attribute(attribute_name="latency", attribute_type="float")
        self.location = self.get_attribute(attribute_name="location")
        self.model = self.get_attribute(attribute_name="model")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.sku = self.get_attribute(attribute_name="pid", attribute_secondary_name="sku")
        self.type = self.get_attribute(attribute_name="type")
        self.vendor = self.get_attribute(attribute_name="vendor")
        self.width = self.get_attribute(attribute_name="width", attribute_type="int")
