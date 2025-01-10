# coding: utf-8
# !/usr/bin/env python

""" gpu.py: Easy UCS Deployment Tool """

from inventory.object import GenericInventoryObject


class GenericGpu(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.model = None
        self.sku = None

    def _determine_sku(self):
        # Small fix for when GPU SKU is not present in UCS catalog
        if not self.sku:
            if any(x in self.model for x in ["UCSB-", "UCSC-", "UCSX-"]):
                self.sku = self.model
            if self.model == "Nvidia GRID K1 P2401-502":
                self.sku = "UCSC-GPU-VGXK1"
            if self.model == "Nvidia GRID K2 P2055-552":
                self.sku = "UCSC-GPU-VGXK2"
            if self.model == "Nvidia M60":
                self.sku = "UCSC-GPU-M60"
