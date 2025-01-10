# coding: utf-8
# !/usr/bin/env python

""" adaptor.py: Easy UCS Deployment Tool """

import re

from inventory.generic.cpu import GenericCpu
from inventory.ucs.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsCpu(GenericCpu, GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "processorUnit"

    def __init__(self, parent=None, processor_unit=None):
        GenericCpu.__init__(self, parent=parent)
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=processor_unit)

        self.arch = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="arch")
        self.cores = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="cores", attribute_type="int")
        self.cores_enabled = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="cores_enabled",
                                                attribute_type="int")
        self.id = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="model")
        self.speed = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="speed")
        self.threads = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="threads", attribute_type="int")
        self.vendor = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="vendor")

        self._get_model_short_name()


class UcsSystemCpu(UcsCpu, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentProcessorUnitCapProvider"

    def __init__(self, parent=None, processor_unit=None):
        UcsCpu.__init__(self, parent=parent, processor_unit=processor_unit)

        self.revision = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="revision")

        if self._inventory.load_from == "live":
            # We convert the speed from GHz to MHz and change it to integer in order to have a consistent value with IMC
            if self.speed != 'unspecified':
                self.speed = int(float(self.speed) * 1000)

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=processor_unit)


class UcsImcCpu(UcsCpu, UcsImcInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogCpu"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "id"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "id"

    def __init__(self, parent=None, processor_unit=None):
        UcsCpu.__init__(self, parent=parent, processor_unit=processor_unit)

        if self._inventory.load_from == "live":
            # We convert the speed string to integer
            if self.speed != 'unspecified':
                self.speed = int(self.speed)

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=processor_unit)
