# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """

import requests
import urllib3
from inventory.object import GenericInventoryObject


class GenericDeviceConnector(GenericInventoryObject):
    def __init__(self, parent=None, device_connector=None):
        GenericInventoryObject.__init__(self, parent=parent)

    def get_request(self, uri):
        # Disable warning at each request
        urllib3.disable_warnings()

        # Sanity check
        if hasattr(self, "_login_cookie"):
            if self._login_cookie:
                auth_header = {'ucsmcookie': "ucsm-cookie=%s" % self._login_cookie}
                try:
                    response = requests.get(uri, verify=False, headers=auth_header)
                    return response.json()
                except Exception as err:
                    self.logger(level="error", message="Couldn't request the device connector information " +
                                                       "from the API for inventory: " + str(err))
            else:
                self.logger(level="error",
                            message="No login cookie, no request can be made to find device connector information")
        else:
            self.logger(level="error",
                        message="No login cookie, no request can be made to find device connector information")

    def get_attribute(self, ucs_sdk_object=None, attribute_name=None, attribute_secondary_name=None,
                      attribute_type=None):
        # We use a modified version of get_attribute from GenericUcsInventoryObject for convenience

        # Sanity checking
        if self._inventory.load_from is None:
            self.logger(level="error", message="Attribute 'load_from' in inventory is not set")
            return None
        # if ucs_sdk_object is None:
        #     self.logger(level="error", message="Missing ucs_sdk_object")
        #     return None
        if attribute_name is None:
            self.logger(level="error", message="Missing attribute name")
            return None

        result = None

        if self._inventory.load_from == "live":
            return None

        elif self._inventory.load_from == "file":
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

    def _get_systems(self):
        uri = "https://" + self._connector_uri + "/Systems"
        response = self.get_request(uri=uri)
        # Sanity check
        if not response:
            return None
        if isinstance(response, list):
            if not response[0]:
                return None
        else:
            return None

        try:
            self.ownership = response[0]["AccountOwnershipState"].lower()
            if self.ownership == "claimed":
                self.ownership_user = response[0]["AccountOwnershipUser"]
                self.ownership_name = response[0]["AccountOwnershipName"]
        except KeyError as err:
            self.logger(level="error", message="Could not find key parameter " + str(err))

    def _get_versions(self):
        uri = "https://" + self._connector_uri + "/Versions"
        response = self.get_request(uri=uri)
        # Sanity check
        if not response:
            return None
        if isinstance(response, list):
            if not response[0]:
                return None
        else:
            return None

        try:
            self.version = response[0]["Version"]
        except KeyError as err:
            self.logger(level="error", message="Could not find key parameter " + str(err))

    def _get_security_tokens(self):
        uri = "https://" + self._connector_uri + "/SecurityTokens"
        response = self.get_request(uri=uri)
        # Sanity check
        if not response:
            return None
        if isinstance(response, list):
            if not response[0]:
                return None
        else:
            return None

        try:
            self.token = response[0]["Token"]
        except KeyError as err:
            self.logger(level="error", message="Could not find key parameter " + str(err))

    def _get_device_identifiers(self):
        uri = "https://" + self._connector_uri + "/DeviceIdentifiers"
        response = self.get_request(uri=uri)
        # Sanity check
        if not response:
            return None
        if isinstance(response, list):
            if not response[0]:
                return None
        else:
            return None

        try:
            self.device_id = response[0]["Id"]
        except KeyError as err:
            self.logger(level="error", message="Could not find key parameter " + str(err))

    def _get_device_connections(self):
        uri = "https://" + self._connector_uri + "/DeviceConnections"
        response = self.get_request(uri=uri)
        # Sanity check
        if not response:
            return None
        if isinstance(response, list):
            if not response[0]:
                return None
        else:
            return None

        try:
            self.intersight_url = response[0]["CloudDns"].lower()
            if self.intersight_url in ["svc.ucs-connect.com", "svc.intersight.com", "svc-static1.intersight.com",
                                       "svc-static1.ucs-connect.com"]:
                self.intersight_url = "intersight.com"
        except KeyError as err:
            self.logger(level="error", message="Could not find key parameter " + str(err))


class UcsSystemDeviceConnector(GenericDeviceConnector):
    def __init__(self, parent=None, device_connector=None):
        GenericDeviceConnector.__init__(self, parent=parent, device_connector=device_connector)

        self._connector_uri = self._parent_having_logger.target + "/connector"
        self._login_cookie = self._parent_having_logger.handle.cookie

        # Systems
        self.ownership = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="ownership")
        self.ownership_user = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="ownership_user")
        self.ownership_name = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="ownership_name")
        # Versions
        self.version = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="version")
        # SecurityTokens
        # self.token = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="token")
        # DeviceIdentifiers
        self.device_id = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="device_id")
        # DeviceConnections
        self.intersight_url = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="intersight_url")

        if self._inventory.load_from == "live":
            self.logger(level="debug", message="Fetching Device Connector objects for inventory")
            self._get_systems()
            self._get_versions()
            # self._get_security_tokens()
            self._get_device_identifiers()
            self._get_device_connections()

            if self.ownership:
                if self.ownership in ["claimed"]:
                    self._parent_having_logger.intersight_status = "claimed"
                elif self.ownership in ["not claimed", "unclaimed"]:
                    self._parent_having_logger.intersight_status = "unclaimed"


class UcsImcDeviceConnector(GenericDeviceConnector):
    def __init__(self, parent=None, device_connector=None):
        GenericDeviceConnector.__init__(self, parent=parent, device_connector=device_connector)

        self._connector_uri = self._parent_having_logger.target + "/connector"
        self._login_cookie = self._parent_having_logger.handle.cookie

        # Systems
        self.ownership = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="ownership")
        self.ownership_user = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="ownership_user")
        self.ownership_name = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="ownership_name")
        # Versions
        self.version = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="version")
        # SecurityTokens
        # self.token = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="token")
        # DeviceIdentifiers
        self.device_id = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="device_id")
        # DeviceConnections
        self.intersight_url = self.get_attribute(ucs_sdk_object=device_connector, attribute_name="intersight_url")

        if self._inventory.load_from == "live":
            self.logger(level="debug", message="Fetching Device Connector objects for inventory")
            self._get_systems()
            self._get_versions()
            # self._get_security_tokens()
            self._get_device_identifiers()
            self._get_device_connections()

            if self.ownership:
                if self.ownership in ["claimed"]:
                    self._parent_having_logger.intersight_status = "claimed"
                elif self.ownership in ["not claimed", "unclaimed"]:
                    self._parent_having_logger.intersight_status = "unclaimed"
