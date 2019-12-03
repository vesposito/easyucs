# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


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


class GenericUcsInventoryObject(GenericInventoryObject):
    def __init__(self, parent=None, ucs_sdk_object=None):
        self.dn = None
        if ucs_sdk_object is not None:
            if hasattr(ucs_sdk_object, "dn"):
                self.dn = ucs_sdk_object.dn
            self._ucs_sdk_object = ucs_sdk_object
        GenericInventoryObject.__init__(self, parent=parent)

    def _determine_locator_led_status(self):
        # We check if we already have fetched the list of equipmentLocatorLed catalog objects
        if "equipmentLocatorLed" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["equipmentLocatorLed"] is not None:
                # Looking for the matching equipmentLocatorLed object
                equipment_locator_led_list = [equipment_locator_led for equipment_locator_led in
                                              self._inventory.sdk_objects["equipmentLocatorLed"] if
                                              self.dn + "/locator-led" == equipment_locator_led.dn]
                if (len(equipment_locator_led_list)) != 1:
                    # We avoid logging for Storage PCH devices since they don't have an equipmentLocatorLed
                    if "storage-PCH" in self.dn:
                        return None

                    self.logger(
                        level="debug",
                        message="Could not find the appropriate locator LED for object with DN " +
                                str(self.dn) + " of model \"" + str(self.model) + "\"")
                    return None
                else:
                    # We return the equipmentLocatorLed found operState value
                    if hasattr(equipment_locator_led_list[0], "oper_state"):
                        return equipment_locator_led_list[0].oper_state
        return None

    def get_attribute(self, ucs_sdk_object=None, attribute_name=None, attribute_secondary_name=None,
                      attribute_type=None):
        # Sanity checking
        if self._inventory.load_from is None:
            self.logger(level="error", message="Attribute 'load_from' in inventory is not set")
            return None
        if ucs_sdk_object is None:
            self.logger(level="error", message="Missing ucs_sdk_object")
            return None
        if attribute_name is None:
            self.logger(level="error", message="Missing attribute name")
            return None

        result = None

        if self._inventory.load_from is "live":
            # We are working with an UCS SDK object
            if hasattr(ucs_sdk_object, attribute_name):
                result = getattr(ucs_sdk_object, attribute_name)
            else:
                if attribute_name not in ["variant_type", "vid"]:  # We don't log for those attributes
                    self.logger(level="debug",
                                message="Attribute " + attribute_name + " does not exist in live UCS object " + str(
                                    ucs_sdk_object.dn))
                return None

        elif self._inventory.load_from is "file":
            # We are working with a dictionary
            if attribute_secondary_name is not None:
                if attribute_secondary_name in ucs_sdk_object.keys():
                    result = ucs_sdk_object[attribute_secondary_name]
                elif attribute_name in ucs_sdk_object.keys():
                    result = ucs_sdk_object[attribute_name]
                else:
                    if attribute_name not in ["usr_lbl"]:  # We don't log for those attributes
                        self.logger(level="debug",
                                    message="Attributes " + attribute_name + " or " + attribute_secondary_name +
                                            " do not exist in inventory file for object of class " +
                                            str(self.__class__.__name__))
                    return None
            else:
                if attribute_name in ucs_sdk_object.keys():
                    result = ucs_sdk_object[attribute_name]
                else:
                    return None

        # We filter "empty" results returned by the UCS API
        if result in ["", "none", "None", "(null)"]:
            return None

        # Depending on the type requested, we return the result using the appropriate conversion
        if attribute_type is None:
            return result
        elif attribute_type is "int":
            try:
                return int(result)
            except (ValueError, TypeError):
                return None
        elif attribute_type is "float":
            try:
                return float(result)
            except (ValueError, TypeError):
                return None
        elif attribute_type is "str":
            try:
                return str(result)
            except (ValueError, TypeError):
                return None
        else:
            self.logger(level="debug", message="Attribute " + attribute_name + " requested with unknown type")
            return None


