# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """
from common import read_json_file
from draw.ucs.chassis import UcsChassisDrawFront, UcsChassisDrawRear
from inventory.object import GenericInventoryObject


class GenericChassis(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.imm_compatible = None
        self.short_name = None
        self.sku = None
        self.slots_free_full = None
        self.slots_free_half = None
        self.slots_max = None
        self.slots_populated = None

    def _calculate_chassis_slots_free_full(self):
        if self.slots_max is None:
            return None

        slots_used = []
        if hasattr(self, "blades"):
            for blade in self.blades:
                if not hasattr(blade, "slot_id"):
                    return None
                slots_used.append(int(blade.slot_id))

                # We handle the specific case of a B460 M4 for which we also use the 2 slots above the master blade
                if hasattr(blade, "scaled_mode"):
                    if blade.scaled_mode == "scaled":
                        slots_used.extend([int(blade.slot_id) - 1, int(blade.slot_id) - 2])

        elif hasattr(self, "server_nodes"):
            # Used for standalone S3260 chassis
            for server_node in self.server_nodes:
                if not hasattr(server_node, "id"):
                    return None
                slots_used.append(int(server_node.id))

        slots_free_full = [slot_even for slot_even in range(1, self.slots_max + 1, 2) if slot_even not in slots_used
                           and slot_even + 1 not in slots_used]
        return len(slots_free_full)

    def _calculate_chassis_slots_free_half(self):
        if self.slots_max is None or self.slots_populated is None:
            return None
        return self.slots_max - self.slots_populated

    def _calculate_chassis_slots_populated(self):
        if not hasattr(self, "sku"):
            return None
        if self.sku is None:
            return None

        # We use the catalog file to get the blades widths
        chassis_catalog = read_json_file(file_path="catalog/chassis/" + self.sku + ".json", logger=self)
        if not chassis_catalog:
            self.logger(level="warning", message="Could not calculate populated slots")
            return None

        if "blades_models" not in chassis_catalog:
            self.logger(level="warning",
                        message="Chassis catalog file " + self.sku +
                                ".json has no section \"blades_models\". Could not calculate populated slots.")
            return None

        slots_populated = 0
        if hasattr(self, "blades"):
            for blade in self.blades:
                if not hasattr(blade, "sku"):
                    return None
                for blade_model in chassis_catalog["blades_models"]:
                    if "name" not in blade_model or "width" not in blade_model:
                        self.logger(level="warning",
                                    message="Chassis catalog file " + self.sku + ".json section \"blades_models\"" +
                                            " is incomplete. Could not calculate populated slots.")
                        return None
                    if blade_model["name"] == blade.sku:
                        # We handle the specific case of a B460 M4
                        if hasattr(blade, "scaled_mode"):
                            if blade.scaled_mode == "scaled":
                                slots_populated += 4
                                continue
                        if blade_model["width"] == "half":
                            slots_populated += 1
                        elif blade_model["width"] == "full":
                            slots_populated += 2
                        else:
                            self.logger(level="warning",
                                        message="Chassis catalog file " + self.sku + ".json section \"blades_models\"" +
                                                " is incorrect. Could not calculate populated slots.")
                            return None

        if hasattr(self, "server_nodes"):
            for server_node in self.server_nodes:
                if not hasattr(server_node, "sku"):
                    return None
                for blade_model in chassis_catalog["blades_models"]:
                    if "name" not in blade_model or "width" not in blade_model:
                        self.logger(level="warning",
                                    message="Chassis catalog file " + self.sku + ".json section \"blades_models\"" +
                                            " is incomplete. Could not calculate populated slots.")
                        return None
                    if blade_model["name"] == server_node.sku:
                        if blade_model["width"] == "half":
                            slots_populated += 1
                        elif blade_model["width"] == "full":
                            slots_populated += 2
                        else:
                            self.logger(level="warning",
                                        message="Chassis catalog file " + self.sku + ".json section \"blades_models\"" +
                                                " is incorrect. Could not calculate populated slots.")
                            return None

        return slots_populated

    def _generate_draw(self):
        self._draw_front = UcsChassisDrawFront(parent=self)
        self._draw_rear = UcsChassisDrawRear(parent=self)
        self._draw_infra = None

    def _get_chassis_slots_max(self):
        if not hasattr(self, "sku"):
            return None
        if self.sku is None:
            return None

        # We use the catalog file to get the number of slots in the chassis
        chassis_catalog = read_json_file(file_path="catalog/chassis/" + self.sku + ".json", logger=self)
        if not chassis_catalog:
            self.logger(level="warning", message="Could not determine max slots")
            return None

        if "blades_slots" in chassis_catalog:
            return len(chassis_catalog["blades_slots"])
        elif "blades_slots_rear" in chassis_catalog:
            return len(chassis_catalog["blades_slots_rear"])
        return None

    def _get_imm_compatibility(self):
        """
        Returns Chassis IMM Compatibility status from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the chassis IMM Compatibility status
            chassis_catalog = read_json_file(file_path="catalog/chassis/" + self.sku + ".json", logger=self)
            if chassis_catalog:
                if "imm_compatible" in chassis_catalog:
                    return chassis_catalog["imm_compatible"]

        return None

    def _get_model_short_name(self):
        """
        Returns Chassis short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the chassis short name
            chassis_catalog = read_json_file(file_path="catalog/chassis/" + self.sku + ".json", logger=self)
            if chassis_catalog:
                if "model_short_name" in chassis_catalog:
                    return chassis_catalog["model_short_name"]

        return None


class GenericIom(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.imm_compatible = None
        self.short_name = None
        self.sku = None

    def _get_imm_compatibility(self):
        """
        Returns IO Module IMM Compatibility status from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the IO Module IMM Compatibility status
            iom_catalog = read_json_file(file_path="catalog/io_modules/" + self.sku + ".json", logger=self)
            if iom_catalog:
                if "imm_compatible" in iom_catalog:
                    return iom_catalog["imm_compatible"]

        return None

    def _get_model_short_name(self):
        """
        Returns IO Module short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the IO Module short name
            iom_catalog = read_json_file(file_path="catalog/io_modules/" + self.sku + ".json", logger=self)
            if iom_catalog:
                if "model_short_name" in iom_catalog:
                    return iom_catalog["model_short_name"]

        return None


class GenericXfm(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.imm_compatible = None
        self.short_name = None
        self.sku = None

    def _get_imm_compatibility(self):
        """
        Returns X-Fabric Module IMM Compatibility status from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the X-Fabric Module IMM Compatibility status
            xfm_catalog = read_json_file(file_path="catalog/x_fabric_modules/" + self.sku + ".json", logger=self)
            if xfm_catalog:
                if "imm_compatible" in xfm_catalog:
                    return xfm_catalog["imm_compatible"]

        return None

    def _get_model_short_name(self):
        """
        Returns X-Fabric Module short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the X-Fabric Module short name
            xfm_catalog = read_json_file(file_path="catalog/x_fabric_modules/" + self.sku + ".json", logger=self)
            if xfm_catalog:
                if "model_short_name" in xfm_catalog:
                    return xfm_catalog["model_short_name"]

        return None
