# coding: utf-8
# !/usr/bin/env python

""" device_connector.py: Easy UCS Deployment Tool """

import requests
import urllib3

from config.ucs.object import GenericUcsConfigObject


class UcsDeviceConnector(GenericUcsConfigObject):
    _CONFIG_NAME = "Device Connector"

    def __init__(self, parent=None, json_content=None):
        GenericUcsConfigObject.__init__(self, parent=parent)
        self._connector_uri = self._parent_having_logger.target + "/connector"

        self.enabled = None
        self.intersight_url = None
        self.proxy_host = None
        self.proxy_port = None
        self.proxy_state = None
        self.proxy_username = None
        self.proxy_password = None
        self.read_only = None
        self.tunneled_kvm = None
        self.configuration_from_intersight_only = None

        if self._config.load_from == "live":
            self._cookie = self._parent_having_logger.handle.cookie
            self._get_device_connections()
            self._get_http_proxies()
            self._get_systems()
            if "Imc" in self._parent_having_logger.__class__.__name__:
                self._get_device_configurations()

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def get_request(self, uri):
        # Disable warning at each request
        urllib3.disable_warnings()

        # Sanity check
        if hasattr(self, "_cookie"):
            if self._cookie:
                auth_header = {'ucsmcookie': "ucsm-cookie=%s" % self._cookie}
                try:
                    response = requests.get(uri, verify=False, headers=auth_header)
                    return response.json()
                except Exception as err:
                    self.logger(level="error", message="Couldn't request the device connector information " +
                                                       "from the API for config: " + str(err))
            else:
                self.logger(level="error",
                            message="No login cookie, no request can be made to find device connector information")
        else:
            self.logger(level="error",
                        message="No login cookie, no request can be made to find device connector information")

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
                self.intersight_url = "svc.intersight.com"
        except KeyError as err:
            self.logger(level="error", message="Could not find key parameter " + str(err))

    def _get_device_configurations(self):
        uri = "https://" + self._connector_uri + "/DeviceConfigurations"
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
            self.tunneled_kvm = str(response[0]["KVMTunnellingEnabled"]).lower()
            self.configuration_from_intersight_only = str(response[0]["ConfigurationLockoutEnabled"]).lower()
        except KeyError as err:
            self.logger(level="error", message="Could not find key parameter " + str(err))

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
            self.enabled = str(response[0]["AdminState"]).lower()
            self.read_only = str(response[0]["ReadOnlyMode"]).lower()
        except KeyError as err:
            self.logger(level="error", message="Could not find key parameter " + str(err))

    def _get_http_proxies(self):
        uri = "https://" + self._connector_uri + "/HttpProxies"
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
            self.proxy_state = response[0]["ProxyType"].lower()
            if self.proxy_state == "manual":
                self.proxy_state = "enabled"
                self.proxy_host = response[0]["ProxyHost"]
                self.proxy_port = str(response[0]["ProxyPort"])
                if "ProxyUsername" in response[0]:
                    self.proxy_username = response[0]["ProxyUsername"]
                    self.logger(level="warning", message="Password of " + self._CONFIG_NAME + " Proxy username" +
                                                         self.proxy_username + " can't be exported")
        except KeyError as err:
            self.logger(level="error", message="Could not find key parameter " + str(err))

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        self._cookie = self._parent_having_logger.handle.cookie

        # Pushing HTTP Proxy configuration
        if self.proxy_state:
            proxy_type = ("Manual" if self.proxy_state == "enabled" else self.proxy_state.title())  # Disabled
        else:
            proxy_type = "Disabled"
        if self.proxy_username and self.proxy_password:
            authentication_enabled = "true"
        if self.proxy_username is None:
            self.proxy_username = ""
        if self.proxy_password is None:
            self.proxy_password = ""

        if proxy_type == "Disabled":
            data = '{"HostProperties":{"ProxyHost":"","ProxyPort":""},"AuthProperties":{},"ProxyType":"' + \
                   proxy_type + '"}'
        else:
            data = '{"HostProperties":{"ProxyHost":"","ProxyPort":""},"AuthProperties":{},"ProxyType":"' + \
                   proxy_type + '","ProxyHost":"' + self.proxy_host + '","ProxyPort":' + self.proxy_port + \
                   ',"ProxyUsername":"' + self.proxy_username + '","ProxyPassword":"' + self.proxy_password + \
                   '"}'
        uri = "https://" + self._parent_having_logger.target + "/connector/HttpProxies"
        response = self.put_request(uri=uri, data=data)

        # Pushing Intersight Device Connections
        # FIXME: Check before performing ForceResetIdentity
        # data = '{"CloudDns":"' + self.intersight_url + '", "ForceResetIdentity": true }'
        # uri = "https://" + self._parent_having_logger.target + "/connector/DeviceConnections"
        # response = self.put_request(uri=uri, data=data)

        # Pushing Intersight Systems
        data = '{"ReadOnlyMode":' + self.read_only + ', "AdminState":' + self.enabled + '}'
        uri = "https://" + self._parent_having_logger.target + "/connector/Systems"
        response = self.put_request(uri=uri, data=data)

        # Pushing Intersight Device configuration
        if "Imc" in self._parent_having_logger.__class__.__name__:
            data = '{"KVMTunnellingEnabled":' + self.tunneled_kvm + ', "ConfigurationLockoutEnabled":' +\
                   self.configuration_from_intersight_only + '}'
            uri = "https://" + self._parent_having_logger.target + "/connector/DeviceConfigurations"
            response = self.put_request(uri=uri, data=data)

        return True

    def put_request(self, uri="", data=""):
        """
        Does a put request specific for the proxy settings (subject to change to make it generic?)
        """

        # Disable warning at each request
        urllib3.disable_warnings()

        if not uri or not data:
            self.logger(level="error",
                        message="URI and payload data are required for sending a PUT request to Device Connector!")
            return False

        # Sanity check
        if hasattr(self, "_cookie"):
            if self._cookie:
                auth_header = {'ucsmcookie': "ucsm-cookie=%s" % self._cookie}
                try:
                    response = requests.put(uri, verify=False, headers=auth_header, data=data)
                    if response.status_code != 200:
                        message = "Couldn't push the device connector information to the API, error " + \
                                  str(response.status_code)
                        self.logger(level="error",
                                    message=message)
                        return False
                    elif "InvalidRequest" in response.text:
                        self.logger(level="error",
                                    message=response.json()["message"])

                    return response.json()
                except Exception as err:
                    print(err)
                    self.logger(level="error",
                                message="Couldn't push the device connector information to the API")
            else:
                self.logger(level="error",
                            message="No login cookie, no request can be made to find device connector information")
        else:
            self.logger(level="error",
                        message="No login cookie, no request can be made to find device connector information")

        return False