class UcsSystemInventoryObject(GenericUcsInventoryObject):
    def __init__(self, parent=None, ucs_sdk_object=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ucs_sdk_object)

        if self._inventory.load_from == "live":
            self._cap_provider = self._find_cap_provider()
            self._equipment_manufacturing_def = self._find_equipment_manufacturing_def()
            self._variant_type = self.get_attribute(ucs_sdk_object=ucs_sdk_object, attribute_name="variant_type")
            self._equipment_fru_variant = self._find_equipment_fru_variant()
            self.firmware_package_version = None
            self.firmware_version = None
            self.name = None
            self.part_number = None
            self.sku = None
            self.vid = self.get_attribute(ucs_sdk_object=ucs_sdk_object, attribute_name="vid")
            self._get_manufacturing_details_from_catalog()
            self._get_firmware_version_running()

        elif self._inventory.load_from == "file" and isinstance(ucs_sdk_object, dict):
            for attribute in ["firmware_package_version", "firmware_version", "name", "part_number", "sku", "vid"]:
                setattr(self, attribute, None)
                if attribute in ucs_sdk_object:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=ucs_sdk_object,
                                                                attribute_name=attribute))

    def _find_cap_provider(self):
        # We check if we already have fetched the list of catalog objects
        if self._inventory.sdk_objects["catalog"] is not None and hasattr(self, "_UCS_SDK_CATALOG_OBJECT_NAME")\
                and hasattr(self, "model") and hasattr(self, "vendor") and hasattr(self, "revision"):
            # We return None if the "model" attribute is None as this probably indicates an improperly discovered object
            if self.model is None:
                return None

            # We trim the list of catalog objects to only those corresponding the current object
            catalog_object_type = self._UCS_SDK_CATALOG_OBJECT_NAME[:1].upper() + self._UCS_SDK_CATALOG_OBJECT_NAME[1:]
            object_cap_provider_list = [object_cap_provider for object_cap_provider
                                        in self._inventory.sdk_objects["catalog"]
                                        if object_cap_provider._class_id == catalog_object_type
                                        and self.model == object_cap_provider.model
                                        and self.vendor == object_cap_provider.vendor
                                        and self.revision == object_cap_provider.revision]

            if len(object_cap_provider_list) == 0:
                # We could not find a single corresponding CapProvider object
                self.logger(level="debug",
                            message="Could not find the appropriate catalog element for object with DN " +
                                    str(self.dn) + " of model \"" + str(self.model) + "\"")
                return None

            if len(object_cap_provider_list) == 1:
                # We have only found one corresponding CapProvider object - Returning it
                return object_cap_provider_list[0]

            if len(object_cap_provider_list) > 1:
                # We still found multiple CapProvider objects corresponding to this object
                self.logger(level="debug",
                            message="Found multiple catalog elements for object with DN " + str(self.dn) +
                                    " of model \"" + str(self.model) + "\"")
                return None

        return None

    def _find_equipment_fru_variant(self):
        # We check if we already have found the CapProvider object
        if self._cap_provider is None:
            return None

        # We check if we have a variant type
        if self._variant_type is None:
            return None

        # We check if we already have fetched the list of equipmentFruVariant catalog objects
        if "equipmentFruVariant" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["equipmentFruVariant"] is not None:
                # We have the CapProvider object - Looking for the matching equipmentFruVariant object
                equipment_fru_variant_list = [equipment_fru_variant for equipment_fru_variant in
                                              self._inventory.sdk_objects["equipmentFruVariant"] if
                                              self._cap_provider.dn in equipment_fru_variant.dn and
                                              equipment_fru_variant.type == self._variant_type]
                if (len(equipment_fru_variant_list)) != 1:
                    # We avoid logging for Storage PCH devices since they don't have an equipmentFruVariant
                    if "storage-PCH" in self.dn:
                        return None
                    if hasattr(self, "model"):
                        if any(x in self.model for x in ["Lewisburg", "Patsburg", "Wellsburg"]):
                            return None

                    self.logger(
                        level="debug",
                        message="Could not find the appropriate catalog FRU variant for object with DN " +
                                str(self.dn) + " of model \"" + str(self.model) + "\"")
                    return None
                else:
                    # We return the equipmentFruVariant found
                    return equipment_fru_variant_list[0]
        return None

    def _find_equipment_manufacturing_def(self):
        # We check if we already have found the CapProvider object
        if self._cap_provider is None:
            return None

        # We check if we already have fetched the list of equipmentManufacturingDef catalog objects
        if "equipmentManufacturingDef" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["equipmentManufacturingDef"] is not None:
                # We have the CapProvider object - Looking for the matching equipmentManufacturingDef object
                equipment_manufacturing_def_list = [equipment_manufacturing_def for equipment_manufacturing_def in
                                                    self._inventory.sdk_objects["equipmentManufacturingDef"] if
                                                    self._cap_provider.dn in equipment_manufacturing_def.dn]
                if (len(equipment_manufacturing_def_list)) != 1:
                    # We avoid logging for Storage PCH devices since they don't have an equipmentManufacturingDef
                    if "storage-PCH" in self.dn:
                        return None
                    if hasattr(self, "model"):
                        if any(x in self.model for x in ["Lewisburg", "Patsburg", "Wellsburg"]):
                            return None

                    self.logger(
                        level="debug",
                        message="Could not find the appropriate catalog manufacturing detail for object with DN " +
                                str(self.dn) + " of model \"" + str(self.model) + "\"")
                    return None
                else:
                    # We return the equipmentManufacturingDef found
                    return equipment_manufacturing_def_list[0]
        return None

    def _get_firmware_version_running(self):
        # We verify that we have the required suffix in the object class
        if not hasattr(self, "_UCS_SDK_FIRMWARE_RUNNING_SUFFIX"):
            return False

        # We check if we already have fetched the list of firmwareRunning objects
        if "firmwareRunning" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["firmwareRunning"] is not None:
                # Looking for the matching firmwareRunning object
                firmware_running_list = [firmware_running for firmware_running in
                                         self._inventory.sdk_objects["firmwareRunning"] if self.dn +
                                         self._UCS_SDK_FIRMWARE_RUNNING_SUFFIX == firmware_running.dn]
                if (len(firmware_running_list)) != 1:
                    return False
                else:
                    # We fetch the object's firmware version
                    if hasattr(firmware_running_list[0], "version"):
                        if firmware_running_list[0].version != "":
                            self.firmware_version = firmware_running_list[0].version

                    # We fetch the object's firmware package version
                    if hasattr(firmware_running_list[0], "package_version"):
                        if firmware_running_list[0].package_version != "":
                            self.firmware_package_version = firmware_running_list[0].package_version
                    return True
        return False

    def _get_manufacturing_details_from_catalog(self):
        # We check if we already have found the equipmentManufacturingDef object
        if self._equipment_manufacturing_def is None:
            return False

        # We fetch the object's name
        if hasattr(self._equipment_manufacturing_def, "name"):
            if self._equipment_manufacturing_def.name != "":
                self.name = self._equipment_manufacturing_def.name

        # We fetch the object's part number
        if hasattr(self._equipment_manufacturing_def, "part_number"):
            if self._equipment_manufacturing_def.part_number != "":
                self.part_number = self._equipment_manufacturing_def.part_number

        if self._equipment_fru_variant is not None:
            # We use the equipmentFruVariant PID for retrieving the object's SKU
            if hasattr(self._equipment_fru_variant, "pid"):
                if self._equipment_fru_variant.pid not in ["", "N/A", "NA"]:
                    self.sku = self._equipment_fru_variant.pid
        else:
            # We fetch the object's SKU or if the field is empty, its PID (if not empty as well)
            if hasattr(self._equipment_manufacturing_def, "sku"):
                if self._equipment_manufacturing_def.sku not in ["", "N/A", "NA"]:
                    self.sku = self._equipment_manufacturing_def.sku
            elif hasattr(self._equipment_manufacturing_def, "pid"):
                if self._equipment_manufacturing_def.pid not in ["", "N/A", "NA"]:
                    self.sku = self._equipment_manufacturing_def.pid

        return True


