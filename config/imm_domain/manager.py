# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

from config.device_connector import DeviceConnector
from config.imm_domain.config import ImmDomainConfig
from config.manager import GenericConfigManager
from config.imm_domain.admin import ImmDomainSystemInformation
from __init__ import __version__


class ImmDomainConfigManager(GenericConfigManager):
    def __init__(self, parent=None):
        GenericConfigManager.__init__(self, parent=parent)
        self.config_class_name = ImmDomainConfig

    def fetch_config(self, force=False):
        self.logger(message="Fetching config from live device (can take several minutes)")
        config = ImmDomainConfig(parent=self)
        config.metadata.origin = "live"
        config.metadata.easyucs_version = __version__
        config.load_from = "live"

        if config.device.task is not None:
            config.device.task.taskstep_manager.start_taskstep(
                name="FetchConfigImmDomainApiObjects",
                description="Fetching " + config.device.metadata.device_type_long + " API Config Objects")

        config.device_connector.append(DeviceConnector(parent=config))
        config.system_information.append(ImmDomainSystemInformation(parent=config))

        if config.device.task is not None:
            config.device.task.taskstep_manager.stop_taskstep(
                name="FetchConfigImmDomainApiObjects", status="successful",
                status_message="Successfully fetched " + config.device.metadata.device_type_long +
                               " API Config Objects")

        self.config_list.append(config)
        self.logger(message="Finished fetching config with UUID " + str(config.uuid) + " from live device")
        return config.uuid

    def _fill_config_from_json(self, config=None, config_json=None):
        """
        Fills config using parsed JSON config file
        :param config: config to be filled
        :param config_json: parsed JSON content containing config
        :return: True if successful, False otherwise
        """
        if config is None or config_json is None:
            self.logger(level="debug", message="Missing config or config_json parameter!")
            return False

        if "device_connector" in config_json:
            config.device_connector.append(
                DeviceConnector(parent=config, json_content=config_json["device_connector"][0]))

        if "system_information" in config_json:
            config.system_information.append(
                ImmDomainSystemInformation(parent=config, json_content=config_json["system_information"][0]))

        return True
