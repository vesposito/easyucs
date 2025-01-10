# coding: utf-8
# !/usr/bin/env python

""" memory.py: Easy UCS Deployment Tool """
from common import read_json_file
from inventory.object import GenericInventoryObject

class GenericMemoryArray(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.capacity_max = None

    def _get_max_capacity(self):
        server_catalog = None
        if hasattr(self._parent, "model"):
            if "Blade" in self._parent.__class__.__name__:
                server_catalog = read_json_file("catalog/blades/" + self._parent.model + ".json")
            elif "Rack" in self._parent.__class__.__name__:
                server_catalog = read_json_file("catalog/racks/" + self._parent.model + ".json")
            elif "ServerNode" in self._parent.__class__.__name__:
                server_catalog = read_json_file("catalog/server_nodes/" + self._parent.model + ".json")

            if server_catalog:
                if server_catalog.get("specs"):
                    if server_catalog["specs"].get("memory"):
                        self.capacity_max = server_catalog["specs"]["memory"].get("max_capacity", None)


class GenericMemoryUnit(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.sku = None
