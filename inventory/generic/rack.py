# coding: utf-8
# !/usr/bin/env python

""" rack.py: Easy UCS Deployment Tool """
from common import read_json_file
from draw.ucs.rack import UcsRackDrawFront, UcsRackDrawRear
from inventory.object import GenericInventoryObject


class GenericRack(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.imm_compatible = None
        self.memory_total_marketing = None
        self.short_name = None
        self.sku = None

    def _generate_draw(self):
        self._draw_front = UcsRackDrawFront(parent=self)
        self._draw_rear = UcsRackDrawRear(parent=self)
        self._draw_infra = None

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
        Returns rack server IMM Compatibility status from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the rack IMM Compatibility status
            if self.sku in ["UCSC-C125"]:
                rack_catalog = read_json_file(file_path="catalog/server_nodes/" + self.sku + ".json", logger=self)
            else:
                rack_catalog = read_json_file(file_path="catalog/racks/" + self.sku + ".json", logger=self)
            if rack_catalog:
                if "imm_compatible" in rack_catalog:
                    return rack_catalog["imm_compatible"]

        return None

    def _get_model_short_name(self):
        """
        Returns rack server short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the rack short name
            if self.sku in ["UCSC-C125"]:
                rack_catalog = read_json_file(file_path="catalog/server_nodes/" + self.sku + ".json", logger=self)
            else:
                rack_catalog = read_json_file(file_path="catalog/racks/" + self.sku + ".json", logger=self)
            if rack_catalog:
                if "model_short_name" in rack_catalog:
                    return rack_catalog["model_short_name"]

        return None