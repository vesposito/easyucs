# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """

import time
import urllib

from imcsdk.imcexception import ImcException
from ucscsdk.ucscexception import UcscException
from ucsmsdk.ucsexception import UcsException

import common
from config.object import GenericConfigObject


class GenericUcsConfigObject(GenericConfigObject):
    def __init__(self, parent=None):
        GenericConfigObject.__init__(self, parent=parent)
        self._dn = None
        self._handle = self._config.parent.parent.handle

    def get_attributes_from_json(self, json_content=None):
        if json_content is None:
            return False

        for attribute in json_content.keys():
            if isinstance(json_content[attribute], str):
                setattr(self, attribute, json_content[attribute])
            # Support list of values (like for NTP entries)
            elif isinstance(json_content[attribute], list):
                setattr(self, attribute, [])
                for element in json_content[attribute]:
                    if isinstance(element, (str, dict)):
                        getattr(self, attribute).append(element)
            # Support dict of values (like for operational_state)
            elif isinstance(json_content[attribute], dict):
                setattr(self, attribute, json_content[attribute])
        return True

    def get_operational_state(self, policy_dn="", separator="", policy_name=""):
        """
        Decompose the operational state attribute of a given policy using the given separator into "org" and "name"
        :param policy_dn: DN of the operState of the policy that needs to be decomposed (e.g. operBiosProfileName value)
        :param separator: string within the DN used to separate the org and the name of the policy (e.g. "/bios-prof-")
        :param policy_name: Name of the policy to be included in the operational state attribute
        :return: The decomposed object if successful, None otherwise
        """
        if not separator or not policy_name:
            return None

        if policy_dn:
            policy_dn_split = policy_dn.split(separator)
            if len(policy_dn_split) == 2:
                decomposed_policy = {
                    "org": '/'.join([org.replace("org-", "", 1) for org in policy_dn.split(separator)[0].split("/")]),
                    "name": policy_dn.split(separator)[1]}
                return {policy_name: decomposed_policy}
            else:
                return {policy_name: None}
        else:
            return {policy_name: None}

    def clean_object(self):
        """
        Clean the "NA" or "N/A" or "None" or "none" or empty values of a config object
        :return:
        """

        if self.__class__.__name__ in [
            "UcsCentralBiosPolicy",
            "UcsCentralQosPolicy",
            "UcsCentralStorageConnectionPolicy",
            "UcsCentralVmediaPolicy",
            "UcsImcAdminNetwork",
            "UcsSystemBiosPolicy",
            "UcsSystemDefaultVhbaBehavior",
            "UcsSystemDefaultVnicBehavior",
            "UcsSystemLinkProtocolPolicy",
            "UcsSystemQosPolicy",
            "UcsSystemStorageConnectionPolicy",
            "UcsSystemVmediaPolicy"

        ]:
            # We do not clean "None" values in a BIOS Policy because some parameters are using the string "None"
            # Default vHBA / vNIC Behavior can also contain the string "None" as the default value for "action"
            # Link Protocol Policy is also using the string "none" for value of attribute "recovery_action"
            # Qos Policy of UCSM and  UCSC is using "none" as value of "host_control" attribute
            # Storage Connection Policy of UCSM and UCSC uses "none" as value of "zoning_type" attribute
            # vMedia Policy of UCSM and UCSC uses "none" as value of "authentication_protocol" and
            # "image_name_variable" attribute
            # Admin Network of IMC is also using the string "none" for value of attribute "nic redundancy"

            str_to_avoid = ["N/A", "", "NA"]
        else:
            str_to_avoid = ["N/A", "", "NA", "none", "None"]

        for key in self.__dict__.keys():
            if getattr(self, key) in str_to_avoid:
                # self.logger(level="debug",
                #             message="In " + self._CONFIG_NAME + ", key '" + key + "' with value " +
                #                     (getattr(self, key) if getattr(self, key) != "" else "''") + " cleaned")
                if key not in ["name", "descr"]:
                    # We do not clean a "None" value for the name or descr attributes since a policy can be called
                    # "None" or "NA" or have a description with such a value
                    setattr(self, key, None)
                else:
                    # We only clean an empty "" value for the name or descr attributes
                    if getattr(self, key) in [""]:
                        setattr(self, key, None)

            elif getattr(self, key).__class__.__name__ == "list":
                for item in getattr(self, key):
                    if item.__class__.__name__ == "dict":
                        for item_key, value in item.items():
                            if value in str_to_avoid:
                                # self.logger(level="debug",
                                #             message="In " + self._CONFIG_NAME + ", in " + key + ": key '" + item_key +
                                #                     "' with value " +
                                #                     (item[item_key] if item[item_key] != "" else "''") + " cleaned")
                                item[item_key] = None


