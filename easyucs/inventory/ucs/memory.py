# coding: utf-8
# !/usr/bin/env python

""" memory.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsMemoryArray(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "memoryArray"

    def __init__(self, parent=None, memory_array=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=memory_array)

        self.capacity_current = self.get_attribute(ucs_sdk_object=memory_array, attribute_name="curr_capacity",
                                                   attribute_secondary_name="capacity_current", attribute_type="int")
        self.id = self.get_attribute(ucs_sdk_object=memory_array, attribute_name="id")
        self.slots_max = self.get_attribute(ucs_sdk_object=memory_array, attribute_name="max_devices",
                                            attribute_secondary_name="slots_max", attribute_type="int")
        self.slots_populated = self.get_attribute(ucs_sdk_object=memory_array, attribute_name="populated",
                                                  attribute_secondary_name="slots_populated", attribute_type="int")

        self.memory_units = self._get_memory_units()

    def _get_memory_units(self):
        return []


class UcsSystemMemoryArray(UcsMemoryArray, UcsSystemInventoryObject):
    def __init__(self, parent=None, memory_array=None):
        UcsMemoryArray.__init__(self, parent=parent, memory_array=memory_array)

        self.capacity_max = self.get_attribute(ucs_sdk_object=memory_array, attribute_name="max_capacity",
                                               attribute_secondary_name="capacity_max", attribute_type="int")
        self.revision = self.get_attribute(ucs_sdk_object=memory_array, attribute_name="revision")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=memory_array)

    def _get_memory_units(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemMemoryUnit,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "memory_units" in self._ucs_sdk_object:
            return [UcsSystemMemoryUnit(self, memory_unit) for memory_unit in self._ucs_sdk_object["memory_units"]]
        else:
            return []


class UcsImcMemoryArray(UcsMemoryArray, UcsImcInventoryObject):
    def __init__(self, parent=None, memory_array=None):
        UcsMemoryArray.__init__(self, parent=parent, memory_array=memory_array)
        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=memory_array)

        self.capacity_max = None
        max_ram_capacity = {
            # C200 M2
            "UCSC-BSE-SFF-C200": 196608, "R200-1120402W": 196608,
            # C210 M2
            "R210-2121605W": 196608,
            # C250 M2
            "R250-2480805W": 393216,
            # C260 M2
            "C260-BASE-2646": 1048576,
            # C460 M2
            "UCSC-BASE-M2-C460": 2097152,
            # C22 M3
            "UCSC-C22-M3S": 393216, "UCSC-C22-M3L": 393216,
            # C24 M3
            "UCSC-C24-M3S": 393216, "UCSC-C24-M3S2": 393216, "UCSC-C24-M3L": 393216,
            # C220 M3
            "UCSC-C220-M3S": 524288, "UCSC-C220-M3L": 524288,
            # C240 M3
            "UCSC-C240-M3S": 786432, "UCSC-C240-M3S2": 786432, "UCSC-C240-M3L": 786432,
            # C420 M3
            "UCSC-C420-M3": 1572864,
            # C220 M4
            "UCSC-C220-M4S": 1572864, "UCSC-C220-M4L": 1572864,
            # C240 M4
            "UCSC-C240-M4S": 1572864, "UCSC-C240-M4S2": 1572864, "UCSC-C240-M4SX": 1572864,
            "UCSC-C240-M4L": 1572864,
            # C460 M4
            "UCSC-C460-M4": 6291456,
            # C220 M5
            "UCSC-C220-M5SX": 3145728, "UCSC-C220-M5SN": 3145728,
            # C240 M5
            "UCSC-C240-M5S": 3145728, "UCSC-C240-M5SX": 3145728, "UCSC-C240-M5SN": 3145728,
            "UCSC-C240-M5L": 3145728,
            # C480 M5
            "UCSC-C480-M5": 6291456
        }
        if hasattr(self._parent, "model"):
            if self._parent.model in max_ram_capacity:
                self.capacity_max = max_ram_capacity[self._parent.model]

    def _get_memory_units(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcMemoryUnit,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "memory_units" in self._ucs_sdk_object:
            return [UcsImcMemoryUnit(self, memory_unit) for memory_unit in self._ucs_sdk_object["memory_units"]]
        else:
            return []


class UcsMemoryUnit(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "memoryUnit"

    def __init__(self, parent=None, memory_unit=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=memory_unit)

        self.capacity = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="capacity", attribute_type="int")
        self.clock = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="clock", attribute_type="int")
        self.form_factor = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="form_factor")
        self.id = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="id")
        self.location = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="location")
        self.model = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="serial")
        self.type = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="type")
        self.vendor = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="vendor")
        self.width = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="width", attribute_type="int")


class UcsSystemMemoryUnit(UcsMemoryUnit, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentMemoryUnitCapProvider"

    def __init__(self, parent=None, memory_unit=None):
        UcsMemoryUnit.__init__(self, parent=parent, memory_unit=memory_unit)

        self.latency = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="latency", attribute_type="float")
        self.revision = self.get_attribute(ucs_sdk_object=memory_unit, attribute_name="revision")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=memory_unit)


class UcsImcMemoryUnit(UcsMemoryUnit, UcsImcInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogDimm"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "name"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "location"

    def __init__(self, parent=None, memory_unit=None):
        UcsMemoryUnit.__init__(self, parent=parent, memory_unit=memory_unit)
        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=memory_unit)
