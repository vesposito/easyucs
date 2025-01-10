# coding: utf-8
# !/usr/bin/env python

""" admin.py: Easy UCS Deployment Tool """

from config.object import GenericConfigObject


class ImmDomainSystemInformation(GenericConfigObject):
    _CONFIG_NAME = "System Information"
    _CONFIG_SECTION_NAME = "system_information"

    def __init__(self, parent=None, json_content=None):
        GenericConfigObject.__init__(self, parent=parent)
        self.fabric_interconnects = None
        self.name = None

        if self._config.load_from == "live":
            self._get_name()
            self._get_systeminfo()

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        if self.fabric_interconnects:
            for fabric in self.fabric_interconnects:
                for element in ["fabric", "ip", "ipv6", "gateway", "netmask", "operational_state"]:
                    if element not in fabric:
                        fabric[element] = None

    def _get_name(self):
        uri = "https://" + self._device.target + "/DomainName"
        response = self._device.get_request(uri=uri)

        # Sanity check
        if not response:
            self.logger(level="error", message="GET /CommConfigs failed to return a valid response")
            return

        if response.get("DomainName"):
            self.name = response.get("DomainName")

    def _get_systeminfo(self):
        uri = "https://" + self._device.target + "/SystemInfo"
        response = self._device.get_request(uri=uri)

        # Sanity check
        if not response:
            self.logger(level="error", message="GET /CommConfigs failed to return a valid response")
            return

        if response.get("FIA") or response.get("FIB"):
            self.fabric_interconnects = []

        if response.get("FIA"):
            self.fabric_interconnects.append({
                "fabric": response["FIA"].get("Node"),
                "ip": response["FIA"].get("MgmtIpv4"),
                "ipv6": response["FIA"].get("MgmtIpv6"),
                "operational_state": response["FIA"].get("OperState")
            })

        if response.get("FIB"):
            self.fabric_interconnects.append({
                "fabric": response["FIB"].get("Node"),
                "ip": response["FIB"].get("MgmtIpv4"),
                "ipv6": response["FIB"].get("MgmtIpv6"),
                "operational_state": response["FIB"].get("OperState")
            })