class UcsSystemConfigObject(GenericUcsConfigObject):
    def __init__(self, parent=None, ucs_sdk_object=None):
        GenericUcsConfigObject.__init__(self, parent=parent)

        if self._parent.__class__.__name__ == "UcsSystemServiceProfile":
            if hasattr(self, "_CONFIG_NAME"):
                # We are in presence of a Specific Policy under a Service Profile object
                self._CONFIG_NAME = "Specific " + self._CONFIG_NAME

        self.policy_owner = None
        if ucs_sdk_object is not None:
            if hasattr(ucs_sdk_object, "policy_owner"):
                if ucs_sdk_object.policy_owner in ["policy"]:
                    self.policy_owner = "ucs-central"

    def format_commit_buffer(self):
        """
        Formats the data from the commit buffer, to get all the object types being committed
        return: A string of object types and its count being committed
        """
        # UCS Manager sdk have 2 commit buffers, commit_buff and tagged_commit_buff. In our case, we use
        # tagged_commit_buffer. To get the auto generated tag we use the auto_set_tag_context() method.
        # Using the tag we fetch the tagged_commit_buff to get the object types being pushed.
        tag = self._handle._auto_set_tag_context(tag=None)
        commit_buf = self._handle._get_commit_buf(tag=tag)
        obj_types = {}
        for obj in commit_buf.values():
            if obj.__class__.__name__ not in obj_types:
                obj_types[obj.__class__.__name__] = 1
            else:
                obj_types[obj.__class__.__name__] += 1
        return ", ".join([f"{cls} x {count}" for cls, count in obj_types.items()])

    def commit(self, detail="", show=True, retry=True):
        obj_types = self.format_commit_buffer()
        try:
            self._handle.commit()
            if show:
                if detail:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME + " - " + detail)
                else:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME)
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=obj_types,
                                                                status="success")
            return True

        except UcsException as err:
            if retry:
                if err.error_descr == "Authorization required":
                    self.logger(
                        level="debug",
                        message="Fail to commit: " + err.error_descr + " " + detail + ". Trying to commit again"
                    )
                    if self.retry_commit(detail=detail, show=show):
                        return True
                self._handle.commit_buffer_discard()
                self._config.refresh_config_handle()
            err_message = "Error in configuring " + self._CONFIG_NAME + " - " + detail + " - " + err.error_descr
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=obj_types,
                                                                status="failed", message=err_message)
            if show:
                if detail:
                    self.logger(level="error", message=err_message)
                else:
                    self.logger(
                        level="error",
                        message="Error in configuring " + self._CONFIG_NAME + ": " + err.error_descr
                    )
            return False

        except urllib.error.URLError:
            if retry:
                self.logger(
                    level="debug",
                    message="Fail to commit: Timeout error " + detail + ". Trying to commit again"
                )
                if self.retry_commit(detail=detail, show=show):
                    return True
                self._handle.commit_buffer_discard()
            err_message = "Error in configuring " + self._CONFIG_NAME + ": Timeout error"
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=obj_types,
                                                                status="failed", message=err_message)
            if show:
                self.logger(level="error", message=err_message)
            return False

        except Exception as err:
            err_message = "Unknown error in configuring " + self._CONFIG_NAME + ": " + str(err)
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=obj_types,
                                                                status="failed", message=err_message)
            # We first discard the commit buffer in order to avoid resending the bad buffer content in the next commit
            self._handle.commit_buffer_discard()
            if show:
                self.logger(level="error", message=err_message)
            return False

    def retry_commit(self, detail="", show=True):
        tag = self._handle._auto_set_tag_context(tag=None)
        commit_buf = self._handle._get_commit_buf(tag=tag)
        obj_types = ", ".join([obj.__class__.__name__ for obj in commit_buf.values()])
        for i in range(self._device.push_attempts):
            if detail:
                self.logger(
                    level="warning",
                    message="Trying to push again the " + self._CONFIG_NAME + " " + detail +
                            " configuration (attempt " + str(i + 1) + ")"
                )
            else:
                self.logger(
                    level="warning",
                    message="Trying to push again the " + self._CONFIG_NAME +
                            " configuration (attempt " + str(i + 1) + ")"
                )
            if self._device.is_connected():
                if self.commit(retry=False, show=False):
                    if show:
                        if detail:
                            self.logger(
                                level="debug",
                                message="Successfully configured " + self._CONFIG_NAME + " - " + detail
                            )
                        else:
                            self.logger(
                                level="debug",
                                message="Successfully configured " + self._CONFIG_NAME
                            )
                    self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail,
                                                                        obj_type=obj_types, status="success")
                    return True
            else:
                self.logger(level="error", message="Not successfully connected. Trying to reconnect")
                self._device.connect()
            time.sleep(self._device.push_interval_after_fail)

        # Only accessible if the retries failed to push the commit
        if self._device.push_attempts:
            self.logger(
                level="error",
                message="Impossible to push the " + self._CONFIG_NAME +
                        " configuration even after " + str(i + 1) + " attempts. The buffer will be discarded."
            )
        return False


