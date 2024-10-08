# coding: utf-8
# !/usr/bin/env python

""" memory.py: Easy UCS Deployment Tool """

from inventory.ucs.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


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
            "UCSC-C480-M5": 6291456,
            # C220 M6
            "UCSC-C220-M6S": 4194304, "UCSC-C220-M6N": 4194304,
            # C225 M6
            "UCSC-C225-M6S": 4194304, "UCSC-C225-M6N": 4194304,
            # C240 M6
            "UCSC-C240-M6S": 8388608, "UCSC-C240-M6SX": 8388608, "UCSC-C240-M6N": 8388608, "UCSC-C240-M6SN": 8388608,
            "UCSC-C240-M6L": 8388608,
            # C245 M6
            "UCSC-C245-M6SX": 8388608,
            # C220 M7
            "UCSC-C220-M7S": 4194304, "UCSC-C220-M7N": 4194304,
            # C240 M7
            "UCSC-C240-M7SX": 8388608, "UCSC-C240-M7SN": 8388608,
            # C225 M8
            "UCSC-C225-M8S": 1572864, "UCSC-C225-M8N": 1572864,
            # C245 M8
            "UCSC-C245-M8SX": 6291456
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
