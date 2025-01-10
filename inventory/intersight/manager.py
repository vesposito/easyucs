# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

from __init__ import __version__
from draw.ucs.chassis import UcsChassisDrawInfra
from draw.ucs.rack import UcsRackDrawInfra
from inventory.intersight.rack import IntersightComputeRackUnit
from inventory.intersight.domain import IntersightImmDomain, IntersightUcsmDomain
from inventory.intersight.inventory import IntersightInventory
from inventory.manager import GenericInventoryManager


class IntersightInventoryManager(GenericInventoryManager):
    def __init__(self, parent=None):
        GenericInventoryManager.__init__(self, parent=parent)
        self.inventory_class_name = IntersightInventory

    def draw_inventory(self, uuid=None):
        """
        Draws UCS chassis, racks, FEXs, FIs and LAN/SAN neighbors using the specified inventory
        :param uuid: The UUID of the inventory to be drawn. If not specified, the most recent inventory will be used
        :return: True if draw is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="debug", message="No inventory UUID specified in inventory draw request. Using latest.")
            inventory = self.get_latest_inventory()
        else:
            # Find the inventory that needs to be exported
            inventory_list = [inventory for inventory in self.inventory_list if inventory.uuid == uuid]
            if len(inventory_list) != 1:
                self.logger(level="error", message="Failed to locate inventory with UUID " + str(uuid) + " for draw")
                return False
            else:
                inventory = inventory_list[0]

        if inventory is None:
            # We could not find any inventory
            self.logger(level="error", message="Could not find any inventory to draw!")
            return False

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.start_taskstep(
                name="GenerateReportDrawInventoryIntersight",
                description="Drawing inventory of device " + self.parent.target)

        for ucs_domain in inventory.imm_domains + inventory.ucsm_domains:
            fi_rear_draw_list = []
            for fi in ucs_domain.fabric_interconnects:
                fi._generate_draw()
                fi_rear_draw_list.append(fi._draw_rear)
            # We only keep the FI that have been fully created -> json file and picture
            fi_rear_draw_list = [fi for fi in fi_rear_draw_list if fi.picture_size]

            rotated_fi_draw_list = []
            is_embedded_fi = False
            for fi in fi_rear_draw_list:
                if fi._parent.sku == "UCS-FI-M-6324":
                    is_embedded_fi = True
                    # As we drop the picture before, we need to recreate it and drop it again
                    fi._get_picture()
                    rotated_fi_draw_list.append(fi.rotate_object(fi))
                    fi.picture = None
                elif fi._parent.sku == "UCSX-S9108-100G":
                    is_embedded_fi = True

            fex_rear_draw_list = []
            for fex in ucs_domain.fabric_extenders:
                fex._generate_draw()
                fex_rear_draw_list.append(fex._draw_rear)
            # We only keep the FEX that have been fully created -> json file and picture
            fex_rear_draw_list = [fex for fex in fex_rear_draw_list if fex.picture_size]

            chassis_front_draw_list = []
            chassis_rear_draw_list = []
            for chassis in ucs_domain.chassis:
                chassis._generate_draw()
                chassis_front_draw_list.append(chassis._draw_front)
                chassis_rear_draw_list.append(chassis._draw_rear)
            # We only keep the chassis that have been fully created -> json file and picture
            chassis_front_draw_list = [chassis for chassis in chassis_front_draw_list if chassis.picture_size]
            chassis_rear_draw_list = [chassis for chassis in chassis_rear_draw_list if chassis.picture_size]

            # Draw infra of chassis
            for chassis_draw in chassis_rear_draw_list:
                # if FI is embedded then the chassis 1 is a UCS Mini/X-Direct chassis, so no need to draw infra
                if not (is_embedded_fi and str(chassis_draw._parent.id) == '1'):
                    if fi_rear_draw_list:
                        infra = UcsChassisDrawInfra(chassis=chassis_draw, fi_list=fi_rear_draw_list,
                                                    fex_list=fex_rear_draw_list, parent=fi_rear_draw_list[0]._parent)
                        if hasattr(infra, "_file_name"):
                            # If wires are present
                            chassis_draw._parent._draw_infra = infra
                        else:
                            chassis_draw._parent._draw_infra = None
                    else:
                        chassis_draw._parent._draw_infra = None

            rack_front_draw_list = []
            rack_rear_draw_list = []
            for rack in ucs_domain.rack_units:
                rack._generate_draw()
                rack_front_draw_list.append(rack._draw_front)
                rack_rear_draw_list.append(rack._draw_rear)
            # We only keep the racks that have been fully created -> json file and picture
            rack_front_draw_list = [rack for rack in rack_front_draw_list if rack.picture_size]
            rack_rear_draw_list = [rack for rack in rack_rear_draw_list if rack.picture_size]

            # Draw infra of racks
            for rack_draw in rack_rear_draw_list:
                if fi_rear_draw_list:
                    infra = UcsRackDrawInfra(rack=rack_draw, fi_list=fi_rear_draw_list,
                                             fex_list=fex_rear_draw_list, parent=fi_rear_draw_list[0]._parent)
                    if hasattr(infra, "_file_name"):
                        # If wires are present
                        rack_draw._parent._draw_infra = infra
                    else:
                        rack_draw._parent._draw_infra = None
                else:
                    rack_draw._parent._draw_infra = None

        for rack in inventory.rack_units:
            rack._generate_draw()

        # rack_enclosure_front_draw_list = []
        # rack_enclosure_rear_draw_list = []
        # for rack_enclosure in inventory.rack_enclosures:
        #     rack_enclosure._generate_draw()
        #     rack_enclosure_front_draw_list.append(rack_enclosure._draw_front)
        #     rack_enclosure_rear_draw_list.append(rack_enclosure._draw_rear)
        # # We only keep the racks that have been fully created -> json file and picture
        # rack_enclosure_front_draw_list = [rack_enclosure for rack_enclosure in rack_enclosure_front_draw_list if
        #                                   rack_enclosure.picture_size]
        # rack_enclosure_rear_draw_list = [rack_enclosure for rack_enclosure in rack_enclosure_rear_draw_list if
        #                                  rack_enclosure.picture_size]
        #
        # lan_neighbor_draw_list = []
        # san_neighbor_draw_list = []
        # for lan_neighbor in inventory.lan_neighbors:
        #     lan_neighbor._generate_draw()
        #     lan_neighbor_draw_list.append(lan_neighbor._draw)
        # for san_neighbor in inventory.san_neighbors:
        #     san_neighbor._generate_draw()
        #     san_neighbor_draw_list.append(san_neighbor._draw)
        # if lan_neighbor_draw_list:
        #     # TODO find a better parent
        #     inventory._draw_infra_lan_neighbors = \
        #         UcsSystemDrawInfraNeighborsLan(draw_neighbor_list=lan_neighbor_draw_list,
        #                                        draw_fi_list=fi_rear_draw_list, parent=fi_rear_draw_list[0]._parent)
        # if san_neighbor_draw_list:
        #     inventory._draw_infra_san_neighbors = \
        #         UcsSystemDrawInfraNeighborsSan(draw_neighbor_list=san_neighbor_draw_list,
        #                                        draw_fi_list=fi_rear_draw_list, parent=fi_rear_draw_list[0]._parent)
        #
        # # Draw infra Service Profiles
        # inventory._draw_infra_chassis_service_profiles = []
        # if chassis_front_draw_list or chassis_rear_draw_list:
        #     if fi_rear_draw_list:
        #         inventory._draw_infra_chassis_service_profiles.append(
        #             UcsSystemDrawInfraServiceProfile(draw_chassis_front_list=chassis_front_draw_list,
        #                                              draw_chassis_rear_list=chassis_rear_draw_list,
        #                                              parent=fi_rear_draw_list[0]._parent))
        # if inventory._draw_infra_chassis_service_profiles:
        #     infra = inventory._draw_infra_chassis_service_profiles[0]
        #     while infra.next_page_infra:
        #         inventory._draw_infra_chassis_service_profiles.append(infra.next_page_infra)
        #         infra = infra.next_page_infra
        #
        # inventory._draw_infra_rack_service_profiles = []
        # if rack_front_draw_list:
        #     if fi_rear_draw_list:
        #         inventory._draw_infra_rack_service_profiles.append(
        #             UcsSystemDrawInfraServiceProfile(draw_rack_list=rack_front_draw_list,
        #                                              parent=fi_rear_draw_list[0]._parent))
        # if inventory._draw_infra_rack_service_profiles:
        #     infra = inventory._draw_infra_rack_service_profiles[0]
        #     while infra.next_page_infra:
        #         inventory._draw_infra_rack_service_profiles.append(infra.next_page_infra)
        #         infra = infra.next_page_infra
        #
        # inventory._draw_infra_rack_enclosure_service_profiles = []
        # if rack_enclosure_rear_draw_list:
        #     if fi_rear_draw_list:
        #         inventory._draw_infra_rack_enclosure_service_profiles.append(
        #             UcsSystemDrawInfraServiceProfile(draw_rack_enclosure_list=rack_enclosure_rear_draw_list,
        #                                              parent=fi_rear_draw_list[0]._parent))
        # if inventory._draw_infra_rack_enclosure_service_profiles:
        #     infra = inventory._draw_infra_rack_enclosure_service_profiles[0]
        #     while infra.next_page_infra:
        #         inventory._draw_infra_rack_enclosure_service_profiles.append(infra.next_page_infra)
        #         infra = infra.next_page_infra
        #
        # # Draw infra of equipments
        # for rack_enclosure_draw in rack_enclosure_rear_draw_list:
        #     if fi_rear_draw_list:
        #         infra = UcsSystemDrawInfraRackEnclosure(rack_enclosure=rack_enclosure_draw, fi_list=fi_rear_draw_list,
        #                                                 fex_list=fex_rear_draw_list,
        #                                                 parent=fi_rear_draw_list[0]._parent)
        #         if hasattr(infra, "_file_name"):
        #             # If wires are present
        #             rack_enclosure_draw._parent._draw_infra = infra
        #         else:
        #             rack_enclosure_draw._parent._draw_infra = None
        #     else:
        #         rack_enclosure_draw._parent._draw_infra = None

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.stop_taskstep(
                name="GenerateReportDrawInventoryIntersight", status="successful",
                status_message="Finished drawing inventory of device " + self.parent.target)

        return True

    def export_draw(self, uuid=None, export_format="png", directory=None, export_clear_pictures=False):
        """
        Export all the drawings generated from an inventory
        :param uuid: The UUID of the drawn inventory to be exported. If not specified, most recent will be used
        :param export_format: "png" by default, not used for now
        :param directory: directory to export the pictures to
        :param export_clear_pictures : Also export the pictures without colored ports
        :return: True if successful, False otherwise
        """
        if uuid is None:
            self.logger(level="debug",
                        message="No inventory UUID specified in inventory save draw request. Using latest.")
            inventory = self.get_latest_inventory()
        else:
            # Find the inventory that needs to be exported
            inventory_list = [inventory for inventory in self.inventory_list if inventory.uuid == uuid]
            if len(inventory_list) != 1:
                self.logger(level="error", message="Failed to locate inventory with UUID " + str(uuid) + " for draw")
                return False
            else:
                inventory = inventory_list[0]

        if inventory is None:
            self.logger(level="error", message="No available inventory for draw")
            return False

        for ucs_domain in inventory.imm_domains + inventory.ucsm_domains:
            for fi in ucs_domain.fabric_interconnects:
                if hasattr(fi, "_draw_front"):
                    if fi._draw_front:
                        fi._draw_front.save_image(output_directory=directory, format=export_format)
                if hasattr(fi, "_draw_rear"):
                    if fi._draw_rear:
                        fi._draw_rear.save_image(output_directory=directory, format=export_format)
                        if export_clear_pictures:
                            if hasattr(fi._draw_rear, "clear_version"):
                                fi._draw_rear.clear_version.save_image(output_directory=directory,
                                                                       format=export_format)

            for fex in ucs_domain.fabric_extenders:
                if hasattr(fex, "_draw_front"):
                    if fex._draw_front:
                        fex._draw_front.save_image(output_directory=directory, format=export_format)
                if hasattr(fex, "_draw_rear"):
                    if fex._draw_rear:
                        fex._draw_rear.save_image(output_directory=directory, format=export_format)
                        if export_clear_pictures:
                            if hasattr(fex._draw_rear, "clear_version"):
                                fex._draw_rear.clear_version.save_image(output_directory=directory,
                                                                        format=export_format)

            for chassis in ucs_domain.chassis:
                if hasattr(chassis, "_draw_front"):
                    if chassis._draw_front:
                        chassis._draw_front.save_image(output_directory=directory, format=export_format)
                if hasattr(chassis, "_draw_rear"):
                    if chassis._draw_rear:
                        chassis._draw_rear.save_image(output_directory=directory, format=export_format)
                        if export_clear_pictures:
                            if hasattr(chassis._draw_rear, "clear_version"):
                                chassis._draw_rear.clear_version.save_image(output_directory=directory,
                                                                            format=export_format)
                if hasattr(chassis, "_draw_infra"):
                    if chassis._draw_infra:
                        chassis._draw_infra.save_image(output_directory=directory, format=export_format)

            for rack in ucs_domain.rack_units:
                if hasattr(rack, "_draw_front"):
                    if rack._draw_front:
                        rack._draw_front.save_image(output_directory=directory, format=export_format)
                if hasattr(rack, "_draw_rear"):
                    if rack._draw_rear:
                        rack._draw_rear.save_image(output_directory=directory, format=export_format)
                        if export_clear_pictures:
                            if hasattr(rack._draw_rear, "clear_version"):
                                rack._draw_rear.clear_version.save_image(output_directory=directory, format=export_format)
                if hasattr(rack, "_draw_infra"):
                    if rack._draw_infra:
                        rack._draw_infra.save_image(output_directory=directory, format=export_format)

        for rack in inventory.rack_units:
            if hasattr(rack, "_draw_front"):
                if rack._draw_front:
                    rack._draw_front.save_image(output_directory=directory, format=export_format)
            if hasattr(rack, "_draw_rear"):
                if rack._draw_rear:
                    rack._draw_rear.save_image(output_directory=directory, format=export_format)
                    if export_clear_pictures:
                        if hasattr(rack._draw_rear, "clear_version"):
                            rack._draw_rear.clear_version.save_image(output_directory=directory, format=export_format)

        #
        # for rack_enclosure in inventory.rack_enclosures:
        #     if hasattr(rack_enclosure, "_draw_front"):
        #         if rack_enclosure._draw_front:
        #             rack_enclosure._draw_front.save_image(output_directory=directory, format=export_format)
        #     if hasattr(rack_enclosure, "_draw_rear"):
        #         if rack_enclosure._draw_rear:
        #             rack_enclosure._draw_rear.save_image(output_directory=directory, format=export_format)
        #             if export_clear_pictures:
        #                 if hasattr(rack_enclosure._draw_rear, "clear_version"):
        #                     rack_enclosure._draw_rear.clear_version.save_image(output_directory=directory,
        #                                                                        format=export_format)
        #     if hasattr(rack_enclosure, "_draw_infra"):
        #         if rack_enclosure._draw_infra:
        #             rack_enclosure._draw_infra.save_image(output_directory=directory, format=export_format)
        #
        # if inventory._draw_infra_san_neighbors:
        #     inventory._draw_infra_san_neighbors.save_image(output_directory=directory, format=export_format)
        # if inventory._draw_infra_lan_neighbors:
        #     inventory._draw_infra_lan_neighbors.save_image(output_directory=directory, format=export_format)
        # if inventory._draw_infra_rack_service_profiles:
        #     for infra in inventory._draw_infra_rack_service_profiles:
        #         infra.save_image(output_directory=directory, format=export_format)
        # if inventory._draw_infra_chassis_service_profiles:
        #     for infra in inventory._draw_infra_chassis_service_profiles:
        #         infra.save_image(output_directory=directory, format=export_format)
        # if inventory._draw_infra_rack_enclosure_service_profiles:
        #     for infra in inventory._draw_infra_rack_enclosure_service_profiles:
        #         infra.save_image(output_directory=directory, format=export_format)

        return True

    def fetch_inventory(self, force=False):
        self.logger(message="Fetching inventory from live device (can take several minutes)")
        inventory = IntersightInventory(parent=self)
        inventory.metadata.origin = "live"
        inventory.metadata.easyucs_version = __version__
        inventory.load_from = "live"
        inventory._fetch_sdk_objects(force=force)

        # If any of the mandatory task steps fails then return None
        from api.api_server import easyucs
        if easyucs and self.parent.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.parent.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more SDK objects. Stopping the inventory fetch.")
            return None

        self.logger(level="debug", message="Finished fetching Intersight SDK objects for inventory")

        for asset_device_registration in inventory.sdk_objects.get("asset_device_registration", []):
            if asset_device_registration.platform_type == "UCSFI":
                # We are working with a UCS Manager domain claimed on this Intersight account
                for top_system in inventory.sdk_objects.get("top_system", []):
                    if top_system.registered_device.moid == asset_device_registration.moid:
                        inventory.ucsm_domains.append(IntersightUcsmDomain(parent=inventory, top_system=top_system))

            elif asset_device_registration.platform_type == "UCSFIISM":
                # We are working with an IMM domain claimed on this Intersight account
                inventory.imm_domains.append(IntersightImmDomain(parent=inventory,
                                                                 asset_device_registration=asset_device_registration))

            elif asset_device_registration.platform_type in ["IMC", "IMCM4", "IMCM5", "IMCRack"] and \
                    not asset_device_registration.parent_connection:
                # We are working with a standalone rack server (CIMC) (no parent connection to a UCS domain)
                for compute_rack_unit in inventory.sdk_objects.get("compute_rack_unit", []):
                    if compute_rack_unit.registered_device.moid == asset_device_registration.moid:
                        inventory.rack_units.append(IntersightComputeRackUnit(parent=inventory,
                                                                              compute_rack_unit=compute_rack_unit))

            # We sort the list of UCSM domains to return objects in an appropriate order
            inventory.ucsm_domains = sorted(inventory.ucsm_domains,
                                            key=lambda x: x.name if getattr(x, "name", None) else 0)

            # We sort the list of IMM domains to return objects in an appropriate order
            inventory.imm_domains = sorted(inventory.imm_domains,
                                           key=lambda x: x.name if getattr(x, "name", None) else 0)

            # We sort the list of rack servers to return objects in an appropriate order
            inventory.rack_units = sorted(inventory.rack_units,
                                          key=lambda x: x.name if getattr(x, "name", None) else 0)

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

        if "imm_domains" in inventory_json:
            for imm_domain in inventory_json["imm_domains"]:
                inventory.imm_domains.append(IntersightImmDomain(parent=inventory, asset_device_registration=imm_domain))

        if "rack_units" in inventory_json:
            for rack_unit in inventory_json["rack_units"]:
                inventory.rack_units.append(IntersightComputeRackUnit(parent=inventory, compute_rack_unit=rack_unit))

        if "ucsm_domains" in inventory_json:
            for ucsm_domain in inventory_json["ucsm_domains"]:
                inventory.ucsm_domains.append(IntersightUcsmDomain(parent=inventory, top_system=ucsm_domain))

        return True
