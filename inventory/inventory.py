# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """

import uuid

from repository.metadata import InventoryMetadata


class GenericInventory:
    def __init__(self, parent=None):
        self.custom = False
        self.device = parent.parent
        self.load_from = None
        self.parent = parent
        self.status = None
        self.uuid = uuid.uuid4()

        # Needs to be created after UUID
        self.metadata = InventoryMetadata(parent=self)

        self._parent_having_logger = self._find_logger()

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in inventory")
            return None

    def __str__(self):
        return str(vars(self))
