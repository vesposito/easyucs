# coding: utf-8
# !/usr/bin/env python

""" tpm.py: Easy UCS Deployment Tool """

from inventory.object import GenericInventoryObject


class GenericTpm(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.sku = None
