# coding: utf-8
# !/usr/bin/env python

""" adaptor.py: Easy UCS Deployment Tool """
from __init__ import __author__, __copyright__,  __version__, __status__


from inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsGpu(GenericUcsInventoryObject):
    def __init__(self, parent=None, graphics_card=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=graphics_card)

        self.id = self.get_attribute(ucs_sdk_object=graphics_card, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=graphics_card, attribute_name="model")
        self.vendor = self.get_attribute(ucs_sdk_object=graphics_card, attribute_name="vendor")


class UcsSystemGpu(UcsGpu, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentGraphicsCardCapProvider"
    _UCS_SDK_OBJECT_NAME = "graphicsCard"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/fw-system"

    def __init__(self, parent=None, graphics_card=None):
        UcsGpu.__init__(self, parent=parent, graphics_card=graphics_card)

        self.pci_slot = self.get_attribute(ucs_sdk_object=graphics_card, attribute_name="pci_slot")
        self.revision = self.get_attribute(ucs_sdk_object=graphics_card, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=graphics_card, attribute_name="serial")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=graphics_card)


class UcsImcGpu(UcsGpu, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "pciEquipSlot"
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogPCIAdapter"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "slot"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "id"

    def __init__(self, parent=None, graphics_card=None):
        UcsGpu.__init__(self, parent=parent, graphics_card=graphics_card)

        self.firmware_version = self.get_attribute(ucs_sdk_object=graphics_card, attribute_name="version",
                                                   attribute_secondary_name="firmware_version")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=graphics_card)