# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

from __init__ import __version__
from inventory.imm_domain.inventory import ImmDomainInventory
from inventory.manager import GenericInventoryManager


class ImmDomainInventoryManager(GenericInventoryManager):
    def __init__(self, parent=None):
        GenericInventoryManager.__init__(self, parent=parent)
        self.inventory_class_name = ImmDomainInventory

    def fetch_inventory(self, force=False):
        self.logger(message="Fetching inventory from live device (can take several minutes)")
        inventory = ImmDomainInventory(parent=self)
        inventory.metadata.origin = "live"
        inventory.metadata.easyucs_version = __version__
        inventory.load_from = "live"

        if inventory.device.task is not None:
            inventory.device.task.taskstep_manager.start_taskstep(
                name="FetchInventoryImmDomainApiObjects",
                description="Fetching " + inventory.device.metadata.device_type_long + " API Inventory Objects")

        # TODO: Fetch the relevant inventory

        if inventory.device.task is not None:
            inventory.device.task.taskstep_manager.stop_taskstep(
                name="FetchInventoryImmDomainApiObjects", status="successful",
                status_message="Successfully fetched " + inventory.device.metadata.device_type_long +
                               " API Inventory Objects")

        self.inventory_list.append(inventory)
        self.logger(message="Finished fetching inventory with UUID " + str(inventory.uuid) + " from live device")
        return inventory.uuid

    def _fill_inventory_from_json(self, inventory=None, inventory_json=None):
        """
        Fills inventory using parsed JSON inventory file
        :param inventory: inventory to be filled
        :param inventory_json: parsed JSON content containing inventory
        :return: True if successful, False otherwise
        """
        if inventory is None or inventory_json is None:
            self.logger(level="debug", message="Missing inventory or inventory_json parameter!")
            return False

        # TODO: Populate the EasyUCS inventory with the relevant inventory json
        # if "rack_units" in inventory_json:
        #     for rack_unit in inventory_json["rack_units"]:
        #         inventory.rack_units.append(IntersightComputeRackUnit(parent=inventory, compute_rack_unit=rack_unit))
        #
        # if "ucsm_domains" in inventory_json:
        #     for ucsm_domain in inventory_json["ucsm_domains"]:
        #         inventory.ucsm_domains.append(IntersightUcsmDomain(parent=inventory, top_system=ucsm_domain))

        return True
