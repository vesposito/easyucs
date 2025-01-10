# coding: utf-8
# !/usr/bin/env python

""" pcie_node.py: Easy UCS Deployment Tool """
from common import read_json_file
from inventory.object import GenericInventoryObject


class GenericPcieNode(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.sku = None

    def _get_imm_compatibility(self):
        """
        Returns PCIe node IMM Compatibility status from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the PCIe node IMM Compatibility status
            pcie_node_catalog = read_json_file(file_path="catalog/pcie_nodes/" + self.sku + ".json", logger=self)

            if pcie_node_catalog:
                if "imm_compatible" in pcie_node_catalog:
                    return pcie_node_catalog["imm_compatible"]

        return None

    def _get_model_short_name(self):
        """
        Returns PCIe node short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the PCIe node short name
            pcie_node_catalog = read_json_file(file_path="catalog/pcie_nodes/" + self.sku + ".json", logger=self)

            if pcie_node_catalog:
                if "model_short_name" in pcie_node_catalog:
                    return pcie_node_catalog["model_short_name"]

        return None
