# coding: utf-8
# !/usr/bin/env python

""" blade.py: Easy UCS Deployment Tool """
from common import read_json_file
from inventory.object import GenericInventoryObject


class GenericBlade(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.imm_compatible = None
        self.memory_total_marketing = None
        self.model = None
        self.short_name = None
        self.sku = None
        self.sku_scaled = None

    def _get_front_mezzanine_model(self):
        # Determining the front mezzanine model for X-Series blades
        if self.model and self.model.startswith("UCSX-"):
            front_mezzanine = {
                "model": None,
                "name": None,
                "serial": None,
                "sku": None,
                "vendor": None
            }
            if hasattr(self, "storage_controllers") and self.storage_controllers:
                for storage_controller in self.storage_controllers:
                    if storage_controller.id and storage_controller.id in ["MRAID"]:
                        for key in front_mezzanine.keys():
                            front_mezzanine[key] = getattr(storage_controller, key, None)

                        return front_mezzanine

        return None

    def _get_memory_total_marketing(self):
        # Adding a human-readable attribute for memory capacity
        if hasattr(self, "memory_total"):
            if self.memory_total:
                if self.memory_total / 1024 < 1024:
                    memory_total_gb = str(self.memory_total / 1024)
                    memory_total_gb = memory_total_gb.rstrip('0').rstrip(
                        '.') if '.' in memory_total_gb else memory_total_gb
                    self.memory_total_marketing = memory_total_gb + " GB"
                else:
                    memory_total_tb = str(self.memory_total / 1048576)
                    memory_total_tb = memory_total_tb.rstrip('0').rstrip(
                        '.') if '.' in memory_total_tb else memory_total_tb
                    self.memory_total_marketing = memory_total_tb + " TB"

    def _get_imm_compatibility(self):
        """
        Returns blade server IMM Compatibility status from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the blade IMM Compatibility status
            if self.sku_scaled:
                blade_catalog = read_json_file(file_path="catalog/blades/" + self.sku_scaled + ".json", logger=self)
            else:
                blade_catalog = read_json_file(file_path="catalog/blades/" + self.sku + ".json", logger=self)

            if blade_catalog:
                if "imm_compatible" in blade_catalog:
                    return blade_catalog["imm_compatible"]

        return None

    def _get_model_short_name(self):
        """
        Returns blade server short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the blade short name
            if self.sku_scaled:
                blade_catalog = read_json_file(file_path="catalog/blades/" + self.sku_scaled + ".json", logger=self)
            else:
                blade_catalog = read_json_file(file_path="catalog/blades/" + self.sku + ".json", logger=self)

            if blade_catalog:
                if "model_short_name" in blade_catalog:
                    return blade_catalog["model_short_name"]

        return None