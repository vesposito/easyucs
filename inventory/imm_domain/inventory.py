# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """

from inventory.inventory import GenericInventory


class ImmDomainInventory(GenericInventory):
    def __init__(self, parent=None):
        GenericInventory.__init__(self, parent=parent)

        self.export_list = None

        # TODO: Fetch the relevant inventory
        self.rack_units = []
        self.ucsm_domains = []

        # List of attributes to be exported in an inventory export
        self.export_list = ["rack_units", "ucsm_domains"]
