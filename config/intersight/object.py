# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """

import copy
import importlib
import json
import re
import uuid

from intersight.exceptions import ApiAttributeError, ApiValueError, ApiTypeError, ApiException, ApiKeyError

from config.object import GenericConfigObject
from config.ucs.object import GenericUcsConfigObject


class IntersightConfigObject(GenericConfigObject):
    def __init__(self, parent=None, sdk_object=None):
        GenericConfigObject.__init__(self, parent=parent)

        self._moid = None
        self._object = sdk_object
        # Set to empty dictionary in cases where user does not provide 'sdk_object' argument. Eg. When copy() and
        # deepcopy() we create an empty objects without a 'sdk_object' argument.
        if not self._object:
            self._object = {}
        self.tags = None

        if self._config.load_from == "live":
            self._moid = self.get_attribute(attribute_name="moid")
            # Uncomment for debug purposes
            # self.moid = self._moid

            if hasattr(self._object, "tags"):
                self.tags = []
                for tag in self._object.tags:
                    if not tag.get("key", "").startswith("cisco.meta"):  # Ignoring system defined tags
                        self.tags.append({"key": tag["key"], "value": tag["value"]})

        elif self._config.load_from == "file":
            for attribute in ["tags"]:
                setattr(self, attribute, None)
                if not isinstance(self._object, IntersightConfigObject):
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

    def commit(self, object_type="", payload="", detail="", show=True, return_relationship=False, modify_present=False,
               key_attributes=["name"], retry=True):
        """
        Commits (either creates or updates) the object with associated payload.
        :param object_type: The type of object to be committed. Used for loading the appropriate modules from SDK
        :param payload: The attributes of the object to be committed
        :param detail: Extra detail to display for the logger method
        :param show: Whether logging should be shown
        :param return_relationship: If the commit should return the equivalent Relationship object or the real one
        :param modify_present: Whether the commit should overwrite existing object attributes
        :param key_attributes: Attributes used to uniquely identify the object when searching for an existing object
        :param retry: A flag to retry if create or update API fails
        :return: The newly created object if successful, False otherwise
        """
        if not object_type:
            err_message = "An object_type must be provided for the commit"
            self.logger(level="error", message=err_message)
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=object_type,
                                                                status="failed", message=err_message)
            return False
        if not payload:
            err_message = "A payload must be provided for the commit"
            self.logger(level="error", message=err_message)
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=object_type,
                                                                status="failed", message=err_message)
            return False

        if getattr(self._config, "update_existing_intersight_objects", False):
            modify_present = True

        sdk_object_type = ""

        try:
            # We first need to decompose the object type to use the appropriate API
            api_prefix = object_type.split(".")[0]

            # We dynamically import the intersight module that we need for talking to the API
            api_module = importlib.import_module('intersight.api.' + api_prefix + '_api')
            api_class = getattr(api_module, api_prefix.title() + 'Api')
            api_instance = api_class(self._device.handle)

            # We also decompose the object type to get the name of the API call we need to make
            sdk_object_type = re.sub(r'(?<!^)(?=[A-Z])', '_', object_type.replace(".", "")).lower()

            # We first query the API to see if an object with the same key attributes already exists (in the same org)
            update_existing = False
            existing_object = None
            existing_object_moid = None
            message_str = ""
            all_key_attributes_present = True
            for key_attribute in key_attributes:
                if not hasattr(payload, key_attribute):
                    all_key_attributes_present = False
            if all_key_attributes_present:
                # We first need to capitalize the key attributes for the filter string (e.g. port_id --> PortId)
                key_attributes_dict = {}
                for key_attribute in key_attributes:
                    key_attributes_dict[key_attribute] = key_attribute.title().replace("_", "")
                filter_str = ""
                for key_attribute in key_attributes_dict.keys():
                    attribute = getattr(payload, key_attribute)
                    if attribute.__class__.__name__ in ["MoMoRef"]:
                        # We are facing a key attribute that is a reference to an object like fabric.PortPolicy
                        # or vnic.LanConnectivityPolicy. We will use the Moid of that reference as a key
                        # attribute. To do this, we add it to the filter string (like "PortPolicy/Moid eq ...")
                        filter_str += attribute.object_type.split(".")[-1] + "/Moid eq '" + \
                            str(attribute.moid) + "' and "
                    elif isinstance(getattr(payload, key_attribute), int):
                        filter_str += key_attributes_dict[key_attribute] + " eq " + str(attribute) + " and "
                    else:
                        filter_str += key_attributes_dict[key_attribute] + " eq '" + str(attribute) + "' and "
                if hasattr(payload, "organization"):
                    filter_str += "Organization/Moid eq '" + payload.organization.moid + "'"
                else:
                    if filter_str[-5:] == " and ":
                        filter_str = filter_str[:-5]
                existing_objects = self._device.query(object_type=object_type, filter=filter_str)
                if existing_objects:
                    if len(existing_objects) == 1:
                        message_str = ""
                        for key_attribute in key_attributes:
                            attribute = getattr(payload, key_attribute)
                            if attribute.__class__.__name__ in ["MoMoRef"]:
                                message_str += attribute.object_type.split(".")[-1] + ".Moid='" + \
                                    str(attribute.moid) + "' and "
                            else:
                                message_str += key_attribute + "='" + str(attribute) + "' and "
                        if message_str[-5:] == " and ":
                            message_str = message_str[:-5]

                        self.logger(level="debug",
                                    message="Object of type " + object_type + " with " + message_str +
                                            " already exists (Moid " + existing_objects[0].moid + ").")

                        if hasattr(existing_objects[0], "moid"):
                            existing_object = existing_objects[0]
                            existing_object_moid = existing_objects[0].moid
                        if modify_present:
                            update_existing = True

                        # TODO: Handle special cases like sending modifications that cascade dependencies
                        # Or we could skip modifying this object and log an error

                    else:
                        # We found multiple objects with the filter, or something wrong happened.
                        message_str = ""
                        for key_attribute in key_attributes:
                            attribute = getattr(payload, key_attribute)
                            if attribute.__class__.__name__ in ["MoMoRef"]:
                                message_str += attribute.object_type.split(".")[-1] + ".Moid='" + \
                                    str(attribute.moid) + "' and "
                            message_str += key_attribute + "='" + str(attribute) + "' and "
                        if message_str[-5:] == " and ":
                            message_str = message_str[:-5]
                        err_message = "Unable to uniquely identify an existing object of type " + object_type + \
                                      " with " + message_str + ". Skipping update."
                        self.logger(level="warning",
                                    message=err_message)
                        self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail,
                                                                            obj_type=object_type, status="failed",
                                                                            message=err_message)
                        return False

            if update_existing:
                if existing_object_moid:
                    # We update the existing object
                    self.logger(level="info",
                                message=f"Updating existing object of type {object_type} with {message_str} using "
                                        f"the values from config.")
                    if sdk_object_type == "iam_account":
                        # Handling "iam_account" with PATCH due to a backend issue preventing use of POST call
                        result = getattr(api_instance, "patch_" + sdk_object_type)(existing_object_moid, payload)
                    else:
                        result = getattr(api_instance, "update_" + sdk_object_type)(existing_object_moid, payload)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=detail, obj_type=object_type, status="success")
                else:
                    err_message = "Unable to identify existing object MOID. Skipping update."
                    self.logger(level="warning", message=err_message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=detail, obj_type=object_type, status="failed", message=err_message)
                    return False
            else:
                if existing_object_moid:
                    message = f"Skipping push of object type {object_type} with {message_str} as it already exists"
                    self.logger(level="info",
                                message=message)
                    result = existing_object
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=detail, obj_type=object_type, status="skipped", message=message)
                else:
                    # We do a simple create operation
                    result = getattr(api_instance, "create_" + sdk_object_type)(payload)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=detail, obj_type=object_type, status="success")

            if result:
                if show:
                    if detail:
                        self.logger(level="debug",
                                    message="Successfully configured " + self._CONFIG_NAME + " - " + detail)
                    else:
                        self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME)

                if return_relationship:
                    relationship_object = self.create_relationship_equivalent(sdk_object=result)
                    if relationship_object:
                        result = relationship_object

                return result
            else:
                if show:
                    if detail:
                        err_message = "Error in configuring " + self._CONFIG_NAME + " - " + detail
                        self.logger(level="debug", message=err_message)
                    else:
                        err_message = "Error in configuring " + self._CONFIG_NAME
                        self.logger(level="debug", message=err_message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=detail, obj_type=object_type, status="failed", message=err_message)
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=detail, obj_type=object_type, status="failed")
                return False

        except (ApiValueError, ApiTypeError, ApiException) as err:
            error_message = str(err)
            # We try to simplify the error message displayed
            if hasattr(err, "body"):
                try:
                    err_json = json.loads(err.body)
                    if "messageId" in err_json and err_json["messageId"] == "malibu_pool_unsupported_update":
                        err_message = f"Pool {self.name} does not support this update operation."
                        self.logger(level="debug", message=err_message)
                        self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail,
                                                                            obj_type=object_type, status="failed",
                                                                            message=err_message)
                        return False
                    if "message" in err_json:
                        error_message = str(err_json["message"])
                except json.decoder.JSONDecodeError as err_json_decode:
                    self.logger(level="error", message="JSON Decode error while fetching objects of class " +
                                                       sdk_object_type + ": " + str(err_json_decode))

            if show:
                if detail:
                    err_message = "Server Error in configuring " + self._CONFIG_NAME + " - " + detail + ": " + \
                                  error_message
                    self.logger(level="error", message=err_message)
                else:
                    err_message = "Server Error in configuring " + self._CONFIG_NAME + ": " + error_message
                    self.logger(level="error", message=err_message)
                self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=object_type,
                                                                    status="failed", message=err_message)
            else:
                self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=object_type,
                                                                    status="failed")

        except AttributeError:
            if show:
                if detail:
                    err_message = "Error in configuring " + self._CONFIG_NAME + " - " + detail + \
                                  ": Unable to execute API call create_" + sdk_object_type
                    self.logger(level="error", message=err_message)
                else:
                    err_message = "Error in configuring " + self._CONFIG_NAME + \
                                  ": Unable to execute API call create_" + sdk_object_type
                    self.logger(level="error", message=err_message)
                self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=object_type,
                                                                    status="failed", message=err_message)
            else:
                self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=object_type,
                                                                    status="failed")

        except Exception as err:
            if show:
                if detail:
                    err_message = "Unknown error in configuring " + self._CONFIG_NAME + " - " + detail + ": " + str(err)
                    self.logger(level="error", message=err_message)
                else:
                    err_message = "Unknown error in configuring " + self._CONFIG_NAME + ": " + str(err)
                    self.logger(level="error", message=err_message)
                self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=object_type,
                                                                    status="failed", message=err_message)
            else:
                self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=object_type,
                                                                    status="failed")

        if retry:
            if detail:
                self.logger(level="info", message="Retrying to commit " + self._CONFIG_NAME + " - " + detail)
            else:
                self.logger(level="info", message="Retrying to commit " + self._CONFIG_NAME)
            return self.commit(object_type=object_type, payload=payload, detail=detail, show=show,
                               return_relationship=return_relationship, modify_present=modify_present,
                               key_attributes=key_attributes, retry=False)

        return False

    def create_relationship_equivalent(self, sdk_object=None):
        """
        Creates the Relationship object equivalent to the SDK object provided (used for referencing)
        (e.g. organization.OrganizationRelationship for an organization.Organization SDK object)
        :param sdk_object: The SDK object to create the Relationship equivalent object for
        :return: The Relationship object created if successful, None otherwise
        """
        if not sdk_object:
            self.logger(level="error", message="An sdk_object must be provided")
            return None

        # We first need to determine the object type of the SDK object provided
        if hasattr(sdk_object, "object_type"):
            object_type = sdk_object.object_type
        else:
            self.logger(level="error", message="Could not determine the object type for SDK object provided")
            return None

        from intersight.model.mo_mo_ref import MoMoRef
        mo_mo_ref = MoMoRef(moid=sdk_object.moid, class_id='mo.MoRef', object_type=object_type)
        return mo_mo_ref

    def create_tags(self):
        """
        Creates MoTags based on tags attributes of the current object
        :return: List of MoTags if successful, None otherwise
        """
        if self.tags is not None:
            from intersight.model.mo_tag import MoTag
            tag_list = []
            dup_check = []
            for tag in self.tags:
                kwargs = {}
                if tag["key"] is not None:
                    if tag["key"] not in dup_check:
                        kwargs["key"] = tag["key"]
                        dup_check.append(tag['key'])
                    else:
                        self.logger(
                            level="warning",
                            message=f"Skipping the tag key '{tag['key']}' of {self._CONFIG_NAME} - {self.name}, "
                            f"as it is not possible to have duplicate tag keys.")

                        continue
                if tag["value"] is not None:
                    kwargs["value"] = tag["value"]

                tag_list.append(MoTag(**kwargs))
            del dup_check
            return tag_list

        return None

    def get_attribute(self, attribute_name=None, attribute_secondary_name=None, attribute_type=None):
        """
        Get an attribute of the object stored in self._object
        :param attribute_name: Name of the attribute to get
        :param attribute_secondary_name: Other possible name of the attribute to get
        :param attribute_type: Type of the attribute to be returned. Can be either None, int, float or str
        :return: The requested attribute if successful, None otherwise
        """
        # Sanity checking
        if self._config.load_from is None:
            self.logger(level="error", message="Attribute 'load_from' in config is not set")
            return None
        if self._object is None:
            self.logger(level="error", message="Missing SDK object")
            return None
        if attribute_name is None:
            self.logger(level="error", message="Missing attribute name")
            return None

        result = None

        if self._config.load_from == "live":
            # We are working with an Intersight SDK object
            if attribute_name in self._object.attribute_map:
                try:
                    result = getattr(self._object, attribute_name)
                except TypeError:
                    # Workaround for when attribute is an "Unhashable Type"
                    result = self._object._data_store[attribute_name]
                except (ApiAttributeError, ApiKeyError):
                    return None
            else:
                if attribute_name not in []:  # We don't log for those attributes
                    self.logger(level="debug",
                                message="Attribute " + attribute_name + " does not exist in live Intersight object " +
                                        "of class " + str(self._object.object_type) + " with MOID " + str(self._moid))
                return None

        elif isinstance(self._object, IntersightConfigObject):
            # We are working with a copy of an EasyUCS object (used for conversion to handle policies in other orgs)
            if attribute_secondary_name is not None:
                if hasattr(self._object, attribute_secondary_name):
                    result = getattr(self._object, attribute_secondary_name)
                elif hasattr(self._object, attribute_name):
                    result = getattr(self._object, attribute_name)
                else:
                    if attribute_name not in ["description"]:  # We don't log for those attributes
                        self.logger(level="debug",
                                    message="Attributes " + attribute_name + " or " + attribute_secondary_name +
                                            " do not exist in copy of object of class " +
                                            str(self.__class__.__name__))
                    return None
            else:
                if hasattr(self._object, attribute_name):
                    result = getattr(self._object, attribute_name)
                else:
                    return None

        elif self._config.load_from == "file":
            # We are working with a dictionary
            if attribute_secondary_name is not None:
                if attribute_secondary_name in self._object.keys():
                    result = self._object[attribute_secondary_name]
                elif attribute_name in self._object.keys():
                    result = self._object[attribute_name]
                else:
                    if attribute_name not in ["description"]:  # We don't log for those attributes
                        self.logger(level="debug",
                                    message="Attributes " + attribute_name + " or " + attribute_secondary_name +
                                            " do not exist in config file for object of class " +
                                            str(self.__class__.__name__))
                    return None
            else:
                if attribute_name in self._object.keys():
                    result = self._object[attribute_name]
                else:
                    return None

            if isinstance(result, dict) and "password" not in result and "encrypted_password" in result:
                from api.api_server import easyucs
                if easyucs:
                    decrypted_password = easyucs.repository_manager.cipher_suite.decrypt(
                        bytes(result["encrypted_password"], encoding='utf8')).decode('utf-8')
                    result["password"] = decrypted_password
            elif isinstance(result, list):
                for instance in result:
                    if isinstance(instance, dict) and "password" not in instance and "encrypted_password" in instance:
                        from api.api_server import easyucs
                        if easyucs:
                            decrypted_password = easyucs.repository_manager.cipher_suite.decrypt(
                                bytes(instance["encrypted_password"], encoding='utf8')).decode('utf-8')
                            instance["password"] = decrypted_password

        # We filter "empty" results returned by the API
        if self.__class__.__name__ in ["IntersightBiosPolicy", "IntersightFcZonePolicy"]:
            # We do not clean "None" values in a BIOS Policy because some parameters are using the string "None"
            # We do not clean "None" values in an FC Zone Policy because fc_target_zoning_type parameter is using
            # the string "None"
            if result in ["", "(null)", "::", "0.0.0.0"]:
                return None
        else:
            if result in ["", "none", "None", "NONE", "(null)", "::", "0.0.0.0"]:
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

    def get_config_objects_from_ref(self, ref=None):
        """
        Get SDK objects from a given reference (containing ObjectType & Moid or Name attributes)
        :param ref: Reference of an object or a list of objects to use
        :return: A list of SDK objects if successful, an emtpy list otherwise
        """
        if not ref:
            return []

        moid_dict = {}
        name_dict = {}

        # If ref is a single object, we make it a list for simpler operations
        if not isinstance(ref, list):
            ref = [ref]

        for target_object in ref:
            object_type = ""
            moid = ""
            name = ""
            # We first try to identify if our ref is an object or a manually crafted dict for a specific query
            if isinstance(target_object, dict):
                # We exclude refs that do not contain an ObjectType nor a Moid
                if "object_type" not in target_object.keys() and \
                        ("moid" not in target_object.keys() or "name" not in target_object.keys()):
                    continue
                else:
                    object_type = target_object["object_type"]
                    if "moid" in target_object:
                        moid = target_object["moid"]
                    elif "name" in target_object:
                        name = target_object["name"]

            else:
                # We exclude refs that do not contain an ObjectType nor a Moid/Name
                if not hasattr(target_object, "object_type") and not \
                        (hasattr(target_object, "moid") or hasattr(target_object, "name")):
                    continue
                else:
                    object_type = target_object.object_type
                    if hasattr(target_object, "moid"):
                        moid = target_object.moid
                    elif hasattr(target_object, "name"):
                        name = target_object.name

            # We convert the ObjectType value to the naming used in the fetched SDK objects
            # Ex: iam.User is converted to iam_user
            sdk_object_type = re.sub(r'(?<!^)(?=[A-Z])', '_', object_type.replace(".", "")).lower()

            if moid:
                if sdk_object_type not in moid_dict.keys():
                    moid_dict[sdk_object_type] = []
                moid_dict[sdk_object_type].append(moid)
            elif name:
                if sdk_object_type not in name_dict.keys():
                    name_dict[sdk_object_type] = []
                name_dict[sdk_object_type].append(name)

        filtered_sdk_objects_list = []
        for sdk_object_type, moid_list in moid_dict.items():
            if sdk_object_type in self._config.sdk_objects.keys():
                if self._config.sdk_objects[sdk_object_type] is not None:
                    for sdk_object in self._config.sdk_objects[sdk_object_type]:
                        if sdk_object.moid in moid_list:
                            filtered_sdk_objects_list.append(sdk_object)

        for sdk_object_type, name_list in name_dict.items():
            if sdk_object_type in self._config.sdk_objects.keys():
                if self._config.sdk_objects[sdk_object_type] is not None:
                    for sdk_object in self._config.sdk_objects[sdk_object_type]:
                        if sdk_object.name in name_list:
                            filtered_sdk_objects_list.append(sdk_object)

        return filtered_sdk_objects_list

    def get_live_object(self, object_name=None, object_type=None, query_filter=None, return_reference=True, log=True):
        """
        This function will return the reference of a live Managed Object (or the Managed Object itself).

        Args:
            object_name ([str], optional): Name of the Intersight Object such as Policies, Profiles, Pools.
            Defaults to None.
            object_type ([str], optional): Type of Intersight config object class to be searched. Defaults to None.
            query_filter ([str], optional): User defined Filter for searching an Intersight config object.
            Defaults to None.
            return_reference ([bool], optional): Specifies if the returned object is a reference to the Managed Object.
            Defaults to True.
            log ([bool], optional): Specifies whether we need to log the warning messages

        Returns:
            [MoMoRef]: Reference of Managed Object in JSON format if successful,
            None otherwise
        """
        if not object_type:
            return None

        if query_filter:
            object_list = self._device.query(object_type=object_type, filter=query_filter)
        else:
            if not (object_name and self._parent.__class__.__name__ == "IntersightOrganization"):
                return None

            if "/" in object_name:
                org_ref = self.get_org_relationship(org_name=object_name.split("/")[0])
                if not org_ref:
                    if log:
                        self.logger(
                            level="warning",
                            message=f"Could not find parent org Moid for object {str(object_type)} with name "
                                    f"'{str(object_name)}' to assign to {str(self._CONFIG_NAME)} {str(self.name)}"
                        )
                    return None
                org_ref_moid = org_ref.moid
                object_name = object_name.split("/")[1]
            else:
                if not self._parent._moid:
                    org_ref = self.get_parent_org_relationship()
                    if not org_ref:
                        if log:
                            self.logger(
                                level="warning",
                                message=f"Could not find parent org Moid for object {str(object_type)} with name "
                                        f"'{str(object_name)}' to assign to {str(self._CONFIG_NAME)} {str(self.name)}"
                            )
                        return None

                    self._parent._moid = org_ref.moid
                org_ref_moid = self._parent._moid

            object_list = self._device.query(
                object_type=object_type,
                filter="Name eq '" + object_name + "' and Organization.Moid eq '" + org_ref_moid + "'"
            )

        if object_list and len(object_list) == 1:
            if return_reference:
                return self.create_relationship_equivalent(object_list[0])
            else:
                return object_list[0]

        if log:
            self.logger(
                level="warning",
                message=f"Could not find a unique object {str(object_type)} with name '{str(object_name)}' "
                        f"to assign to {str(self._CONFIG_NAME)} {str(self.name)}"
            )
        return None

    def get_org_relationship(self, org_name=None):
        """
        Get organization Relationship object
        :return: OrganizationOrganizationRelationship object if found, None otherwise
        """
        if not org_name:
            self.logger(level="error", message="No Org Name provided")
            return None

        org_list = self._device.query(object_type="organization.Organization", filter="Name eq '%s'" % org_name)

        if len(org_list) != 1:
            self.logger(level="error", message="Could not find org object with name " + org_name)
            return None

        # We return the corresponding OrganizationOrganizationRelationship object
        return self.create_relationship_equivalent(sdk_object=org_list[0])

    def get_parent_org_relationship(self):
        """
        Get parent organization Relationship object
        :return: OrganizationOrganizationRelationship object if found, None otherwise
        """
        # We first need to make sure that the parent object is an IntersightOrganization
        if not self._parent.__class__.__name__ == "IntersightOrganization":
            return None

        # We return the corresponding OrganizationOrganizationRelationship object
        return self.get_org_relationship(org_name=self._parent.name)

    def _get_policy_name(self, policy):
        """
        Get policy name using the Relationship object (Used during 'fetch_config()', under '__init__()')
        :param policy: Intersight relationship object
        :return: Name of the policy or "<shared_org_name>/<policy_name>" if policy is in a shared organization
        """
        if not policy:
            self.logger(level="warning", message="No Policy/Pool Provided")
            return None

        policy_list = self.get_config_objects_from_ref(ref=policy)
        if (len(policy_list)) != 1:
            self.logger(level="debug", message="Could not find the appropriate " + str(policy.object_type) +
                                               " with MOID " + str(policy.moid))
            return None
        else:
            # Check if the referenced policy's organization differs from the organization of the
            # current (self) object. If true then the policy is in a shared organization, return
            # "<shared_org_name>/<policy_name>", otherwise return just "<policy_name>".
            if policy_list[0].organization.moid != self._object.organization.moid:
                source_org_list = self.get_config_objects_from_ref(ref=policy_list[0].organization)
                if len(source_org_list) != 1:
                    self.logger(level="debug",
                                message=f"Could not find the appropriate {str(policy_list[0].organization.object_type)}"
                                        f" with MOID {str(policy_list[0].organization.moid)}")
                else:
                    return f"{source_org_list[0].name}/{policy_list[0].name}"

            # We return the name attribute of the matching policy
            return policy_list[0].name

    def instantiate_config_objects_under_org(self, org=None, object_class=None):
        """
        Instantiates EasyUCS Intersight config objects under a specified org
        :param org: The IntersightOrganization object under which config objects should be instantiated
        :param object_class: The EasyUCS Intersight config object class to be instantiated
        :return: The list of config objects instantiated if successful, None otherwise
        """
        if not org and not object_class:
            return None

        sdk_object_type = re.sub(r'(?<!^)(?=[A-Z])', '_',
                                 object_class._INTERSIGHT_SDK_OBJECT_NAME.replace(".", "")).lower()

        filtered_sdk_objects_list = []
        if sdk_object_type in self._config.sdk_objects.keys():
            if self._config.sdk_objects[sdk_object_type] is not None:
                for sdk_object in self._config.sdk_objects[sdk_object_type]:
                    if hasattr(sdk_object, "organization"):
                        if hasattr(sdk_object.organization, "moid"):
                            if sdk_object.organization.moid == org._moid:
                                # WWPN and WWNN use the same object class (fcpool.Pool).
                                # We use the "pool_purpose" parameter to differentiate them.
                                if object_class.__name__ in ["IntersightWwnnPool"]:
                                    if sdk_object.pool_purpose != "WWNN":
                                        continue
                                if object_class.__name__ in ["IntersightWwpnPool"]:
                                    if sdk_object.pool_purpose != "WWPN":
                                        continue
                                # Skipping objects imported using "Import Server Profile" feature & tagged as incomplete
                                # as they can contain SDK-unsupported attribute values
                                if any(tag.get("key", None) == "cisco.meta.configimport.Incomplete" and
                                       tag.get("value", None) == "true" for tag in getattr(sdk_object, "tags", [])):
                                    self.logger(level="warning",
                                                message="Skipping " + getattr(object_class, "_CONFIG_NAME", "None") +
                                                        " object with name '" + getattr(sdk_object, "name", "None") +
                                                        "' as it is tagged with incomplete Server Profile import")
                                    continue
                                filtered_sdk_objects_list.append(sdk_object)

        easyucs_objects_list = []
        for sdk_object in filtered_sdk_objects_list:
            # We instantiate an Intersight Config Object for each corresponding SDK object
            easyucs_objects_list.append(object_class(org, sdk_object))
        return easyucs_objects_list

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __contains__(self, key):
        return key in self.__dict__

    def get(self, key, default=None):
        return getattr(self, key, default)
