# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

from __init__ import __version__
from inventory.intersight.compute import IntersightComputeRackUnit
from inventory.intersight.domain import IntersightUcsmDomain
from inventory.intersight.inventory import IntersightInventory
from inventory.manager import GenericInventoryManager


class IntersightInventoryManager(GenericInventoryManager):
    def __init__(self, parent=None):
        GenericInventoryManager.__init__(self, parent=parent)
        self.inventory_class_name = IntersightInventory

    def fetch_inventory(self, force=False):
        self.logger(message="Fetching inventory from live device (can take several minutes)")
        inventory = IntersightInventory(parent=self)
        inventory.metadata.origin = "live"
        inventory.metadata.easyucs_version = __version__
        inventory.load_from = "live"
        inventory._fetch_sdk_objects(force=force)

        # If any of the mandatory tasksteps fails then return None
        from api.api_server import easyucs
        if easyucs and self.parent.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.parent.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more SDK objects. Stopping the inventory fetch.")
            return None

        self.logger(level="debug", message="Finished fetching Intersight SDK objects for inventory")

        if "top_system" in inventory.sdk_objects.keys():
            for top_system in inventory.sdk_objects["top_system"]:
                if "mode" in top_system.attribute_map:
                    if top_system.mode in ["cluster"]:  # TODO: Test whether a standalone FI is declared as a cluster in Intersight
                        # We are working with a UCS Manager domain
                        inventory.ucsm_domains.append(IntersightUcsmDomain(parent=inventory,
                                                                           top_system=top_system))
                    elif top_system.mode in ["stand-alone"]:
                        # We are working with a CIMC
                        if top_system.compute_rack_units:
                            server_moid = top_system.compute_rack_units[0].moid
                            if "compute_rack_unit" in inventory.sdk_objects.keys():
                                for compute_rack_unit in inventory.sdk_objects["compute_rack_unit"]:
                                    if compute_rack_unit.moid == server_moid:
                                        inventory.rack_units.append(
                                            IntersightComputeRackUnit(parent=inventory,
                                                                      compute_rack_unit=compute_rack_unit))

                        # elif top_system.compute_blades:
                            # Case of an S3260

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

        if "rack_units" in inventory_json:
            for rack_unit in inventory_json["rack_units"]:
                inventory.rack_units.append(IntersightComputeRackUnit(parent=inventory, compute_rack_unit=rack_unit))

        if "ucsm_domains" in inventory_json:
            for ucsm_domain in inventory_json["ucsm_domains"]:
                inventory.ucsm_domains.append(IntersightUcsmDomain(parent=inventory, top_system=ucsm_domain))

        return True
