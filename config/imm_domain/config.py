# coding: utf-8
# !/usr/bin/env python

""" config.py: Easy UCS Deployment Tool """

from config.config import GenericConfig


class ImmDomainConfig(GenericConfig):
    _CONFIG_SECTION_ATTRIBUTES_MAP = {
        "device_connector": "Device Connector",
        "system_information": "System Information",
    }

    def __init__(self, parent=None):
        GenericConfig.__init__(self, parent=parent)

        self.api_objects = {}

        self.device_connector = []
        self.system_information = []

        # List of attributes to be exported in a config export
        self.export_list = self._CONFIG_SECTION_ATTRIBUTES_MAP.keys()
