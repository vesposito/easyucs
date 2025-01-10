# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """

import re

from inventory.object import GenericInventoryObject


class IntersightInventoryObject(GenericInventoryObject):
    def __init__(self, parent=None, sdk_object=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self._moid = None
        self._object = sdk_object
        self.tags = None

        if self._inventory.load_from == "live":
            self._moid = self.get_attribute(attribute_name="moid")
            # Uncomment for debug purposes
            # self.moid = self._moid

            if hasattr(self._object, "tags"):
                self.tags = []
                for tag in self._object.tags:
                    if not tag.get("key", "").startswith("cisco.meta"):  # Ignoring system defined tags
                        self.tags.append({"key": tag["key"], "value": tag["value"]})

        elif self._inventory.load_from == "file":
            for attribute in ["tags"]:
                setattr(self, attribute, None)
                if not isinstance(self._object, IntersightInventoryObject):
                    if attribute in self._object:
                        setattr(self, attribute, self.get_attribute(attribute_name=attribute))
                else:
                    if getattr(self._object, attribute, None):
                        setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # We use this to make sure all attributes of a Tag are set to None if they are not present
            if self.tags:
                for tag in self.tags:
                    for attribute in ["key", "value"]:
                        if attribute not in tag:
                            tag[attribute] = None

    def get_attribute(self, attribute_name=None, attribute_secondary_name=None, attribute_type=None):
        # Sanity checking
        if self._inventory.load_from is None:
            self.logger(level="error", message="Attribute 'load_from' in inventory is not set")
            return None
        if self._object is None:
            self.logger(level="error", message="Missing SDK object")
            return None
        if attribute_name is None:
            self.logger(level="error", message="Missing attribute name")
            return None

        result = None

        if self._inventory.load_from == "live":
            # We are working with an Intersight SDK object
            if attribute_name in self._object.attribute_map:
                try:
                    result = getattr(self._object, attribute_name)
                except TypeError:
                    # Workaround for when attribute is an "Unhashable Type"
                    result = self._object._data_store[attribute_name]
            else:
                if attribute_name not in []:  # We don't log for those attributes
                    self.logger(level="debug",
                                message="Attribute " + attribute_name + " does not exist in live Intersight object " +
                                        "of class " + str(self._object.object_type) + " with MOID " + str(self._moid))
                return None

        elif self._inventory.load_from == "file":
            # We are working with a dictionary
            if attribute_secondary_name is not None:
                if attribute_secondary_name in self._object.keys():
                    result = self._object[attribute_secondary_name]
                elif attribute_name in self._object.keys():
                    result = self._object[attribute_name]
                else:
                    if attribute_name not in ["aggregate_port_id"]:  # We don't log for those attributes
                        self.logger(level="debug",
                                    message="Attributes " + attribute_name + " or " + attribute_secondary_name +
                                            " do not exist in inventory file for object of class " +
                                            str(self.__class__.__name__))
                    return None
            else:
                if attribute_name in self._object.keys():
                    result = self._object[attribute_name]
                else:
                    return None

        # We filter "empty" results returned by the API
        if result in ["", "none", "None", "(null)", "::", "N/A"]:
            return None

        # Depending on the type requested, we return the result using the appropriate conversion
        if attribute_type is None:
            return result
        elif attribute_type == "int":
            try:
                return int(result)
            except (ValueError, TypeError):
                return None
        elif attribute_type == "float":
            try:
                return float(result)
            except (ValueError, TypeError):
                return None
        elif attribute_type == "str":
            try:
                return str(result)
            except (ValueError, TypeError):
                return None
        else:
            self.logger(level="debug", message="Attribute " + attribute_name + " requested with unknown type")
            return None

    def get_inventory_objects_from_ref(self, ref=None, object_class=None, parent=None):
        if not ref:
            return []

        moid_dict = {}

        # If ref is a single object, we make it a list for simpler operations
        if not isinstance(ref, list):
            ref = [ref]

        for target_object in ref:
            # We first try to identify if our ref is an object or a manually crafted dict for a specific query
            if isinstance(target_object, dict):
                # We exclude refs that do not contain an ObjectType nor a Moid
                if "object_type" not in target_object.keys() and "moid" not in target_object.keys():
                    continue
                else:
                    object_type = target_object["object_type"]
                    moid = target_object["moid"]

            else:
                # We exclude refs that do not contain an ObjectType nor a Moid
                if not hasattr(target_object, "object_type") and not hasattr(target_object, "moid"):
                    continue
                else:
                    object_type = target_object.object_type
                    moid = target_object.moid

            # We convert the ObjectType value to the naming used in the fetched SDK objects
            # Ex: equipment.Psu is converted to equipment_psu
            sdk_object_type = re.sub(r'(?<!^)(?=[A-Z])', '_', object_type.replace(".", "")).lower()

            if sdk_object_type not in moid_dict.keys():
                moid_dict[sdk_object_type] = []
            moid_dict[sdk_object_type].append(moid)

        filtered_sdk_objects_list = []
        for sdk_object_type, moid_list in moid_dict.items():
            if sdk_object_type in self._inventory.sdk_objects.keys():
                if self._inventory.sdk_objects[sdk_object_type] is not None:
                    for sdk_object in self._inventory.sdk_objects[sdk_object_type]:
                        if sdk_object.moid not in moid_list:
                            continue
                        # Filter objects that have a "presence" attribute set as "missing"
                        if hasattr(sdk_object, "presence") and sdk_object.presence in ["missing", "no"]:
                            continue
                        if object_class and object_class.__name__ in ["IntersightFi"]:
                            # We filter out network.Element objects that don't have a valid switchId
                            if hasattr(sdk_object, "switch_id") and sdk_object.switch_id not in ["A", "B"]:
                                continue
                        if object_class and object_class.__name__ in ["IntersightIom"]:
                            # We filter out UCS Mini/X-Direct as IOMs (will be inventoried as embedded FIs)
                            if hasattr(sdk_object, "model") and sdk_object.model in ["UCS-FI-M-6324",
                                                                                     "UCSX-S9108-100G"]:
                                continue
                        if object_class and object_class.__name__ in ["IntersightStorageController"]:
                            # We filter out FlexFlash controllers as we handle them separately
                            if hasattr(sdk_object, "type") and sdk_object.type in ["FlexFlash"]:
                                continue
                            # We also filter out NVMe controllers as we handle them separately
                            if hasattr(sdk_object, "type") and sdk_object.type in ["Nvme", "NVME"]:
                                continue
                        filtered_sdk_objects_list.append(sdk_object)

        # We sort the list of SDK objects to return objects in an appropriate order
        if filtered_sdk_objects_list:
            # We use "ID" as the default attribute used to sort objects
            sort_attr = "id"

            if object_class:
                if object_class.__name__ == "IntersightMemoryArray":
                    sort_attr = "array_id"
                elif object_class.__name__ == "IntersightChassis":
                    sort_attr = "chassis_id"
                elif object_class.__name__ == "IntersightStorageController":
                    sort_attr = "controller_id"
                elif object_class.__name__ in ["IntersightStorageControllerNvmeDrive", "IntersightStorageLocalDisk"]:
                    sort_attr = "disk_id"
                elif object_class.__name__ == "IntersightAdaptorPort":
                    sort_attr = "ext_eth_interface_id"
                elif object_class.__name__ == "IntersightGpu":
                    sort_attr = "gpu_id"
                elif object_class.__name__ == "IntersightMemoryUnit":
                    sort_attr = "memory_id"
                elif object_class.__name__ in ["IntersightFex", "IntersightIom"]:
                    sort_attr = "module_id"
                elif object_class.__name__ == "IntersightAdaptor":
                    sort_attr = "pci_slot"
                elif object_class.__name__ in ["IntersightFexFabricPort", "IntersightFexHostPort",
                                               "IntersightIomPort"]:
                    sort_attr = "port_id"
                elif object_class.__name__ == "IntersightCpu":
                    sort_attr = "processor_id"
                elif object_class.__name__ == "IntersightPsu":
                    sort_attr = "psu_id"
                elif object_class.__name__ == "IntersightComputeRackUnit":
                    sort_attr = "server_id"
                elif object_class.__name__ == "IntersightComputeBlade":
                    sort_attr = "slot_id"
                elif object_class.__name__ == "IntersightFi":
                    sort_attr = "switch_id"
                elif object_class.__name__ == "IntersightTpm":
                    sort_attr = "tpm_id"

            filtered_sdk_objects_list = sorted(filtered_sdk_objects_list,
                                               key=lambda x: getattr(x, sort_attr, 0) if hasattr(x, sort_attr) else 0)

        if object_class and parent:
            easyucs_objects_list = []
            for sdk_object in filtered_sdk_objects_list:
                # We instantiate an Inventory Object for each corresponding SDK object
                easyucs_objects_list.append(object_class(parent, sdk_object))
            return easyucs_objects_list
        else:
            return filtered_sdk_objects_list

    def _determine_firmware_version(self, source_obj=None, filter_attr="", filter_value=""):
        if not source_obj:
            source_obj = self._object
        # We check if we already have fetched the list of firmware_running_firmware catalog objects
        if "firmware_running_firmware" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["firmware_running_firmware"] is not None:
                # We check if the associated SDK object has a running_firmware attribute
                running_firmware_list = None
                if hasattr(source_obj, "running_firmware") and source_obj.running_firmware:
                    running_firmware_list = self.get_inventory_objects_from_ref(ref=source_obj.running_firmware)
                elif hasattr(source_obj, "ucsm_running_firmware") and source_obj.ucsm_running_firmware:
                    running_firmware_list = self.get_inventory_objects_from_ref(ref=source_obj.ucsm_running_firmware)

                if running_firmware_list:
                    if filter_attr and filter_value:
                        filtered_running_firmware_list = running_firmware_list
                        # We filter the list of firmware objects to only keep those matching the filter criteria
                        for running_firmware in running_firmware_list:
                            if not (hasattr(running_firmware, filter_attr) and filter_value in getattr(running_firmware,
                                                                                                       filter_attr)):
                                filtered_running_firmware_list.remove(running_firmware)
                        running_firmware_list = filtered_running_firmware_list

                    if (len(running_firmware_list)) != 1:
                        self.logger(
                            level="debug",
                            message="Could not find the appropriate running firmware for object of class " +
                                    str(self.__class__.__name__) + " with MOID " + str(self._moid))
                        return None
                    else:
                        # We return the firmware_running_firmware found version value
                        if hasattr(running_firmware_list[0], "version") and running_firmware_list[0].version:
                            return running_firmware_list[0].version
        return None

    def _determine_locator_led_status(self):
        # We check if we already have fetched the list of equipment_locator_led catalog objects
        if "equipment_locator_led" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["equipment_locator_led"] is not None:
                # We check if the associated SDK object has a locator_led attribute
                target_moid = None
                if hasattr(self._object, "locator_led") and self._object.locator_led:
                    target_moid = self._object.locator_led.moid

                # Looking for the matching equipment_locator_led object
                if target_moid:
                    equipment_locator_led_list = [equipment_locator_led for equipment_locator_led in
                                                  self._inventory.sdk_objects["equipment_locator_led"] if
                                                  target_moid == equipment_locator_led.moid]
                    if (len(equipment_locator_led_list)) != 1:
                        self.logger(
                            level="debug",
                            message="Could not find the appropriate locator LED for object of class " +
                                    str(self.__class__.__name__) + " with MOID " + str(self._moid))
                        return None
                    else:
                        # We return the equipment_locator_led found oper_state value
                        if hasattr(equipment_locator_led_list[0], "oper_state"):
                            return equipment_locator_led_list[0].oper_state
        return None
