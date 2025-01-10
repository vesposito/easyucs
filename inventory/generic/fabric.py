# coding: utf-8
# !/usr/bin/env python

""" fabric.py: Easy UCS Deployment Tool """
from common import read_json_file
from draw.ucs.fabric import UcsFexDrawFront, UcsFexDrawRear, UcsFiDrawFront, UcsFiDrawRear
from inventory.object import GenericInventoryObject


class GenericFex(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.sku = None

    def _generate_draw(self):
        self._draw_rear = UcsFexDrawRear(parent=self)
        self._draw_front = UcsFexDrawFront(parent=self)

    def _get_imm_compatibility(self):
        """
        Returns Fabric Extender IMM Compatibility status from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the FEX IMM Compatibility status
            fex_catalog = read_json_file(file_path="catalog/fabric_extenders/" + self.sku + ".json", logger=self)
            if fex_catalog:
                if "imm_compatible" in fex_catalog:
                    return fex_catalog["imm_compatible"]

        return None

    def _get_model_short_name(self):
        """
        Returns Fabric Extender short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the FEX short name
            fex_catalog = read_json_file(file_path="catalog/fabric_extenders/" + self.sku + ".json", logger=self)
            if fex_catalog:
                if "model_short_name" in fex_catalog:
                    return fex_catalog["model_short_name"]

        return None


class GenericFi(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.name = None
        self.sku = None

    def _generate_draw(self):
        self._draw_rear = UcsFiDrawRear(parent=self)
        if self.sku not in ["UCS-FI-M-6324", "UCSX-S9108-100G"]:
            self._draw_front = UcsFiDrawFront(parent=self)

    def _get_imm_compatibility(self):
        """
        Returns Fabric Interconnect IMM Compatibility status from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the FI IMM Compatibility status
            fi_catalog = read_json_file(file_path="catalog/fabric_interconnects/" + self.sku + ".json", logger=self)
            if fi_catalog:
                if "imm_compatible" in fi_catalog:
                    return fi_catalog["imm_compatible"]

        return None

    def _get_model_short_name(self):
        """
        Returns Fabric Interconnect short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the FI short name
            fi_catalog = read_json_file(file_path="catalog/fabric_interconnects/" + self.sku + ".json", logger=self)
            if fi_catalog:
                if "model_short_name" in fi_catalog:
                    return fi_catalog["model_short_name"]

        return None

    def _get_name(self):
        """
        Returns Fabric Interconnect name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the FI short name
            fi_catalog = read_json_file(file_path="catalog/fabric_interconnects/" + self.sku + ".json", logger=self)
            if fi_catalog:
                if "name" in fi_catalog:
                    return fi_catalog["name"]

        return None
