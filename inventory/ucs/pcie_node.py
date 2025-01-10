# coding: utf-8
# !/usr/bin/env python

""" pcie_node.py: Easy UCS Deployment Tool """

from inventory.generic.pcie_node import GenericPcieNode
from inventory.ucs.gpu import UcsSystemGpu
from inventory.ucs.object import GenericUcsInventoryObject, UcsSystemInventoryObject


class UcsPcieNode(GenericPcieNode, GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentPcieNode"

    def __init__(self, parent=None, equipment_pcie_node=None):
        GenericPcieNode.__init__(self, parent=parent)
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_pcie_node)

        self.model = self.get_attribute(ucs_sdk_object=equipment_pcie_node, attribute_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_pcie_node, attribute_name="serial_number",
                                         attribute_secondary_name="serial")
        self.slot_id = self.get_attribute(ucs_sdk_object=equipment_pcie_node, attribute_name="slot_id")
        self.type = self.get_attribute(ucs_sdk_object=equipment_pcie_node, attribute_name="type")
        self.vendor = self.get_attribute(ucs_sdk_object=equipment_pcie_node, attribute_name="vendor")

        self.gpus = self._get_gpus()

    def _get_gpus(self):
        return []


class UcsSystemPcieNode(UcsPcieNode, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentPcieNodeCapProvider"

    def __init__(self, parent=None, equipment_pcie_node=None):
        UcsPcieNode.__init__(self, parent=parent, equipment_pcie_node=equipment_pcie_node)

        self.chassis_id = self.get_attribute(ucs_sdk_object=equipment_pcie_node, attribute_name="chassis_id")
        self.id = str(self.chassis_id) + "/" + str(self.slot_id)

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_pcie_node)

        # Small fix for when PCIe Node SKU is not present in UCS catalog
        if hasattr(self, "sku"):
            if not self.sku:
                if any(x in self.model for x in ["UCSX-"]):
                    self.sku = self.model

        if self._inventory.load_from == "live":
            self._peer_dn = self.get_attribute(ucs_sdk_object=equipment_pcie_node, attribute_name="peer_dn")
            self.peer = self._get_peer_server()
            self.short_name = self._get_model_short_name()
            self.imm_compatible = self._get_imm_compatibility()

        elif self._inventory.load_from == "file":
            for attribute in ["imm_compatible", "peer", "short_name"]:
                setattr(self, attribute, None)
                if attribute in equipment_pcie_node:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=equipment_pcie_node,
                                                                attribute_name=attribute))

    def _get_gpus(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemGpu, parent=self)
        elif self._inventory.load_from == "file" and "gpus" in self._ucs_sdk_object:
            return [UcsSystemGpu(self, gpu) for gpu in self._ucs_sdk_object["gpus"]]
        else:
            return []

    def _get_peer_server(self):
        if hasattr(self, "_peer_dn"):
            if self._peer_dn:
                peer_dn = self._peer_dn.split('/')

                if peer_dn[1].startswith("chassis-") and peer_dn[2].startswith("blade-"):
                    peer = {
                        "chassis": peer_dn[1].split("-")[-1],
                        "blade": peer_dn[2].split("-")[-1]
                    }
                    return peer
        return None
