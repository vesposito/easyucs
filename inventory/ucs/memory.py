# coding: utf-8
# !/usr/bin/env python

""" memory.py: Easy UCS Deployment Tool """
from inventory.generic.blade import GenericBlade
from inventory.generic.memory import GenericMemoryArray, GenericMemoryUnit
from inventory.ucs.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsMemoryArray(GenericMemoryArray, GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "memoryArray"

    def __init__(self, parent=None, memory_array=None):
        GenericMemoryArray.__init__(self, parent=parent)
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

        # We use the catalog to determine the value if it is missing from the API
        self._get_max_capacity()

    def _get_memory_units(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcMemoryUnit,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "memory_units" in self._ucs_sdk_object:
            return [UcsImcMemoryUnit(self, memory_unit) for memory_unit in self._ucs_sdk_object["memory_units"]]
        else:
            return []


class UcsMemoryUnit(GenericMemoryUnit, GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "memoryUnit"

    def __init__(self, parent=None, memory_unit=None):
        GenericMemoryUnit.__init__(self, parent=parent)
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

        if self._inventory.load_from == "live":
            # Manually fixing type "Other" for memory units in some servers
            if self.type in ["Other"]:
                if hasattr(self._parent._parent, "model"):
                    if self._parent._parent.model is not None:
                        if self._parent._parent.model in ["N20-B6625-1"]:
                            self.type = "DDR3"

            self.errors_address_parity = None
            self.errors_ecc_multibit = None
            self.errors_ecc_singlebit = None
            self.errors_mismatch = None
            error_stats = self._find_corresponding_memory_error_stats()
            if error_stats:
                self.errors_address_parity = int(error_stats.address_parity_errors)
                self.errors_ecc_multibit = int(error_stats.ecc_multibit_errors)
                self.errors_ecc_singlebit = int(error_stats.ecc_singlebit_errors)
                self.errors_mismatch = int(error_stats.mismatch_errors)

        elif self._inventory.load_from == "file":
            for attribute in ["errors_address_parity", "errors_ecc_multibit", "errors_ecc_singlebit",
                              "errors_mismatch"]:
                setattr(self, attribute, None)
                if attribute in memory_unit:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=memory_unit, attribute_name=attribute))

    def _find_corresponding_memory_error_stats(self):
        if "memoryErrorStats" not in self._inventory.sdk_objects.keys():
            return None

        # We check if we already have fetched the list of memoryErrorStats objects
        if self._inventory.sdk_objects["memoryErrorStats"] is not None:

            # We need to find the matching memoryErrorStats object
            memory_error_stats_list = [memory_error_stats for memory_error_stats in
                                       self._inventory.sdk_objects["memoryErrorStats"] if
                                       self.dn + "/error-stats" == memory_error_stats.dn]
            if (len(memory_error_stats_list)) != 1:
                self.logger(level="debug",
                            message="Could not find the corresponding memoryErrorStats for object with DN " +
                                    self.dn + " of model \"" + str(self.model) + "\" with ID " + str(self.id))
                if hasattr(self._parent, "id"):
                    self.logger(level="info", message="Error stats of memory unit with id " + str(self.id) +
                                                      " for server " + self._parent.id + " are not available.")
                else:
                    self.logger(level="info", message="Error stats of memory unit with id " + str(self.id) +
                                                      " for server " + self._parent.dn + " are not available.")

                return None
            else:
                return memory_error_stats_list[0]

        return None


class UcsImcMemoryUnit(UcsMemoryUnit, UcsImcInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogDimm"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "name"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "location"

    def __init__(self, parent=None, memory_unit=None):
        UcsMemoryUnit.__init__(self, parent=parent, memory_unit=memory_unit)
        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=memory_unit)
