# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """


class GenericInventoryObject:
    def __init__(self, parent=None):
        self._draw = None
        self._parent = parent
        self._parent_having_logger = self._find_logger()

        self._inventory = self.__find_inventory()

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, '_parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object._parent

        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in inventory object")
            return None

    def __str__(self):
        return self.__class__.__name__ + "\n" +\
               str({key: value for key, value in vars(self).items() if not key.startswith('_')})

    def __find_inventory(self):
        # Method to find the Inventory object - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, '_parent') and not hasattr(current_object, 'timestamp'):
            current_object = current_object._parent
        if hasattr(current_object, 'timestamp'):
            return current_object
        else:
            return None