class UcsImcConfigObject(GenericUcsConfigObject):
    def __init__(self, parent=None):
        GenericUcsConfigObject.__init__(self, parent=parent)

    def commit(self, mo=None, detail=""):
        try:
            if mo is not None:
                self._handle.set_mo(mo=mo)
                if detail:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME + " - " + detail)
                else:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME)
                return True

        except ImcException as err:
            if detail:
                self.logger(
                    level="error",
                    message="Error in configuring " + self._CONFIG_NAME + " - " + detail + " - " + err.error_descr
                )
            else:
                self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + ": " + err.error_descr)

        except urllib.error.URLError:
            self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + ": Timeout error")

        except TimeoutError:
            self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + ": Timeout error")

        except Exception as err:
            self.logger(level="debug", message="Unknown error in configuring " + self._CONFIG_NAME + " " + str(err))
            self.logger(level="error", message="Unknown error in configuring " + self._CONFIG_NAME)
        return False

    def get_operational_state(self, policy_dn="", separator="", policy_name=""):
        self.logger(level="error", message="Not available for device of type " + self._parent.metadata.device_type_long)


class UcsCentralConfigObject(GenericUcsConfigObject):
    def __init__(self, parent=None, ucs_sdk_object=None):
        GenericUcsConfigObject.__init__(self, parent=parent)

        self.tags = None

        # Fetching tags assigned to this UCS Central object
        if ucs_sdk_object is not None:
            if "tagInstance" in self._config.sdk_objects:
                self.tags = []
                for tag_instance in self._config.sdk_objects["tagInstance"]:
                    if tag_instance.tagged_object_dn == ucs_sdk_object.dn:
                        self.logger(
                            level="debug",
                            message=f"Fetching the tag instance of DN '{tag_instance.tagged_object_dn}'"
                        )
                        self.tags.append({"type": tag_instance.def_name, "value": tag_instance.value})

    def format_commit_buffer(self):
        """
        Formats the data from the commit buffer, to get all the object types being committed
        return: A string of object types and its count being committed
        """
        # UCS Central sdk have 2 commit buffers, commit_buff and tagged_commit_buff. In our case, we use
        # tagged_commit_buffer. To get the auto generated tag we use the auto_set_tag_context() method.
        # Using the tag we fetch the tagged_commit_buff to get the object types being pushed.
        tag = self._handle._auto_set_tag_context(tag=None)
        try:
            commit_buf = self._handle._get_commit_buf(tag=tag)
        except KeyError:
            # We might encounter KeyError because of empty commit buffer, in that case we return empty string
            return ""
        obj_types = {}
        for obj in commit_buf.values():
            if obj.__class__.__name__ not in obj_types:
                obj_types[obj.__class__.__name__] = 1
            else:
                obj_types[obj.__class__.__name__] += 1
        return ", ".join([f"{cls} x {count}" for cls, count in obj_types.items()])

    def commit(self, detail="", show=True, retry=True):
        obj_types = self.format_commit_buffer()
        try:
            self._handle.commit()
            if show:
                if detail:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME + " - " + detail)
                else:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME)
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=obj_types,
                                                                status="success")
            return True

        except UcscException as err:
            if retry:
                if err.error_descr == "Authorization required":
                    self.logger(
                        level="debug",
                        message="Fail to commit: " + err.error_descr + " " + detail + ". Trying to commit again"
                    )
                    if self.retry_commit(detail=detail, show=show):
                        return True
                self._handle.commit_buffer_discard()
                self._config.refresh_config_handle()
            err_message = "Error in configuring " + self._CONFIG_NAME + " - " + detail + " - " + err.error_descr
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=obj_types,
                                                                status="failed", message=err_message)
            if show:
                if detail:
                    self.logger(level="error", message=err_message)
                else:
                    self.logger(
                        level="error",
                        message="Error in configuring " + self._CONFIG_NAME + ": " + err.error_descr
                    )
            return False

        except urllib.error.URLError:
            if retry:
                self.logger(
                    level="debug",
                    message="Fail to commit: Timeout error " + detail + ". Trying to commit again"
                )
                if self.retry_commit(detail=detail, show=show):
                    return True
                self._handle.commit_buffer_discard()
            err_message = "Error in configuring " + self._CONFIG_NAME + ": Timeout error"
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=obj_types,
                                                                status="failed", message=err_message)
            if show:
                self.logger(level="error", message=err_message)
            return False

        except Exception as err:
            err_message = "Unknown error in configuring " + self._CONFIG_NAME + ": " + str(err)
            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail, obj_type=obj_types,
                                                                status="failed", message=err_message)
            # We first discard the commit buffer in order to avoid resending the bad buffer content in the next commit
            self._handle.commit_buffer_discard()
            if show:
                self.logger(level="error", message=err_message)
            return False

    def retry_commit(self, detail="", show=True):
        tag = self._handle._auto_set_tag_context(tag=None)
        commit_buf = self._handle._get_commit_buf(tag=tag)
        obj_types = ", ".join([obj.__class__.__name__ for obj in commit_buf.values()])
        for i in range(self._device.push_attempts):
            if detail:
                self.logger(
                    level="warning",
                    message="Trying to push again the " + self._CONFIG_NAME + " " + detail +
                            " configuration (attempt " + str(i + 1) + ")"
                )
            else:
                self.logger(
                    level="warning",
                    message="Trying to push again the " + self._CONFIG_NAME +
                            " configuration (attempt " + str(i + 1) + ")"
                )
            if self._device.is_connected():
                if self.commit(retry=False, show=False):
                    if show:
                        if detail:
                            self.logger(
                                level="debug",
                                message="Successfully configured " + self._CONFIG_NAME + " - " + detail
                            )
                        else:
                            self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME)
                    self._config.push_summary_manager.add_object_status(obj=self, obj_detail=detail,
                                                                        obj_type=obj_types, status="success")
                    return True
            else:
                self.logger(level="error", message="Not successfully connected. Trying to reconnect")
                self._device.connect()
            time.sleep(self._device.push_interval_after_fail)

        # Only accessible if the retries failed to push the commit
        if self._device.push_attempts:
            self.logger(
                level="error",
                message="Impossible to push the " + self._CONFIG_NAME +
                        " configuration even after " + str(i + 1) + " attempts. The buffer will be discarded."
            )
        return False