class UcsImcInventoryObject(GenericUcsInventoryObject):
    def __init__(self, parent=None, ucs_sdk_object=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ucs_sdk_object)

        if self._inventory.load_from == "live":
            self._pid_catalog = self._find_pid_catalog()
            self.sku = self._find_sku_from_catalog()
        elif self._inventory.load_from == "file":
            self.sku = self.get_attribute(ucs_sdk_object=ucs_sdk_object, attribute_name="sku")

    def _find_pid_catalog(self):
        # We check if we already have fetched the list of catalog objects
        if self._inventory.sdk_objects["catalog"] is not None\
                and hasattr(self, "_UCS_SDK_CATALOG_OBJECT_NAME")\
                and hasattr(self, "_UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE")\
                and hasattr(self, "_UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE"):
            # We trim the list of catalog objects to only those corresponding the current object
            catalog_object_type = self._UCS_SDK_CATALOG_OBJECT_NAME[:1].upper() + self._UCS_SDK_CATALOG_OBJECT_NAME[1:]
            sdk_object_identify_attribute = getattr(self, self._UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE)

            if sdk_object_identify_attribute is None:
                return None

            # Workaround for HBA slot naming inconsistency: SLOT-HBA vs HBA
            if sdk_object_identify_attribute.startswith("SLOT-"):
                sdk_object_identify_attribute = sdk_object_identify_attribute.split("SLOT-")[1]

            object_pid_catalog_list = [object_pid_catalog for object_pid_catalog
                                       in self._inventory.sdk_objects["catalog"]
                                       if object_pid_catalog._class_id == catalog_object_type
                                       and sdk_object_identify_attribute ==
                                       getattr(object_pid_catalog, self._UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE)
                                       and object_pid_catalog.dn.split("board")[0] in self.dn]

            if len(object_pid_catalog_list) == 0:
                # We could not find a single corresponding PidCatalog object
                self.logger(level="debug",
                            message="Could not find the appropriate catalog element for object with DN " + str(self.dn)
                                    + " of model \"" + str(self.model) + "\"")
                return None

            if len(object_pid_catalog_list) == 1:
                # We have only found one corresponding PidCatalog object - Returning it
                return object_pid_catalog_list[0]

            if len(object_pid_catalog_list) > 1:
                # We still found multiple PidCatalog objects corresponding to this object
                self.logger(level="debug",
                            message="Found multiple catalog elements for object with DN " + str(self.dn) +
                                    " of model \"" + str(self.model))
                return None

        return None

    def _find_sku_from_catalog(self):
        # We check if we already have found the PidCatalog object
        if self._pid_catalog is None:
            return None
        else:
            if hasattr(self._pid_catalog, "pid"):
                if self._pid_catalog.pid not in ["N/A", "UNKNOWN"]:
                    return self._pid_catalog.pid


