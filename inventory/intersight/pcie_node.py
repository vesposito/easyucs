# coding: utf-8
# !/usr/bin/env python

""" pcie_node.py: Easy UCS Deployment Tool """
from inventory.generic.pcie_node import GenericPcieNode
from inventory.intersight.gpu import IntersightGpu
from inventory.intersight.object import IntersightInventoryObject


class IntersightPcieNode(GenericPcieNode, IntersightInventoryObject):
    def __init__(self, parent=None, pci_node=None):
        GenericPcieNode.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=pci_node)

        self.chassis_id = self.get_attribute(attribute_name="chassis_id", attribute_type="int")
        self.model = self.get_attribute(attribute_name="model")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.slot_id = self.get_attribute(attribute_name="slot_id", attribute_type="int")
        self.vendor = self.get_attribute(attribute_name="vendor")

        self.id = str(self.chassis_id) + "/" + str(self.slot_id)

        self.gpus = self._get_gpus()

        if self._inventory.load_from == "live":
            self.sku = self.model
            self.peer = self._get_peer_server()
            self.short_name = self._get_model_short_name()

        elif self._inventory.load_from == "file":
            for attribute in ["peer", "short_name", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_gpus(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.graphics_cards, object_class=IntersightGpu,
                                                       parent=self)
        elif self._inventory.load_from == "file" and "gpus" in self._object:
            return [IntersightGpu(self, gpu) for gpu in self._object["gpus"]]
        else:
            return []

    def _get_peer_server(self):
        chassis_id = int(self._object.chassis_id)
        compute_blade = self.get_inventory_objects_from_ref(ref=self._object.compute_blade)
        if len(compute_blade) == 1:
            slot_id = compute_blade[0].slot_id
            peer = {
                "chassis": chassis_id,
                "blade": slot_id
            }
            return peer
        return None
