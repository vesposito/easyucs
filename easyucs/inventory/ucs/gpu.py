# coding: utf-8
# !/usr/bin/env python

""" adaptor.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


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

        # Small fix for when GPU SKU is not present in UCS catalog
        if hasattr(self, "sku"):
            if not self.sku:
                if any(x in self.model for x in ["UCSB-", "UCSC-"]):
                    self.sku = self.model
                if self.model == "Nvidia GRID K1 P2401-502":
                    self.sku = "UCSC-GPU-VGXK1"
                if self.model == "Nvidia GRID K2 P2055-552":
                    self.sku = "UCSC-GPU-VGXK2"
                if self.model == "Nvidia M60":
                    self.sku = "UCSC-GPU-M60"


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