class UcsCentralInventoryObject(GenericUcsInventoryObject):
    def __init__(self, parent=None, ucs_sdk_object=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ucs_sdk_object)

        if self._inventory.load_from == "live":
            self._cap_provider = self._find_cap_provider()
            self._equipment_manufacturing_def = self._find_equipment_manufacturing_def()
            self._variant_type = self.get_attribute(ucs_sdk_object=ucs_sdk_object, attribute_name="variant_type")
            self._equipment_fru_variant = self._find_equipment_fru_variant()
            self.firmware_package_version = None
            self.firmware_version = None
            self.name = None
            self.part_number = None
            self.sku = None
            self.vid = self.get_attribute(ucs_sdk_object=ucs_sdk_object, attribute_name="vid")
            self._get_manufacturing_details_from_catalog()
            self._get_firmware_version_running()

        elif self._inventory.load_from == "file" and isinstance(ucs_sdk_object, dict):
            for attribute in ["firmware_package_version", "firmware_version", "name", "part_number", "sku", "vid"]:
                setattr(self, attribute, None)
                if attribute in ucs_sdk_object:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=ucs_sdk_object,
                                                                attribute_name=attribute))

    def _find_cap_provider(self):
        # We check if we already have fetched the list of catalog objects
        if self._inventory.sdk_objects["catalog"] is not None and hasattr(self, "_UCS_SDK_CATALOG_OBJECT_NAME")\
                and hasattr(self, "model") and hasattr(self, "vendor") and hasattr(self, "revision"):
            # We return None if the "model" attribute is None as this probably indicates an improperly discovered object
            if self.model is None:
                return None

            # We trim the list of catalog objects to only those corresponding the current object
            catalog_object_type = self._UCS_SDK_CATALOG_OBJECT_NAME[:1].upper() + self._UCS_SDK_CATALOG_OBJECT_NAME[1:]
            object_cap_provider_list = [object_cap_provider for object_cap_provider
                                        in self._inventory.sdk_objects["catalog"]
                                        if object_cap_provider._class_id == catalog_object_type
                                        and self.model == object_cap_provider.model
                                        and self.vendor == object_cap_provider.vendor
                                        and self.revision == object_cap_provider.revision]

            if len(object_cap_provider_list) == 0:
                # We could not find a single corresponding CapProvider object
                self.logger(level="debug",
                            message="Could not find the appropriate catalog element for object with DN " +
                                    str(self.dn) + " of model \"" + str(self.model) + "\"")
                return None

            if len(object_cap_provider_list) == 1:
                # We have only found one corresponding CapProvider object - Returning it
                return object_cap_provider_list[0]

            if len(object_cap_provider_list) > 1:
                # We still found multiple CapProvider objects corresponding to this object
                self.logger(level="debug",
                            message="Found multiple catalog elements for object with DN " + str(self.dn) +
                                    " of model \"" + str(self.model) + "\"")
                return None

        return None

    def _find_equipment_fru_variant(self):
        # We check if we already have found the CapProvider object
        if self._cap_provider is None:
            return None

        # We check if we have a variant type
        if self._variant_type is None:
            return None

        # We check if we already have fetched the list of equipmentFruVariant catalog objects
        if "equipmentFruVariant" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["equipmentFruVariant"] is not None:
                # We have the CapProvider object - Looking for the matching equipmentFruVariant object
                equipment_fru_variant_list = [equipment_fru_variant for equipment_fru_variant in
                                              self._inventory.sdk_objects["equipmentFruVariant"] if
                                              self._cap_provider.dn in equipment_fru_variant.dn and
                                              equipment_fru_variant.type == self._variant_type]
                if (len(equipment_fru_variant_list)) != 1:
                    # We avoid logging for Storage PCH devices since they don't have an equipmentFruVariant
                    if "storage-PCH" in self.dn:
                        return None
                    if hasattr(self, "model"):
                        if any(x in self.model for x in ["Lewisburg", "Patsburg", "Wellsburg"]):
                            return None

                    self.logger(
                        level="debug",
                        message="Could not find the appropriate catalog FRU variant for object with DN " +
                                str(self.dn) + " of model \"" + str(self.model) + "\"")
                    return None
                else:
                    # We return the equipmentFruVariant found
                    return equipment_fru_variant_list[0]
        return None

    def _find_equipment_manufacturing_def(self):
        # We check if we already have found the CapProvider object
        if self._cap_provider is None:
            return None

        # We check if we already have fetched the list of equipmentManufacturingDef catalog objects
        if "equipmentManufacturingDef" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["equipmentManufacturingDef"] is not None:
                # We have the CapProvider object - Looking for the matching equipmentManufacturingDef object
                equipment_manufacturing_def_list = [equipment_manufacturing_def for equipment_manufacturing_def in
                                                    self._inventory.sdk_objects["equipmentManufacturingDef"] if
                                                    self._cap_provider.dn in equipment_manufacturing_def.dn]
                if (len(equipment_manufacturing_def_list)) != 1:
                    # We avoid logging for Storage PCH devices since they don't have an equipmentManufacturingDef
                    if "storage-PCH" in self.dn:
                        return None
                    if hasattr(self, "model"):
                        if any(x in self.model for x in ["Lewisburg", "Patsburg", "Wellsburg"]):
                            return None

                    self.logger(
                        level="debug",
                        message="Could not find the appropriate catalog manufacturing detail for object with DN " +
                                str(self.dn) + " of model \"" + str(self.model) + "\"")
                    return None
                else:
                    # We return the equipmentManufacturingDef found
                    return equipment_manufacturing_def_list[0]
        return None

    def _get_firmware_version_running(self):
        # We verify that we have the required suffix in the object class
        if not hasattr(self, "_UCS_SDK_FIRMWARE_RUNNING_SUFFIX"):
            return False

        # We check if we already have fetched the list of firmwareRunning objects
        if "firmwareRunning" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["firmwareRunning"] is not None:
                # Looking for the matching firmwareRunning object
                firmware_running_list = [firmware_running for firmware_running in
                                         self._inventory.sdk_objects["firmwareRunning"] if self.dn +
                                         self._UCS_SDK_FIRMWARE_RUNNING_SUFFIX == firmware_running.dn]
                if (len(firmware_running_list)) != 1:
                    return False
                else:
                    # We fetch the object's firmware version
                    if hasattr(firmware_running_list[0], "version"):
                        if firmware_running_list[0].version != "":
                            self.firmware_version = firmware_running_list[0].version

                    # We fetch the object's firmware package version
                    if hasattr(firmware_running_list[0], "package_version"):
                        if firmware_running_list[0].package_version != "":
                            self.firmware_package_version = firmware_running_list[0].package_version
                    return True
        return False

    def _get_manufacturing_details_from_catalog(self):
        # We check if we already have found the equipmentManufacturingDef object
        if self._equipment_manufacturing_def is None:
            return False

        # We fetch the object's name
        if hasattr(self._equipment_manufacturing_def, "name"):
            if self._equipment_manufacturing_def.name != "":
                self.name = self._equipment_manufacturing_def.name

        # We fetch the object's part number
        if hasattr(self._equipment_manufacturing_def, "part_number"):
            if self._equipment_manufacturing_def.part_number != "":
                self.part_number = self._equipment_manufacturing_def.part_number

        if self._equipment_fru_variant is not None:
            # We use the equipmentFruVariant PID for retrieving the object's SKU
            if hasattr(self._equipment_fru_variant, "pid"):
                if self._equipment_fru_variant.pid not in ["", "N/A", "NA"]:
                    self.sku = self._equipment_fru_variant.pid
        else:
            # We fetch the object's SKU or if the field is empty, its PID (if not empty as well)
            if hasattr(self._equipment_manufacturing_def, "sku"):
                if self._equipment_manufacturing_def.sku not in ["", "N/A", "NA"]:
                    self.sku = self._equipment_manufacturing_def.sku
            elif hasattr(self._equipment_manufacturing_def, "pid"):
                if self._equipment_manufacturing_def.pid not in ["", "N/A", "NA"]:
                    self.sku = self._equipment_manufacturing_def.pid

        return True
