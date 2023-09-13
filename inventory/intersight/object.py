# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """

import re

from inventory.object import GenericInventoryObject


class IntersightInventoryObject(GenericInventoryObject):
    def __init__(self, parent=None, sdk_object=None):
        GenericInventoryObject.__init__(self, parent=parent)
        self._object = sdk_object

        self._moid = None

        if self._inventory.load_from == "live":
            self._moid = self.get_attribute(attribute_name="moid")

            # Uncomment for debug purposes
            # self.moid = self._moid

        elif self._inventory.load_from == "file":
            for attribute in []:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

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
                    if attribute_name not in []:  # We don't log for those attributes
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
        if result in ["", "none", "None", "(null)", "::"]:
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
        if not ref or not object_class or not parent:
            return []

        moid_dict = {}

        # If ref is a single object, we make it a list for simpler operations
        if not isinstance(ref, list):
            ref = [ref]

        for target_object in ref:
            # We first try to identify if our ref is an object or a manually crafted dict for a specific query
            if isinstance(target_object, dict):
                # We exclude refs that do not contain an ObjectType nor an Moid
                if "object_type" not in target_object.keys() and "moid" not in target_object.keys():
                    continue
                else:
                    object_type = target_object["object_type"]
                    moid = target_object["moid"]

            else:
                # We exclude refs that do not contain an ObjectType nor an Moid
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
                        # Filter objects that have a "presence" attribute set as "missing"
                        if hasattr(sdk_object, "presence") and sdk_object.presence == "missing":
                            continue
                        if sdk_object.moid in moid_list:
                            filtered_sdk_objects_list.append(sdk_object)

        easyucs_objects_list = []
        for sdk_object in filtered_sdk_objects_list:
            # We instantiate an Inventory Object for each corresponding SDK object
            easyucs_objects_list.append(object_class(parent, sdk_object))
        return easyucs_objects_list

    def _determine_locator_led_status(self):
        # We check if we already have fetched the list of equipment_locator_led catalog objects
        if "equipment_locator_led" in self._inventory.sdk_objects.keys():
            if self._inventory.sdk_objects["equipment_locator_led"] is not None:
                # We check if the associated SDK object has a locator_led attribute
                target_moid = None
                if hasattr(self._object, "locator_led"):
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
