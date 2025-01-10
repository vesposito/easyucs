# coding: utf-8
# !/usr/bin/env python

""" mgmt.py: Easy UCS Deployment Tool """

from inventory.object import GenericInventoryObject


class GenericMgmtInterface(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)
