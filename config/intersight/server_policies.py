# coding: utf-8
# !/usr/bin/env python

""" server_policies.py: Easy UCS Deployment Tool """
from common import format_descr, generate_self_signed_cert, get_decoded_pem_certificate, \
    get_encoded_pem_certificate, is_ipv4_address_valid, is_ipv6_address_valid, read_json_file
from config.intersight.object import IntersightConfigObject
from config.intersight.pools import IntersightIpPool, IntersightIqnPool, \
    IntersightMacPool, IntersightWwnnPool, IntersightWwpnPool


class IntersightAdapterConfigurationPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Adapter Configuration Policy"
    _CONFIG_SECTION_NAME = "adapter_configuration_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "adapter.ConfigPolicy"

    def __init__(self, parent=None, adapter_config_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=adapter_config_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.vic_adapter_configurations = None

        if self._config.load_from == "live":
            if hasattr(self._object, "settings"):
                if self._object.settings:
                    self.vic_adapter_configurations = []
                    for adapter_adapter_config in self._object.settings:
                        adapter_configuration = {
                            "dce_interface_settings": [],
                            "pci_slot": adapter_adapter_config.slot_id
                        }
                        if hasattr(adapter_adapter_config, "eth_settings"):
                            if adapter_adapter_config.eth_settings:
                                adapter_configuration["enable_lldp"] = \
                                    adapter_adapter_config.eth_settings["lldp_enabled"]

                        if hasattr(adapter_adapter_config, "fc_settings"):
                            if adapter_adapter_config.fc_settings:
                                adapter_configuration["enable_fip"] = \
                                    adapter_adapter_config.fc_settings["fip_enabled"]

                        if hasattr(adapter_adapter_config, "port_channel_settings"):
                            if adapter_adapter_config.port_channel_settings:
                                adapter_configuration["enable_port_channel"] = \
                                    adapter_adapter_config.port_channel_settings["enabled"]

                        if hasattr(adapter_adapter_config, "physical_nic_mode_settings"):
                            if adapter_adapter_config.physical_nic_mode_settings:
                                adapter_configuration["enable_physical_nic_mode"] = \
                                    adapter_adapter_config.physical_nic_mode_settings["phy_nic_enabled"]

                        if hasattr(adapter_adapter_config, "dce_interface_settings"):
                            if adapter_adapter_config.dce_interface_settings:
                                for adapter_dce_interface_settings in adapter_adapter_config.dce_interface_settings:
                                    adapter_configuration["dce_interface_settings"].append(
                                        {
                                            "interface_id": adapter_dce_interface_settings["interface_id"] + 1,
                                            "fec_mode": adapter_dce_interface_settings["fec_mode"]
                                        }
                                    )
                        self.vic_adapter_configurations.append(adapter_configuration)

        elif self._config.load_from == "file":
            for attribute in ["vic_adapter_configurations"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a VIC Adapter Configuration are set to None if they are not present
        if self.vic_adapter_configurations:
            for adapter_config in self.vic_adapter_configurations:
                for attribute in ["dce_interface_settings", "enable_fip", "enable_lldp", "enable_physical_nic_mode",
                                  "enable_port_channel", "pci_slot"]:
                    if attribute not in adapter_config:
                        adapter_config[attribute] = None

                if adapter_config.get("dce_interface_settings"):
                    for dce_interface_settings in adapter_config["dce_interface_settings"]:
                        for attribute in ["fec_mode", "interface_id"]:
                            if attribute not in dce_interface_settings:
                                dce_interface_settings[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.adapter_config_policy import AdapterConfigPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        if self.vic_adapter_configurations is not None:
            from intersight.model.adapter_adapter_config import AdapterAdapterConfig
            settings = []

            for vic_adapter_config in self.vic_adapter_configurations:
                adapter_adapter_config_kwargs = {
                    "object_type": "adapter.AdapterConfig",
                    "class_id": "adapter.AdapterConfig"
                }
                if vic_adapter_config["pci_slot"] is not None:
                    adapter_adapter_config_kwargs["slot_id"] = vic_adapter_config["pci_slot"]

                if vic_adapter_config["dce_interface_settings"] is not None:
                    from intersight.model.adapter_dce_interface_settings import AdapterDceInterfaceSettings
                    adapter_dce_interface_settings = []

                    for dce_interface_settings in vic_adapter_config["dce_interface_settings"]:
                        adapter_dce_interface_settings_kwargs = {
                            "object_type": "adapter.DceInterfaceSettings",
                            "class_id": "adapter.DceInterfaceSettings"
                        }
                        if dce_interface_settings["fec_mode"] is not None:
                            adapter_dce_interface_settings_kwargs["fec_mode"] = dce_interface_settings["fec_mode"]
                        if dce_interface_settings["interface_id"] is not None:
                            adapter_dce_interface_settings_kwargs["interface_id"] = \
                                dce_interface_settings["interface_id"] - 1

                        adapter_dce_interface_settings.append(
                            AdapterDceInterfaceSettings(**adapter_dce_interface_settings_kwargs)
                        )
                    adapter_adapter_config_kwargs["dce_interface_settings"] = adapter_dce_interface_settings

                if vic_adapter_config["enable_fip"] is not None:
                    from intersight.model.adapter_fc_settings import AdapterFcSettings

                    adapter_fc_settings_kwargs = {
                        "object_type": "adapter.FcSettings",
                        "class_id": "adapter.FcSettings",
                        "fip_enabled": vic_adapter_config["enable_fip"]
                    }
                    adapter_adapter_config_kwargs["fc_settings"] = AdapterFcSettings(**adapter_fc_settings_kwargs)

                if vic_adapter_config["enable_lldp"] is not None:
                    from intersight.model.adapter_eth_settings import AdapterEthSettings

                    adapter_eth_settings_kwargs = {
                        "object_type": "adapter.EthSettings",
                        "class_id": "adapter.EthSettings",
                        "lldp_enabled": vic_adapter_config["enable_lldp"]
                    }
                    adapter_adapter_config_kwargs["eth_settings"] = AdapterEthSettings(**adapter_eth_settings_kwargs)

                if vic_adapter_config["enable_port_channel"] is not None:
                    from intersight.model.adapter_port_channel_settings import AdapterPortChannelSettings

                    adapter_port_channel_settings_kwargs = {
                        "object_type": "adapter.PortChannelSettings",
                        "class_id": "adapter.PortChannelSettings",
                        "enabled": vic_adapter_config["enable_port_channel"]
                    }
                    adapter_adapter_config_kwargs["port_channel_settings"] = \
                        AdapterPortChannelSettings(**adapter_port_channel_settings_kwargs)

                if vic_adapter_config["enable_physical_nic_mode"] is not None:
                    from intersight.model.adapter_physical_nic_mode_settings import AdapterPhysicalNicModeSettings

                    physical_nic_mode_settings_kwargs = {
                        "object_type": "adapter.PhysicalNicModeSettings",
                        "class_id": "adapter.PhysicalNicModeSettings",
                        "phy_nic_enabled": vic_adapter_config["enable_physical_nic_mode"]
                    }
                    adapter_adapter_config_kwargs["physical_nic_mode_settings"] = \
                        AdapterPhysicalNicModeSettings(**physical_nic_mode_settings_kwargs)

                settings.append(AdapterAdapterConfig(**adapter_adapter_config_kwargs))

            kwargs["settings"] = settings

        adapter_config_policy = AdapterConfigPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=adapter_config_policy,
                           detail=self.name):
            return False

        return True


class IntersightBiosPolicy(IntersightConfigObject):
    _CONFIG_NAME = "BIOS Policy"
    _CONFIG_SECTION_NAME = "bios_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "bios.Policy"

    def __init__(self, parent=None, bios_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=bios_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")

        # Set all the BIOS options
        if self._config.bios_table:
            for token in self._config.bios_table:
                setattr(self, token, self.get_attribute(attribute_name=token))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.bios_policy import BiosPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        bios_table = read_json_file(
            file_path="config/intersight/bios_table.json", logger=self)
        if not bios_table:
            self.logger(level="error", message="BIOS Table not imported.")

        # Set all the BIOS options
        if bios_table:
            for token in bios_table:
                if hasattr(self, token):
                    if getattr(self, token) is not None:
                        kwargs[token] = getattr(self, token)

        bios_policy = BiosPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=bios_policy, detail=self.name):
            return False

        return True


class IntersightBootPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Boot Policy"
    _CONFIG_SECTION_NAME = "boot_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "boot.PrecisionPolicy"

    def __init__(self, parent=None, boot_precision_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=boot_precision_policy)

        self.boot_mode = self.get_attribute(attribute_name="configured_boot_mode", attribute_secondary_name="boot_mode")
        self.boot_devices = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_secure_boot = self.get_attribute(attribute_name="enforce_uefi_secure_boot",
                                                     attribute_secondary_name="enable_secure_boot")
        self.name = self.get_attribute(attribute_name="name")

        if self._config.load_from == "live":
            if hasattr(self._object, "boot_devices"):
                self.boot_devices = []
                for boot_device in self._object.boot_devices:
                    boot_entry = {"device_name": boot_device.name, "enabled": boot_device.enabled}
                    if hasattr(boot_device, "bootloader"):
                        boot_entry["bootloader_name"] = None
                        boot_entry["bootloader_description"] = None
                        boot_entry["bootloader_path"] = None
                        if boot_device.bootloader:
                            if boot_device.bootloader.name:
                                boot_entry["bootloader_name"] = boot_device.bootloader.name
                            if boot_device.bootloader.description:
                                boot_entry["bootloader_description"] = boot_device.bootloader.description
                            if boot_device.bootloader.path:
                                boot_entry["bootloader_path"] = boot_device.bootloader.path

                    if boot_device.class_id in ["boot.Iscsi"]:
                        boot_entry["device_type"] = "iscsi_boot"
                        boot_entry["slot"] = boot_device.slot
                        boot_entry["interface_name"] = boot_device.interface_name
                        boot_entry["port"] = boot_device.port
                    elif boot_device.class_id in ["boot.FlexMmc"]:
                        boot_entry["device_type"] = "flex_mmc"
                        boot_entry["subtype"] = boot_device.subtype
                    elif boot_device.class_id in ["boot.LocalCdd"]:
                        boot_entry["device_type"] = "local_cdd"
                    elif boot_device.class_id in ["boot.LocalDisk"]:
                        boot_entry["device_type"] = "local_disk"
                        boot_entry["slot"] = boot_device.slot
                    elif boot_device.class_id in ["boot.Nvme"]:
                        boot_entry["device_type"] = "nvme"
                    elif boot_device.class_id in ["boot.PchStorage"]:
                        boot_entry["device_type"] = "pch_storage"
                        boot_entry["lun"] = boot_device.lun
                    elif boot_device.class_id in ["boot.Pxe"]:
                        boot_entry["device_type"] = "pxe_boot"
                        boot_entry["ip_type"] = boot_device.ip_type
                        boot_entry["slot"] = boot_device.slot
                        boot_entry["interface_source"] = boot_device.interface_source
                        if boot_entry["interface_source"] in ["name"]:
                            boot_entry["interface_name"] = boot_device.interface_name
                        elif boot_entry["interface_source"] in ["mac"]:
                            boot_entry["mac_address"] = boot_device.mac_address
                        elif boot_entry["interface_source"] in ["port"]:
                            boot_entry["port"] = boot_device.port
                    elif boot_device.class_id in ["boot.San"]:
                        boot_entry["device_type"] = "san_boot"
                        boot_entry["lun"] = boot_device.lun
                        boot_entry["slot"] = boot_device.slot
                        boot_entry["interface_name"] = boot_device.interface_name
                        boot_entry["target_wwpn"] = boot_device.wwpn
                    elif boot_device.class_id in ["boot.SdCard"]:
                        boot_entry["device_type"] = "sd_card"
                        boot_entry["lun"] = boot_device.lun
                        boot_entry["subtype"] = boot_device.subtype
                    elif boot_device.class_id in ["boot.UefiShell"]:
                        boot_entry["device_type"] = "uefi_shell"
                    elif boot_device.class_id in ["boot.Usb"]:
                        boot_entry["device_type"] = "usb"
                        boot_entry["subtype"] = boot_device.subtype
                    elif boot_device.class_id in ["boot.VirtualMedia"]:
                        boot_entry["device_type"] = "virtual_media"
                        boot_entry["subtype"] = boot_device.subtype
                    elif boot_device.class_id in ["boot.Http"]:
                        boot_entry["device_type"] = "http_boot"
                        boot_entry["ip_type"] = boot_device.ip_type
                        boot_entry["ip_config_type"] = boot_device.ip_config_type
                        boot_entry["slot"] = boot_device.slot
                        boot_entry["protocol"] = boot_device.protocol
                        boot_entry["uri"] = boot_device.uri
                        if boot_entry["ip_config_type"] in ["Static"]:
                            if boot_device.ip_type == "IPv4" and getattr(boot_device, "static_ip_v4_settings"):
                                boot_entry["static_ip"] = boot_device.static_ip_v4_settings["ip"]
                                boot_entry["dns_ip"] = boot_device.static_ip_v4_settings["dns_ip"]
                                boot_entry["gateway_ip"] = boot_device.static_ip_v4_settings["gateway_ip"]
                                boot_entry["network_mask"] = boot_device.static_ip_v4_settings["network_mask"]

                            elif boot_device.ip_type == "IPv6" and getattr(boot_device, "static_ip_v6_settings"):
                                boot_entry["static_ip"] = boot_device.static_ip_v6_settings["ip"]
                                boot_entry["dns_ip"] = boot_device.static_ip_v6_settings["dns_ip"]
                                boot_entry["gateway_ip"] = boot_device.static_ip_v6_settings["gateway_ip"]
                                boot_entry["prefix_length"] = boot_device.static_ip_v6_settings["prefix_length"]

                        boot_entry["interface_source"] = boot_device.interface_source
                        if boot_entry["interface_source"] in ["name"]:
                            boot_entry["interface_name"] = boot_device.interface_name
                        elif boot_entry["interface_source"] in ["mac"]:
                            boot_entry["mac_address"] = boot_device.mac_address
                        elif boot_entry["interface_source"] in ["port"]:
                            boot_entry["port"] = boot_device.port

                    self.boot_devices.append(boot_entry)

        elif self._config.load_from == "file":
            for attribute in ["boot_devices"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a Boot Device are set to None if they are not present
        if self.boot_devices:
            for boot_device in self.boot_devices:
                for attribute in [
                    "device_type", "device_name", "dns_ip", "enabled", "bootloader_name", "bootloader_description",
                    "bootloader_path", "gateway_ip", "interface_name", "interface_source", "ip_config_type", "ip_type",
                    "lun", "mac_address", "network_mask", "port", "prefix_length", "protocol", "slot", "subtype",
                    "static_ip", "target_wwpn", "uri"
                ]:
                    if attribute not in boot_device:
                        boot_device[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.boot_precision_policy import BootPrecisionPolicy
        from intersight.model.boot_bootloader import BootBootloader

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.boot_mode is not None:
            kwargs["configured_boot_mode"] = self.boot_mode
        if self.enable_secure_boot is not None:
            kwargs["enforce_uefi_secure_boot"] = self.enable_secure_boot

        if self.boot_devices is not None:
            kwargs["boot_devices"] = []
            for boot_device in self.boot_devices:
                kwargs_bootloader = {
                    'class_id': 'boot.Bootloader',
                    'description': '',
                    'name': '',
                    'object_type': 'boot.Bootloader',
                    'path': ''
                }
                if boot_device["device_type"] == "iscsi_boot":
                    from intersight.model.boot_iscsi import BootIscsi
                    kwargs_boot_device = {
                        "object_type": "boot.Iscsi",
                        "class_id": "boot.Iscsi",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["interface_name"] is not None:
                        kwargs_boot_device["interface_name"] = boot_device["interface_name"]
                    if boot_device["port"] is not None:
                        kwargs_boot_device["port"] = boot_device["port"]
                    if boot_device["slot"] is not None:
                        kwargs_boot_device["slot"] = boot_device["slot"]

                    if boot_device["bootloader_name"] is not None:
                        kwargs_boot_device["bootloader_name"] = boot_device["bootloader_name"]
                    if boot_device["bootloader_path"] is not None:
                        kwargs_boot_device["bootloader_path"] = boot_device["bootloader_path"]
                    if boot_device["bootloader_description"] is not None:
                        kwargs_boot_device["bootloader_description"] = boot_device["bootloader_description"]
                    kwargs["boot_devices"].append(BootIscsi(**kwargs_boot_device))

                elif boot_device["device_type"] == "local_cdd":
                    from intersight.model.boot_local_cdd import BootLocalCdd
                    kwargs_boot_device = {
                        "object_type": "boot.LocalCdd",
                        "class_id": "boot.LocalCdd",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    kwargs["boot_devices"].append(BootLocalCdd(**kwargs_boot_device))

                elif boot_device["device_type"] == "local_disk":
                    from intersight.model.boot_local_disk import BootLocalDisk
                    kwargs_boot_device = {
                        "object_type": "boot.LocalDisk",
                        "class_id": "boot.LocalDisk",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["slot"] is not None:
                        kwargs_boot_device["slot"] = boot_device["slot"]

                    if boot_device["bootloader_name"] is not None:
                        kwargs_bootloader["name"] = boot_device["bootloader_name"]
                    if boot_device["bootloader_path"] is not None:
                        kwargs_bootloader["path"] = boot_device["bootloader_path"]
                    if boot_device["bootloader_description"] is not None:
                        kwargs_bootloader["description"] = boot_device["bootloader_description"]
                    kwargs_boot_device["bootloader"] = BootBootloader(**kwargs_bootloader)

                    kwargs["boot_devices"].append(BootLocalDisk(**kwargs_boot_device))

                elif boot_device["device_type"] == "flex_mmc":
                    from intersight.model.boot_flex_mmc import BootFlexMmc
                    kwargs_boot_device = {
                        "object_type": "boot.FlexMmc",
                        "class_id": "boot.FlexMmc",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["subtype"] is not None:
                        kwargs_boot_device["subtype"] = boot_device["subtype"]
                    if boot_device["bootloader_name"] is not None:
                        kwargs_bootloader["name"] = boot_device["bootloader_name"]
                    if boot_device["bootloader_path"] is not None:
                        kwargs_bootloader["path"] = boot_device["bootloader_path"]
                    if boot_device["bootloader_description"] is not None:
                        kwargs_bootloader["description"] = boot_device["bootloader_description"]
                    kwargs_boot_device["bootloader"] = BootBootloader(**kwargs_bootloader)

                    kwargs["boot_devices"].append(BootFlexMmc(**kwargs_boot_device))

                elif boot_device["device_type"] == "nvme":
                    from intersight.model.boot_nvme import BootNvme
                    kwargs_boot_device = {
                        "object_type": "boot.Nvme",
                        "class_id": "boot.Nvme",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]

                    if boot_device["bootloader_name"] is not None:
                        kwargs_bootloader["name"] = boot_device["bootloader_name"]
                    if boot_device["bootloader_path"] is not None:
                        kwargs_bootloader["path"] = boot_device["bootloader_path"]
                    if boot_device["bootloader_description"] is not None:
                        kwargs_bootloader["description"] = boot_device["bootloader_description"]
                    kwargs_boot_device["bootloader"] = BootBootloader(**kwargs_bootloader)

                    kwargs["boot_devices"].append(BootNvme(**kwargs_boot_device))

                elif boot_device["device_type"] == "pch_storage":
                    from intersight.model.boot_pch_storage import BootPchStorage
                    kwargs_boot_device = {
                        "object_type": "boot.PchStorage",
                        "class_id": "boot.PchStorage",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["lun"] is not None:
                        kwargs_boot_device["lun"] = boot_device["lun"]

                    if boot_device["bootloader_name"] is not None:
                        kwargs_bootloader["name"] = boot_device["bootloader_name"]
                    if boot_device["bootloader_path"] is not None:
                        kwargs_bootloader["path"] = boot_device["bootloader_path"]
                    if boot_device["bootloader_description"] is not None:
                        kwargs_bootloader["description"] = boot_device["bootloader_description"]
                    kwargs_boot_device["bootloader"] = BootBootloader(**kwargs_bootloader)

                    kwargs["boot_devices"].append(BootPchStorage(**kwargs_boot_device))

                elif boot_device["device_type"] == "http_boot":
                    from intersight.model.boot_http import BootHttp
                    kwargs_boot_device = {
                        "object_type": "boot.Http",
                        "class_id": "boot.Http",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["interface_name"] is not None:
                        kwargs_boot_device["interface_name"] = boot_device["interface_name"]
                    if boot_device["interface_source"] is not None:
                        kwargs_boot_device["interface_source"] = boot_device["interface_source"]
                    if boot_device["ip_type"] is not None:
                        kwargs_boot_device["ip_type"] = boot_device["ip_type"]
                    if boot_device["mac_address"] is not None:
                        kwargs_boot_device["mac_address"] = boot_device["mac_address"]
                    if boot_device["port"] is not None:
                        kwargs_boot_device["port"] = boot_device["port"]
                    if boot_device["slot"] is not None:
                        kwargs_boot_device["slot"] = boot_device["slot"]
                    if boot_device["ip_config_type"] is not None:
                        kwargs_boot_device["ip_config_type"] = boot_device["ip_config_type"]
                    if boot_device["protocol"] is not None:
                        kwargs_boot_device["protocol"] = boot_device["protocol"]
                    if boot_device["uri"] is not None:
                        kwargs_boot_device["uri"] = boot_device["uri"]
                    if boot_device["ip_config_type"] == "Static" and boot_device["ip_type"] == "IPv4":
                        from intersight.model.boot_static_ip_v4_settings import BootStaticIpV4Settings
                        kwargs_boot_static_ipv4_settings = {
                            "object_type": "boot.StaticIpV4Settings",
                            "class_id": "boot.StaticIpV4Settings"
                        }
                        kwargs_boot_static_ipv4_settings["dns_ip"] = boot_device["dns_ip"]
                        kwargs_boot_static_ipv4_settings["gateway_ip"] = boot_device["gateway_ip"]
                        kwargs_boot_static_ipv4_settings["ip"] = boot_device["static_ip"]
                        kwargs_boot_static_ipv4_settings["network_mask"] = boot_device["network_mask"]
                        kwargs_boot_device["static_ip_v4_settings"] = BootStaticIpV4Settings(
                            **kwargs_boot_static_ipv4_settings)

                    elif boot_device["ip_config_type"] == "Static" and boot_device["ip_type"] == "IPv6":
                        from intersight.model.boot_static_ip_v6_settings import BootStaticIpV6Settings
                        kwargs_boot_static_ipv6_settings = {
                            "object_type": "boot.StaticIpV6Settings",
                            "class_id": "boot.StaticIpV6Settings"
                        }
                        kwargs_boot_static_ipv6_settings["dns_ip"] = boot_device["dns_ip"]
                        kwargs_boot_static_ipv6_settings["gateway_ip"] = boot_device["gateway_ip"]
                        kwargs_boot_static_ipv6_settings["ip"] = boot_device["static_ip"]
                        kwargs_boot_static_ipv6_settings["prefix_length"] = boot_device["prefix_length"]
                        kwargs_boot_device["static_ip_v6_settings"] = BootStaticIpV6Settings(
                            **kwargs_boot_static_ipv6_settings)

                    kwargs["boot_devices"].append(BootHttp(**kwargs_boot_device))

                elif boot_device["device_type"] == "pxe_boot":
                    from intersight.model.boot_pxe import BootPxe
                    kwargs_boot_device = {
                        "object_type": "boot.Pxe",
                        "class_id": "boot.Pxe",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["interface_name"] is not None:
                        kwargs_boot_device["interface_name"] = boot_device["interface_name"]
                    if boot_device["interface_source"] is not None:
                        kwargs_boot_device["interface_source"] = boot_device["interface_source"]
                    if boot_device["ip_type"] is not None:
                        kwargs_boot_device["ip_type"] = boot_device["ip_type"]
                    if boot_device["mac_address"] is not None:
                        kwargs_boot_device["mac_address"] = boot_device["mac_address"]
                    if boot_device["port"] is not None:
                        kwargs_boot_device["port"] = boot_device["port"]
                    if boot_device["slot"] is not None:
                        kwargs_boot_device["slot"] = boot_device["slot"]
                    kwargs["boot_devices"].append(BootPxe(**kwargs_boot_device))

                elif boot_device["device_type"] == "san_boot":
                    from intersight.model.boot_san import BootSan
                    kwargs_boot_device = {
                        "object_type": "boot.San",
                        "class_id": "boot.San",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["interface_name"] is not None:
                        kwargs_boot_device["interface_name"] = boot_device["interface_name"]
                    if boot_device["lun"] is not None:
                        kwargs_boot_device["lun"] = boot_device["lun"]
                    if boot_device["slot"] is not None:
                        kwargs_boot_device["slot"] = boot_device["slot"]
                    if boot_device["target_wwpn"] is not None:
                        kwargs_boot_device["wwpn"] = boot_device["target_wwpn"]

                    if boot_device["bootloader_name"] is not None:
                        kwargs_bootloader["name"] = boot_device["bootloader_name"]
                    if boot_device["bootloader_path"] is not None:
                        kwargs_bootloader["path"] = boot_device["bootloader_path"]
                    if boot_device["bootloader_description"] is not None:
                        kwargs_bootloader["description"] = boot_device["bootloader_description"]
                    kwargs_boot_device["bootloader"] = BootBootloader(**kwargs_bootloader)

                    kwargs["boot_devices"].append(BootSan(**kwargs_boot_device))

                elif boot_device["device_type"] == "sd_card":
                    from intersight.model.boot_sd_card import BootSdCard
                    kwargs_boot_device = {
                        "object_type": "boot.SdCard",
                        "class_id": "boot.SdCard",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["lun"] is not None:
                        kwargs_boot_device["lun"] = boot_device["lun"]
                    if boot_device["subtype"] is not None:
                        kwargs_boot_device["subtype"] = boot_device["subtype"]

                    if boot_device["bootloader_name"] is not None:
                        kwargs_bootloader["name"] = boot_device["bootloader_name"]
                    if boot_device["bootloader_path"] is not None:
                        kwargs_bootloader["path"] = boot_device["bootloader_path"]
                    if boot_device["bootloader_description"] is not None:
                        kwargs_bootloader["description"] = boot_device["bootloader_description"]
                    kwargs_boot_device["bootloader"] = BootBootloader(**kwargs_bootloader)

                    kwargs["boot_devices"].append(BootSdCard(**kwargs_boot_device))

                elif boot_device["device_type"] == "uefi_shell":
                    from intersight.model.boot_uefi_shell import BootUefiShell
                    kwargs_boot_device = {
                        "object_type": "boot.UefiShell",
                        "class_id": "boot.UefiShell",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    kwargs["boot_devices"].append(BootUefiShell(**kwargs_boot_device))

                elif boot_device["device_type"] == "usb":
                    from intersight.model.boot_usb import BootUsb
                    kwargs_boot_device = {
                        "object_type": "boot.Usb",
                        "class_id": "boot.Usb",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["subtype"] is not None:
                        kwargs_boot_device["subtype"] = boot_device["subtype"]
                    kwargs["boot_devices"].append(BootUsb(**kwargs_boot_device))

                elif boot_device["device_type"] == "virtual_media":
                    from intersight.model.boot_virtual_media import BootVirtualMedia
                    kwargs_boot_device = {
                        "object_type": "boot.VirtualMedia",
                        "class_id": "boot.VirtualMedia",
                        "name": boot_device["device_name"]
                    }
                    if boot_device["enabled"] is not None:
                        kwargs_boot_device["enabled"] = boot_device["enabled"]
                    if boot_device["subtype"] is not None:
                        kwargs_boot_device["subtype"] = boot_device["subtype"]
                    kwargs["boot_devices"].append(BootVirtualMedia(**kwargs_boot_device))

        boot_precision_policy = BootPrecisionPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=boot_precision_policy,
                           detail=self.name):
            return False

        return True


class IntersightCertificateManagementPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Certificate Management Policy"
    _CONFIG_SECTION_NAME = "certificate_management_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "certificatemanagement.Policy"

    def __init__(self, parent=None, certificatemanagement_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=certificatemanagement_policy)

        self.name = self.get_attribute(attribute_name="name")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.certificates = None

        if self._config.load_from == "live":
            if hasattr(self._object, "certificates") and self._object.certificates is not None:
                for cert in self._object.certificates:
                    cert_type = getattr(cert, "object_type", None)
                    certificate_data = {}

                    if hasattr(cert, "certificate"):
                        cert_contents = getattr(cert, "certificate")
                        if hasattr(cert_contents, "pem_certificate"):
                            certificate_data["certificate"] = get_decoded_pem_certificate(
                                certificate=getattr(cert_contents, "pem_certificate")
                            )

                    if hasattr(cert, "enabled"):
                        certificate_data["enable"] = cert.enabled

                    if cert_type == "certificatemanagement.Imc":
                        if hasattr(cert, "is_privatekey_set") and cert.is_privatekey_set:
                            self.logger(
                                level="warning",
                                message=f"Private Key of {self._CONFIG_NAME} {self.name} - IMC Certificate can't be exported"
                            )
                        if certificate_data:
                            if self.certificates is None:
                                self.certificates = {}
                            self.certificates["imc_certificate"] = certificate_data

                    elif cert_type == "certificatemanagement.RootCaCertificate":
                        if hasattr(cert, "certificate_name"):
                            certificate_data["certificate_name"] = cert.certificate_name
                        if certificate_data:
                            if self.certificates is None:
                                self.certificates = {}
                            if "root_ca_certificates" not in self.certificates:
                                self.certificates["root_ca_certificates"] = []
                            self.certificates["root_ca_certificates"].append(certificate_data)

        elif self._config.load_from == "file":
            for attribute in ["certificates"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a Certificate are set to None if they are not present
        if self.certificates:
            for attribute in ["imc_certificate", "root_ca_certificates"]:
                if attribute not in self.certificates:
                    self.certificates[attribute] = None

                if self.certificates.get("imc_certificate"):
                    for sub_attribute in ["certificate", "enable", "private_key"]:
                        if sub_attribute not in self.certificates["imc_certificate"]:
                            self.certificates["imc_certificate"][sub_attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.certificatemanagement_policy import CertificatemanagementPolicy
        from intersight.model.certificatemanagement_root_ca_certificate import CertificatemanagementRootCaCertificate
        from intersight.model.x509_certificate import X509Certificate
        from intersight.model.certificatemanagement_imc import CertificatemanagementImc

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        existing_certificates = []

        # Query Intersight to check if a policy with the specified name already exists
        existing_policies = self._device.query(
            object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
            filter=f"Name eq '{self.name}' and Organization.Moid eq '{self.get_parent_org_relationship().moid}'"
        )
        # If the policy exists, retrieve its details
        if existing_policies:
            existing_policy = existing_policies[0]
            if hasattr(existing_policy, "certificates") and existing_policy.certificates:
                existing_certificates = existing_policy.certificates

        # Check if "overwrite" is enabled in settings
        overwrite_enabled = getattr(self._config, "update_existing_intersight_objects", False)

        # Preserve existing certificates
        # Ensure existing certificates are retained and not overwritten
        certificates = existing_certificates.copy()

        # Modify the existing IMC certificate ONLY if overwrite is enabled AND a new IMC cert is provided
        if overwrite_enabled and self.certificates.get("imc_certificate"):
            certificates = [cert for cert in certificates if cert.object_type != "certificatemanagement.Imc"]

        # Check if an IMC certificate already exists in the current policy
        existing_imc_certificate = any(
            cert.object_type == "certificatemanagement.Imc" for cert in existing_certificates
        )

        if self.certificates:
            # Process IMC Certificate
            if self.certificates.get("imc_certificate"):
                if existing_imc_certificate and not overwrite_enabled:
                    self.logger(level="warning", message="IMC certificate already exists in policy. Skipping addition.")
                else:
                    # Remove existing IMC certificate if overwrite is enabled
                    certificates = [cert for cert in certificates if cert.object_type != "certificatemanagement.Imc"]

                    imc_certificate = self.certificates["imc_certificate"]
                    cert_kwargs = {
                        "object_type": "certificatemanagement.Imc",
                        "class_id": "certificatemanagement.Imc"
                    }
                    if imc_certificate.get("enable") is not None:
                        cert_kwargs["enabled"] = imc_certificate["enable"]

                    # Because we cannot fetch the original private key from Intersight, we can have 2 scenarios:
                    # 1. The config file is explicitly populated with certificate and private key fields. In this case we
                    # use them and proceed with the push config.
                    # 2. We only have certificate, but not the private key. In this case we generate our own certificate
                    # and private key which enables us to successfully push the policy to Intersight.
                    certificate = None
                    if imc_certificate.get("certificate"):
                        certificate = imc_certificate.get("certificate")

                    if imc_certificate.get("private_key"):
                        private_key = imc_certificate.get("private_key")
                    else:
                        self.logger(level="warning", message="Private Key not found. Using self signed certificate"
                                                             " to create " + self._CONFIG_NAME + " " + self.name)
                        try:
                            private_key, certificate = generate_self_signed_cert()
                        except Exception as err:
                            err_message = "Error in generating certificate and private key: " + str(err)
                            self.logger(level="error", message=err_message)
                            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=self.name,
                                                                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                                                                                status="failed", message=err_message)
                            return False

                    if private_key:
                        cert_kwargs["privatekey"] = get_encoded_pem_certificate(private_key)

                    if certificate:
                        x509_certificate_kwargs = {
                            "object_type": "x509.Certificate",
                            "class_id": "x509.Certificate",
                            "pem_certificate": get_encoded_pem_certificate(certificate)
                        }
                        cert_kwargs["certificate"] = X509Certificate(**x509_certificate_kwargs)

                    certificates.append(CertificatemanagementImc(**cert_kwargs))

            # Process Root CA Certificates
            if self.certificates.get("root_ca_certificates"):
                for root_ca_cert in self.certificates["root_ca_certificates"]:
                    cert_name = root_ca_cert.get("certificate_name")
                    # Check if a Root CA certificate with the same name already exists in the policy
                    existing_root_ca_cert = next(
                        (cert for cert in existing_certificates if
                         cert.object_type == "certificatemanagement.RootCaCertificate"
                         and getattr(cert, "certificate_name", None) == cert_name), None
                    )

                    if existing_root_ca_cert:
                        if overwrite_enabled:
                            self.logger(level="info",
                                        message=f"Overwriting existing Root CA certificate '{cert_name}' in policy.")
                            certificates = [
                                cert for cert in certificates
                                if not (
                                            cert.object_type == "certificatemanagement.RootCaCertificate"
                                            and cert.certificate_name == cert_name)
                            ]
                        else:
                            self.logger(level="warning",
                                        message=f"Root CA certificate '{cert_name}' already exists. Skipping addition.")
                            continue
                    cert_kwargs = {
                        "object_type": "certificatemanagement.RootCaCertificate",
                        "class_id": "certificatemanagement.RootCaCertificate"
                    }
                    if root_ca_cert.get("enable") is not None:
                        cert_kwargs["enabled"] = root_ca_cert["enable"]
                    if root_ca_cert.get("certificate_name"):
                        cert_kwargs["certificate_name"] = root_ca_cert["certificate_name"]

                    if root_ca_cert.get("certificate"):
                        x509_certificate_kwargs = {
                            "object_type": "x509.Certificate",
                            "class_id": "x509.Certificate",
                            "pem_certificate": get_encoded_pem_certificate(root_ca_cert["certificate"])
                        }
                        cert_kwargs["certificate"] = X509Certificate(**x509_certificate_kwargs)

                    certificates.append(CertificatemanagementRootCaCertificate(**cert_kwargs))

        kwargs["certificates"] = certificates

        certificatemanagement_policy = CertificatemanagementPolicy(**kwargs)

        # Set modify_present based on overwrite settings
        modify_present = overwrite_enabled
        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=certificatemanagement_policy,
                           detail=self.name, modify_present=modify_present):
            return False

        self._config.push_summary_manager.add_object_message(
            obj=self,
            message="Successfully created Certificate Management Policy with automatic self-signed certificate and " +
                    "private key. Please update the policy manually in Intersight if a specific certificate is desired."
        )
        return True


class IntersightDeviceConnectorPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Device Connector Policy"
    _CONFIG_SECTION_NAME = "device_connector_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "deviceconnector.Policy"

    def __init__(self, parent=None, deviceconnector_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=deviceconnector_policy)

        self.configuration_from_intersight_only = \
            self.get_attribute(attribute_name="lockout_enabled",
                               attribute_secondary_name="configuration_from_intersight_only")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.deviceconnector_policy import DeviceconnectorPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.configuration_from_intersight_only is not None:
            kwargs["lockout_enabled"] = self.configuration_from_intersight_only

        deviceconnector_policy = DeviceconnectorPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=deviceconnector_policy,
                           detail=self.name):
            return False

        return True


class IntersightDriveSecurityPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Drive Security Policy"
    _CONFIG_SECTION_NAME = "drive_security_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "storage.DriveSecurityPolicy"

    def __init__(self, parent=None, storage_drive_security_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=storage_drive_security_policy)

        self.name = self.get_attribute(attribute_name="name")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.primary_kmip_server = None
        self.secondary_kmip_server = None
        self.server_public_root_ca_certificate = None
        self.authentication_credentials = None

        if self._config.load_from == "live":
            if hasattr(self._object, "key_setting"):
                storage_key_setting = getattr(self._object, "key_setting")
                if hasattr(storage_key_setting, "remote_key"):
                    if storage_key_setting.remote_key.auth_credentials:
                        self.authentication_credentials = {}
                        self.authentication_credentials["enable_authentication"] = \
                            storage_key_setting.remote_key.auth_credentials.use_authentication
                        if self.authentication_credentials["enable_authentication"]:
                            self.authentication_credentials["username"] = \
                                storage_key_setting.remote_key.auth_credentials.username
                            if storage_key_setting.remote_key.auth_credentials.is_password_set:
                                self.logger(
                                    level="warning",
                                    message=f"The Password of {self._CONFIG_NAME} '{self.name}' of user - " +
                                            f"{storage_key_setting.remote_key.auth_credentials.username} " +
                                            f"can't be exported"
                                )

                    if hasattr(storage_key_setting.remote_key, "primary_server"):
                        if getattr(storage_key_setting.remote_key, "primary_server"):
                            self.primary_kmip_server = {}
                            self.primary_kmip_server["enable_drive_security"] = True if \
                                storage_key_setting.remote_key.primary_server.enable_drive_security is True else False
                            if self.primary_kmip_server["enable_drive_security"]:

                                storage_kmip_server = storage_key_setting.remote_key.primary_server
                                self.primary_kmip_server.update({"ip_address": storage_kmip_server.ip_address,
                                                                 "port": storage_kmip_server.port,
                                                                 "timeout": storage_kmip_server.timeout})

                    if hasattr(storage_key_setting.remote_key, "secondary_server"):
                        if getattr(storage_key_setting.remote_key, "secondary_server"):
                            self.secondary_kmip_server = {}
                            self.secondary_kmip_server["enable_drive_security"] = True if \
                                storage_key_setting.remote_key.secondary_server.enable_drive_security is True else False
                            if self.secondary_kmip_server["enable_drive_security"]:
                                storage_kmip_server = storage_key_setting.remote_key.secondary_server
                                self.secondary_kmip_server.update({"ip_address": storage_kmip_server.ip_address,
                                                                   "port": storage_kmip_server.port,
                                                                   "timeout": storage_kmip_server.timeout})

                    if hasattr(storage_key_setting.remote_key, "server_certificate") and \
                            getattr(storage_key_setting.remote_key, "server_certificate"):
                        self.server_public_root_ca_certificate = get_decoded_pem_certificate(
                            storage_key_setting.remote_key.server_certificate)

        elif self._config.load_from == "file":
            for attribute in ["primary_kmip_server", "secondary_kmip_server", "server_public_root_ca_certificate",
                              "authentication_credentials"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        if self.primary_kmip_server:
            for attribute in ["enable_drive_security", "ip_address", "port", "timeout"]:
                if attribute not in self.primary_kmip_server:
                    self.primary_kmip_server[attribute] = None

        if self.secondary_kmip_server:
            for attribute in ["enable_drive_security", "ip_address", "port", "timeout"]:
                if attribute not in self.secondary_kmip_server:
                    self.secondary_kmip_server[attribute] = None

        if self.authentication_credentials:
            for attribute in ["enable_authentication", "username", "password"]:
                if attribute not in self.authentication_credentials:
                    self.authentication_credentials[attribute] = None

    @staticmethod
    def _get_valid_certificate(certificate=None):
        """Provides a valid PEM certificate"""
        # Split the certificate by lines
        lines = certificate.split()

        # Join lines with '\n' except the first and last
        valid_certificate = ' '.join(
            [lines[0], lines[1]]) + ''.join([f"\n{line}" for line in lines[2:-2]] + [f"\n{lines[-2]} {lines[-1]}"])

        return valid_certificate

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.storage_drive_security_policy import StorageDriveSecurityPolicy

        self.logger(message=f"pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }

        if self.name:
            kwargs["name"] = self.name
        if self.descr:
            kwargs["description"] = self.descr
        if self.tags:
            kwargs["tags"] = self.create_tags()

        from intersight.model.storage_key_setting import StorageKeySetting

        key_setting_kwargs = {
            "object_type": "storage.KeySetting",
            "class_id": "storage.KeySetting"
        }

        from intersight.model.storage_remote_key_setting import StorageRemoteKeySetting

        remote_key_setting_kwargs = {
            "object_type": "storage.RemoteKeySetting",
            "class_id": "storage.RemoteKeySetting"
        }

        if self.server_public_root_ca_certificate:
            remote_key_setting_kwargs["server_certificate"] = get_encoded_pem_certificate(
                self.server_public_root_ca_certificate)

        if self.authentication_credentials:
            from intersight.model.storage_kmip_auth_credentials import StorageKmipAuthCredentials
            kmip_auth_credentials_kwargs = {
                "object_type": "storage.KmipAuthCredentials",
                "class_id": "storage.KmipAuthCredentials"
            }
            if self.authentication_credentials["enable_authentication"]:
                kmip_auth_credentials_kwargs["use_authentication"] = \
                    self.authentication_credentials["enable_authentication"]
            if self.authentication_credentials["username"]:
                kmip_auth_credentials_kwargs["username"] = self.authentication_credentials["username"]

                if self.authentication_credentials["password"]:
                    kmip_auth_credentials_kwargs["password"] = self.authentication_credentials["password"]

                else:
                    self.logger(
                        level="warning",
                        message="No password provided for field 'password' of object storage.KmipAuthCredentials"
                    )
            remote_key_setting_kwargs["auth_credentials"] = StorageKmipAuthCredentials(**kmip_auth_credentials_kwargs)

        if self.primary_kmip_server or self.secondary_kmip_server:
            from intersight.model.storage_kmip_server import StorageKmipServer

            kmip_properties_present = False
            kmip_server_kwargs = {
                "object_type": "storage.KmipServer",
                "class_id": "storage.KmipServer"
            }
            kmip_server_attributes = ["enable_drive_security", "ip_address", "port", "timeout"]
            if self.primary_kmip_server:
                for attribute in kmip_server_attributes:
                    if self.primary_kmip_server[attribute]:
                        kmip_properties_present = True
                        kmip_server_kwargs[attribute] = self.primary_kmip_server[attribute]
                if kmip_properties_present:
                    remote_key_setting_kwargs["primary_server"] = StorageKmipServer(**kmip_server_kwargs)
                    kmip_properties_present = False
            if self.secondary_kmip_server:
                for attribute in kmip_server_attributes:
                    if self.secondary_kmip_server[attribute]:
                        kmip_properties_present = True
                        kmip_server_kwargs[attribute] = self.secondary_kmip_server[attribute]
                if kmip_properties_present:
                    remote_key_setting_kwargs["secondary_server"] = StorageKmipServer(**kmip_server_kwargs)

        key_setting_kwargs["remote_key"] = StorageRemoteKeySetting(**remote_key_setting_kwargs)
        kwargs["key_setting"] = StorageKeySetting(**key_setting_kwargs)

        drive_security_policy = StorageDriveSecurityPolicy(**kwargs)

        if not self.commit(
                object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=drive_security_policy, detail=self.name):
            return False


class IntersightEthernetAdapterPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Ethernet Adapter Policy"
    _CONFIG_SECTION_NAME = "ethernet_adapter_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.EthAdapterPolicy"

    def __init__(self, parent=None, ethernet_adapter_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=ethernet_adapter_policy)

        self.completion_queue_count = None
        self.completion_ring_size = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_accelerated_receive_flow_steering = None
        self.enable_advanced_filter = self.get_attribute(attribute_name="advanced_filter",
                                                         attribute_secondary_name="enable_advanced_filter")
        self.enable_etherchannel_pinning = self.get_attribute(attribute_name="ether_channel_pinning_enabled",
                                                              attribute_secondary_name="enable_etherchannel_pinning")
        self.enable_geneve_offload = self.get_attribute(attribute_name="geneve_enabled",
                                                        attribute_secondary_name="enable_geneve_offload")
        self.enable_interrupt_scaling = self.get_attribute(attribute_name="interrupt_scaling",
                                                           attribute_secondary_name="enable_interrupt_scaling")
        self.enable_nvgre_offload = None
        self.enable_precision_time_protocol = None
        self.enable_vxlan_offload = None
        self.interrupt_settings = None
        self.name = self.get_attribute(attribute_name="name")
        self.receive_queue_count = None
        self.receive_ring_size = None
        self.roce_settings = None
        self.rss_settings = None
        self.tcp_offload_settings = None
        self.transmit_queue_count = None
        self.transmit_ring_size = None
        self.uplink_failback_timeout = self.get_attribute(attribute_name="uplink_failback_timeout")

        if self._config.load_from == "live":
            if hasattr(self._object, "vxlan_settings"):
                if self._object.vxlan_settings:
                    self.enable_vxlan_offload = self._object.vxlan_settings.enabled

            if hasattr(self._object, "nvgre_settings"):
                if self._object.nvgre_settings:
                    self.enable_nvgre_offload = self._object.nvgre_settings.enabled

            if hasattr(self._object, "ptp_settings"):
                if self._object.ptp_settings:
                    self.enable_precision_time_protocol = self._object.ptp_settings.enabled

            if hasattr(self._object, "arfs_settings"):
                if self._object.arfs_settings:
                    self.enable_accelerated_receive_flow_steering = self._object.arfs_settings.enabled

            if hasattr(self._object, "roce_settings"):
                if self._object.roce_settings:
                    self.roce_settings = {}
                    self.roce_settings["enable_rdma_over_converged_ethernet"] = self._object.roce_settings.enabled
                    if self._object.roce_settings.enabled:
                        self.roce_settings["queue_pairs"] = self._object.roce_settings.queue_pairs
                        self.roce_settings["memory_regions"] = self._object.roce_settings.memory_regions
                        self.roce_settings["resource_groups"] = self._object.roce_settings.resource_groups
                        self.roce_settings["version"] = self._object.roce_settings.version
                        self.roce_settings["class_of_service"] = self._object.roce_settings.class_of_service

            if hasattr(self._object, "interrupt_settings"):
                if self._object.interrupt_settings:
                    self.interrupt_settings = {}
                    self.interrupt_settings["interrupts"] = self._object.interrupt_settings.count
                    self.interrupt_settings["interrupt_mode"] = self._object.interrupt_settings.mode
                    self.interrupt_settings["interrupt_timer"] = self._object.interrupt_settings.coalescing_time
                    self.interrupt_settings["interrupt_coalescing_type"] = \
                        self._object.interrupt_settings.coalescing_type.title()

            if hasattr(self._object, "rx_queue_settings"):
                if self._object.rx_queue_settings:
                    self.receive_queue_count = self._object.rx_queue_settings.count
                    self.receive_ring_size = self._object.rx_queue_settings.ring_size

            if hasattr(self._object, "tx_queue_settings"):
                if self._object.tx_queue_settings:
                    self.transmit_queue_count = self._object.tx_queue_settings.count
                    self.transmit_ring_size = self._object.tx_queue_settings.ring_size

            if hasattr(self._object, "completion_queue_settings"):
                if self._object.completion_queue_settings:
                    self.completion_queue_count = self._object.completion_queue_settings.count
                    self.completion_ring_size = self._object.completion_queue_settings.ring_size

            if hasattr(self._object, "tcp_offload_settings"):
                if self._object.tcp_offload_settings:
                    self.tcp_offload_settings = {}
                    self.tcp_offload_settings["enable_tx_checksum_offload"] = \
                        self._object.tcp_offload_settings.tx_checksum
                    self.tcp_offload_settings["enable_rx_checksum_offload"] = \
                        self._object.tcp_offload_settings.rx_checksum
                    self.tcp_offload_settings["enable_large_send_offload"] = \
                        self._object.tcp_offload_settings.large_send
                    self.tcp_offload_settings["enable_large_receive_offload"] = \
                        self._object.tcp_offload_settings.large_receive

            self.rss_settings = {
                "enable_receive_side_scaling": self.get_attribute(
                    attribute_name="rss_settings", attribute_secondary_name="enable_receive_side_scaling")
            }
            if hasattr(self._object, "rss_hash_settings"):
                if self._object.rss_hash_settings:
                    self.rss_settings["enable_ipv4_hash"] = self._object.rss_hash_settings.ipv4_hash
                    self.rss_settings["enable_ipv6_hash"] = self._object.rss_hash_settings.ipv6_hash
                    self.rss_settings["enable_ipv6_extensions_hash"] = self._object.rss_hash_settings.ipv6_ext_hash
                    self.rss_settings["enable_tcp_and_ipv4_hash"] = self._object.rss_hash_settings.tcp_ipv4_hash
                    self.rss_settings["enable_tcp_and_ipv6_hash"] = self._object.rss_hash_settings.tcp_ipv6_hash
                    self.rss_settings["enable_tcp_and_ipv6_extensions_hash"] = \
                        self._object.rss_hash_settings.tcp_ipv6_ext_hash
                    self.rss_settings["enable_udp_and_ipv4_hash"] = self._object.rss_hash_settings.udp_ipv4_hash
                    self.rss_settings["enable_udp_and_ipv6_hash"] = self._object.rss_hash_settings.udp_ipv6_hash

        elif self._config.load_from == "file":
            for attribute in ["completion_queue_count", "completion_ring_size",
                              "enable_accelerated_receive_flow_steering", "enable_nvgre_offload",
                              "enable_precision_time_protocol", "enable_vxlan_offload", "interrupt_settings",
                              "receive_queue_count", "receive_ring_size", "roce_settings", "rss_settings",
                              "tcp_offload_settings", "transmit_queue_count", "transmit_ring_size"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of RoCE Settings are set to None if they are not present
        if self.roce_settings:
            for attribute in ["class_of_service", "enable_rdma_over_converged_ethernet", "memory_regions",
                              "queue_pairs", "resource_groups", "version"]:
                if attribute not in self.roce_settings:
                    self.roce_settings[attribute] = None

        # We use this to make sure all options of Interrupt Settings are set to None if they are not present
        if self.interrupt_settings:
            for attribute in ["interrupts", "interrupt_mode", "interrupt_timer", "interrupt_coalescing_type"]:
                if attribute not in self.interrupt_settings:
                    self.interrupt_settings[attribute] = None

        # We use this to make sure all options of TCP Offload Settings are set to None if they are not present
        if self.tcp_offload_settings:
            for attribute in ["enable_tx_checksum_offload", "enable_rx_checksum_offload",
                              "enable_large_send_offload", "enable_large_receive_offload"]:
                if attribute not in self.tcp_offload_settings:
                    self.tcp_offload_settings[attribute] = None

        # We use this to make sure all options of RSS Settings are set to None if they are not present
        if self.rss_settings:
            for attribute in ["enable_ipv4_hash", "enable_ipv6_extensions_hash", "enable_ipv6_hash",
                              "enable_receive_side_scaling", "enable_tcp_and_ipv4_hash",
                              "enable_tcp_and_ipv6_extensions_hash", "enable_tcp_and_ipv6_hash",
                              "enable_udp_and_ipv4_hash", "enable_udp_and_ipv6_hash"]:
                if attribute not in self.rss_settings:
                    self.rss_settings[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_eth_adapter_policy import VnicEthAdapterPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enable_advanced_filter is not None:
            kwargs["advanced_filter"] = self.enable_advanced_filter
        if self.enable_etherchannel_pinning is not None:
            kwargs["ether_channel_pinning_enabled"] = self.enable_etherchannel_pinning
        if self.enable_geneve_offload is not None:
            kwargs["geneve_enabled"] = self.enable_geneve_offload
        if self.enable_interrupt_scaling is not None:
            kwargs["interrupt_scaling"] = self.enable_interrupt_scaling
        if self.uplink_failback_timeout is not None:
            kwargs["uplink_failback_timeout"] = self.uplink_failback_timeout

        if self.enable_accelerated_receive_flow_steering is not None:
            from intersight.model.vnic_arfs_settings import VnicArfsSettings

            arfs_settings_kwargs = {
                "object_type": "vnic.ArfsSettings",
                "class_id": "vnic.ArfsSettings"
            }
            if self.enable_accelerated_receive_flow_steering is not None:
                arfs_settings_kwargs["enabled"] = self.enable_accelerated_receive_flow_steering
            kwargs["arfs_settings"] = VnicArfsSettings(**arfs_settings_kwargs)

        if self.enable_nvgre_offload is not None:
            from intersight.model.vnic_nvgre_settings import VnicNvgreSettings

            nvgre_settings_kwargs = {
                "object_type": "vnic.NvgreSettings",
                "class_id": "vnic.NvgreSettings"
            }
            if self.enable_nvgre_offload is not None:
                nvgre_settings_kwargs["enabled"] = self.enable_nvgre_offload
            kwargs["nvgre_settings"] = VnicNvgreSettings(**nvgre_settings_kwargs)

        if self.enable_precision_time_protocol is not None:
            from intersight.model.vnic_ptp_settings import VnicPtpSettings

            ptp_settings_kwargs = {
                "object_type": "vnic.PtpSettings",
                "class_id": "vnic.PtpSettings"
            }
            if self.enable_precision_time_protocol is not None:
                ptp_settings_kwargs["enabled"] = self.enable_precision_time_protocol
            kwargs["ptp_settings"] = VnicPtpSettings(**ptp_settings_kwargs)

        if self.enable_vxlan_offload is not None:
            from intersight.model.vnic_vxlan_settings import VnicVxlanSettings

            vxlan_settings_kwargs = {
                "object_type": "vnic.VxlanSettings",
                "class_id": "vnic.VxlanSettings"
            }
            if self.enable_vxlan_offload is not None:
                vxlan_settings_kwargs["enabled"] = self.enable_vxlan_offload
            kwargs["vxlan_settings"] = VnicVxlanSettings(**vxlan_settings_kwargs)

        if self.completion_queue_count is not None or self.completion_ring_size is not None:
            from intersight.model.vnic_completion_queue_settings import VnicCompletionQueueSettings

            completion_queue_settings_kwargs = {
                "object_type": "vnic.CompletionQueueSettings",
                "class_id": "vnic.CompletionQueueSettings"
            }
            if self.completion_queue_count is not None:
                completion_queue_settings_kwargs["count"] = self.completion_queue_count
            if self.completion_ring_size is not None:
                completion_queue_settings_kwargs["ring_size"] = self.completion_ring_size
            kwargs["completion_queue_settings"] = VnicCompletionQueueSettings(**completion_queue_settings_kwargs)

        if self.receive_queue_count is not None or self.receive_ring_size is not None:
            from intersight.model.vnic_eth_rx_queue_settings import VnicEthRxQueueSettings

            eth_rx_queue_settings_kwargs = {
                "object_type": "vnic.EthRxQueueSettings",
                "class_id": "vnic.EthRxQueueSettings"
            }
            if self.receive_queue_count is not None:
                eth_rx_queue_settings_kwargs["count"] = self.receive_queue_count
            if self.receive_ring_size is not None:
                eth_rx_queue_settings_kwargs["ring_size"] = self.receive_ring_size
            kwargs["rx_queue_settings"] = VnicEthRxQueueSettings(**eth_rx_queue_settings_kwargs)

        if self.transmit_queue_count is not None or self.transmit_ring_size is not None:
            from intersight.model.vnic_eth_tx_queue_settings import VnicEthTxQueueSettings

            eth_tx_queue_settings_kwargs = {
                "object_type": "vnic.EthTxQueueSettings",
                "class_id": "vnic.EthTxQueueSettings"
            }
            if self.transmit_queue_count is not None:
                eth_tx_queue_settings_kwargs["count"] = self.transmit_queue_count
            if self.transmit_ring_size is not None:
                eth_tx_queue_settings_kwargs["ring_size"] = self.transmit_ring_size
            kwargs["tx_queue_settings"] = VnicEthTxQueueSettings(**eth_tx_queue_settings_kwargs)

        if self.interrupt_settings is not None:
            from intersight.model.vnic_eth_interrupt_settings import VnicEthInterruptSettings

            interrupt_settings_kwargs = {
                "object_type": "vnic.EthInterruptSettings",
                "class_id": "vnic.EthInterruptSettings"
            }
            if self.interrupt_settings["interrupts"] is not None:
                interrupt_settings_kwargs["count"] = self.interrupt_settings["interrupts"]
            if self.interrupt_settings["interrupt_mode"] is not None:
                interrupt_settings_kwargs["mode"] = self.interrupt_settings["interrupt_mode"]
            if self.interrupt_settings["interrupt_timer"] is not None:
                interrupt_settings_kwargs["coalescing_time"] = self.interrupt_settings["interrupt_timer"]
            if self.interrupt_settings["interrupt_coalescing_type"] is not None:
                interrupt_settings_kwargs["coalescing_type"] = \
                    self.interrupt_settings["interrupt_coalescing_type"].upper()
            kwargs["interrupt_settings"] = VnicEthInterruptSettings(**interrupt_settings_kwargs)

        if self.roce_settings is not None:
            from intersight.model.vnic_roce_settings import VnicRoceSettings

            roce_settings_kwargs = {
                "object_type": "vnic.RoceSettings",
                "class_id": "vnic.RoceSettings"
            }
            if self.roce_settings["enable_rdma_over_converged_ethernet"] is not None:
                roce_settings_kwargs["enabled"] = self.roce_settings["enable_rdma_over_converged_ethernet"]
            if self.roce_settings["queue_pairs"] is not None:
                roce_settings_kwargs["queue_pairs"] = self.roce_settings["queue_pairs"]
            if self.roce_settings["memory_regions"] is not None:
                roce_settings_kwargs["memory_regions"] = self.roce_settings["memory_regions"]
            if self.roce_settings["resource_groups"] is not None:
                roce_settings_kwargs["resource_groups"] = self.roce_settings["resource_groups"]
            if self.roce_settings["version"] is not None:
                roce_settings_kwargs["version"] = self.roce_settings["version"]
            if self.roce_settings["class_of_service"] is not None:
                roce_settings_kwargs["class_of_service"] = self.roce_settings["class_of_service"]
            kwargs["roce_settings"] = VnicRoceSettings(**roce_settings_kwargs)

        if self.rss_settings is not None:
            if self.rss_settings["enable_receive_side_scaling"] is not None:
                kwargs["rss_settings"] = self.rss_settings["enable_receive_side_scaling"]

            if self.rss_settings["enable_receive_side_scaling"]:
                from intersight.model.vnic_rss_hash_settings import VnicRssHashSettings

                rss_hash_settings_kwargs = {
                    "object_type": "vnic.RssHashSettings",
                    "class_id": "vnic.RssHashSettings"
                }

                if self.rss_settings["enable_ipv4_hash"] is not None:
                    rss_hash_settings_kwargs["ipv4_hash"] = self.rss_settings["enable_ipv4_hash"]
                if self.rss_settings["enable_ipv6_extensions_hash"] is not None:
                    rss_hash_settings_kwargs["ipv6_ext_hash"] = self.rss_settings["enable_ipv6_extensions_hash"]
                if self.rss_settings["enable_ipv6_hash"] is not None:
                    rss_hash_settings_kwargs["ipv6_hash"] = self.rss_settings["enable_ipv6_hash"]
                if self.rss_settings["enable_tcp_and_ipv4_hash"] is not None:
                    rss_hash_settings_kwargs["tcp_ipv4_hash"] = self.rss_settings["enable_tcp_and_ipv4_hash"]
                if self.rss_settings["enable_tcp_and_ipv6_extensions_hash"] is not None:
                    rss_hash_settings_kwargs["tcp_ipv6_ext_hash"] = \
                        self.rss_settings["enable_tcp_and_ipv6_extensions_hash"]
                if self.rss_settings["enable_tcp_and_ipv6_hash"] is not None:
                    rss_hash_settings_kwargs["tcp_ipv6_hash"] = self.rss_settings["enable_tcp_and_ipv6_hash"]
                if self.rss_settings["enable_udp_and_ipv4_hash"] is not None:
                    rss_hash_settings_kwargs["udp_ipv4_hash"] = self.rss_settings["enable_udp_and_ipv4_hash"]
                if self.rss_settings["enable_udp_and_ipv6_hash"] is not None:
                    rss_hash_settings_kwargs["udp_ipv6_hash"] = self.rss_settings["enable_udp_and_ipv6_hash"]
                kwargs["rss_hash_settings"] = VnicRssHashSettings(**rss_hash_settings_kwargs)

        if self.tcp_offload_settings is not None:
            from intersight.model.vnic_tcp_offload_settings import VnicTcpOffloadSettings

            tcp_offload_settings_kwargs = {
                "object_type": "vnic.TcpOffloadSettings",
                "class_id": "vnic.TcpOffloadSettings"
            }
            if self.tcp_offload_settings["enable_tx_checksum_offload"] is not None:
                tcp_offload_settings_kwargs["tx_checksum"] = self.tcp_offload_settings["enable_tx_checksum_offload"]
            if self.tcp_offload_settings["enable_rx_checksum_offload"] is not None:
                tcp_offload_settings_kwargs["rx_checksum"] = self.tcp_offload_settings["enable_rx_checksum_offload"]
            if self.tcp_offload_settings["enable_large_send_offload"] is not None:
                tcp_offload_settings_kwargs["large_send"] = self.tcp_offload_settings["enable_large_send_offload"]
            if self.tcp_offload_settings["enable_large_receive_offload"] is not None:
                tcp_offload_settings_kwargs["large_receive"] = self.tcp_offload_settings["enable_large_receive_offload"]
            kwargs["tcp_offload_settings"] = VnicTcpOffloadSettings(**tcp_offload_settings_kwargs)

        ethernet_adapter_policy = VnicEthAdapterPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=ethernet_adapter_policy,
                           detail=self.name):
            return False

        return True


class IntersightEthernetNetworkControlPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Ethernet Network Control Policy"
    _CONFIG_SECTION_NAME = "ethernet_network_control_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.EthNetworkControlPolicy"

    def __init__(self, parent=None, ethernet_network_control_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=ethernet_network_control_policy)

        self.action_on_uplink_fail = self.get_attribute(attribute_name="uplink_fail_action",
                                                        attribute_secondary_name="action_on_uplink_fail")
        self.cdp_enable = self.get_attribute(attribute_name="cdp_enabled", attribute_secondary_name="cdp_enable")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.lldp_transmit_enable = None
        self.lldp_receive_enable = None
        self.mac_register_mode = self.get_attribute(attribute_name="mac_registration_mode",
                                                    attribute_secondary_name="mac_register_mode")
        self.mac_security_forge = self.get_attribute(attribute_name="forge_mac",
                                                     attribute_secondary_name="mac_security_forge")
        self.name = self.get_attribute(attribute_name="name")

        if self._config.load_from == "live":
            if hasattr(self._object, "lldp_settings"):
                if self._object.lldp_settings:
                    self.lldp_transmit_enable = self._object.lldp_settings.transmit_enabled
                    self.lldp_receive_enable = self._object.lldp_settings.receive_enabled

        elif self._config.load_from == "file":
            for attribute in ["lldp_transmit_enable", "lldp_receive_enable"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_eth_network_control_policy import FabricEthNetworkControlPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.action_on_uplink_fail is not None:
            kwargs["uplink_fail_action"] = self.action_on_uplink_fail
        if self.cdp_enable is not None:
            kwargs["cdp_enabled"] = self.cdp_enable
        if self.mac_register_mode is not None:
            kwargs["mac_registration_mode"] = self.mac_register_mode
        if self.mac_security_forge is not None:
            kwargs["forge_mac"] = self.mac_security_forge

        from intersight.model.fabric_lldp_settings import FabricLldpSettings
        lldp_settings_kwargs = {
            "object_type": "fabric.LldpSettings",
            "class_id": "fabric.LldpSettings",
        }
        if self.lldp_transmit_enable is not None:
            lldp_settings_kwargs["transmit_enabled"] = self.lldp_transmit_enable
        if self.lldp_receive_enable is not None:
            lldp_settings_kwargs["receive_enabled"] = self.lldp_receive_enable
        if len(lldp_settings_kwargs) != 0:
            kwargs["lldp_settings"] = FabricLldpSettings(**lldp_settings_kwargs)

        ethernet_network_control_policy = FabricEthNetworkControlPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=ethernet_network_control_policy,
                           detail=self.name):
            return False

        return True


class IntersightEthernetNetworkGroupPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Ethernet Network Group Policy"
    _CONFIG_SECTION_NAME = "ethernet_network_group_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.EthNetworkGroupPolicy"

    def __init__(self, parent=None, ethernet_network_group_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=ethernet_network_group_policy)

        self.allowed_vlans = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_q_in_q_tunneling = None
        self.name = self.get_attribute(attribute_name="name")
        self.native_vlan = None
        self.q_in_q_vlan = None

        if self._config.load_from == "live":
            if hasattr(self._object, "vlan_settings"):
                if self._object.vlan_settings:
                    self.enable_q_in_q_tunneling = self._object.vlan_settings.qinq_enabled
                    self.native_vlan = self._object.vlan_settings.native_vlan
                    if self.enable_q_in_q_tunneling:
                        self.q_in_q_vlan = self._object.vlan_settings.qinq_vlan
                    else:
                        self.allowed_vlans = self._object.vlan_settings.allowed_vlans

        elif self._config.load_from == "file":
            for attribute in ["allowed_vlans", "enable_q_in_q_tunneling", "native_vlan", "q_in_q_vlan"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_eth_network_group_policy import FabricEthNetworkGroupPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        from intersight.model.fabric_vlan_settings import FabricVlanSettings
        vlan_settings_kwargs = {
            "object_type": "fabric.VlanSettings",
            "class_id": "fabric.VlanSettings",
        }
        if self.allowed_vlans is not None:
            vlan_settings_kwargs["allowed_vlans"] = self.allowed_vlans
        if self.enable_q_in_q_tunneling is not None:
            vlan_settings_kwargs["qinq_enabled"] = self.enable_q_in_q_tunneling
        if self.native_vlan is not None:
            vlan_settings_kwargs["native_vlan"] = self.native_vlan
        if self.q_in_q_vlan is not None:
            vlan_settings_kwargs["qinq_vlan"] = self.q_in_q_vlan
        if len(vlan_settings_kwargs) != 0:
            kwargs["vlan_settings"] = FabricVlanSettings(**vlan_settings_kwargs)

        ethernet_network_group_policy = FabricEthNetworkGroupPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=ethernet_network_group_policy,
                           detail=self.name):
            return False

        return True


class IntersightEthernetNetworkPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Ethernet Network Policy"
    _CONFIG_SECTION_NAME = "ethernet_network_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.EthNetworkPolicy"

    def __init__(self, parent=None, eth_network_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=eth_network_policy)

        self.default_vlan = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.target_platform = self.get_attribute(attribute_name="target_platform")
        self.vlan_mode = None

        if self._config.load_from == "live":
            # Renaming Target Platform to be more user-friendly
            if self.target_platform == "FIAttached":
                self.target_platform = "FI-Attached"

            if hasattr(self._object, "vlan_settings"):
                if self._object.vlan_settings:
                    self.vlan_mode = self._object.vlan_settings.mode.lower()
                    self.default_vlan = self._object.vlan_settings.default_vlan

        elif self._config.load_from == "file":
            for attribute in ["default_vlan", "vlan_mode"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_eth_network_policy import VnicEthNetworkPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.target_platform is not None:
            if self.target_platform in ["FI-Attached"]:
                kwargs["target_platform"] = "FIAttached"
            else:
                kwargs["target_platform"] = self.target_platform

        from intersight.model.vnic_vlan_settings import VnicVlanSettings
        vlan_settings_kwargs = {
            "object_type": "vnic.VlanSettings",
            "class_id": "vnic.VlanSettings"
        }
        if self.default_vlan is not None:
            vlan_settings_kwargs["default_vlan"] = self.default_vlan
        if self.vlan_mode is not None:
            vlan_settings_kwargs["mode"] = self.vlan_mode.upper()
        kwargs["vlan_settings"] = VnicVlanSettings(**vlan_settings_kwargs)

        eth_network_policy = VnicEthNetworkPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=eth_network_policy, detail=self.name):
            return False

        return True


class IntersightEthernetQosPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Ethernet QoS Policy"
    _CONFIG_SECTION_NAME = "ethernet_qos_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.EthQosPolicy"

    def __init__(self, parent=None, eth_qos_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=eth_qos_policy)

        self.burst = self.get_attribute(attribute_name="burst")
        self.class_of_service = self.get_attribute(attribute_name="cos", attribute_secondary_name="class_of_service")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_trust_host_cos = self.get_attribute(attribute_name="trust_host_cos",
                                                        attribute_secondary_name="enable_trust_host_cos")
        self.mtu = self.get_attribute(attribute_name="mtu")
        self.name = self.get_attribute(attribute_name="name")
        self.priority = self.get_attribute(attribute_name="priority")
        self.rate_limit = self.get_attribute(attribute_name="rate_limit")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_eth_qos_policy import VnicEthQosPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.burst is not None:
            kwargs["burst"] = self.burst
        if self.class_of_service is not None:
            kwargs["cos"] = self.class_of_service
        if self.enable_trust_host_cos is not None:
            kwargs["trust_host_cos"] = self.enable_trust_host_cos
        if self.mtu is not None:
            kwargs["mtu"] = self.mtu
        if self.priority is not None:
            kwargs["priority"] = self.priority
        if self.rate_limit is not None:
            kwargs["rate_limit"] = self.rate_limit

        eth_qos_policy = VnicEthQosPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=eth_qos_policy, detail=self.name):
            return False

        return True


class IntersightFcZonePolicy(IntersightConfigObject):
    _CONFIG_NAME = "FC Zone Policy"
    _CONFIG_SECTION_NAME = "fc_zone_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.FcZonePolicy"

    def __init__(self, parent=None, fabric_fc_zone_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_fc_zone_policy)

        self.name = self.get_attribute(attribute_name="name")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.fc_target_zoning_type = self.get_attribute(attribute_name="fc_target_zoning_type")
        self.fc_zone_targets = None

        if self._config.load_from == "live":
            if self.fc_target_zoning_type:
                if self.fc_target_zoning_type in ["SIST"]:
                    self.fc_target_zoning_type = "single_initiator_single_target"
                elif self.fc_target_zoning_type in ["SIMT"]:
                    self.fc_target_zoning_type = "single_initiator_multiple_targets"
                elif self.fc_target_zoning_type in ["None"]:
                    self.fc_target_zoning_type = "none"

            if self.fc_target_zoning_type not in ["none"]:
                if hasattr(self._object, "fc_target_members"):
                    if self._object.fc_target_members is not None:
                        fc_targets_list = []
                        for fc_target in self._object.fc_target_members:
                            fc_targets_list.append({"name": fc_target.name,
                                                    "switch_id": fc_target.switch_id,
                                                    "vsan_id": fc_target.vsan_id,
                                                    "wwpn": fc_target.wwpn})
                        self.fc_zone_targets = fc_targets_list

        elif self._config.load_from == "file":
            for attribute in ["fc_target_zoning_type", "fc_zone_targets"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of an FC Zone Target are set to None if they are not present
        if self.fc_zone_targets:
            for target in self.fc_zone_targets:
                for attribute in ["name", "switch_id", "vsan_id", "wwpn"]:
                    if attribute not in target:
                        target[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_fc_zone_policy import FabricFcZonePolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.fc_target_zoning_type is not None:
            fc_target_zoning_type = self.fc_target_zoning_type

            if fc_target_zoning_type == "single_initiator_single_target":
                fc_target_zoning_type = "SIST"
            elif fc_target_zoning_type == "single_initiator_multiple_targets":
                fc_target_zoning_type = "SIMT"
            elif fc_target_zoning_type == "none":
                fc_target_zoning_type = "None"
            kwargs["fc_target_zoning_type"] = fc_target_zoning_type

        if self.fc_zone_targets is not None:
            from intersight.model.fabric_fc_zone_member import FabricFcZoneMember
            targets = []
            for target in self.fc_zone_targets:
                target_kwargs = {
                    "object_type": "fabric.FcZoneMember",
                    "class_id": "fabric.FcZoneMember",
                }
                if target.get("name"):
                    target_kwargs["name"] = target["name"]
                if target.get("switch_id"):
                    target_kwargs["switch_id"] = target["switch_id"]
                if target.get("vsan_id"):
                    target_kwargs["vsan_id"] = target["vsan_id"]
                if target.get("wwpn"):
                    target_kwargs["wwpn"] = target["wwpn"]

                targets.append(FabricFcZoneMember(**target_kwargs))

            kwargs["fc_target_members"] = targets

        fc_zone_policy = FabricFcZonePolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fc_zone_policy, detail=self.name):
            return False

        return True


class IntersightFibreChannelAdapterPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Fibre Channel Adapter Policy"
    _CONFIG_SECTION_NAME = "fibre_channel_adapter_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.FcAdapterPolicy"

    def __init__(self, parent=None, fc_adapter_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fc_adapter_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.error_detection_timeout = self.get_attribute(attribute_name="error_detection_timeout")
        self.error_recovery_settings = None
        self.flogi_retries = None
        self.flogi_timeout = None
        self.name = self.get_attribute(attribute_name="name")
        self.interrupt_settings = None
        self.io_throttle_count = self.get_attribute(attribute_name="io_throttle_count")
        self.lun_queue_depth = self.get_attribute(attribute_name="lun_queue_depth")
        self.max_luns_per_target = self.get_attribute(attribute_name="lun_count",
                                                      attribute_secondary_name="max_luns_per_target")
        self.plogi_retries = None
        self.plogi_timeout = None
        self.receive_ring_size = None
        self.resource_allocation_timeout = self.get_attribute(attribute_name="resource_allocation_timeout")
        self.scsi_io_queue_count = None
        self.scsi_io_ring_size = None
        self.transmit_ring_size = None

        if self._config.load_from == "live":
            if hasattr(self._object, "interrupt_settings"):
                if self._object.interrupt_settings:
                    self.interrupt_settings = {}
                    self.interrupt_settings["interrupt_mode"] = self._object.interrupt_settings.mode

            if hasattr(self._object, "rx_queue_settings"):
                if self._object.rx_queue_settings:
                    self.receive_ring_size = self._object.rx_queue_settings.ring_size

            if hasattr(self._object, "tx_queue_settings"):
                if self._object.tx_queue_settings:
                    self.transmit_ring_size = self._object.tx_queue_settings.ring_size

            if hasattr(self._object, "scsi_queue_settings"):
                if self._object.scsi_queue_settings:
                    self.scsi_io_queue_count = self._object.scsi_queue_settings.count
                    self.scsi_io_ring_size = self._object.scsi_queue_settings.ring_size

            if hasattr(self._object, "error_recovery_settings"):
                if self._object.error_recovery_settings:
                    self.error_recovery_settings = {}
                    self.error_recovery_settings["enable_fcp_error_recovery"] = \
                        self._object.error_recovery_settings.enabled
                    self.error_recovery_settings["port_down_timeout"] = \
                        self._object.error_recovery_settings.port_down_timeout
                    self.error_recovery_settings["link_down_timeout"] = \
                        self._object.error_recovery_settings.link_down_timeout
                    self.error_recovery_settings["io_retry_timeout"] = \
                        self._object.error_recovery_settings.io_retry_timeout
                    self.error_recovery_settings["port_down_io_retry"] = \
                        self._object.error_recovery_settings.io_retry_count

            if hasattr(self._object, "flogi_settings"):
                if self._object.flogi_settings:
                    self.flogi_retries = self._object.flogi_settings.retries
                    self.flogi_timeout = self._object.flogi_settings.timeout

            if hasattr(self._object, "plogi_settings"):
                if self._object.plogi_settings:
                    self.plogi_retries = self._object.plogi_settings.retries
                    self.plogi_timeout = self._object.plogi_settings.timeout

        elif self._config.load_from == "file":
            for attribute in ["error_recovery_settings", "flogi_retries", "flogi_timeout", "interrupt_settings",
                              "plogi_retries", "plogi_timeout", "receive_ring_size", "scsi_io_queue_count",
                              "scsi_io_ring_size", "transmit_ring_size"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of Interrupt Settings are set to None if they are not present
        if self.interrupt_settings:
            for attribute in ["interrupt_mode"]:
                if attribute not in self.interrupt_settings:
                    self.interrupt_settings[attribute] = None

        # We use this to make sure all options of Error Recovery Settings are set to None if they are not present
        if self.error_recovery_settings:
            for attribute in ["enable_fcp_error_recovery", "io_retry_timeout", "link_down_timeout",
                              "port_down_io_retry", "port_down_timeout"]:
                if attribute not in self.error_recovery_settings:
                    self.error_recovery_settings[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_fc_adapter_policy import VnicFcAdapterPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.error_detection_timeout is not None:
            kwargs["error_detection_timeout"] = self.error_detection_timeout
        if self.io_throttle_count is not None:
            kwargs["io_throttle_count"] = self.io_throttle_count
        if self.lun_queue_depth is not None:
            kwargs["lun_queue_depth"] = self.lun_queue_depth
        if self.max_luns_per_target is not None:
            kwargs["lun_count"] = self.max_luns_per_target
        if self.resource_allocation_timeout is not None:
            kwargs["resource_allocation_timeout"] = self.resource_allocation_timeout

        if self.flogi_retries is not None or self.flogi_timeout is not None:
            from intersight.model.vnic_flogi_settings import VnicFlogiSettings

            flogi_settings_kwargs = {
                "object_type": "vnic.FlogiSettings",
                "class_id": "vnic.FlogiSettings"
            }
            if self.flogi_retries is not None:
                flogi_settings_kwargs["retries"] = self.flogi_retries
            if self.flogi_timeout is not None:
                flogi_settings_kwargs["timeout"] = self.flogi_timeout
            kwargs["flogi_settings"] = VnicFlogiSettings(**flogi_settings_kwargs)

        if self.plogi_retries is not None or self.plogi_timeout is not None:
            from intersight.model.vnic_plogi_settings import VnicPlogiSettings

            plogi_settings_kwargs = {
                "object_type": "vnic.PlogiSettings",
                "class_id": "vnic.PlogiSettings"
            }
            if self.plogi_retries is not None:
                plogi_settings_kwargs["retries"] = self.plogi_retries
            if self.plogi_timeout is not None:
                plogi_settings_kwargs["timeout"] = self.plogi_timeout
            kwargs["plogi_settings"] = VnicPlogiSettings(**plogi_settings_kwargs)

        if self.receive_ring_size is not None:
            from intersight.model.vnic_fc_queue_settings import VnicFcQueueSettings

            fc_rx_queue_settings_kwargs = {
                "object_type": "vnic.FcQueueSettings",
                "class_id": "vnic.FcQueueSettings",
                "ring_size": self.receive_ring_size
            }
            kwargs["rx_queue_settings"] = VnicFcQueueSettings(**fc_rx_queue_settings_kwargs)

        if self.transmit_ring_size is not None:
            from intersight.model.vnic_fc_queue_settings import VnicFcQueueSettings

            fc_tx_queue_settings_kwargs = {
                "object_type": "vnic.FcQueueSettings",
                "class_id": "vnic.FcQueueSettings",
                "ring_size": self.transmit_ring_size
            }
            kwargs["tx_queue_settings"] = VnicFcQueueSettings(**fc_tx_queue_settings_kwargs)

        if self.scsi_io_queue_count is not None or self.scsi_io_ring_size is not None:
            from intersight.model.vnic_scsi_queue_settings import VnicScsiQueueSettings

            scsi_queue_settings_kwargs = {
                "object_type": "vnic.ScsiQueueSettings",
                "class_id": "vnic.ScsiQueueSettings"
            }
            if self.scsi_io_queue_count is not None:
                scsi_queue_settings_kwargs["count"] = self.scsi_io_queue_count
            if self.scsi_io_ring_size is not None:
                scsi_queue_settings_kwargs["ring_size"] = self.scsi_io_ring_size
            kwargs["scsi_queue_settings"] = VnicScsiQueueSettings(**scsi_queue_settings_kwargs)

        if self.interrupt_settings is not None:
            from intersight.model.vnic_fc_interrupt_settings import VnicFcInterruptSettings

            interrupt_settings_kwargs = {
                "object_type": "vnic.FcInterruptSettings",
                "class_id": "vnic.FcInterruptSettings"
            }
            if self.interrupt_settings["interrupt_mode"] is not None:
                interrupt_settings_kwargs["mode"] = self.interrupt_settings["interrupt_mode"]
            kwargs["interrupt_settings"] = VnicFcInterruptSettings(**interrupt_settings_kwargs)

        if self.error_recovery_settings is not None:
            from intersight.model.vnic_fc_error_recovery_settings import VnicFcErrorRecoverySettings

            error_recovery_settings_kwargs = {
                "object_type": "vnic.FcErrorRecoverySettings",
                "class_id": "vnic.FcErrorRecoverySettings"
            }
            if self.error_recovery_settings["enable_fcp_error_recovery"] is not None:
                error_recovery_settings_kwargs["enabled"] = self.error_recovery_settings["enable_fcp_error_recovery"]
            if self.error_recovery_settings["io_retry_timeout"] is not None:
                error_recovery_settings_kwargs["io_retry_timeout"] = self.error_recovery_settings["io_retry_timeout"]
            if self.error_recovery_settings["link_down_timeout"] is not None:
                error_recovery_settings_kwargs["link_down_timeout"] = self.error_recovery_settings["link_down_timeout"]
            if self.error_recovery_settings["port_down_io_retry"] is not None:
                error_recovery_settings_kwargs["io_retry_count"] = self.error_recovery_settings["port_down_io_retry"]
            if self.error_recovery_settings["port_down_timeout"] is not None:
                error_recovery_settings_kwargs["port_down_timeout"] = self.error_recovery_settings["port_down_timeout"]
            kwargs["error_recovery_settings"] = VnicFcErrorRecoverySettings(**error_recovery_settings_kwargs)

        fc_adapter_policy = VnicFcAdapterPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fc_adapter_policy, detail=self.name):
            return False

        return True


class IntersightFibreChannelNetworkPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Fibre Channel Network Policy"
    _CONFIG_SECTION_NAME = "fibre_channel_network_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.FcNetworkPolicy"

    def __init__(self, parent=None, fc_network_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fc_network_policy)

        self.default_vlan = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.vsan_id = None

        if self._config.load_from == "live":
            if hasattr(self._object, "vsan_settings"):
                if self._object.vsan_settings:
                    self.vsan_id = self._object.vsan_settings.id
                    self.default_vlan = self._object.vsan_settings.default_vlan_id

        elif self._config.load_from == "file":
            for attribute in ["default_vlan", "vsan_id"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_fc_network_policy import VnicFcNetworkPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        from intersight.model.vnic_vsan_settings import VnicVsanSettings
        vsan_settings_kwargs = {
            "object_type": "vnic.VsanSettings",
            "class_id": "vnic.VsanSettings"
        }
        if self.default_vlan is not None:
            vsan_settings_kwargs["default_vlan_id"] = self.default_vlan
        if self.vsan_id is not None:
            vsan_settings_kwargs["id"] = self.vsan_id
        kwargs["vsan_settings"] = VnicVsanSettings(**vsan_settings_kwargs)

        fc_network_policy = VnicFcNetworkPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fc_network_policy, detail=self.name):
            return False

        return True


class IntersightFibreChannelQosPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Fibre Channel QoS Policy"
    _CONFIG_SECTION_NAME = "fibre_channel_qos_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.FcQosPolicy"

    def __init__(self, parent=None, fc_qos_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fc_qos_policy)

        self.burst = self.get_attribute(attribute_name="burst")
        self.class_of_service = self.get_attribute(attribute_name="cos", attribute_secondary_name="class_of_service")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.max_data_field_size = self.get_attribute(attribute_name="max_data_field_size")
        self.name = self.get_attribute(attribute_name="name")
        self.rate_limit = self.get_attribute(attribute_name="rate_limit")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_fc_qos_policy import VnicFcQosPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.burst is not None:
            kwargs["burst"] = self.burst
        if self.class_of_service is not None:
            kwargs["cos"] = self.class_of_service
        if self.max_data_field_size is not None:
            kwargs["max_data_field_size"] = self.max_data_field_size
        if self.rate_limit is not None:
            kwargs["rate_limit"] = self.rate_limit

        fc_qos_policy = VnicFcQosPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fc_qos_policy, detail=self.name):
            return False

        return True


class IntersightFirmwarePolicy(IntersightConfigObject):
    _CONFIG_NAME = "Firmware Policy"
    _CONFIG_SECTION_NAME = "firmware_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "firmware.Policy"

    def __init__(self, parent=None, firmware_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=firmware_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.excluded_components = self.get_attribute(attribute_name="exclude_component_list")
        self.models = None
        self.name = self.get_attribute(attribute_name="name")
        self.target_platform = self.get_attribute(attribute_name="target_platform")

        if self._config.load_from == "live":
            if self.target_platform == "FIAttached":
                self.target_platform = "FI-Attached"
            if hasattr(self._object, "model_bundle_combo"):
                if self._object.model_bundle_combo:
                    self.models = []
                    for models in self._object.model_bundle_combo:
                        self.models.append({"server_model": models.get("model_family"),
                                            "firmware_version": models.get("bundle_version")})

        elif self._config.load_from == "file":
            for attribute in ["excluded_components", "models", "target_platform"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a Model Bundle Combo are set to None if they are not present
        if self.models:
            for models in self.models:
                for attribute in ["server_model", "firmware_version"]:
                    if attribute not in models:
                        models[attribute] = None

    def push_object(self):
        from intersight.model.firmware_policy import FirmwarePolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.target_platform is not None:
            kwargs["target_platform"] = "FIAttached" if self.target_platform == "FI-Attached" else self.target_platform
        if self.excluded_components is not None:
            kwargs["exclude_component_list"] = self.excluded_components

        if self.models is not None:
            from intersight.model.firmware_model_bundle_version import FirmwareModelBundleVersion

            models_list = []
            for models in self.models:
                models_kwargs = {
                    "class_id": "firmware.ModelBundleVersion",
                    "object_type": "firmware.ModelBundleVersion"
                }
                models_kwargs["model_family"] = models["server_model"]
                models_kwargs["bundle_version"] = models["firmware_version"]

                models_list.append(FirmwareModelBundleVersion(**models_kwargs))

            kwargs["model_bundle_combo"] = models_list

        firmware_policy = FirmwarePolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=firmware_policy, detail=self.name):
            return False

        return True


class IntersightImcAccessPolicy(IntersightConfigObject):
    _CONFIG_NAME = "IMC Access Policy"
    _CONFIG_SECTION_NAME = "imc_access_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "access.Policy"
    _POLICY_MAPPING_TABLE = {
        "inband_ip_pool": IntersightIpPool,
        "out_of_band_ip_pool": IntersightIpPool
    }
    UCS_TO_INTERSIGHT_POOL_MAPPING_TABLE = {
        "inband_ipv4_pool": IntersightIpPool,
        "inband_ipv6_pool": IntersightIpPool,
        "outband_ipv4_pool": IntersightIpPool
    }

    def __init__(self, parent=None, access_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=access_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.inband_configuration = None
        self.inband_ip_pool = None
        self.inband_vlan_id = None
        self.ipv4_address_configuration = None
        self.ipv6_address_configuration = None
        self.name = self.get_attribute(attribute_name="name")
        self.out_of_band_configuration = None
        self.out_of_band_ip_pool = None

        if self._config.load_from == "live":
            if hasattr(self._object, "configuration_type"):
                if self._object.configuration_type:
                    self.inband_configuration = self._object.configuration_type.configure_inband
                    self.out_of_band_configuration = self._object.configuration_type.configure_out_of_band
                    if self.inband_configuration:
                        self.inband_ip_pool = self._get_inband_ip_pool()
                        self.inband_vlan_id = self.get_attribute(attribute_name="inband_vlan",
                                                                 attribute_secondary_name="inband_vlan_id")
                    if self.out_of_band_configuration:
                        self.out_of_band_ip_pool = self._get_out_of_band_ip_pool()

            if hasattr(self._object, "address_type"):
                if self._object.address_type:
                    if self.inband_configuration:
                        self.ipv4_address_configuration = self._object.address_type.enable_ip_v4
                        self.ipv6_address_configuration = self._object.address_type.enable_ip_v6

        elif self._config.load_from == "file":
            for attribute in ["inband_configuration", "inband_ip_pool", "inband_vlan_id", "ipv4_address_configuration",
                              "ipv6_address_configuration", "out_of_band_configuration", "out_of_band_ip_pool"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_inband_ip_pool(self):
        if hasattr(self._object, "inband_ip_pool"):
            if self._object.inband_ip_pool is not None:
                return self._get_policy_name(policy=self._object.inband_ip_pool)

        return None

    def _get_out_of_band_ip_pool(self):
        if hasattr(self._object, "out_of_band_ip_pool"):
            if self._object.out_of_band_ip_pool is not None:
                return self._get_policy_name(policy=self._object.out_of_band_ip_pool)

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.access_policy import AccessPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")
        org = self.get_parent_org_relationship()
        if not org:
            return False

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.inband_vlan_id is not None:
            kwargs["inband_vlan"] = self.inband_vlan_id

        from intersight.model.access_configuration_type import AccessConfigurationType
        configuration_type_kwargs = {
            "object_type": "access.ConfigurationType",
            "class_id": "access.ConfigurationType"
        }
        if self.inband_configuration is not None:
            configuration_type_kwargs["configure_inband"] = self.inband_configuration
        else:
            configuration_type_kwargs["configure_inband"] = False
        if self.out_of_band_configuration is not None:
            configuration_type_kwargs["configure_out_of_band"] = self.out_of_band_configuration
        else:
            configuration_type_kwargs["configure_out_of_band"] = False
        kwargs["configuration_type"] = AccessConfigurationType(**configuration_type_kwargs)

        if self.inband_ip_pool is not None:
            # We need to identify the IP Pool object reference
            inband_ip_pool = self.get_live_object(object_name=self.inband_ip_pool, object_type="ippool.Pool")
            if inband_ip_pool:
                kwargs["inband_ip_pool"] = inband_ip_pool
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Inband IP Pool '{self.inband_ip_pool}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find IP Pool '{self.inband_ip_pool}'"
                )

        if self.out_of_band_ip_pool is not None:
            # We need to identify the IP Pool object reference
            out_of_band_ip_pool = self.get_live_object(object_name=self.out_of_band_ip_pool, object_type="ippool.Pool")
            if out_of_band_ip_pool:
                kwargs["out_of_band_ip_pool"] = out_of_band_ip_pool
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Out of Band IP Pool '{self.out_of_band_ip_pool}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find IP Pool '{self.out_of_band_ip_pool}'"
                )

        from intersight.model.access_address_type import AccessAddressType
        address_type_kwargs = {
            "object_type": "access.AddressType",
            "class_id": "access.AddressType",
        }
        if self.ipv4_address_configuration is not None:
            address_type_kwargs["enable_ip_v4"] = self.ipv4_address_configuration
        if self.ipv6_address_configuration is not None:
            address_type_kwargs["enable_ip_v6"] = self.ipv6_address_configuration
        if len(address_type_kwargs) != 0:
            kwargs["address_type"] = AccessAddressType(**address_type_kwargs)

        imc_access_policy = AccessPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=imc_access_policy, detail=self.name):
            return False

        return True


class IntersightIpmiOverLanPolicy(IntersightConfigObject):
    _CONFIG_NAME = "IPMI over LAN Policy"
    _CONFIG_SECTION_NAME = "ipmi_over_lan_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "ipmioverlan.Policy"

    def __init__(self, parent=None, ipmioverlan_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=ipmioverlan_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enabled = self.get_attribute(attribute_name="enabled")
        self.name = self.get_attribute(attribute_name="name")
        self.privilege_level = self.get_attribute(attribute_name="privilege",
                                                  attribute_secondary_name="privilege_level")
        self.encryption_key = self.get_attribute(attribute_name="encryption_key")

        if self._config.load_from == "live":
            if hasattr(self._object, "is_encryption_key_set"):
                if self._object.is_encryption_key_set:
                    self.logger(level="warning", message="Encryption key of " + self._CONFIG_NAME + " " +
                                                         str(self.name) + " can't be exported")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.ipmioverlan_policy import IpmioverlanPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enabled is not None:
            kwargs["enabled"] = self.enabled
        if self.privilege_level is not None:
            kwargs["privilege"] = self.privilege_level
        if self.encryption_key is not None:
            kwargs["encryption_key"] = self.encryption_key

        ipmioverlan_policy = IpmioverlanPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=ipmioverlan_policy, detail=self.name):
            return False

        return True


class IntersightIscsiAdapterPolicy(IntersightConfigObject):
    _CONFIG_NAME = "iSCSI Adapter Policy"
    _CONFIG_SECTION_NAME = "iscsi_adapter_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.IscsiAdapterPolicy"

    def __init__(self, parent=None, iscsi_adapter_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=iscsi_adapter_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.tcp_connection_timeout = self.get_attribute(attribute_name="connection_time_out",
                                                         attribute_secondary_name="tcp_connection_timeout")
        self.dhcp_timeout = self.get_attribute(attribute_name="dhcp_timeout")
        self.lun_busy_retry_count = self.get_attribute(attribute_name="lun_busy_retry_count")
        self.name = self.get_attribute(attribute_name="name")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_iscsi_adapter_policy import VnicIscsiAdapterPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.tcp_connection_timeout is not None:
            kwargs["connection_time_out"] = self.tcp_connection_timeout
        if self.dhcp_timeout is not None:
            kwargs["dhcp_timeout"] = self.dhcp_timeout
        if self.lun_busy_retry_count is not None:
            kwargs["lun_busy_retry_count"] = self.lun_busy_retry_count

        iscsi_adapter_policy = VnicIscsiAdapterPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                           payload=iscsi_adapter_policy, detail=self.name):
            return False

        return True


# This Policy is not placed alphabetically because 'IntersightIscsiStaticTargetPolicy' mapping needs to be placed in
# '_POLICY_MAPPING_TABLE' of 'IntersightIscsiBootPolicy'. So 'IntersightIscsiStaticTargetPolicy' is placed before
# 'IntersightIscsiBootPolicy'.
class IntersightIscsiStaticTargetPolicy(IntersightConfigObject):
    _CONFIG_NAME = "iSCSI Static Target Policy"
    _CONFIG_SECTION_NAME = "iscsi_static_target_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.IscsiStaticTargetPolicy"

    def __init__(self, parent=None, iscsi_static_target_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=iscsi_static_target_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.target_name = self.get_attribute(attribute_name="target_name")
        self.port = self.get_attribute(attribute_name="port")
        self.ipv4_address = None
        self.ipv6_address = None
        # We keep this for compatibility purposes, but "ip_address" attribute
        # is deprecated starting with EasyUCS 1.0.4 (replaced by "ipv4_address")
        self.ip_address = None
        self.ipv4_address = self.get_attribute(attribute_name="ip_address", attribute_secondary_name="ipv4_address")
        if not self.ipv4_address or not is_ipv4_address_valid(self.ipv4_address):
            self.ipv4_address = None
            self.ipv6_address = self.get_attribute(attribute_name="ip_address", attribute_secondary_name="ipv6_address")
        self.ip_protocol = self.get_attribute(attribute_name="iscsi_ip_type", attribute_secondary_name="ip_protocol")
        self.name = self.get_attribute(attribute_name="name")
        self.lun = None

        if self._config.load_from == "live":
            if hasattr(self._object, "lun"):
                if self._object.lun:
                    self.lun = {}
                    self.lun["lun_id"] = self._object.lun.lun_id

        elif self._config.load_from == "file":
            for attribute in ["lun"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all lun_id of iSCSI Target Lun is set to None if it is not present
        if self.lun:
            for attribute in ["lun_id"]:
                if attribute not in self.lun:
                    self.lun[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_iscsi_static_target_policy import VnicIscsiStaticTargetPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.target_name is not None:
            kwargs["target_name"] = self.target_name
        if self.port is not None:
            kwargs["port"] = self.port
        if self.ipv4_address is not None:
            kwargs["ip_address"] = self.ipv4_address
            kwargs["iscsi_ip_type"] = "IPv4"
        elif self.ipv6_address is not None:
            kwargs["ip_address"] = self.ipv6_address
            kwargs["iscsi_ip_type"] = "IPv6"
        if self.lun is not None:
            from intersight.model.vnic_lun import VnicLun

            lun_kwargs = {
                "object_type": "vnic.Lun",
                "class_id": "vnic.Lun"
            }
            if self.lun["lun_id"] is not None:
                lun_kwargs["lun_id"] = self.lun["lun_id"]
            kwargs["lun"] = VnicLun(**lun_kwargs)

        iscsi_static_target_policy = VnicIscsiStaticTargetPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=iscsi_static_target_policy,
                           detail=self.name):
            return False

        return True


class IntersightIscsiBootPolicy(IntersightConfigObject):
    _CONFIG_NAME = "iSCSI Boot Policy"
    _CONFIG_SECTION_NAME = "iscsi_boot_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.IscsiBootPolicy"
    _POLICY_MAPPING_TABLE = {
        "ip_pool": IntersightIpPool,
        "iscsi_adapter_policy": IntersightIscsiAdapterPolicy,
        "primary_target_policy": IntersightIscsiStaticTargetPolicy,
        "secondary_target_policy": IntersightIscsiStaticTargetPolicy,
    }
    UCS_TO_INTERSIGHT_POOL_MAPPING_TABLE = {
        # IP Pool Attribute for UCS Systems
        "initiator_ip_address_policy": IntersightIpPool,
        # IP Pool Attribute for UCS Central
        "ip_pool": IntersightIpPool
    }

    def __init__(self, parent=None, iscsi_boot_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=iscsi_boot_policy)

        self.chap = None
        self.mutual_chap = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.dhcp_vendor_id_iqn = self.get_attribute(attribute_name="auto_targetvendor_name",
                                                     attribute_secondary_name="dhcp_vendor_id_iqn")
        self.initiator_ip_source = self.get_attribute(attribute_name="initiator_ip_source")
        self.initiator_static_ip_v4_config = None
        self.initiator_static_ip_v6_config = None
        # We keep this for compatibility purposes, but "ip_address" attribute
        # is deprecated starting with EasyUCS 1.0.4 (replaced by "ipv4_address")
        self.ip_address = None
        self.ip_protocol = self.get_attribute(attribute_name="iscsi_ip_type",
                                              attribute_secondary_name="ip_protocol")
        self.ipv4_address = self.get_attribute(attribute_name="initiator_static_ip_v4_address",
                                            attribute_secondary_name="ipv4_address")
        if not self.ipv4_address:
            self.ipv4_address = self.get_attribute(attribute_name="initiator_static_ip_v4_address",
                                                attribute_secondary_name="ip_address")
        self.ipv6_address = self.get_attribute(attribute_name="initiator_static_ip_v6_address",
                                              attribute_secondary_name="ipv6_address")
        self.ip_pool = None
        self.iscsi_adapter_policy = None
        self.name = self.get_attribute(attribute_name="name")
        self.primary_target_policy = None
        self.secondary_target_policy = None
        self.target_source_type = self.get_attribute(attribute_name="target_source_type")

        if self._config.load_from == "live":
            self.ip_pool = self._get_initiator_ip_pool()
            self.iscsi_adapter_policy = self._get_iscsi_adapter_policy()
            self.primary_target_policy = self._get_primary_target_policy()
            self.secondary_target_policy = self._get_secondary_target_policy()

            if self.target_source_type == "Static" and hasattr(self._object, "chap"):
                if self._object.chap:
                    if getattr(self._object.chap, "user_id", None):
                        self.chap = {}
                        self.chap["user_id"] = self._object.chap.user_id
                        if self._object.chap.is_password_set:
                            self.logger(level="warning",
                                        message="Password of " + self._CONFIG_NAME + " '" + self.name +
                                                "' - CHAP user '" + str(self._object.chap.user_id) +
                                                "' can't be exported")
                    # self._object.chap.password

            if self.target_source_type == "Static" and hasattr(self._object, "mutual_chap"):
                if self._object.mutual_chap:
                    if getattr(self._object.mutual_chap, "user_id", None):
                        self.mutual_chap = {}
                        self.mutual_chap["user_id"] = self._object.mutual_chap.user_id
                        if self._object.mutual_chap.is_password_set:
                            self.logger(level="warning",
                                        message="Password of " + self._CONFIG_NAME + " '" + self.name +
                                                "' - Mutual CHAP user '" + str(self._object.mutual_chap.user_id) +
                                                "' can't be exported")
                    # self._object.mutual_chap.password

            if self.target_source_type == "Static" and self.initiator_ip_source == "Static" and \
                    hasattr(self._object, "initiator_static_ip_v4_config") and self.ip_protocol == "IPv4":
                if self._object.initiator_static_ip_v4_config:
                    self.initiator_static_ip_v4_config = {}
                    self.initiator_static_ip_v4_config["default_gateway"] = \
                        getattr(self._object.initiator_static_ip_v4_config, "gateway", None)
                    self.initiator_static_ip_v4_config["subnet_mask"] = \
                        getattr(self._object.initiator_static_ip_v4_config, "netmask", None)
                    self.initiator_static_ip_v4_config["primary_dns"] = \
                        getattr(self._object.initiator_static_ip_v4_config, "primary_dns", None)
                    self.initiator_static_ip_v4_config["secondary_dns"] = \
                        getattr(self._object.initiator_static_ip_v4_config, "secondary_dns", None)
            elif self.target_source_type == "Static" and self.initiator_ip_source == "Static" and \
                    hasattr(self._object, "initiator_static_ip_v6_config") and self.ip_protocol == "IPv6":
                if self._object.initiator_static_ip_v6_config:
                    self.initiator_static_ip_v6_config = {}
                    self.initiator_static_ip_v6_config["default_gateway"] = \
                        getattr(self._object.initiator_static_ip_v6_config, "gateway", None)
                    self.initiator_static_ip_v6_config["prefix"] = \
                        getattr(self._object.initiator_static_ip_v6_config, "prefix", None)
                    self.initiator_static_ip_v6_config["primary_dns"] = \
                        getattr(self._object.initiator_static_ip_v6_config, "primary_dns", None)
                    self.initiator_static_ip_v6_config["secondary_dns"] = \
                        getattr(self._object.initiator_static_ip_v6_config, "secondary_dns", None)

        elif self._config.load_from == "file":
            for attribute in ["chap", "initiator_static_ip_v4_config", "initiator_static_ip_v6_config", "ip_pool",
                              "iscsi_adapter_policy", "mutual_chap", "primary_target_policy", "secondary_target_policy"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def _get_iscsi_adapter_policy(self):
        if hasattr(self._object, "iscsi_adapter_policy"):
            if self._object.iscsi_adapter_policy is not None:
                return self._get_policy_name(policy=self._object.iscsi_adapter_policy)

        return None

    def _get_primary_target_policy(self):
        if hasattr(self._object, "primary_target_policy"):
            if self._object.primary_target_policy is not None:
                return self._get_policy_name(policy=self._object.primary_target_policy)

        return None

    def _get_secondary_target_policy(self):
        if hasattr(self._object, "secondary_target_policy"):
            if self._object.secondary_target_policy is not None:
                return self._get_policy_name(policy=self._object.secondary_target_policy)

        return None

    def _get_initiator_ip_pool(self):
        if hasattr(self._object, "initiator_ip_pool"):
            if self._object.initiator_ip_pool is not None:
                return self._get_policy_name(policy=self._object.initiator_ip_pool)

        return None

    def clean_object(self):
        # We use this to make sure all attributes of Chap and Mutual
        # Chap are set to None if they are not present
        if self.chap:
            for attribute in ["user_id", "password"]:
                if attribute not in self.chap:
                    self.chap[attribute] = None

        if self.mutual_chap:
            for attribute in ["user_id", "password"]:
                if attribute not in self.mutual_chap:
                    self.mutual_chap[attribute] = None

        # We use this to make sure all attributes of Initiator
        # Static IPv4 Config are set to None if they are not present
        if self.initiator_static_ip_v4_config:
            for attribute in ["default_gateway", "subnet_mask", "primary_dns", "secondary_dns"]:
                if attribute not in self.initiator_static_ip_v4_config:
                    self.initiator_static_ip_v4_config[attribute] = None

        # We use this to make sure all attributes of Initiator
        # Static IPv6 Config are set to None if they are not present
        if self.initiator_static_ip_v6_config:
            for attribute in ["default_gateway", "prefix", "primary_dns", "secondary_dns"]:
                if attribute not in self.initiator_static_ip_v6_config:
                    self.initiator_static_ip_v6_config[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_iscsi_boot_policy import VnicIscsiBootPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")
        org = self.get_parent_org_relationship()
        if not org:
            return False

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.iscsi_adapter_policy is not None:
            # We need to identify the iSCSI Adapter Policy object reference
            iscsi_adapter_policy = self.get_live_object(
                object_name=self.iscsi_adapter_policy,
                object_type="vnic.IscsiAdapterPolicy"
            )
            if iscsi_adapter_policy:
                kwargs["iscsi_adapter_policy"] = iscsi_adapter_policy
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching iSCSI Adapter Policy '{self.iscsi_adapter_policy}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find iSCSI Adapter Policy '{self.iscsi_adapter_policy}'"
                )

        if self.target_source_type is not None:
            kwargs["target_source_type"] = self.target_source_type
        if self.target_source_type == "Auto":
            if self.dhcp_vendor_id_iqn is not None:
                kwargs["auto_targetvendor_name"] = self.dhcp_vendor_id_iqn
        elif self.target_source_type == "Static":
            if self.primary_target_policy is not None:
                # We need to identify the iSCSI Static Target Policy object reference
                iscsi_static_target_policy = self.get_live_object(
                    object_name=self.primary_target_policy,
                    object_type="vnic.IscsiStaticTargetPolicy"
                )
                if iscsi_static_target_policy:
                    kwargs["primary_target_policy"] = iscsi_static_target_policy
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching Primary Target Policy '{self.primary_target_policy}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                        message=f"Failed to find iSCSI Static Target Policy '{self.primary_target_policy}'"
                    )

            if self.secondary_target_policy is not None:
                # We need to identify the iSCSI Static Target Policy object reference
                iscsi_static_target_policy = self.get_live_object(
                    object_name=self.secondary_target_policy,
                    object_type="vnic.IscsiStaticTargetPolicy"
                )
                if iscsi_static_target_policy:
                    kwargs["secondary_target_policy"] = iscsi_static_target_policy
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching Secondary Target Policy '{self.secondary_target_policy}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                        message=f"Failed to find iSCSI Static Target Policy '{self.secondary_target_policy}'"
                    )
            if self.chap is not None:
                from intersight.model.vnic_iscsi_auth_profile import VnicIscsiAuthProfile

                chap_kwargs = {
                    "object_type": "vnic.IscsiAuthProfile",
                    "class_id": "vnic.IscsiAuthProfile"
                }
                if self.chap["user_id"] is not None:
                    chap_kwargs["user_id"] = self.chap["user_id"]
                if chap_kwargs["user_id"] != '':
                    if self.chap.get("password") is not None:
                        chap_kwargs["password"] = self.chap["password"]
                    else:
                        self.logger(
                            level="warning",
                            message="No password provided for field 'password' of object vnic.IscsiAuthProfile"
                        )
                else:
                    chap_kwargs["password"] = ''
                kwargs["chap"] = VnicIscsiAuthProfile(**chap_kwargs)
            if self.mutual_chap is not None:
                from intersight.model.vnic_iscsi_auth_profile import VnicIscsiAuthProfile

                mutual_chap_kwargs = {
                    "object_type": "vnic.IscsiAuthProfile",
                    "class_id": "vnic.IscsiAuthProfile"
                }
                if self.mutual_chap["user_id"] is not None:
                    mutual_chap_kwargs["user_id"] = self.mutual_chap["user_id"]
                if mutual_chap_kwargs["user_id"] != '':
                    if self.mutual_chap.get("password") is not None:
                        mutual_chap_kwargs["password"] = self.mutual_chap["password"]
                    else:
                        self.logger(
                            level="warning",
                            message="No password provided for field 'password' of object vnic.IscsiAuthProfile"
                        )
                else:
                    mutual_chap_kwargs["password"] = ''
                kwargs["mutual_chap"] = VnicIscsiAuthProfile(**mutual_chap_kwargs)

            if self.initiator_ip_source is not None:
                kwargs["initiator_ip_source"] = self.initiator_ip_source
            if self.initiator_ip_source == "Pool":
                if self.ip_pool is not None:
                    # We need to identify the IP Pool object reference
                    ip_pool = self.get_live_object(object_name=self.ip_pool, object_type="ippool.Pool")
                    if ip_pool:
                        kwargs["initiator_ip_pool"] = ip_pool
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching IP Pool '{self.ip_pool}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find IP Pool '{self.ip_pool}'"
                        )

            elif self.initiator_ip_source == "Static" and self.ipv4_address is not None:
                kwargs["initiator_static_ip_v4_address"] = self.ipv4_address
                kwargs["iscsi_ip_type"] = "IPv4"
                if self.initiator_static_ip_v4_config is not None:
                    from intersight.model.ippool_ip_v4_config import IppoolIpV4Config

                    initiator_static_ip_v4_config_kwargs = {
                        "object_type": "ippool.IpV4Config",
                        "class_id": "ippool.IpV4Config"
                    }
                    if self.initiator_static_ip_v4_config["default_gateway"] is not None:
                        initiator_static_ip_v4_config_kwargs["gateway"] = \
                            self.initiator_static_ip_v4_config["default_gateway"]
                    if self.initiator_static_ip_v4_config["subnet_mask"] is not None:
                        initiator_static_ip_v4_config_kwargs["netmask"] = \
                            self.initiator_static_ip_v4_config["subnet_mask"]
                    if self.initiator_static_ip_v4_config["primary_dns"] is not None:
                        initiator_static_ip_v4_config_kwargs["primary_dns"] = \
                            self.initiator_static_ip_v4_config["primary_dns"]
                    if self.initiator_static_ip_v4_config["secondary_dns"] is not None:
                        initiator_static_ip_v4_config_kwargs["secondary_dns"] = \
                            self.initiator_static_ip_v4_config["secondary_dns"]
                    kwargs["initiator_static_ip_v4_config"] = IppoolIpV4Config(**initiator_static_ip_v4_config_kwargs)
                
            elif self.initiator_ip_source == "Static" and self.ipv6_address is not None:
                kwargs["initiator_static_ip_v6_address"] = self.ipv6_address
                kwargs["iscsi_ip_type"] = "IPv6"
                if self.initiator_static_ip_v6_config is not None:
                    from intersight.model.ippool_ip_v6_config import IppoolIpV6Config

                    initiator_static_ip_v6_config_kwargs = {
                        "object_type": "ippool.IpV6Config",
                        "class_id": "ippool.IpV6Config"
                    }
                    if self.initiator_static_ip_v6_config["default_gateway"] is not None:
                        initiator_static_ip_v6_config_kwargs["gateway"] = \
                            self.initiator_static_ip_v6_config["default_gateway"]
                    if self.initiator_static_ip_v6_config["prefix"] is not None:
                        initiator_static_ip_v6_config_kwargs["prefix"] = \
                            self.initiator_static_ip_v6_config["prefix"]
                    if self.initiator_static_ip_v6_config["primary_dns"] is not None:
                        initiator_static_ip_v6_config_kwargs["primary_dns"] = \
                            self.initiator_static_ip_v6_config["primary_dns"]
                    if self.initiator_static_ip_v6_config["secondary_dns"] is not None:
                        initiator_static_ip_v6_config_kwargs["secondary_dns"] = \
                            self.initiator_static_ip_v6_config["secondary_dns"]
                    kwargs["initiator_static_ip_v6_config"] = IppoolIpV6Config(**initiator_static_ip_v6_config_kwargs)

        iscsi_boot_policy = VnicIscsiBootPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=iscsi_boot_policy, detail=self.name):
            return False

        return True


class IntersightLanConnectivityPolicy(IntersightConfigObject):
    from config.intersight.network_policies import IntersightVnicTemplate
    _CONFIG_NAME = "LAN Connectivity Policy"
    _CONFIG_SECTION_NAME = "lan_connectivity_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.LanConnectivityPolicy"
    _POLICY_MAPPING_TABLE = {
        "iqn_pool": IntersightIqnPool,
        "vnics": [
            {
                "ethernet_adapter_policy": IntersightEthernetAdapterPolicy,
                "ethernet_network_control_policy": IntersightEthernetNetworkControlPolicy,
                "ethernet_network_group_policies": [IntersightEthernetNetworkGroupPolicy],
                "ethernet_network_group_policy": IntersightEthernetNetworkGroupPolicy,  # Deprecated
                "ethernet_network_policy": IntersightEthernetNetworkPolicy,
                "ethernet_qos_policy": IntersightEthernetQosPolicy,
                "iscsi_boot_policy": IntersightIscsiBootPolicy,
                "mac_address_pool": IntersightMacPool,
                "usnic_settings": {
                    "usnic_adapter_policy": IntersightEthernetAdapterPolicy
                },
                "vmq_settings": {
                    "vmmq_adapter_policy": IntersightEthernetAdapterPolicy
                },
                "vnic_template": IntersightVnicTemplate
            }
        ]
    }
    UCS_TO_INTERSIGHT_POLICY_MAPPING_TABLE = {
        "adapter_policy": "ethernet_adapter_policy",
        "network_control_policy": "ethernet_network_control_policy",
        "qos_policy": "ethernet_qos_policy"
    }
    UCS_TO_INTERSIGHT_POOL_MAPPING_TABLE = {
        "mac_address_pool": IntersightMacPool,
        # IQN Pool from Global Identifier
        "iscsi_iqn_pool_name": IntersightIqnPool,
        # IQN Pool from Individual iSCSI vNIC
        "iqn_pool": IntersightIqnPool
    }

    def __init__(self, parent=None, lan_connectivity_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=lan_connectivity_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_azure_stack_host_qos = self.get_attribute(attribute_name="azure_qos_enabled",
                                                              attribute_secondary_name="enable_azure_stack_host_qos")
        self.iqn_allocation_type = self.get_attribute(attribute_name="iqn_allocation_type")
        self.iqn_identifier = self.get_attribute(attribute_name="static_iqn_name",
                                                 attribute_secondary_name="iqn_identifier")
        self.iqn_pool = None
        self.name = self.get_attribute(attribute_name="name")
        self.target_platform = self.get_attribute(attribute_name="target_platform")
        self.vnic_placement_mode = self.get_attribute(attribute_name="placement_mode",
                                                      attribute_secondary_name="vnic_placement_mode")
        # TODO: Change default to empty list
        self.vnics = None

        if self._config.load_from == "live":
            # Renaming Target Platform to be more user-friendly
            if self.target_platform == "FIAttached":
                self.target_platform = "FI-Attached"

            # Renaming IQN Allocation Type to lowercase to be more user-friendly
            # (and aligned with vNIC mac_address_allocation_type)
            if self.iqn_allocation_type:
                self.iqn_allocation_type = self.iqn_allocation_type.lower()

            if self.iqn_allocation_type == "pool":
                # We avoid fetching the IQN Pool in case IQN Allocation Type is not "pool". This prevents an issue in
                # case Intersight has both a pool and a static entry defined (EASYUCS-666).
                if lan_connectivity_policy.iqn_pool:
                    self.iqn_pool = self._get_policy_name(policy=lan_connectivity_policy.iqn_pool)
            self.vnics = self._get_vnics()

        elif self._config.load_from == "file":
            for attribute in ["iqn_pool", "vnics"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # We use this to make sure all options of a vNIC are set to None if they are not present
            if self.vnics:
                for vnic in self.vnics:
                    for attribute in ["automatic_pci_link_assignment", "automatic_slot_id_assignment", "cdn_source",
                                      "cdn_value", "enable_failover", "enable_virtual_machine_multi_queue",
                                      "ethernet_adapter_policy", "ethernet_network_control_policy",
                                      "ethernet_network_group_policies", "ethernet_network_group_policy",
                                      "ethernet_network_policy", "ethernet_qos_policy", "iscsi_boot_policy",
                                      "mac_address_allocation_type", "mac_address_pool", "mac_address_static", "name",
                                      "pci_link", "pci_link_assignment_mode", "pci_order", "pin_group_name", "slot_id",
                                      "sriov_settings", "switch_id", "uplink_port", "usnic_settings", "vmq_settings"]:
                        if attribute not in vnic:
                            vnic[attribute] = None

                    if vnic["sriov_settings"]:
                        for attribute in ["completion_queue_count_per_vf", "interrupt_count_per_vf", "number_of_vfs",
                                          "receive_queue_count_per_vf", "transmit_queue_count_per_vf"]:
                            if attribute not in vnic["sriov_settings"].keys():
                                vnic["sriov_settings"][attribute] = None

                    if vnic["usnic_settings"]:
                        for attribute in ["class_of_service", "number_of_usnics", "usnic_adapter_policy"]:
                            if attribute not in vnic["usnic_settings"].keys():
                                vnic["usnic_settings"][attribute] = None

                    if vnic["vmq_settings"]:
                        for attribute in ["enable_virtual_machine_multi_queue", "number_of_interrupts",
                                          "number_of_sub_vnics", "number_of_virtual_machine_queues",
                                          "vmmq_adapter_policy"]:
                            if attribute not in vnic["vmq_settings"].keys():
                                vnic["vmq_settings"][attribute] = None

    def _get_vnics(self):
        # Fetches the vNICs configuration of a LAN Connectivity Policy
        if "vnic_eth_if" in self._config.sdk_objects:
            vnics = []
            for vnic_eth_if in self._config.sdk_objects["vnic_eth_if"]:
                overriden_list = []
                if vnic_eth_if.lan_connectivity_policy:
                    if vnic_eth_if.lan_connectivity_policy.moid == self._moid:
                        vnic = {
                            "name": vnic_eth_if.name,
                            "pci_order": vnic_eth_if.order
                        }

                        if self.target_platform in ["FI-Attached"]:
                            # If the vNIC is created from a vNIC template, fetch the source vNIC template
                            if vnic_eth_if.src_template:
                                src_vnic_template = self._get_policy_name(policy=vnic_eth_if.src_template)
                                if src_vnic_template:
                                    vnic["vnic_template"] = src_vnic_template
                                # If the vNIC is created from a template and overrides are allowed in a template,
                                # Fetch the overridden list
                                if vnic_eth_if.overridden_list:
                                    overriden_list = vnic_eth_if.overridden_list

                        if vnic_eth_if.placement:
                            vnic["automatic_slot_id_assignment"] = vnic_eth_if.placement.auto_slot_id
                            if not vnic_eth_if.placement.auto_slot_id:
                                vnic["slot_id"] = vnic_eth_if.placement.id
                            vnic["automatic_pci_link_assignment"] = vnic_eth_if.placement.auto_pci_link
                            if not vnic_eth_if.placement.auto_pci_link:
                                vnic["pci_link_assignment_mode"] = vnic_eth_if.placement.pci_link_assignment_mode
                                if vnic_eth_if.placement.pci_link_assignment_mode in ["Custom"]:
                                    vnic["pci_link"] = vnic_eth_if.placement.pci_link

                            if self.target_platform in ["FI-Attached"]:

                                # Add 'switch_id' to the vnic dictionary if vNIC template is absent or 'switch_id' is an
                                # overridden field
                                if not vnic.get("vnic_template") or "Placement.SwitchId" in overriden_list:
                                    vnic["switch_id"] = vnic_eth_if.placement.switch_id
                                    # Handle 'None' as a string in 'switch_id'
                                    if vnic["switch_id"] in ["None"]:
                                        vnic["switch_id"] = None

                            elif self.target_platform in ["Standalone"]:
                                vnic["uplink_port"] = vnic_eth_if.placement.uplink

                        # Add CDN to the vNIC dictionary if vNIC template is absent
                        if not vnic.get("vnic_template"):
                            if vnic_eth_if.cdn:
                                vnic["cdn_source"] = vnic_eth_if.cdn.source
                                vnic["cdn_value"] = vnic_eth_if.cdn.value

                        if self.target_platform in ["FI-Attached"]:
                            # Add the following attributes to the vNIC dictionary if vNIC Template is absent or
                            # attribute is an overridden field
                            if not vnic.get("vnic_template") or "PinGroupName" in overriden_list:
                                vnic["pin_group_name"] = vnic_eth_if.pin_group_name if vnic_eth_if.pin_group_name \
                                    else None
                            if not vnic.get("vnic_template"):
                                vnic["enable_failover"] = vnic_eth_if.failover_enabled
                            if not vnic.get("vnic_template") or "MacPool" in overriden_list:
                                vnic["mac_address_allocation_type"] = vnic_eth_if.mac_address_type.lower()
                                # We only fetch the MAC Address Pool or Static MAC for FI-Attached servers
                                if vnic_eth_if.mac_address_type in ["POOL"]:
                                    if vnic_eth_if.mac_pool:
                                        mac_pool = self._get_policy_name(policy=vnic_eth_if.mac_pool)
                                        if mac_pool:
                                            vnic["mac_address_pool"] = mac_pool
                                elif vnic_eth_if.mac_address_type in ["STATIC"]:
                                    vnic["mac_address_static"] = vnic_eth_if.static_mac_address
                            # We only fetch Ethernet Network Group Policy, Ethernet Network Control Policy &
                            # iSCSI Boot Policy for FI-Attached servers
                            if not vnic.get("vnic_template"):
                                # If vNIC Template is attached then Ethernet Network Group Policy and Ethernet
                                # Network Control Policy are set at the Template level and cannot be overridden.
                                # If vNIC Template is not attached, then these fields are set at the vNIC level.
                                if vnic_eth_if.fabric_eth_network_group_policy:
                                    if len(vnic_eth_if.fabric_eth_network_group_policy) == 1:
                                        fabric_eth_network_group_policy = self._get_policy_name(
                                            policy=vnic_eth_if.fabric_eth_network_group_policy[0])
                                        if fabric_eth_network_group_policy:
                                            vnic["ethernet_network_group_policies"] = [fabric_eth_network_group_policy]
                                    elif len(vnic_eth_if.fabric_eth_network_group_policy) > 1:
                                        vnic["ethernet_network_group_policies"] = []
                                        for eth_network_group_policy in vnic_eth_if.fabric_eth_network_group_policy:
                                            fabric_eth_network_group_policy = self._get_policy_name(
                                                policy=eth_network_group_policy)
                                            if fabric_eth_network_group_policy:
                                                vnic["ethernet_network_group_policies"].append(
                                                    fabric_eth_network_group_policy)
                                    else:
                                        self.logger(level="error", message="No Ethernet Network Group Policies " +
                                                                           "assigned to vNIC " + vnic_eth_if.name)
                                if vnic_eth_if.fabric_eth_network_control_policy:
                                    fabric_eth_network_control_policy = \
                                        self._get_policy_name(policy=vnic_eth_if.fabric_eth_network_control_policy)
                                    if fabric_eth_network_control_policy:
                                        vnic["ethernet_network_control_policy"] = fabric_eth_network_control_policy
                            if not vnic.get("vnic_template") or "IscsiBootPolicy" in overriden_list:
                                if vnic_eth_if.iscsi_boot_policy:
                                    iscsi_boot_policy = self._get_policy_name(policy=vnic_eth_if.iscsi_boot_policy)
                                    if iscsi_boot_policy:
                                        vnic["iscsi_boot_policy"] = iscsi_boot_policy

                        elif self.target_platform in ["Standalone"]:
                            # We only fetch Ethernet Network Policy for Standalone servers
                            if vnic_eth_if.eth_network_policy:
                                eth_network_policy = \
                                    self._get_policy_name(policy=vnic_eth_if.eth_network_policy)
                                if eth_network_policy:
                                    vnic["ethernet_network_policy"] = eth_network_policy

                        if not vnic.get("vnic_template"):
                            # If vNIC Template is attached then Ethernet Qos Policy, usnic_settings, vmq_settings,
                            # sriov_settings are set at the Template level and cannot be overridden.
                            # If vNIC Template is not attached, then these fields are set at the vNIC level.
                            if vnic_eth_if.eth_qos_policy:
                                eth_qos_policy = self._get_policy_name(policy=vnic_eth_if.eth_qos_policy)
                                if eth_qos_policy:
                                    vnic["ethernet_qos_policy"] = eth_qos_policy
                            if vnic_eth_if.usnic_settings:
                                if vnic_eth_if.usnic_settings.count > 0:
                                    vnic["usnic_settings"] = {
                                        "number_of_usnics": vnic_eth_if.usnic_settings.count
                                    }
                                    if self.target_platform in ["Standalone"]:
                                        vnic["usnic_settings"]["class_of_service"] = vnic_eth_if.usnic_settings.cos
                                    if vnic_eth_if.usnic_settings.usnic_adapter_policy:
                                        # usNIC Settings is not a reference object, rather it's a complex type in the
                                        # intersight backend. Which means there is no Moid or Name attributes in
                                        # usNIC Settings. So to fetch usNIC Adapter Policy we iterate over the fetched
                                        # Eth Adapter Policy SDK objects and find the relevant object.
                                        for vnic_eth_adapter_policy in self._config.sdk_objects["vnic_eth_adapter_policy"]:
                                            if vnic_eth_if.usnic_settings.usnic_adapter_policy == \
                                                    vnic_eth_adapter_policy.moid:
                                                vnic["usnic_settings"]["usnic_adapter_policy"] = self._get_policy_name(
                                                    policy=vnic_eth_adapter_policy)
                                                break
                            if vnic_eth_if.vmq_settings:
                                if vnic_eth_if.vmq_settings.enabled:
                                    vnic["vmq_settings"] = {
                                        "enable_virtual_machine_multi_queue": vnic_eth_if.vmq_settings.multi_queue_support
                                    }
                                    if not vnic_eth_if.vmq_settings.multi_queue_support:
                                        vnic["vmq_settings"]["number_of_interrupts"] = \
                                            vnic_eth_if.vmq_settings.num_interrupts
                                        vnic["vmq_settings"]["number_of_virtual_machine_queues"] = \
                                            vnic_eth_if.vmq_settings.num_vmqs
                                    else:
                                        vnic["vmq_settings"]["number_of_sub_vnics"] = vnic_eth_if.vmq_settings.num_sub_vnics
                                        # VMQ Settings is not a reference object, rather it's a complex type in the
                                        # intersight backend. Which means there is no Moid or Name attributes in
                                        # VMQ Settings. So to fetch VMQ Adapter Policy we iterate over the fetched
                                        # Eth Adapter Policy SDK objects and find the relevant object.
                                        for vmmq_adapter_policy in self._config.sdk_objects["vnic_eth_adapter_policy"]:
                                            if vnic_eth_if.vmq_settings.vmmq_adapter_policy == vmmq_adapter_policy.moid:
                                                vnic["vmq_settings"]["vmmq_adapter_policy"] = self._get_policy_name(
                                                    policy=vmmq_adapter_policy)
                                                break
                            if vnic_eth_if.sriov_settings:
                                if vnic_eth_if.sriov_settings.enabled:
                                    vnic["sriov_settings"] = {
                                        "number_of_vfs": vnic_eth_if.sriov_settings.vf_count,
                                        "receive_queue_count_per_vf": vnic_eth_if.sriov_settings.rx_count_per_vf,
                                        "transmit_queue_count_per_vf": vnic_eth_if.sriov_settings.tx_count_per_vf,
                                        "completion_queue_count_per_vf": vnic_eth_if.sriov_settings.comp_count_per_vf,
                                        "interrupt_count_per_vf": vnic_eth_if.sriov_settings.int_count_per_vf
                                    }
                        # Add the Ethernet Adapter Policy to the vNIC dictionary if vNIC Template is absent or
                        # attribute is an overridden field
                        if not vnic.get("vnic_template") or "EthAdapterPolicy" in overriden_list:
                            if vnic_eth_if.eth_adapter_policy:
                                eth_adapter_policy = self._get_policy_name(policy=vnic_eth_if.eth_adapter_policy)
                                if eth_adapter_policy:
                                    vnic["ethernet_adapter_policy"] = eth_adapter_policy

                        vnics.append(vnic)

            return vnics

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_lan_connectivity_policy import VnicLanConnectivityPolicy
        from intersight.model.vnic_vnic_template import VnicVnicTemplate

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enable_azure_stack_host_qos is not None:
            kwargs["azure_qos_enabled"] = self.enable_azure_stack_host_qos
        if self.iqn_allocation_type is not None:
            kwargs["iqn_allocation_type"] = self.iqn_allocation_type.title()
        if self.iqn_identifier is not None:
            kwargs["static_iqn_name"] = self.iqn_identifier
        if self.target_platform is not None:
            if self.target_platform in ["FI-Attached"]:
                kwargs["target_platform"] = "FIAttached"
            else:
                kwargs["target_platform"] = self.target_platform
        if self.vnic_placement_mode is not None:
            kwargs["placement_mode"] = self.vnic_placement_mode

        # We need to map the IQN Pool in case it is used
        if self.iqn_pool is not None:
            # We need to identify the IQN Pool object reference
            iqn_pool = self.get_live_object(
                object_name=self.iqn_pool,
                object_type="iqnpool.Pool"
            )
            if iqn_pool:
                kwargs["iqn_pool"] = iqn_pool
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching IQN Pool '{self.iqn_pool}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find IQN Pool '{self.iqn_pool}'"
                )

        lan_connectivity_policy = VnicLanConnectivityPolicy(**kwargs)

        lcp = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=lan_connectivity_policy,
                          detail=self.name, return_relationship=True)
        if not lcp:
            return False

        # We now create the vnic.EthIf objects for each vNIC
        if self.vnics is not None:
            from intersight.model.vnic_eth_if import VnicEthIf
            from intersight.model.motemplate_action_entry import MotemplateActionEntry

            for vnic in self.vnics:
                # We first need to check if vNIC with the same name already exists
                vnic_ethif = self.get_live_object(
                    object_name=vnic.get("name"),
                    object_type="vnic.EthIf",
                    return_reference=False,
                    log=False,
                    query_filter=f"Name eq '{vnic['name']}' and LanConnectivityPolicy/Moid eq '{lcp.moid}'"
                )

                if not getattr(self._config, "update_existing_intersight_objects", False) and vnic_ethif:
                    message = f"Object type vnic.EthIf with name={vnic.get('name')} " \
                              f"already exists"
                    self.logger(level="info", message=message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=vnic['name'], obj_type="vnic.EthIf", status="skipped",
                        message=message)
                    continue

                # In case this vNIC is derived from vNIC template, we use the 'derive' mechanism to create it
                if vnic.get("vnic_template"):
                    if not vnic_ethif:
                        from intersight.model.bulk_mo_cloner import BulkMoCloner

                        # The vNIC is newly derived from a vNIC template and is not a pre-existing entity.
                        # Therefore, we need to Attach the source template from which the vNIC is derived and target
                        # fields that can be set at the vNIC level, including overridden fields to the BulkMoCloner.
                        kwargs_mo_cloner = {
                            "sources": [],
                            "targets": []
                        }
                        # We need to identify the Moid of the source vNIC Template
                        vnic_template = self.get_live_object(object_name=vnic["vnic_template"],
                                                             object_type="vnic.VnicTemplate")

                        if vnic_template:
                            template_moid = vnic_template.moid
                            source_template = {
                                "moid": template_moid,
                                "object_type": "vnic.VnicTemplate"
                            }
                            kwargs_mo_cloner["sources"].append(VnicVnicTemplate(**source_template))
                        else:
                            err_message = "Unable to locate source vNIC Template " + \
                                          vnic['vnic_template'] + " to derive vNIC Template " + vnic['name']
                            self.logger(level="error", message=err_message)
                            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=vnic['name'],
                                                                                obj_type="vnic.VnicTemplate",
                                                                                status="failed", message=err_message)
                            continue

                        # We now need to specify the attribute of the target vNIC
                        target_vnic = {
                            "object_type": "vnic.EthIf",
                            "class_id": "vnic.EthIf",
                            "lan_connectivity_policy": lcp
                        }
                        if vnic.get("name") is not None:
                            target_vnic["name"] = vnic["name"]
                        if vnic.get("mac_address_allocation_type") is not None:
                            target_vnic["mac_address_type"] = vnic["mac_address_allocation_type"].upper()
                        if vnic.get("pci_order") is not None:
                            target_vnic["order"] = vnic["pci_order"]
                        if vnic.get("pin_group_name"):
                            target_vnic["pin_group_name"] = vnic["pin_group_name"]

                        # It is essential to manage overridden values effectively.
                        # This includes handling overridden attributes such as MAC pool, placement settings,
                        # pin group name, eth adapter policy, and iscsi boot policy.
                        if vnic.get("mac_address_allocation_type") in ["pool"]:
                            if vnic.get("mac_address_pool"):
                                # We need to identify the MAC Pool object reference
                                mac_pool = self.get_live_object(
                                    object_name=vnic["mac_address_pool"],
                                    object_type="macpool.Pool"
                                )
                                if mac_pool:
                                    target_vnic["mac_pool"] = mac_pool
                                else:
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=f"Attaching MAC Pool '{vnic['mac_address_pool']}' to vNIC - "
                                                             f"{str(vnic['name'])}",
                                        obj_type="vnic.EthIf", status="failed",
                                        message=f"Failed to find MAC Pool '{vnic['mac_address_pool']}'"
                                    )
                        elif vnic.get("mac_address_allocation_type") in ["static"]:
                            if vnic.get("mac_address_static"):
                                target_vnic["static_mac_address"] = vnic["mac_address_static"]

                        # Handling the placement settings of the vNIC
                        from intersight.model.vnic_placement_settings import VnicPlacementSettings
                        vnic_placement_settings = {
                            "object_type": "vnic.PlacementSettings",
                            "class_id": "vnic.PlacementSettings"
                        }

                        if vnic.get("switch_id") is not None:
                            vnic_placement_settings["switch_id"] = vnic["switch_id"]
                        if vnic.get("automatic_slot_id_assignment", False):
                            vnic_placement_settings["auto_slot_id"] = True
                        elif vnic.get("slot_id") is not None:  # We have a Slot ID value
                            vnic_placement_settings["auto_slot_id"] = False
                            vnic_placement_settings["id"] = vnic["slot_id"]
                        else:  # We don't have any slot ID value - we set Auto Slot ID to enabled
                            vnic_placement_settings["auto_slot_id"] = True

                        if vnic.get("automatic_pci_link_assignment", False):
                            vnic_placement_settings["auto_pci_link"] = True
                        # We have a PCI Link value - We set assignment mode to Custom
                        elif vnic.get("pci_link") is not None:
                            vnic_placement_settings["auto_pci_link"] = False
                            vnic_placement_settings["pci_link_assignment_mode"] = "Custom"
                            vnic_placement_settings["pci_link"] = vnic["pci_link"]
                        elif vnic.get("pci_link_assignment_mode") in ["Load-Balanced"]:
                            # Assignment mode set to Load-Balanced
                            vnic_placement_settings["auto_pci_link"] = False
                            vnic_placement_settings["pci_link_assignment_mode"] = "Load-Balanced"
                        else:  # We don't have any PCI Link value - we set Auto PCI Link to enabled
                            vnic_placement_settings["auto_pci_link"] = True

                        if vnic.get("uplink_port") is not None:
                            vnic_placement_settings["uplink"] = vnic["uplink_port"]
                        target_vnic["placement"] = VnicPlacementSettings(**vnic_placement_settings)

                        if vnic.get("ethernet_adapter_policy"):
                            # We need to identify the Ethernet Adapter Policy object reference
                            eth_adapter_policy = self.get_live_object(
                                object_name=vnic["ethernet_adapter_policy"],
                                object_type="vnic.EthAdapterPolicy"
                            )
                            if eth_adapter_policy:
                                target_vnic["eth_adapter_policy"] = eth_adapter_policy
                            else:
                                self._config.push_summary_manager.add_object_status(
                                    obj=self,
                                    obj_detail=f"Attaching Eth Adapter Policy '{vnic['ethernet_adapter_policy']}' "
                                               f"to - vNIC - {str(vnic['name'])}",
                                    obj_type="vnic.EthIf", status="failed",
                                    message=f"Failed to find Eth Adapter Policy '{vnic['ethernet_adapter_policy']}'"
                                )
                        if vnic.get("iscsi_boot_policy"):
                            # We need to identify the iSCSI Boot Policy object reference
                            iscsi_boot_policy = self.get_live_object(
                                object_name=vnic["iscsi_boot_policy"],
                                object_type="vnic.IscsiBootPolicy"
                            )
                            if iscsi_boot_policy:
                                target_vnic["iscsi_boot_policy"] = iscsi_boot_policy
                            else:
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"Attaching iSCSI Boot Policy '{vnic['iscsi_boot_policy']}' "
                                                         f"to vNIC - {str(vnic['name'])}",
                                    obj_type="vnic.EthIf", status="failed",
                                    message=f"Failed to find iSCSI Boot Policy '{vnic['iscsi_boot_policy']}'"
                                )

                        kwargs_mo_cloner["targets"].append(VnicEthIf(**target_vnic))

                        mo_cloner = BulkMoCloner(**kwargs_mo_cloner)

                        self.commit(object_type="bulk.MoCloner", payload=mo_cloner,
                                    detail=self.name + " - vNIC " + str(vnic["name"]))
                        continue
                    else:
                        # We found a vNIC with the same name,
                        # we need to check if it is bound to the same vNIC Template or a different vNIC Template
                        # If vNIC is derived from different vNIC Template we will detach it from its Template and
                        # reattach it to the desired Template.
                        if vnic_ethif.src_template:
                            src_template = self._device.query(
                                object_type="vnic.VnicTemplate",
                                filter="Moid eq '" + vnic_ethif.src_template.moid + "'"
                            )
                            if len(src_template) == 1:
                                if src_template[0].name == vnic.get("vnic_template"):
                                    # This vNIC is already derived from the same vNIC Template
                                    info_message = "vNIC " + vnic.get("name") + " exists and is already derived " + \
                                                   "from same vNIC Template " + vnic.get("vnic_template")
                                    self.logger(level="info", message=info_message)
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=vnic.get("name"), obj_type="vnic.EthIf",
                                        status="skipped", message=info_message)
                                    continue
                                else:
                                    # vNIC is derived from another vNIC Template
                                    # We will detach it from its Template and reattach it to the desired Template
                                    self.logger(
                                        level="info",
                                        message="vNIC " + vnic.get("name") +
                                                " exists and is derived from different vNIC Template " +
                                                src_template[0].name
                                    )
                                    self.logger(
                                        level="info",
                                        message="Detaching vNIC " + vnic.get("name") +
                                                " from vNIC Template " + src_template[0].name
                                    )
                                    kwargs = {
                                        "object_type": "vnic.EthIf",
                                        "class_id": "vnic.EthIf",
                                        "name": vnic.get("name"),
                                        "lan_connectivity_policy": lcp,
                                        "src_template": None
                                    }
                                    vnic_ethif_payload = VnicEthIf(**kwargs)

                                    if not self.commit(object_type="vnic.EthIf",
                                                       payload=vnic_ethif_payload,
                                                       detail="Detaching from template " + src_template[0].name,
                                                       key_attributes=["name", "lan_connectivity_policy"]):
                                        continue

                                    self.logger(
                                        level="info",
                                        message="Attaching vNIC " + vnic.get("name") +
                                                " to vNIC Template " + vnic.get("vnic_template")
                                    )
                                    # We need to identify the Moid of the vNIC Template
                                    vnic_template = self.get_live_object(
                                        object_name=vnic.get("vnic_template"),
                                        object_type="vnic.VnicTemplate"
                                    )

                                    # Attach action needs to be specified in the TemplateActions
                                    # To attach vNIC to a template
                                    kwargs_template_actions = {
                                        "object_type": "motemplate.ActionEntry",
                                        "class_id": "motemplate.ActionEntry",
                                        "type": "Attach"
                                    }
                                    kwargs["template_actions"] = [MotemplateActionEntry(**kwargs_template_actions)]
                                    kwargs["src_template"] = vnic_template
                                    vnic_ethif_payload = VnicEthIf(**kwargs)

                                    self.commit(object_type="vnic.EthIf",
                                                payload=vnic_ethif_payload,
                                                detail="Attaching to template " + vnic.get("vnic_template"),
                                                key_attributes=["name", "lan_connectivity_policy"])
                                    continue
                            else:
                                err_message = "Could not find vNIC Template " + vnic.get("vnic_template")
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=vnic['name'], obj_type="vnic.EthIf",
                                    status="failed",
                                    message=err_message)
                                continue
                        else:
                            # vNIC is not currently bound to a template. So we just need to bind it
                            # We need to identify the Moid of the Attached vNIC Template
                            vnic_template = self.get_live_object(
                                object_name=vnic.get("vnic_template"),
                                object_type="vnic.VnicTemplate"
                            )
                            # Attach action needs to be specified in the TemplateActions to attach vNIC to a template.
                            kwargs_template_actions = {
                                "object_type": "motemplate.ActionEntry",
                                "class_id": "motemplate.ActionEntry",
                                "type": "Attach"
                            }

                            kwargs = {
                                "object_type": "vnic.EthIf",
                                "class_id": "vnic.EthIf",
                                "name": vnic.get("name"),
                                "lan_connectivity_policy": lcp,
                                "template_actions": [MotemplateActionEntry(**kwargs_template_actions)],
                                "src_template": vnic_template
                            }
                            vnic_ethif_payload = VnicEthIf(**kwargs)

                            self.commit(object_type="vnic.EthIf", payload=vnic_ethif_payload,
                                        detail="Attaching to template " + vnic.get("vnic_template"))
                            continue

                # We now need to specify the attributes of the target vNIC if it is not created from a template
                kwargs = {
                    "object_type": "vnic.EthIf",
                    "class_id": "vnic.EthIf",
                    "lan_connectivity_policy": lcp
                }
                if vnic.get("name") is not None:
                    kwargs["name"] = vnic["name"]
                if vnic.get("enable_failover") is not None:
                    kwargs["failover_enabled"] = vnic["enable_failover"]
                if vnic.get("pci_order") is not None:
                    kwargs["order"] = vnic["pci_order"]
                if vnic.get("pin_group_name") is not None:
                    kwargs["pin_group_name"] = vnic["pin_group_name"]

                # Handling the MAC Address settings of the vNIC
                if vnic.get("mac_address_allocation_type") is not None:
                    kwargs["mac_address_type"] = vnic["mac_address_allocation_type"].upper()
                if vnic.get("mac_address_allocation_type") in ["pool"]:
                    if vnic.get("mac_address_pool") is not None:
                        # We need to identify the MAC Pool object reference
                        mac_pool = self.get_live_object(
                            object_name=vnic["mac_address_pool"],
                            object_type="macpool.Pool"
                        )
                        if mac_pool:
                            kwargs["mac_pool"] = mac_pool
                        else:
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"Attaching MAC Pool '{vnic['mac_address_pool']}' to vNIC - "
                                                     f"{str(vnic['name'])}",
                                obj_type="vnic.EthIf", status="failed",
                                message=f"Failed to find MAC Pool '{vnic['mac_address_pool']}'"
                            )

                elif vnic.get("mac_address_allocation_type") in ["static"]:
                    if vnic["mac_address_static"] is not None:
                        kwargs["static_mac_address"] = vnic["mac_address_static"]

                # Handling the placement settings of the vNIC
                from intersight.model.vnic_placement_settings import VnicPlacementSettings
                kwargs_placement = {
                    "object_type": "vnic.PlacementSettings",
                    "class_id": "vnic.PlacementSettings"
                }
                if vnic.get("switch_id") is not None:
                    kwargs_placement["switch_id"] = vnic["switch_id"]

                if vnic.get("automatic_slot_id_assignment", False):
                    kwargs_placement["auto_slot_id"] = True
                elif vnic.get("slot_id") is not None:  # We have a Slot ID value
                    kwargs_placement["auto_slot_id"] = False
                    kwargs_placement["id"] = vnic["slot_id"]
                else:  # We don't have any slot ID value - we set Auto Slot ID to enabled
                    kwargs_placement["auto_slot_id"] = True

                if vnic.get("automatic_pci_link_assignment", False):
                    kwargs_placement["auto_pci_link"] = True
                elif vnic.get("pci_link") is not None:  # We have a PCI Link value - We set assignment mode to Custom
                    kwargs_placement["auto_pci_link"] = False
                    kwargs_placement["pci_link_assignment_mode"] = "Custom"
                    kwargs_placement["pci_link"] = vnic["pci_link"]
                elif vnic.get("pci_link_assignment_mode") in ["Load-Balanced"]:  # Assignment mode set to Load-Balanced
                    kwargs_placement["auto_pci_link"] = False
                    kwargs_placement["pci_link_assignment_mode"] = "Load-Balanced"
                else:  # We don't have any PCI Link value - we set Auto PCI Link to enabled
                    kwargs_placement["auto_pci_link"] = True

                if vnic.get("uplink_port") is not None:
                    kwargs_placement["uplink"] = vnic["uplink_port"]
                kwargs["placement"] = VnicPlacementSettings(**kwargs_placement)

                # Handling the CDN settings of the vNIC
                from intersight.model.vnic_cdn import VnicCdn
                kwargs_cdn = {
                    "object_type": "vnic.Cdn",
                    "class_id": "vnic.Cdn"
                }
                if vnic.get("cdn_source") is not None:
                    kwargs_cdn["source"] = vnic["cdn_source"]
                if vnic.get("cdn_value") is not None:
                    kwargs_cdn["value"] = vnic["cdn_value"]
                # We only add the CDN Settings if at least one attribute is set
                if len(kwargs_cdn.keys()) > 2:
                    kwargs["cdn"] = VnicCdn(**kwargs_cdn)

                # Handling the policies attachments of the vNIC
                if vnic.get("ethernet_adapter_policy") is not None:
                    # We need to identify the Ethernet Adapter Policy object reference
                    eth_adapter_policy = self.get_live_object(
                        object_name=vnic["ethernet_adapter_policy"],
                        object_type="vnic.EthAdapterPolicy"
                    )
                    if eth_adapter_policy:
                        kwargs["eth_adapter_policy"] = eth_adapter_policy
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Eth Adapter Policy '{vnic['ethernet_adapter_policy']}' "
                                                 f"to - vNIC - {str(vnic['name'])}",
                            obj_type="vnic.EthIf", status="failed",
                            message=f"Failed to find Eth Adapter Policy '{vnic['ethernet_adapter_policy']}'"
                        )

                if vnic.get("ethernet_network_control_policy") is not None:
                    # We need to identify the Ethernet Network Control Policy object reference
                    eth_nw_ctrl_policy = self.get_live_object(
                        object_name=vnic["ethernet_network_control_policy"],
                        object_type="fabric.EthNetworkControlPolicy"
                    )
                    if eth_nw_ctrl_policy:
                        kwargs["fabric_eth_network_control_policy"] = eth_nw_ctrl_policy
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Eth Network Control Policy "
                                                 f"'{vnic['ethernet_network_control_policy']}' to - vNIC - "
                                                 f"{str(vnic['name'])}",
                            obj_type="vnic.EthIf", status="failed",
                            message=f"Failed to find Eth Network Control Policy "
                                    f"'{vnic['ethernet_network_control_policy']}'"
                        )

                if vnic.get("ethernet_network_group_policies") is not None:
                    # We need to identify the Ethernet Network Group Policies objects references
                    kwargs["fabric_eth_network_group_policy"] = []
                    for engp in vnic["ethernet_network_group_policies"]:
                        eth_nw_grp_policy = self.get_live_object(
                            object_name=engp,
                            object_type="fabric.EthNetworkGroupPolicy"
                        )
                        if eth_nw_grp_policy:
                            kwargs["fabric_eth_network_group_policy"].append(eth_nw_grp_policy)
                        else:
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"Attaching Eth Network Group Policy "
                                                     f"'{engp}' to vNIC '{str(vnic['name'])}'",
                                obj_type="vnic.EthIf", status="failed",
                                message=f"Failed to find Eth Network Group Policy '{engp}'"
                            )
                elif vnic.get("ethernet_network_group_policy") is not None:
                    # We keep this section for compatibility purposes, but "ethernet_network_group_policy" attribute
                    # is deprecated starting with EasyUCS 1.0.2 (replaced by "ethernet_network_group_policies")
                    # We need to identify the Ethernet Network Group Policy object reference
                    eth_nw_grp_policy = self.get_live_object(
                        object_name=vnic["ethernet_network_group_policy"],
                        object_type="fabric.EthNetworkGroupPolicy"
                    )
                    if eth_nw_grp_policy:
                        kwargs["fabric_eth_network_group_policy"] = [eth_nw_grp_policy]
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Eth Network Group Policy "
                                                 f"'{vnic['ethernet_network_group_policy']}' to vNIC - "
                                                 f"{str(vnic['name'])}",
                            obj_type="vnic.EthIf", status="failed",
                            message=f"Failed to find Eth Network Group Policy '{vnic['ethernet_network_group_policy']}'"
                        )

                if vnic.get("ethernet_network_policy") is not None:
                    # We need to identify the Ethernet Network Policy object reference
                    eth_nw_policy = self.get_live_object(
                        object_name=vnic["ethernet_network_policy"],
                        object_type="vnic.EthNetworkPolicy"
                    )
                    if eth_nw_policy:
                        kwargs["eth_network_policy"] = eth_nw_policy
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Eth Network Policy '{vnic['ethernet_network_policy']}' "
                                                 f"to vNIC - {str(vnic['name'])}",
                            obj_type="vnic.EthIf", status="failed",
                            message=f"Failed to find Eth Network Policy '{vnic['ethernet_network_policy']}'"
                        )

                if vnic.get("ethernet_qos_policy") is not None:
                    # We need to identify the Ethernet QoS Policy object reference
                    eth_qos_policy = self.get_live_object(
                        object_name=vnic["ethernet_qos_policy"],
                        object_type="vnic.EthQosPolicy"
                    )
                    if eth_qos_policy:
                        kwargs["eth_qos_policy"] = eth_qos_policy
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Eth QOS Policy '{vnic['ethernet_qos_policy']}' "
                                                 f"to vNIC - {str(vnic['name'])}",
                            obj_type="vnic.EthIf", status="failed",
                            message=f"Failed to find Eth OQS Policy '{vnic['ethernet_qos_policy']}'"
                        )

                if vnic.get("iscsi_boot_policy") is not None:
                    # We need to identify the iSCSI Boot Policy object reference
                    iscsi_boot_policy = self.get_live_object(
                        object_name=vnic["iscsi_boot_policy"],
                        object_type="vnic.IscsiBootPolicy"
                    )
                    if iscsi_boot_policy:
                        kwargs["iscsi_boot_policy"] = iscsi_boot_policy
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching iSCSI Boot Policy '{vnic['iscsi_boot_policy']}' "
                                                 f"to vNIC - {str(vnic['name'])}",
                            obj_type="vnic.EthIf", status="failed",
                            message=f"Failed to find iSCSI Boot Policy '{vnic['iscsi_boot_policy']}'"
                        )

                # Handling the usNIC Settings of the vNIC
                if vnic.get("usnic_settings") is not None:
                    from intersight.model.vnic_usnic_settings import VnicUsnicSettings
                    kwargs_usnic = {
                        "object_type": "vnic.UsnicSettings",
                        "class_id": "vnic.UsnicSettings"
                    }
                    if vnic["usnic_settings"].get("number_of_usnics") is not None:
                        kwargs_usnic["count"] = vnic["usnic_settings"]["number_of_usnics"]
                    if vnic["usnic_settings"].get("class_of_service") is not None:
                        kwargs_usnic["cos"] = vnic["usnic_settings"]["class_of_service"]
                    if vnic["usnic_settings"].get("usnic_adapter_policy") is not None:
                        eth_adapter_policy = self.get_live_object(
                            object_name=vnic["usnic_settings"].get("usnic_adapter_policy"),
                            object_type="vnic.EthAdapterPolicy"
                        )
                        if eth_adapter_policy:
                            kwargs_usnic["usnic_adapter_policy"] = eth_adapter_policy.moid
                        else:
                            self._config.push_summary_manager.add_object_status(
                                obj=self,
                                obj_detail=f"Attaching Eth Adapter Policy "
                                           f"'{vnic['usnic_settings']['usnic_adapter_policy']}' "
                                           f"to - vNIC - {str(vnic['name'])} - usNIC Settings",
                                obj_type="vnic.EthIf", status="failed",
                                message=f"Failed to find Eth Adapter Policy "
                                        f"'{vnic['usnic_settings']['usnic_adapter_policy']}'"
                            )
                    kwargs["usnic_settings"] = VnicUsnicSettings(
                        **kwargs_usnic)

                # Handling the VMQ Settings of the vNIC
                if vnic.get("vmq_settings") is not None:
                    from intersight.model.vnic_vmq_settings import VnicVmqSettings
                    kwargs_vmq = {
                        "object_type": "vnic.VmqSettings",
                        "class_id": "vnic.VmqSettings",
                        "enabled": True
                    }
                    if vnic["vmq_settings"].get("enable_virtual_machine_multi_queue") is not None:
                        kwargs_vmq["multi_queue_support"] = vnic["vmq_settings"]["enable_virtual_machine_multi_queue"]
                    if vnic["vmq_settings"].get("number_of_sub_vnics") is not None:
                        kwargs_vmq["num_sub_vnics"] = vnic["vmq_settings"]["number_of_sub_vnics"]
                    if vnic["vmq_settings"].get("vmmq_adapter_policy") is not None:
                        eth_adapter_policy = self.get_live_object(
                            object_name=vnic["vmq_settings"].get("vmmq_adapter_policy"),
                            object_type="vnic.EthAdapterPolicy"
                        )
                        if eth_adapter_policy:
                            kwargs_vmq["vmmq_adapter_policy"] = eth_adapter_policy.moid
                        else:
                            self._config.push_summary_manager.add_object_status(
                                obj=self,
                                obj_detail=f"Attaching Eth Adapter Policy "
                                           f"'{vnic['vmq_settings']['vmmq_adapter_policy']}' "
                                           f"to - vNIC - {str(vnic['name'])} - VMQ Settings",
                                obj_type="vnic.EthIf", status="failed",
                                message=f"Failed to find Eth Adapter Policy "
                                        f"'{vnic['vmq_settings']['vmmq_adapter_policy']}'"
                            )
                    if vnic["vmq_settings"].get("number_of_interrupts") is not None:
                        kwargs_vmq["num_interrupts"] = vnic["vmq_settings"]["number_of_interrupts"]
                    if vnic["vmq_settings"].get("number_of_virtual_machine_queues") is not None:
                        kwargs_vmq["num_vmqs"] = vnic["vmq_settings"]["number_of_virtual_machine_queues"]
                    kwargs["vmq_settings"] = VnicVmqSettings(**kwargs_vmq)

                # Handling the SRIOV Settings of the vNIC
                if vnic.get("sriov_settings") is not None:
                    from intersight.model.vnic_sriov_settings import VnicSriovSettings
                    kwargs_sriov = {
                        "object_type": "vnic.SriovSettings",
                        "class_id": "vnic.SriovSettings",
                        "enabled": True
                    }
                    if vnic["sriov_settings"].get("number_of_vfs") is not None:
                        kwargs_sriov["vf_count"] = vnic["sriov_settings"]["number_of_vfs"]
                    if vnic["sriov_settings"].get("receive_queue_count_per_vf") is not None:
                        kwargs_sriov["rx_count_per_vf"] = vnic["sriov_settings"]["receive_queue_count_per_vf"]
                    if vnic["sriov_settings"].get("transmit_queue_count_per_vf") is not None:
                        kwargs_sriov["tx_count_per_vf"] = vnic["sriov_settings"]["transmit_queue_count_per_vf"]
                    if vnic["sriov_settings"].get("completion_queue_count_per_vf") is not None:
                        kwargs_sriov["comp_count_per_vf"] = vnic["sriov_settings"]["completion_queue_count_per_vf"]
                    if vnic["sriov_settings"].get("interrupt_count_per_vf") is not None:
                        kwargs_sriov["int_count_per_vf"] = vnic["sriov_settings"]["interrupt_count_per_vf"]
                    kwargs["sriov_settings"] = VnicSriovSettings(**kwargs_sriov)

                vnic_payload = VnicEthIf(**kwargs)

                self.commit(object_type="vnic.EthIf", payload=vnic_payload,
                            detail=self.name + " - vNIC " + str(vnic["name"]),
                            key_attributes=["name", "lan_connectivity_policy"])

        return True


class IntersightLdapPolicy(IntersightConfigObject):
    _CONFIG_NAME = "LDAP Policy"
    _CONFIG_SECTION_NAME = "ldap_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "iam.LdapPolicy"

    def __init__(self, parent=None, ldap_policy=None, appliance_management_ldap=False):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=ldap_policy)

        self.base_properties = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.dns_parameters = None
        self.enable_ldap = None
        self.enable_dns = None
        self.groups = None
        self.name = self.get_attribute(attribute_name="name")
        self.providers = None
        self.user_search_precedence = None

        if self._config.load_from == "live":
            if hasattr(self._object, "enabled"):
                self.enable_ldap = getattr(self._object, 'enabled')
                if getattr(self._object, "enabled") is True:
                    base_properties = {}
                    if hasattr(self._object, "base_properties"):
                        ldap_base_properties = getattr(self._object, "base_properties")
                        if hasattr(ldap_base_properties, "base_dn") and getattr(ldap_base_properties, "base_dn"):
                            base_properties["base_dn"] = getattr(ldap_base_properties, "base_dn")
                        if hasattr(ldap_base_properties, "domain") and getattr(ldap_base_properties, "domain")\
                                and not appliance_management_ldap:
                            base_properties["domain"] = getattr(ldap_base_properties, "domain")
                        if hasattr(ldap_base_properties, "enable_nested_group_search"):
                            base_properties[
                                "enable_nested_group_search"] = ldap_base_properties.enable_nested_group_search
                        if hasattr(ldap_base_properties, "timeout") and getattr(ldap_base_properties, "timeout")\
                                and not appliance_management_ldap:
                            base_properties["timeout"] = getattr(ldap_base_properties, "timeout")
                        if hasattr(ldap_base_properties, "enable_encryption"):
                            base_properties["enable_encryption"] = getattr(ldap_base_properties, "enable_encryption")
                        if hasattr(ldap_base_properties, "bind_method") and \
                                getattr(ldap_base_properties, "bind_method"):
                            base_properties["bind_method"] = getattr(ldap_base_properties, "bind_method")
                            if getattr(ldap_base_properties, "bind_method") == "ConfiguredCredentials":
                                if hasattr(ldap_base_properties, "bind_dn") and \
                                        getattr(ldap_base_properties, "bind_dn"):
                                    base_properties["bind_dn"] = getattr(ldap_base_properties, "bind_dn")
                                if hasattr(ldap_base_properties, "is_password_set"):
                                    if getattr(ldap_base_properties, "is_password_set") is True:
                                        self.logger(level="warning",
                                                    message="Password of " + self._CONFIG_NAME + " '" + self.name +
                                                            "' - Bind DN can't be exported")
                        if hasattr(ldap_base_properties, "filter") and getattr(ldap_base_properties, "filter")\
                                and not appliance_management_ldap:
                            base_properties["filter"] = getattr(ldap_base_properties, "filter")
                        if hasattr(ldap_base_properties, "group_attribute") and \
                                getattr(ldap_base_properties, "group_attribute"):
                            base_properties["group_attribute"] = getattr(ldap_base_properties, "group_attribute")
                        if hasattr(ldap_base_properties, "attribute") and getattr(ldap_base_properties, "attribute")\
                                and not appliance_management_ldap:
                            base_properties["attribute"] = getattr(ldap_base_properties, "attribute")
                        if hasattr(ldap_base_properties, "enable_group_authorization") and not appliance_management_ldap:
                            base_properties["enable_group_authorization"] = getattr(ldap_base_properties,
                                                                                    "enable_group_authorization")
                        if (hasattr(ldap_base_properties, "nested_group_search_depth") and \
                                getattr(ldap_base_properties, "nested_group_search_depth") and
                                not appliance_management_ldap):
                            base_properties["nested_group_search_depth"] = getattr(ldap_base_properties,
                                                                                   "nested_group_search_depth")
                    self.base_properties = base_properties
                    if hasattr(self._object, "enable_dns"):
                        if not appliance_management_ldap:
                            self.enable_dns = getattr(self._object, "enable_dns")
                        if getattr(self._object, "enable_dns") is True:
                            dns_parameters = {}
                            if hasattr(self._object, "dns_parameters"):
                                ldap_dns_parameters = getattr(self._object, "dns_parameters")
                                if hasattr(ldap_dns_parameters, "source"):
                                    if getattr(ldap_dns_parameters, "source") in ["Configured", "ConfiguredExtracted"]:
                                        dns_parameters["source"] = getattr(ldap_dns_parameters, "source")
                                        if hasattr(ldap_dns_parameters, "search_domain"):
                                            dns_parameters["search_domain"] = getattr(ldap_dns_parameters,
                                                                                      "search_domain")
                                        if hasattr(ldap_dns_parameters, "search_forest"):
                                            dns_parameters["search_forest"] = getattr(ldap_dns_parameters,
                                                                                      "search_forest")
                                    else:
                                        dns_parameters["source"] = getattr(ldap_dns_parameters, "source")
                            self.dns_parameters = dns_parameters
                        else:
                            if hasattr(self._object, "providers"):
                                self.providers = (
                                    self._get_ldap_providers(appliance_management_ldap=appliance_management_ldap))

                    if hasattr(self._object, "user_search_precedence") and \
                            getattr(self._object, "user_search_precedence") and not appliance_management_ldap:
                        self.user_search_precedence = getattr(self._object, "user_search_precedence")
                    if hasattr(self._object, "groups") and not appliance_management_ldap:
                        self.groups = self._get_ldap_groups()

        elif self._config.load_from == "file":
            for attribute in ["base_properties", "dns_parameters", "enable_dns",
                              "enable_ldap", "groups", "providers", "user_search_precedence"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        if self.tags:
            for tag in self.tags:
                for attribute in ["key", "value"]:
                    if attribute not in tag:
                        tag[attribute] = None

        if self.base_properties:
            for attribute in [
                "attribute", "base_dn", "bind_dn", "bind_method", "bind_password", "domain",
                "enable_encryption", "enable_group_authorization", "enable_nested_group_search", "filter",
                "group_attribute", "nested_group_search_depth", "timeout"
            ]:
                if attribute not in self.base_properties:
                    self.base_properties[attribute] = None

        if self.dns_parameters:
            for attribute in ["search_domain", "search_forest", "source"]:
                if attribute not in self.dns_parameters:
                    self.dns_parameters[attribute] = None

        if self.groups:
            for group in self.groups:
                for attribute in ["domain", "name", "group_dn", "role"]:
                    if attribute not in group:
                        group[attribute] = None

        if self.providers:
            for provider in self.providers:
                for attribute in ["ldap_server", "ldap_server_port", "vendor"]:
                    if attribute not in provider:
                        provider[attribute] = None


    def _get_ldap_groups(self):
        # Fetches the LDAP groups of LDAP policy
        if "iam_ldap_group" in self._config.sdk_objects:
            groups = []
            for ldap_group in self._config.sdk_objects["iam_ldap_group"]:
                if ldap_group.ldap_policy:
                    if ldap_group.ldap_policy.moid == self._moid:
                        role = None
                        # We first need to find the iam.EndPointRole object with the same name and same type.
                        if hasattr(ldap_group, "end_point_role"):
                            iam_end_point_role = self.get_config_objects_from_ref(ref=ldap_group.end_point_role)
                            if iam_end_point_role:
                                role = iam_end_point_role[0].name
                        group = {
                            "name": ldap_group.name,
                            "domain": ldap_group.domain,
                            "group_dn": ldap_group.group_dn,
                            "role": role
                        }
                        groups.append(group)

            return groups

        return None

    def _get_ldap_providers(self, appliance_management_ldap=False):
        # Fetches the ldap providers of LDAP policy when enable dns is disabled
        if "iam_ldap_provider" in self._config.sdk_objects:
            ldap_providers = []
            for ldap_provider in self._config.sdk_objects["iam_ldap_provider"]:
                if ldap_provider.ldap_policy:
                    if ldap_provider.ldap_policy.moid == self._moid:
                        provider = {
                            "ldap_server": ldap_provider.server,
                            "ldap_server_port": ldap_provider.port
                        }
                        if not appliance_management_ldap:
                            provider["vendor"] = ldap_provider.vendor
                        ldap_providers.append(provider)

            return ldap_providers
        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self, appliance_management_ldap=False):
        from intersight.model.iam_ldap_policy import IamLdapPolicy

        if appliance_management_ldap:
            self.logger(message=f"Pushing LDAP/AD settings: {self.name}")
        else:
            self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME
        }

        if not appliance_management_ldap:
            kwargs["organization"] = self.get_parent_org_relationship()
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enable_ldap is not None:
            if self.enable_ldap is True:
                kwargs["enabled"] = self.enable_ldap
                if self.base_properties is not None:
                    from intersight.model.iam_ldap_base_properties import IamLdapBaseProperties

                    ldap_base_settings = self.base_properties
                    base_properties_kwargs = {
                        "object_type": "iam.LdapBaseProperties",
                        "class_id": "iam.LdapBaseProperties"
                    }
                    if ldap_base_settings["base_dn"] is not None:
                        base_properties_kwargs["base_dn"] = ldap_base_settings["base_dn"]
                    if ldap_base_settings["domain"] is not None:
                        base_properties_kwargs["domain"] = ldap_base_settings["domain"]
                    if ldap_base_settings["timeout"] is not None:
                        base_properties_kwargs["timeout"] = ldap_base_settings["timeout"]
                    if ldap_base_settings["enable_encryption"] is not None:
                        base_properties_kwargs["enable_encryption"] = ldap_base_settings["enable_encryption"]
                    if ldap_base_settings["bind_method"] is not None:
                        base_properties_kwargs["bind_method"] = ldap_base_settings["bind_method"]
                        if ldap_base_settings["bind_method"] == "ConfiguredCredentials":
                            if ldap_base_settings["bind_dn"] is not None:
                                base_properties_kwargs["bind_dn"] = ldap_base_settings["bind_dn"]
                            if ldap_base_settings.get("bind_password") is not None:
                                base_properties_kwargs["password"] = ldap_base_settings["bind_password"]
                            else:
                                self.logger(
                                    level="warning",
                                    message="No password provided for field 'password' of object iam.LdapBaseProperties"
                                )
                    if ldap_base_settings["filter"] is not None:
                        base_properties_kwargs["filter"] = ldap_base_settings["filter"]
                    if ldap_base_settings["group_attribute"] is not None:
                        base_properties_kwargs["group_attribute"] = ldap_base_settings["group_attribute"]
                    if ldap_base_settings["attribute"] is not None:
                        base_properties_kwargs["attribute"] = ldap_base_settings["attribute"]
                    if ldap_base_settings["enable_group_authorization"] is not None:
                        base_properties_kwargs["enable_group_authorization"] = \
                            ldap_base_settings["enable_group_authorization"]
                    if ldap_base_settings["enable_nested_group_search"] is not None:
                        base_properties_kwargs["enable_nested_group_search"] = ldap_base_settings[
                            "enable_nested_group_search"]
                    if ldap_base_settings["nested_group_search_depth"] is not None:
                        base_properties_kwargs["nested_group_search_depth"] = \
                            ldap_base_settings["nested_group_search_depth"]

                    kwargs["base_properties"] = IamLdapBaseProperties(**base_properties_kwargs)
                if self.enable_dns is not None:
                    kwargs["enable_dns"] = self.enable_dns
                if self.dns_parameters is not None:
                    from intersight.model.iam_ldap_dns_parameters import IamLdapDnsParameters

                    ldap_dns_parameters = self.dns_parameters
                    dns_parameters_kwargs = {
                        "object_type": "iam.LdapDnsParameters",
                        "class_id": "iam.LdapDnsParameters"
                    }
                    if ldap_dns_parameters["source"] is not None:
                        if ldap_dns_parameters["source"] in ["ConfiguredExtracted", "Configured"]:
                            dns_parameters_kwargs["source"] = ldap_dns_parameters["source"]
                            if ldap_dns_parameters["search_domain"] is not None:
                                dns_parameters_kwargs["search_domain"] = ldap_dns_parameters["search_domain"]
                            if ldap_dns_parameters["search_forest"] is not None:
                                dns_parameters_kwargs["search_forest"] = ldap_dns_parameters["search_forest"]
                        else:
                            dns_parameters_kwargs["source"] = ldap_dns_parameters["source"]
                    kwargs["dns_parameters"] = IamLdapDnsParameters(**dns_parameters_kwargs)

                if self.user_search_precedence is not None:
                    kwargs["user_search_precedence"] = self.user_search_precedence
                iam_ldap_policy = IamLdapPolicy(**kwargs)

                iamlp = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=iam_ldap_policy,
                                    detail=self.name, return_relationship=True)
                if not iamlp:
                    return False

                if self.groups is not None:
                    from intersight.model.iam_ldap_group import IamLdapGroup

                    for ldap_group in self.groups:
                        ldap_group_kwargs = {
                            "object_type": "iam.LdapGroup",
                            "class_id": "iam.LdapGroup",
                            "ldap_policy": iamlp
                        }
                        if ldap_group["name"] is not None:
                            ldap_group_kwargs["name"] = ldap_group["name"]
                        if ldap_group["domain"] is not None:
                            ldap_group_kwargs["domain"] = ldap_group["domain"]
                        if ldap_group["group_dn"] is not None:
                            ldap_group_kwargs["group_dn"] = ldap_group["group_dn"]
                        if ldap_group["role"] is not None:
                            end_point_role = self._device.query(
                                object_type="iam.EndPointRole",
                                filter="(Name eq '" + ldap_group["role"] + "') and (Type eq 'IMC')"
                            )
                            if len(end_point_role) == 1:
                                ldap_group_kwargs["end_point_role"] = \
                                    [self.create_relationship_equivalent(sdk_object=end_point_role[0])]
                            else:
                                err_message = f"Could not find unique iam.EndPointRole with name " \
                                              f"{ldap_group['role']}. Skipping LDAP Group {ldap_group['role']}."
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"LDAP Group - '{ldap_group.get('name')}'",
                                    obj_type="iam.LdapGroup", status="failed", message=err_message
                                )
                                continue

                        ldap_groups = (IamLdapGroup(**ldap_group_kwargs))

                        self.commit(object_type="iam.LdapGroup", payload=ldap_groups,
                                    detail="LDAP Group - '" + ldap_group.get("name") + "'",
                                    key_attributes=["name", "ldap_policy"])
                if self.providers is not None:

                    from intersight.model.iam_ldap_provider import IamLdapProvider

                    for ldap_provider in self.providers:
                        ldap_provider_kwargs = {
                            "object_type": "iam.LdapProvider",
                            "class_id": "iam.LdapProvider",
                            "ldap_policy": iamlp
                        }
                        if ldap_provider["ldap_server"] is not None:
                            ldap_provider_kwargs["server"] = ldap_provider["ldap_server"]
                        if ldap_provider["ldap_server_port"] is not None:
                            ldap_provider_kwargs["port"] = ldap_provider["ldap_server_port"]
                        if ldap_provider.get("vendor") is not None:
                            ldap_provider_kwargs["vendor"] = ldap_provider["vendor"]

                        ldap_providers = (IamLdapProvider(**ldap_provider_kwargs))

                        self.commit(object_type="iam.LdapProvider", payload=ldap_providers,
                                    detail="LDAP Server - '" + ldap_provider.get("ldap_server") + "'",
                                    key_attributes=["server", "ldap_policy", "port"])
            else:
                kwargs["enabled"] = False
                iam_ldap_policy = IamLdapPolicy(**kwargs)

                if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=iam_ldap_policy,
                                   detail=self.name, return_relationship=True):
                    return False

        return True


class IntersightLocalUserPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Local User Policy"
    _CONFIG_SECTION_NAME = "local_user_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "iam.EndPointUserPolicy"

    def __init__(self, parent=None, local_user_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=local_user_policy)

        self.always_send_user_password = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enforce_strong_password = None
        self.enable_password_expiry = None
        self.grace_period = None
        self.local_users = None
        self.name = self.get_attribute(attribute_name="name")
        self.notification_period = None
        self.password_expiry_duration = None
        self.password_history = None

        if self._config.load_from == "live":
            if hasattr(self._object, "password_properties"):
                if self._object.password_properties:
                    self.always_send_user_password = self._object.password_properties.force_send_password
                    self.enforce_strong_password = self._object.password_properties.enforce_strong_password
                    self.enable_password_expiry = self._object.password_properties.enable_password_expiry
                    self.grace_period = self._object.password_properties.grace_period
                    self.notification_period = self._object.password_properties.notification_period
                    self.password_expiry_duration = self._object.password_properties.password_expiry_duration
                    self.password_history = self._object.password_properties.password_history

            if hasattr(self._object, "end_point_user_roles"):
                if self._object.end_point_user_roles:
                    self.local_users = self._get_local_users()

        elif self._config.load_from == "file":
            for attribute in ["always_send_user_password", "enforce_strong_password", "enable_password_expiry",
                              "grace_period", "local_users", "notification_period", "password_expiry_duration",
                              "password_history"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of Local Users are set to None if they are not present
        if self.local_users:
            for local_user in self.local_users:
                for attribute in ["enable", "password", "role", "username"]:
                    if attribute not in local_user:
                        local_user[attribute] = None

    def _get_local_users(self):
        # Fetches the Local Users' configuration of a Local User Policy
        if "iam_end_point_user_role" in self._config.sdk_objects:
            local_users = []
            for iam_end_point_user_role in self._config.sdk_objects["iam_end_point_user_role"]:
                if hasattr(iam_end_point_user_role, "end_point_user_policy"):
                    if iam_end_point_user_role.end_point_user_policy.moid == self._moid:
                        end_point_user = self.get_config_objects_from_ref(ref=iam_end_point_user_role.end_point_user)
                        end_point_role = self.get_config_objects_from_ref(ref=iam_end_point_user_role.end_point_role)
                        username = None
                        if end_point_user:
                            username = end_point_user[0].name
                        role = None
                        if end_point_role:
                            role = end_point_role[0].name
                        if iam_end_point_user_role.is_password_set:
                            self.logger(level="warning",
                                        message="Password of " + self._CONFIG_NAME + " '" + self.name +
                                                "' - Local User '" + str(username) + "' can't be exported")
                        local_users.append({"username": username, "role": role,
                                            "enable": iam_end_point_user_role.enabled})

            return local_users

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.iam_end_point_user_policy import IamEndPointUserPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        from intersight.model.iam_end_point_password_properties import IamEndPointPasswordProperties
        password_properties_kwargs = {
            "object_type": "iam.EndPointPasswordProperties",
            "class_id": "iam.EndPointPasswordProperties"
        }
        if self.always_send_user_password is not None:
            password_properties_kwargs["force_send_password"] = self.always_send_user_password
        if self.enforce_strong_password is not None:
            password_properties_kwargs["enforce_strong_password"] = self.enforce_strong_password
        if self.enable_password_expiry is not None:
            password_properties_kwargs["enable_password_expiry"] = self.enable_password_expiry
        if self.grace_period is not None:
            password_properties_kwargs["grace_period"] = self.grace_period
        if self.notification_period is not None:
            password_properties_kwargs["notification_period"] = self.notification_period
        if self.password_expiry_duration is not None:
            password_properties_kwargs["password_expiry_duration"] = self.password_expiry_duration
        if self.password_history is not None:
            password_properties_kwargs["password_history"] = self.password_history
        kwargs["password_properties"] = IamEndPointPasswordProperties(**password_properties_kwargs)

        iam_end_point_user_policy = IamEndPointUserPolicy(**kwargs)

        iepup = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=iam_end_point_user_policy,
                            detail=self.name, return_relationship=True)
        if not iepup:
            return False

        if self.local_users:
            from intersight.model.iam_end_point_user_role import IamEndPointUserRole
            from intersight.model.iam_end_point_user import IamEndPointUser

            for local_user in self.local_users:
                end_point_user_role_kwargs = {
                    "object_type": "iam.EndPointUserRole",
                    "class_id": "iam.EndPointUserRole",
                    "end_point_user_policy": iepup
                }
                if local_user.get("enable") is not None:
                    end_point_user_role_kwargs["enabled"] = local_user.get("enable")
                if local_user.get("password") is not None:
                    end_point_user_role_kwargs["password"] = local_user.get("password")
                else:
                    self.logger(
                        level="warning",
                        message="No password provided for field 'password' of object iam.EndPointUserRole"
                    )

                if local_user.get("username") is not None:
                    # We first need to check if an iam.EndPointUser object with the same name already exists
                    end_point_user = self._device.query(
                        object_type="iam.EndPointUser",
                        filter="(Name eq '" + local_user.get("username") + "') and (PermissionResources.Moid eq '" +
                               kwargs["organization"].moid + "')"
                    )
                    if len(end_point_user) == 1:
                        self.logger(
                            level="debug",
                            message="iam.EndPointUser object with name '" + local_user.get("username", "") +
                                    "' already exists, referencing it in the iam.EndPointUserRole object"
                        )
                        end_point_user_role_kwargs["end_point_user"] = \
                            self.create_relationship_equivalent(sdk_object=end_point_user[0])
                    elif len(end_point_user) > 1:
                        self.logger(
                            level="error",
                            message="Could not find unique iam.EndPointUser with name " + local_user.get("username")
                        )
                        return False
                    else:
                        # We create the required iam.EndPointUser object
                        end_point_user_kwargs = {
                            "object_type": "iam.EndPointUser",
                            "class_id": "iam.EndPointUser",
                            "name": local_user.get("username"),
                            "organization": self.get_parent_org_relationship()
                        }
                        iam_end_point_user = IamEndPointUser(**end_point_user_kwargs)

                        iepu = self.commit(object_type="iam.EndPointUser",
                                           payload=iam_end_point_user,
                                           detail="User '" + local_user.get("username") + "'",
                                           return_relationship=True)
                        if iepu:
                            end_point_user_role_kwargs["end_point_user"] = iepu

                if local_user.get("role") is not None:
                    # We first need to find the iam.EndPointRole object with the same name
                    end_point_role = self._device.query(
                        object_type="iam.EndPointRole",
                        filter="(Name eq '" + local_user.get("role") + "') and (Type eq 'IMC')"
                    )
                    if len(end_point_role) == 1:
                        end_point_user_role_kwargs["end_point_role"] = \
                            [self.create_relationship_equivalent(sdk_object=end_point_role[0])]
                    else:
                        err_message = "Could not find unique iam.EndPointRole with name " + local_user.get("role")
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"User '{local_user.get('username', '')}' with role "
                                                 f"'{local_user.get('role', '')}'",
                            obj_type="iam.EndPointUserRole", status="failed", message=err_message
                        )
                        return False

                iam_end_point_user_role = IamEndPointUserRole(**end_point_user_role_kwargs)

                self.commit(object_type="iam.EndPointUserRole", payload=iam_end_point_user_role,
                            detail="User '" + str(local_user.get("username", "")) + "' with role '" +
                                   str(local_user.get("role", "")) + "'")

        return True


class IntersightNetworkConnectivityPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Network Connectivity Policy"
    _CONFIG_SECTION_NAME = "network_connectivity_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "networkconfig.Policy"

    def __init__(self, parent=None, networkconfig_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=networkconfig_policy)

        self.alternate_ipv4_dns_server = None
        self.alternate_ipv6_dns_server = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.dynamic_dns_domain = None
        self.enable_dynamic_dns = self.get_attribute(attribute_name="enable_dynamic_dns")
        self.enable_ipv6 = self.get_attribute(attribute_name="enable_ipv6")
        self.name = self.get_attribute(attribute_name="name")
        self.obtain_ipv4_dns_from_dhcp = self.get_attribute(attribute_name="enable_ipv4dns_from_dhcp",
                                                            attribute_secondary_name="obtain_ipv4_dns_from_dhcp")
        self.obtain_ipv6_dns_from_dhcp = None
        self.preferred_ipv4_dns_server = None
        self.preferred_ipv6_dns_server = None

        if self.enable_dynamic_dns:
            self.dynamic_dns_domain = self.get_attribute(attribute_name="dynamic_dns_domain")

        if not self.obtain_ipv4_dns_from_dhcp:
            self.preferred_ipv4_dns_server = self.get_attribute(attribute_name="preferred_ipv4dns_server",
                                                                attribute_secondary_name="preferred_ipv4_dns_server")
            self.alternate_ipv4_dns_server = self.get_attribute(attribute_name="alternate_ipv4dns_server",
                                                                attribute_secondary_name="alternate_ipv4_dns_server")

        if self.enable_ipv6:
            self.obtain_ipv6_dns_from_dhcp = self.get_attribute(attribute_name="enable_ipv6dns_from_dhcp",
                                                                attribute_secondary_name="obtain_ipv6_dns_from_dhcp")
            if not self.obtain_ipv6_dns_from_dhcp:
                self.preferred_ipv6_dns_server = \
                    self.get_attribute(attribute_name="preferred_ipv6dns_server",
                                       attribute_secondary_name="preferred_ipv6_dns_server")
                self.alternate_ipv6_dns_server = \
                    self.get_attribute(attribute_name="alternate_ipv6dns_server",
                                       attribute_secondary_name="alternate_ipv6_dns_server")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.networkconfig_policy import NetworkconfigPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enable_dynamic_dns is not None:
            kwargs["enable_dynamic_dns"] = self.enable_dynamic_dns
        if self.dynamic_dns_domain is not None:
            kwargs["dynamic_dns_domain"] = self.dynamic_dns_domain
        if self.obtain_ipv4_dns_from_dhcp is not None:
            kwargs["enable_ipv4dns_from_dhcp"] = self.obtain_ipv4_dns_from_dhcp
        if self.preferred_ipv4_dns_server is not None:
            kwargs["preferred_ipv4dns_server"] = self.preferred_ipv4_dns_server
        if self.alternate_ipv4_dns_server is not None:
            kwargs["alternate_ipv4dns_server"] = self.alternate_ipv4_dns_server
        if self.enable_ipv6 is not None:
            kwargs["enable_ipv6"] = self.enable_ipv6
        if self.obtain_ipv6_dns_from_dhcp is not None:
            kwargs["enable_ipv6dns_from_dhcp"] = self.obtain_ipv6_dns_from_dhcp
        if self.preferred_ipv6_dns_server is not None:
            kwargs["preferred_ipv6dns_server"] = self.preferred_ipv6_dns_server
        if self.alternate_ipv6_dns_server is not None:
            kwargs["alternate_ipv6dns_server"] = self.alternate_ipv6_dns_server

        networkconfig_policy = NetworkconfigPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=networkconfig_policy,
                           detail=self.name):
            return False

        return True


class IntersightNtpPolicy(IntersightConfigObject):
    _CONFIG_NAME = "NTP Policy"
    _CONFIG_SECTION_NAME = "ntp_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "ntp.Policy"

    def __init__(self, parent=None, ntp_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=ntp_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enabled = self.get_attribute(attribute_name="enabled")
        self.name = self.get_attribute(attribute_name="name")
        self.ntp_servers = self.get_attribute(attribute_name="ntp_servers")
        self.timezone = self.get_attribute(attribute_name="timezone")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.ntp_policy import NtpPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enabled is not None:
            kwargs["enabled"] = self.enabled
        if self.ntp_servers is not None:
            kwargs["ntp_servers"] = self.ntp_servers
        if self.timezone is not None:
            kwargs["timezone"] = self.timezone

        ntp_policy = NtpPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=ntp_policy, detail=self.name):
            return False

        return True


class IntersightPersistentMemoryPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Persistent Memory Policy"
    _CONFIG_SECTION_NAME = "persistent_memory_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "memory.PersistentMemoryPolicy"

    def __init__(self, parent=None, memory_persistent_memory_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=memory_persistent_memory_policy)

        self.name = self.get_attribute(attribute_name="name")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_goal = None
        self.management_mode = None
        self.enable_security_passphrase = None
        self.goals = None
        self.local_security = None
        self.logical_namespaces = None
        self.memory_mode = None
        self.retain_namespaces = None

        if self._config.load_from == "live":
            if hasattr(self._object, "management_mode"):
                if self._object.management_mode in ["configured-from-operating-system"]:
                    self.management_mode = "configured-from-operating-system"
                else:
                    self.management_mode = "configured-from-intersight"
                    if hasattr(self._object, "local_security"):
                        if self._object.local_security is not None:
                            sps = getattr(self._object, "local_security")
                            local_security = {}
                            if hasattr(sps, "enabled"):
                                local_security["enable_security_passphrase"] = getattr(sps, "enabled")
                            if sps.is_secure_passphrase_set:
                                self.logger(level="warning",
                                            message="Secure passphrase of " + self._CONFIG_NAME + " '" + self.name +
                                                    "' can't be exported ")
                            self.local_security = local_security

                    if hasattr(self._object, "retain_namespaces"):
                        self.retain_namespaces = getattr(self._object, "retain_namespaces")
                    if hasattr(self._object, "goals"):
                        if self._object.goals is not None:
                            goals = {}
                            for goal in self._object.goals:
                                if hasattr(goal, "memory_mode_percentage"):
                                    goals["memory_mode_percentage"] = goal.memory_mode_percentage
                                    goals["enable_goal"] = True
                                if hasattr(goal, "persistent_memory_type"):
                                    goals["persistent_memory_type"] = goal.persistent_memory_type
                            self.goals = goals

                    if hasattr(self._object, "logical_namespaces"):
                        if self._object.logical_namespaces is not None:
                            namespace_list = []
                            for logical_namespace in self._object.logical_namespaces:
                                namespace_list.append({"capacity": logical_namespace.capacity,
                                                       "mode": logical_namespace.mode,
                                                       "name": logical_namespace.name,
                                                       "socket_id": logical_namespace.socket_id,
                                                       "socket_memory_id": logical_namespace.socket_memory_id})
                            self.logical_namespaces = namespace_list

        elif self._config.load_from == "file":
            for attribute in ["goals", "local_security", "logical_namespaces", "management_mode"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.memory_persistent_memory_policy import MemoryPersistentMemoryPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.management_mode is not None:
            management_mode = self.management_mode

            if management_mode == "configured-from-intersight":
                management_mode = "configured-from-intersight"
            else:
                management_mode = "configured-from-operating-system"
            kwargs["management_mode"] = management_mode
        if self.retain_namespaces is not None:
            kwargs["retain_namespaces"] = self.retain_namespaces
        if self.local_security is not None:
            local_security = self.local_security
            from intersight.model.memory_persistent_memory_local_security import MemoryPersistentMemoryLocalSecurity

            persistent_memory_local_security_kwargs = {
                "object_type": "memory.PersistentMemoryLocalSecurity",
                "class_id": "memory.PersistentMemoryLocalSecurity"
            }
            if local_security["enable_security_passphrase"] is not None:
                persistent_memory_local_security_kwargs["enabled"] = local_security["enable_security_passphrase"]
                if local_security.get("secure_passphrase") is not None:
                    persistent_memory_local_security_kwargs["secure_passphrase"] = local_security["secure_passphrase"]
                else:
                    self.logger(
                        level="warning",
                        message="No password provided for field 'secure_passphrase' of object " +
                                "memory.PersistentMemoryLocalSecurity"
                    )
            kwargs["local_security"] = MemoryPersistentMemoryLocalSecurity(**persistent_memory_local_security_kwargs)
        if self.goals is not None:
            from intersight.model.memory_persistent_memory_goal import MemoryPersistentMemoryGoal

            goal_settings = []
            g_kwargs = {
                "object_type": "memory.PersistentMemoryGoal",
                "class_id": "memory.PersistentMemoryGoal",
            }
            if self.goals.get("memory_mode_percentage") is not None:
                g_kwargs["memory_mode_percentage"] = self.goals["memory_mode_percentage"]
            if self.goals.get("persistent_memory_type") is not None:
                g_kwargs["persistent_memory_type"] = self.goals["persistent_memory_type"]

            goal_settings.append(MemoryPersistentMemoryGoal(**g_kwargs))
            kwargs["goals"] = goal_settings

        if self.logical_namespaces is not None:
            from intersight.model.memory_persistent_memory_logical_namespace import \
                MemoryPersistentMemoryLogicalNamespace
            name_spaces = []
            for name_space in self.logical_namespaces:
                name_space_kwargs = {
                    "object_type": "memory.PersistentMemoryLogicalNamespace",
                    "class_id": "memory.PersistentMemoryLogicalNamespace",
                }
                if name_space.get("name"):
                    name_space_kwargs["name"] = name_space["name"]
                if name_space.get("socket_id"):
                    name_space_kwargs["socket_id"] = name_space["socket_id"]
                if name_space.get("socket_memory_id"):
                    name_space_kwargs["socket_memory_id"] = name_space["socket_memory_id"]
                if name_space.get("capacity"):
                    name_space_kwargs["capacity"] = name_space["capacity"]
                if name_space.get("mode"):
                    name_space_kwargs["mode"] = name_space["mode"]

                name_spaces.append(MemoryPersistentMemoryLogicalNamespace(**name_space_kwargs))

            kwargs["logical_namespaces"] = name_spaces

        persistent_memory_policy = MemoryPersistentMemoryPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=persistent_memory_policy,
                           detail=self.name):
            return False

        return True


class IntersightPowerPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Power Policy"
    _CONFIG_SECTION_NAME = "power_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "power.Policy"

    def __init__(self, parent=None, power_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=power_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.dynamic_power_rebalancing = self.get_attribute(attribute_name="dynamic_rebalancing",
                                                            attribute_secondary_name="dynamic_power_rebalancing")
        self.extended_power_capacity = self.get_attribute(attribute_name="extended_power_capacity")
        self.power_allocation = self.get_attribute(attribute_name="allocated_budget",
                                                   attribute_secondary_name="power_allocation")
        self.power_priority = self.get_attribute(attribute_name="power_priority")
        self.power_profiling = self.get_attribute(attribute_name="power_profiling")
        self.power_redundancy = self.get_attribute(attribute_name="redundancy_mode",
                                                   attribute_secondary_name="power_redundancy")
        self.power_restore = self.get_attribute(attribute_name="power_restore_state",
                                                attribute_secondary_name="power_restore")
        self.power_save_mode = self.get_attribute(attribute_name="power_save_mode")
        self.processor_package_power_limit = self.get_attribute(attribute_name="processor_package_power_limit")

        if self._config.load_from == "live":
            power_redundancy_dict = {
                "Grid": "Grid",
                "NotRedundant": "Not Redundant",
                "N+1": "N+1",
                "N+2": "N+2"
            }
            self.power_redundancy = power_redundancy_dict.get(self.power_redundancy)

            power_restore_dict = {
                "AlwaysOff": "Always Off",
                "AlwaysOn": "Always On",
                "LastSate": "Last State"
            }
            self.power_restore = power_restore_dict.get(self.power_restore)

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.power_policy import PowerPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")
        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.dynamic_power_rebalancing is not None:
            kwargs["dynamic_rebalancing"] = self.dynamic_power_rebalancing
        if self.extended_power_capacity is not None:
            kwargs["extended_power_capacity"] = self.extended_power_capacity
        if self.power_allocation is not None:
            kwargs["allocated_budget"] = self.power_allocation
        if self.power_priority is not None:
            kwargs["power_priority"] = self.power_priority
        if self.power_profiling is not None:
            kwargs["power_profiling"] = self.power_profiling
        if self.power_redundancy is not None:
            power_redundancy_dict = {
                "Grid": "Grid",
                "Not Redundant": "NotRedundant",
                "N+1": "N+1",
                "N+2": "N+2"
            }
            kwargs["redundancy_mode"] = power_redundancy_dict.get(self.power_redundancy)
        if self.power_restore is not None:
            power_restore_dict = {
                "Always Off": "AlwaysOff",
                "Always On": "AlwaysOn",
                "Last State": "LastState"
            }
            kwargs["power_restore_state"] = power_restore_dict.get(self.power_restore)
        if self.power_save_mode is not None:
            kwargs["power_save_mode"] = self.power_save_mode
        if self.processor_package_power_limit is not None:
            kwargs["processor_package_power_limit"] = self.processor_package_power_limit

        power_policy = PowerPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=power_policy, detail=self.name):
            return False

        return True


class IntersightSanConnectivityPolicy(IntersightConfigObject):
    from config.intersight.network_policies import IntersightVhbaTemplate
    _CONFIG_NAME = "SAN Connectivity Policy"
    _CONFIG_SECTION_NAME = "san_connectivity_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.SanConnectivityPolicy"
    _POLICY_MAPPING_TABLE = {
        "vhbas": [
            {
                "fibre_channel_adapter_policy": IntersightFibreChannelAdapterPolicy,
                "fibre_channel_qos_policy": IntersightFibreChannelQosPolicy,
                "fibre_channel_network_policy": IntersightFibreChannelNetworkPolicy,
                "fc_zone_policies": [IntersightFcZonePolicy],
                "vhba_template": IntersightVhbaTemplate,
                "wwpn_pool": IntersightWwpnPool
            }
        ],
        "wwnn_pool": IntersightWwnnPool
    }
    UCS_TO_INTERSIGHT_POLICY_MAPPING_TABLE = {
        "adapter_policy": "fibre_channel_adapter_policy",
        "qos_policy": "fibre_channel_qos_policy"
    }
    UCS_TO_INTERSIGHT_POOL_MAPPING_TABLE = {
        "wwnn_pool": IntersightWwnnPool,
        "wwpn_pool": IntersightWwpnPool
    }

    def __init__(self, parent=None, san_connectivity_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=san_connectivity_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.target_platform = self.get_attribute(attribute_name="target_platform")
        self.vhba_placement_mode = self.get_attribute(attribute_name="placement_mode",
                                                      attribute_secondary_name="vhba_placement_mode")
        # TODO: Change default to empty list
        self.vhbas = None
        self.wwnn_allocation_type = self.get_attribute(attribute_name="wwnn_address_type",
                                                       attribute_secondary_name="wwnn_allocation_type")
        self.wwnn_pool = None
        self.wwnn_static = self.get_attribute(attribute_name="static_wwnn_address",
                                              attribute_secondary_name="wwnn_static")

        if self._config.load_from == "live":
            # Renaming Target Platform to be more user-friendly
            if self.target_platform == "FIAttached":
                self.target_platform = "FI-Attached"

            elif self.target_platform == "Standalone":
                # We force WWNN Allocation Type to be set to None, since it is not supported in Standalone mode
                self.wwnn_allocation_type = None

            # Renaming WWNN Allocation Type to lowercase to be more user-friendly
            # (and aligned with vHBA wwpn_allocation_type)
            if self.wwnn_allocation_type:
                self.wwnn_allocation_type = self.wwnn_allocation_type.lower()

            if san_connectivity_policy.wwnn_pool:
                self.wwnn_pool = self._get_policy_name(policy=san_connectivity_policy.wwnn_pool)
            self.vhbas = self._get_vhbas()

        elif self._config.load_from == "file":
            for attribute in ["vhbas", "wwnn_pool"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # We use this to make sure all options of a vHBA are set to None if they are not present
            if self.vhbas:
                for vhba in self.vhbas:
                    for attribute in ["automatic_pci_link_assignment", "automatic_slot_id_assignment",
                                      "fc_zone_policies", "fibre_channel_adapter_policy",
                                      "fibre_channel_network_policy", "fibre_channel_qos_policy", "name", "pci_link",
                                      "pci_link_assignment_mode", "pci_order", "persistent_lun_bindings",
                                      "pin_group_name", "slot_id", "switch_id", "uplink_port", "vhba_type",
                                      "wwpn_allocation_type", "wwpn_pool", "wwpn_static"]:
                        if attribute not in vhba:
                            vhba[attribute] = None

    def _get_vhbas(self):
        # Fetches the vHBAs configuration of a SAN Connectivity Policy
        if "vnic_fc_if" in self._config.sdk_objects:
            vhbas = []
            for vnic_fc_if in self._config.sdk_objects["vnic_fc_if"]:
                overriden_list = []
                if vnic_fc_if.san_connectivity_policy:
                    if vnic_fc_if.san_connectivity_policy.moid == self._moid:
                        vhba = {
                            "name": vnic_fc_if.name,
                            "pci_order": vnic_fc_if.order
                        }
                        if self.target_platform in ["FI-Attached"]:
                            # If the vHBA is created from a vHBA template, fetch the source vHBA template
                            if vnic_fc_if.src_template:
                                src_vhba_template = self._get_policy_name(policy=vnic_fc_if.src_template)
                                if src_vhba_template:
                                    vhba["vhba_template"] = src_vhba_template
                                # If the vHBA is created from a template and overrides are allowed in a vHBA template
                                # Fetch the overridden list
                                if vnic_fc_if.overridden_list:
                                    overriden_list = vnic_fc_if.overridden_list

                        # If the vHBA is created from a vHBA template
                        # Add switch_id, pingroupname, wwpn_pool, fibre_channel_network_policy,
                        # fibre_channel_adapter_policy and fc_zone_policies to the vHBA dictionary
                        # if the vHBA template is absent or if these attributes are overridden fields.
                        if vnic_fc_if.placement:
                            vhba["automatic_slot_id_assignment"] = vnic_fc_if.placement.auto_slot_id
                            if not vnic_fc_if.placement.auto_slot_id:
                                vhba["slot_id"] = vnic_fc_if.placement.id
                            vhba["automatic_pci_link_assignment"] = vnic_fc_if.placement.auto_pci_link
                            if not vnic_fc_if.placement.auto_pci_link:
                                vhba["pci_link_assignment_mode"] = vnic_fc_if.placement.pci_link_assignment_mode
                                if vnic_fc_if.placement.pci_link_assignment_mode in ["Custom"]:
                                    vhba["pci_link"] = vnic_fc_if.placement.pci_link
                            if self.target_platform in ["FI-Attached"]:
                                if not vhba.get("vhba_template") or "Placement.SwitchId" in overriden_list:
                                    vhba["switch_id"] = vnic_fc_if.placement.switch_id
                                    if vhba["switch_id"] in ["None"]:
                                        vhba["switch_id"] = None
                            elif self.target_platform in ["Standalone"]:
                                vhba["uplink_port"] = vnic_fc_if.placement.uplink
                        if self.target_platform in ["FI-Attached"]:
                            if not vhba.get("vhba_template") or "PinGroupName" in overriden_list:
                                vhba["pin_group_name"] = vnic_fc_if.pin_group_name if vnic_fc_if.pin_group_name else None
                            if not vhba.get("vhba_template") or "WwpnPool" in overriden_list:
                                vhba["wwpn_allocation_type"] = vnic_fc_if.wwpn_address_type.lower()
                                # We only fetch the WWPN Address Pool or Static WWPN for FI-Attached servers
                                if vnic_fc_if.wwpn_address_type in ["POOL"]:
                                    if vnic_fc_if.wwpn_pool:
                                        wwpn_pool = self._get_policy_name(policy=vnic_fc_if.wwpn_pool)
                                        if wwpn_pool:
                                            vhba["wwpn_pool"] = wwpn_pool
                                elif vnic_fc_if.wwpn_address_type in ["STATIC"]:
                                    vhba["wwpn_static"] = vnic_fc_if.static_wwpn_address
                        if not vhba.get("vhba_template") or "FcNetworkPolicy" in overriden_list:
                            if vnic_fc_if.fc_network_policy:
                                fc_network_policy = self._get_policy_name(policy=vnic_fc_if.fc_network_policy)
                                if fc_network_policy:
                                    vhba["fibre_channel_network_policy"] = fc_network_policy

                        if not vhba.get("vhba_template"):
                            # If vHBA Template is attached then persistent_lun_bindings, vhba_type and
                            # fibre_channel_qos_policy are set at the Template level and cannot be overriden.
                            # If vHBA Template is not attached, then these fields are set at the vHBA level
                            # Add these fields to the vHBA dictionary
                            vhba["persistent_lun_bindings"] = vnic_fc_if.persistent_bindings
                            vhba["vhba_type"] = vnic_fc_if.type
                            if vnic_fc_if.fc_qos_policy:
                                fc_qos_policy = self._get_policy_name(policy=vnic_fc_if.fc_qos_policy)
                                if fc_qos_policy:
                                    vhba["fibre_channel_qos_policy"] = fc_qos_policy
                        if not vhba.get("vhba_template") or "FcAdapterPolicy" in overriden_list:
                            if vnic_fc_if.fc_adapter_policy:
                                fc_adapter_policy = self._get_policy_name(policy=vnic_fc_if.fc_adapter_policy)
                                if fc_adapter_policy:
                                    vhba["fibre_channel_adapter_policy"] = fc_adapter_policy
                        if not vhba.get("vhba_template") or "FcZonePolicies" in overriden_list:
                            if vnic_fc_if.fc_zone_policies:
                                fc_zone_policy_list = []
                                for fc_zone_policy_ref in vnic_fc_if.fc_zone_policies:
                                    fc_zone_policy = self._get_policy_name(policy=fc_zone_policy_ref)
                                    if fc_zone_policy:
                                        fc_zone_policy_list.append(fc_zone_policy)
                                vhba["fc_zone_policies"] = fc_zone_policy_list

                        vhbas.append(vhba)

            return vhbas

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_san_connectivity_policy import VnicSanConnectivityPolicy
        from intersight.model.vnic_vhba_template import VnicVhbaTemplate

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.wwnn_allocation_type is not None:
            kwargs["wwnn_address_type"] = self.wwnn_allocation_type.upper()
        if self.wwnn_static is not None:
            kwargs["static_wwnn_address"] = self.wwnn_static
        if self.target_platform is not None:
            if self.target_platform in ["FI-Attached"]:
                kwargs["target_platform"] = "FIAttached"
            else:
                kwargs["target_platform"] = self.target_platform
        if self.vhba_placement_mode is not None:
            kwargs["placement_mode"] = self.vhba_placement_mode

        # We need to map the WWNN Pool in case it is used
        if self.wwnn_pool is not None:
            # We need to identify the WWNN Pool object reference
            # Since WWPN & WWNN share the same object type, we need to specify a query filter
            if "/" in self.wwnn_pool:
                wwnn_pool_name = self.wwnn_pool.split("/")[1]
                wwnn_pool_org_ref = self.get_org_relationship(org_name=self.wwnn_pool.split("/")[0])
                wwnn_pool = None
                if wwnn_pool_org_ref:
                    wwnn_pool = self.get_live_object(
                        object_name=wwnn_pool_name,
                        object_type="fcpool.Pool",
                        query_filter="Name eq '" + wwnn_pool_name + "' and Organization/Moid eq '" +
                                     wwnn_pool_org_ref.moid + "' and PoolPurpose eq 'WWNN'"
                    )
            else:
                wwnn_pool = self.get_live_object(
                    object_name=self.wwnn_pool,
                    object_type="fcpool.Pool",
                    query_filter="Name eq '" + self.wwnn_pool + "' and Organization/Moid eq '" +
                                 self.get_parent_org_relationship().moid + "' and PoolPurpose eq 'WWNN'"
                )
            if wwnn_pool:
                kwargs["wwnn_pool"] = wwnn_pool
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching WWNN Pool '{self.wwnn_pool}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find WWNN Pool '{self.wwnn_pool}'"
                )

        san_connectivity_policy = VnicSanConnectivityPolicy(**kwargs)

        scp = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=san_connectivity_policy,
                          detail=self.name, return_relationship=True)
        if not scp:
            return False

        # We now create the vnic.FcIf objects for each vHBA
        if self.vhbas is not None:
            from intersight.model.vnic_fc_if import VnicFcIf
            from intersight.model.motemplate_action_entry import MotemplateActionEntry

            for vhba in self.vhbas:

                # We first need to check if a vHBA with the same name already exists
                vhba_fc_if = self.get_live_object(
                    object_name=vhba.get("name"),
                    object_type="vnic.FcIf",
                    return_reference=False,
                    log=False,
                    query_filter=f"Name eq '{vhba['name']}' and SanConnectivityPolicy/Moid eq '{scp.moid}'"
                )

                if not getattr(self._config, "update_existing_intersight_objects", False) and vhba_fc_if:
                    message = f"Object type vnic.FcIf with name={vhba.get('name')} " \
                              f"already exists"
                    self.logger(level="info", message=message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=vhba['name'], obj_type="vnic.FcIf", status="skipped",
                        message=message)
                    continue
                # In case this vHBA derived from vHBA template, we use the 'derive' mechanism to create it
                if vhba.get("vhba_template"):
                    if not vhba_fc_if:
                        from intersight.model.bulk_mo_cloner import BulkMoCloner

                        # This vHBA is newly derived from a vHBA template and is not a pre-existing entity.
                        # Therefore, we need to Attach the source template from which the vHBA is derived and target
                        # fields that can be set at the vHBA level, including overridden fields to the BulkMoCloner.
                        kwargs_mo_cloner = {
                            "sources": [],
                            "targets": []
                        }
                        # We need to identify the Moid of the source vHBA Template
                        vhba_template = self.get_live_object(object_name=vhba["vhba_template"],
                                                             object_type="vnic.VhbaTemplate")
                        if vhba_template:
                            template_moid = vhba_template.moid
                            source_template = {
                                "moid": template_moid,
                                "object_type": "vnic.VhbaTemplate"
                            }
                            kwargs_mo_cloner["sources"].append(VnicVhbaTemplate(**source_template))
                        else:
                            err_message = "Unable to locate source vHBA Template " + \
                                          vhba['vhba_template'] + " to derive vHBA Template " + vhba['name']
                            self.logger(level="error", message=err_message)
                            self._config.push_summary_manager.add_object_status(obj=self, obj_detail=vhba['name'],
                                                                                obj_type="vnic.VhbaTemplate",
                                                                                status="failed", message=err_message)
                            continue
                        # We now need to specify the attribute of the target vHBA
                        target_vhba = {
                            "object_type": "vnic.FcIf",
                            "class_id": "vnic.FcIf",
                            "san_connectivity_policy": scp
                        }
                        if vhba.get("name") is not None:
                            target_vhba["name"] = vhba["name"]
                        if vhba.get("pci_order") is not None:
                            target_vhba["order"] = vhba["pci_order"]

                        # It is essential to manage overridden values effectively.
                        # This includes handling overridden attributes such as wwpnpool, placement settings,
                        # pingroupname, fc_zone_policies, fibre_channel_adapter_policy and fibre_channel_network_policy.
                        if vhba.get("pin_group_name") is not None:
                            target_vhba["pin_group_name"] = vhba["pin_group_name"]
                        # Handling the WWPN Address settings of the vHBA
                        if vhba.get("wwpn_allocation_type") is not None:
                            target_vhba["wwpn_address_type"] = vhba["wwpn_allocation_type"].upper()
                        if vhba.get("wwpn_allocation_type") in ["pool"]:
                            if vhba.get("wwpn_pool") is not None:
                                # We need to identify the WWPN Pool object reference
                                # Since WWPN & WWNN share the same object type, we need to specify a query filter
                                if "/" in vhba["wwpn_pool"]:
                                    wwpn_pool_name = vhba["wwpn_pool"].split("/")[1]
                                    wwpn_pool_org_ref = self.get_org_relationship(
                                        org_name=vhba["wwpn_pool"].split("/")[0])
                                    wwpn_pool = None
                                    if wwpn_pool_org_ref:
                                        wwpn_pool = self.get_live_object(
                                            object_name=wwpn_pool_name,
                                            object_type="fcpool.Pool",
                                            query_filter="Name eq '" + wwpn_pool_name + "' and Organization/Moid eq '" +
                                                         wwpn_pool_org_ref.moid + "' and PoolPurpose eq 'WWPN'"
                                        )
                                else:
                                    wwpn_pool = self.get_live_object(
                                        object_name=vhba["wwpn_pool"],
                                        object_type="fcpool.Pool",
                                        query_filter="Name eq '" + vhba["wwpn_pool"] + "' and Organization/Moid eq '" +
                                                     self.get_parent_org_relationship().moid + "' and PoolPurpose eq 'WWPN'"
                                    )
                                if wwpn_pool:
                                    target_vhba["wwpn_pool"] = wwpn_pool
                                else:
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=f"Attaching WWPN Pool '{vhba['wwpn_pool']}' to vHBA - "
                                                             f"{str(vhba['name'])}",
                                        obj_type="vnic.FcIf", status="failed",
                                        message=f"Failed to find WWPN Pool '{vhba['wwpn_pool']}'"
                                    )
                        elif vhba.get("wwpn_allocation_type") in ["static"]:
                            if vhba.get("wwpn_static") is not None:
                                target_vhba["static_wwpn_address"] = vhba["wwpn_static"]
                        # Handling the placement settings of the vHBA
                        from intersight.model.vnic_placement_settings import VnicPlacementSettings
                        kwargs_placement = {
                            "object_type": "vnic.PlacementSettings",
                            "class_id": "vnic.PlacementSettings"
                        }
                        if vhba.get("switch_id") is not None:
                            kwargs_placement["switch_id"] = vhba["switch_id"]
                        if vhba.get("automatic_slot_id_assignment", False):
                            kwargs_placement["auto_slot_id"] = True
                        elif vhba.get("slot_id") is not None:  # We have a Slot ID value
                            kwargs_placement["auto_slot_id"] = False
                            kwargs_placement["id"] = vhba["slot_id"]
                        else:  # We don't have any slot ID value - we set Auto Slot ID to enabled
                            kwargs_placement["auto_slot_id"] = True
                        if vhba.get("automatic_pci_link_assignment", False):
                            kwargs_placement["auto_pci_link"] = True
                        # We have a PCI Link value - We set assignment mode to Custom
                        elif vhba.get("pci_link") is not None:
                            kwargs_placement["auto_pci_link"] = False
                            kwargs_placement["pci_link_assignment_mode"] = "Custom"
                            kwargs_placement["pci_link"] = vhba["pci_link"]
                        # Assignment mode set to Load-Balanced
                        elif vhba.get("pci_link_assignment_mode") in ["Load-Balanced"]:
                            kwargs_placement["auto_pci_link"] = False
                            kwargs_placement["pci_link_assignment_mode"] = "Load-Balanced"
                        else:  # We don't have any PCI Link value - we set Auto PCI Link to enabled
                            kwargs_placement["auto_pci_link"] = True
                        if vhba.get("uplink_port") is not None:
                            kwargs_placement["uplink"] = vhba["uplink_port"]
                        target_vhba["placement"] = VnicPlacementSettings(**kwargs_placement)

                        # Handling the policies attachments of the vHBA
                        if vhba.get("fc_zone_policies") is not None:
                            # We need to identify the FC Zone Policy object reference
                            fc_zone_policy_list = []
                            for fc_zone_policy in vhba["fc_zone_policies"]:
                                live_fc_zone_policy = self.get_live_object(
                                    object_name=fc_zone_policy,
                                    object_type="fabric.FcZonePolicy"
                                )
                                if live_fc_zone_policy:
                                    fc_zone_policy_list.append(live_fc_zone_policy)
                                else:
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=f"Attaching FC Zone Policy '{fc_zone_policy}' to vHBA - "
                                                             f"{str(vhba['name'])}",
                                        obj_type="vnic.FcIf", status="failed",
                                        message=f"Failed to find FC Zone Policy '{fc_zone_policy}'"
                                    )
                            target_vhba["fc_zone_policies"] = fc_zone_policy_list
                        if vhba.get("fibre_channel_adapter_policy") is not None:
                            # We need to identify the Fibre Channel Adapter Policy object reference
                            fc_adapter_policy = self.get_live_object(
                                object_name=vhba["fibre_channel_adapter_policy"],
                                object_type="vnic.FcAdapterPolicy"
                            )
                            if fc_adapter_policy:
                                target_vhba["fc_adapter_policy"] = fc_adapter_policy
                            else:
                                self._config.push_summary_manager.add_object_status(
                                    obj=self,
                                    obj_detail=f"Attaching FC Adapter Policy '{vhba['fibre_channel_adapter_policy']}'"
                                               f" to vHBA - {str(vhba['name'])}",
                                    obj_type="vnic.FcIf", status="failed",
                                    message=f"Failed to find FC Adapter Policy '{vhba['fibre_channel_adapter_policy']}'"
                                )
                        if vhba.get("fibre_channel_network_policy") is not None:
                            # We need to identify the Fibre Channel Network Policy object reference
                            fc_nw_policy = self.get_live_object(
                                object_name=vhba["fibre_channel_network_policy"],
                                object_type="vnic.FcNetworkPolicy"
                            )
                            if fc_nw_policy:
                                target_vhba["fc_network_policy"] = fc_nw_policy
                            else:
                                self._config.push_summary_manager.add_object_status(
                                    obj=self,
                                    obj_detail=f"Attaching FC Network Policy '{vhba['fibre_channel_network_policy']}'"
                                               f" to vHBA - {str(vhba['name'])}",
                                    obj_type="vnic.FcIf", status="failed",
                                    message=f"Failed to find FC Network Policy '{vhba['fibre_channel_network_policy']}'"
                                )

                        kwargs_mo_cloner["targets"].append(VnicFcIf(**target_vhba))

                        mo_cloner = BulkMoCloner(**kwargs_mo_cloner)

                        self.commit(object_type="bulk.MoCloner", payload=mo_cloner,
                                    detail=self.name + " - vHBA " + str(vhba["name"]))
                        continue
                    else:
                        # We found a vhba with the same name,
                        # we need to check if it is bound to a same vHBA Template or different vHBA Template
                        # If vHBA is derived from another vHBA Template we will detach it from its Template and
                        # reattach it to the desired Template
                        if vhba_fc_if.src_template:
                            src_template = self._device.query(
                                object_type="vnic.VhbaTemplate",
                                filter="Moid eq '" + vhba_fc_if.src_template.moid + "'"
                            )
                            if len(src_template) == 1:
                                if src_template[0].name == vhba.get("vhba_template"):
                                    # This vHBA is already derived from the same vHBA Template
                                    info_message = "vHBA " + vhba.get("name") + " exists and is already derived " + \
                                                   "from same vHBA Template " + vhba.get("vhba_template")
                                    self.logger(level="info", message=info_message)
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=vhba.get("name"), obj_type="vnic.FcIf",
                                        status="skipped", message=info_message)
                                    continue
                                else:
                                    # vHBA is derived from another vHBA Template
                                    # We will detach it from its Template and reattach it to the desired Template
                                    self.logger(
                                        level="info",
                                        message="vHBA " + vhba.get("name") +
                                                " exists and is derived from different vHBA Template " +
                                                src_template[0].name
                                    )
                                    self.logger(
                                        level="info",
                                        message="Detaching vHBA " + vhba.get("name") +
                                                " from vHBA Template " + src_template[0].name
                                    )
                                    kwargs = {
                                        "object_type": "vnic.FcIf",
                                        "class_id": "vnic.FcIf",
                                        "name": vhba.get("name"),
                                        "san_connectivity_policy": scp,
                                        "src_template": None
                                    }
                                    vnic_fcif_payload = VnicFcIf(**kwargs)

                                    if not self.commit(object_type="vnic.FcIf",
                                                       payload=vnic_fcif_payload,
                                                       detail="Detaching from vHBA template " + src_template[0].name,
                                                       key_attributes=["name", "san_connectivity_policy"]):
                                        continue
                                    self.logger(
                                        level="info",
                                        message="Attaching vHBA " + vhba.get("name") +
                                                " to vHBA Template " + vhba.get("vhba_template")
                                    )
                                    # We need to identify the Moid of the vHBA Template
                                    vhba_template = self.get_live_object(
                                        object_name=vhba.get("vhba_template"),
                                        object_type="vnic.VhbaTemplate"
                                    )
                                    # Attach action needs to be specified in the TemplateActions
                                    # To attach vHBA to a template
                                    kwargs_template_actions = {
                                        "object_type": "motemplate.ActionEntry",
                                        "class_id": "motemplate.ActionEntry",
                                        "type": "Attach"
                                    }
                                    kwargs["template_actions"] = [MotemplateActionEntry(**kwargs_template_actions)]
                                    kwargs["src_template"] = vhba_template
                                    vnic_fcif_payload = VnicFcIf(**kwargs)

                                    self.commit(object_type="vnic.FcIf",
                                                payload=vnic_fcif_payload,
                                                detail="Attaching to template " + vhba.get("vhba_template"),
                                                key_attributes=["name", "san_connectivity_policy"])
                                    continue
                            else:
                                err_message = "Could not find vHBA Template " + vhba.get("vhba_template")
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=vhba['name'], obj_type="vnic.FcIf",
                                    status="failed",
                                    message=err_message)
                                continue
                        else:
                            # vHBA is not currently bound to a template. So we just need to bind it
                            # We need to identify the Moid of the Attached vHBA Template
                            vhba_template = self.get_live_object(
                                object_name=vhba.get("vhba_template"),
                                object_type="vnic.VhbaTemplate"
                            )
                            # Attach action needs to be specified in the TemplateActions to attach vHBA to a template.
                            kwargs_template_actions = {
                                "object_type": "motemplate.ActionEntry",
                                "class_id": "motemplate.ActionEntry",
                                "type": "Attach"
                            }
                            kwargs = {
                                "object_type": "vnic.FcIf",
                                "class_id": "vnic.FcIf",
                                "name": vhba.get("name"),
                                "san_connectivity_policy": scp,
                                "template_actions": [MotemplateActionEntry(**kwargs_template_actions)],
                                "src_template": vhba_template
                            }
                            vnic_fcif_payload = VnicFcIf(**kwargs)
                            self.commit(object_type="vnic.FcIf", payload=vnic_fcif_payload,
                                        detail="Attaching to template " + vhba.get("vhba_template"))
                            continue

                # We now need to specify the attributes of the target vHBA if it is not created from a template
                kwargs = {
                    "object_type": "vnic.FcIf",
                    "class_id": "vnic.FcIf",
                    "san_connectivity_policy": scp
                }
                if vhba.get("name") is not None:
                    kwargs["name"] = vhba["name"]
                if vhba.get("pci_order") is not None:
                    kwargs["order"] = vhba["pci_order"]
                if vhba.get("vhba_type") is not None:
                    kwargs["type"] = vhba["vhba_type"]
                if vhba.get("persistent_lun_bindings") is not None:
                    kwargs["persistent_bindings"] = vhba["persistent_lun_bindings"]
                if vhba.get("pin_group_name") is not None:
                    kwargs["pin_group_name"] = vhba["pin_group_name"]

                # Handling the WWPN Address settings of the vHBA
                if vhba.get("wwpn_allocation_type") is not None:
                    kwargs["wwpn_address_type"] = vhba["wwpn_allocation_type"].upper()
                if vhba.get("wwpn_allocation_type") in ["pool"]:
                    if vhba.get("wwpn_pool") is not None:
                        # We need to identify the WWPN Pool object reference
                        # Since WWPN & WWNN share the same object type, we need to specify a query filter
                        if "/" in vhba["wwpn_pool"]:
                            wwpn_pool_name = vhba["wwpn_pool"].split("/")[1]
                            wwpn_pool_org_ref = self.get_org_relationship(org_name=vhba["wwpn_pool"].split("/")[0])
                            wwpn_pool = None
                            if wwpn_pool_org_ref:
                                wwpn_pool = self.get_live_object(
                                    object_name=wwpn_pool_name,
                                    object_type="fcpool.Pool",
                                    query_filter="Name eq '" + wwpn_pool_name + "' and Organization/Moid eq '" +
                                                 wwpn_pool_org_ref.moid + "' and PoolPurpose eq 'WWPN'"
                                )
                        else:
                            wwpn_pool = self.get_live_object(
                                object_name=vhba["wwpn_pool"],
                                object_type="fcpool.Pool",
                                query_filter="Name eq '" + vhba["wwpn_pool"] + "' and Organization/Moid eq '" +
                                             self.get_parent_org_relationship().moid + "' and PoolPurpose eq 'WWPN'"
                            )
                        if wwpn_pool:
                            kwargs["wwpn_pool"] = wwpn_pool
                        else:
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"Attaching WWPN Pool '{vhba['wwpn_pool']}' to vHBA - "
                                                     f"{str(vhba['name'])}",
                                obj_type="vnic.FcIf", status="failed",
                                message=f"Failed to find WWPN Pool '{vhba['wwpn_pool']}'"
                            )

                elif vhba.get("wwpn_allocation_type") in ["static"]:
                    if vhba.get("wwpn_static") is not None:
                        kwargs["static_wwpn_address"] = vhba["wwpn_static"]

                # Handling the placement settings of the vHBA
                from intersight.model.vnic_placement_settings import VnicPlacementSettings
                kwargs_placement = {
                    "object_type": "vnic.PlacementSettings",
                    "class_id": "vnic.PlacementSettings"
                }
                if vhba.get("switch_id") is not None:
                    kwargs_placement["switch_id"] = vhba["switch_id"]

                if vhba.get("automatic_slot_id_assignment", False):
                    kwargs_placement["auto_slot_id"] = True
                elif vhba.get("slot_id") is not None:  # We have a Slot ID value
                    kwargs_placement["auto_slot_id"] = False
                    kwargs_placement["id"] = vhba["slot_id"]
                else:  # We don't have any slot ID value - we set Auto Slot ID to enabled
                    kwargs_placement["auto_slot_id"] = True

                if vhba.get("automatic_pci_link_assignment", False):
                    kwargs_placement["auto_pci_link"] = True
                elif vhba.get("pci_link") is not None:  # We have a PCI Link value - We set assignment mode to Custom
                    kwargs_placement["auto_pci_link"] = False
                    kwargs_placement["pci_link_assignment_mode"] = "Custom"
                    kwargs_placement["pci_link"] = vhba["pci_link"]
                elif vhba.get("pci_link_assignment_mode") in ["Load-Balanced"]:  # Assignment mode set to Load-Balanced
                    kwargs_placement["auto_pci_link"] = False
                    kwargs_placement["pci_link_assignment_mode"] = "Load-Balanced"
                else:  # We don't have any PCI Link value - we set Auto PCI Link to enabled
                    kwargs_placement["auto_pci_link"] = True

                if vhba.get("uplink_port") is not None:
                    kwargs_placement["uplink"] = vhba["uplink_port"]
                kwargs["placement"] = VnicPlacementSettings(**kwargs_placement)

                # Handling the policies attachments of the vHBA
                if vhba.get("fc_zone_policies") is not None:
                    # We need to identify the FC Zone Policy object reference
                    fc_zone_policy_list = []
                    for fc_zone_policy in vhba["fc_zone_policies"]:
                        live_fc_zone_policy = self.get_live_object(
                            object_name=fc_zone_policy,
                            object_type="fabric.FcZonePolicy"
                        )
                        if live_fc_zone_policy:
                            fc_zone_policy_list.append(live_fc_zone_policy)
                        else:
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"Attaching FC Zone Policy '{fc_zone_policy}' to vHBA - "
                                                     f"{str(vhba['name'])}",
                                obj_type="vnic.FcIf", status="failed",
                                message=f"Failed to find FC Zone Policy '{fc_zone_policy}'"
                            )

                    kwargs["fc_zone_policies"] = fc_zone_policy_list

                if vhba.get("fibre_channel_adapter_policy") is not None:
                    # We need to identify the Fibre Channel Adapter Policy object reference
                    fc_adapter_policy = self.get_live_object(
                        object_name=vhba["fibre_channel_adapter_policy"],
                        object_type="vnic.FcAdapterPolicy"
                    )
                    if fc_adapter_policy:
                        kwargs["fc_adapter_policy"] = fc_adapter_policy
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching FC Adapter Policy '{vhba['fibre_channel_adapter_policy']}'"
                                                 f" to vHBA - {str(vhba['name'])}",
                            obj_type="vnic.FcIf", status="failed",
                            message=f"Failed to find FC Adapter Policy '{vhba['fibre_channel_adapter_policy']}'"
                        )

                if vhba.get("fibre_channel_network_policy") is not None:
                    # We need to identify the Fibre Channel Network Policy object reference
                    fc_nw_policy = self.get_live_object(
                        object_name=vhba["fibre_channel_network_policy"],
                        object_type="vnic.FcNetworkPolicy"
                    )
                    if fc_nw_policy:
                        kwargs["fc_network_policy"] = fc_nw_policy
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching FC Network Policy '{vhba['fibre_channel_network_policy']}'"
                                                 f" to vHBA - {str(vhba['name'])}",
                            obj_type="vnic.FcIf", status="failed",
                            message=f"Failed to find FC Network Policy '{vhba['fibre_channel_network_policy']}'"
                        )

                if vhba.get("fibre_channel_qos_policy") is not None:
                    # We need to identify the Fibre Channel QoS Policy object reference
                    fc_qos_policy = self.get_live_object(
                        object_name=vhba["fibre_channel_qos_policy"],
                        object_type="vnic.FcQosPolicy"
                    )
                    if fc_qos_policy:
                        kwargs["fc_qos_policy"] = fc_qos_policy
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching FC QOS Policy '{vhba['fibre_channel_qos_policy']}' to "
                                                 f"vHBA - {str(vhba['name'])}",
                            obj_type="vnic.FcIf", status="failed",
                            message=f"Failed to find FC QOS Policy '{vhba['fibre_channel_qos_policy']}'"
                        )

                vhba_payload = VnicFcIf(**kwargs)

                self.commit(object_type="vnic.FcIf", payload=vhba_payload,
                            detail=self.name + " - vHBA " + str(vhba["name"]),
                            key_attributes=["name", "san_connectivity_policy"])

        return True


class IntersightScrubPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Scrub Policy"
    _CONFIG_SECTION_NAME = "scrub_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "compute.ScrubPolicy"

    def __init__(self, parent=None, scrub_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=scrub_policy)
        self.name = self.get_attribute(attribute_name="name")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.disk = None
        self.bios = None

        if self._config.load_from == "live":
            if self._object and hasattr(self._object, "scrub_targets"):
                self.disk = "Disk" in self._object.scrub_targets
                self.bios = "BIOS" in self._object.scrub_targets
        elif self._config.load_from == "file":
            if self._object:
                if self._object.get('disk') is not None:
                    self.disk = self._object['disk']
                if self._object.get('bios') is not None:
                    self.bios = self._object['bios']

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.compute_scrub_policy import ComputeScrubPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name:
            kwargs["name"] = self.name
        if self.descr:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        # Convert boolean values to scrub_targets
        scrub_targets = []
        if self.disk:
            scrub_targets.append("Disk")
        if self.bios:
            scrub_targets.append("BIOS")

        if scrub_targets:
            kwargs["scrub_targets"] = scrub_targets

        scrub_policy = ComputeScrubPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=scrub_policy, detail=self.name):
            return False

        return True


class IntersightSdCardPolicy(IntersightConfigObject):
    _CONFIG_NAME = "SD Card Policy"
    _CONFIG_SECTION_NAME = "sd_card_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "sdcard.Policy"

    def __init__(self, parent=None, sdcard_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=sdcard_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.partitions = None
        if self._config.load_from == "live":
            if hasattr(self._object, "partitions"):
                self.partitions = []
                for partition in self._object.partitions:
                    partition_dict = {
                        "type": partition.type,
                        "virtual_drives": []
                    }
                    for virtual_drive in partition.virtual_drives:
                        virtual_drive_dict = {"enable": virtual_drive.enable}
                        if virtual_drive.class_id == "sdcard.OperatingSystem":
                            virtual_drive_dict["object_type"] = "Operating_System"
                        elif virtual_drive.class_id == "sdcard.Diagnostics":
                            virtual_drive_dict["object_type"] = "Diagnostics"
                        elif virtual_drive.class_id == "sdcard.Drivers":
                            virtual_drive_dict["object_type"] = "Drivers"
                        elif virtual_drive.class_id == "sdcard.HostUpgradeUtility":
                            virtual_drive_dict["object_type"] = "Host_Upgrade_Utility"
                        elif virtual_drive.class_id == "sdcard.ServerConfigurationUtility":
                            virtual_drive_dict["object_type"] = "Server_Configuration_Utility"
                        elif virtual_drive.class_id == "sdcard.UserPartition":
                            virtual_drive_dict["object_type"] = "User_Partition"

                        if hasattr(virtual_drive, "name"):
                            virtual_drive_dict["name"] = virtual_drive.name
                        else:
                            virtual_drive_dict["name"] = None

                        partition_dict["virtual_drives"].append(virtual_drive_dict)
                    self.partitions.append(partition_dict)

        elif self._config.load_from == "file":
            for attribute in ["partitions"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of SD Card Partition are set to None if they are not present
        if self.partitions:
            for partition in self.partitions:
                for attribute in ["type", "virtual_drives"]:
                    if attribute not in partition:
                        partition[attribute] = None
                    if attribute == "virtual_drives":
                        for virtual_drive in partition["virtual_drives"]:
                            for sub_attribute in ["enable", "object_type", "name"]:
                                if sub_attribute not in virtual_drive:
                                    virtual_drive[sub_attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.sdcard_policy import SdcardPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.partitions is not None:
            kwargs["partitions"] = self.partitions
        if self.partitions is not None:
            kwargs["partitions"] = []
            for partition in self.partitions:
                from intersight.model.sdcard_partition import SdcardPartition
                kwargs_sd_card_partition = {}
                if partition["type"] is not None:
                    kwargs_sd_card_partition["type"] = partition["type"]
                if partition["virtual_drives"] is not None:
                    kwargs_sd_card_partition["virtual_drives"] = []
                    for virtual_drive in partition["virtual_drives"]:
                        from intersight.model.sdcard_virtual_drive import SdcardVirtualDrive
                        kwargs_sd_card_virtual_drive = {}
                        if virtual_drive["object_type"] is not None:
                            if virtual_drive["object_type"] == "Operating_System":
                                kwargs_sd_card_virtual_drive["object_type"] = "sdcard.OperatingSystem"
                                kwargs_sd_card_virtual_drive["class_id"] = "sdcard.OperatingSystem"
                            elif virtual_drive["object_type"] == "Diagnostics":
                                kwargs_sd_card_virtual_drive["object_type"] = "sdcard.Diagnostics"
                                kwargs_sd_card_virtual_drive["class_id"] = "sdcard.Diagnostics"
                            elif virtual_drive["object_type"] == "Drivers":
                                kwargs_sd_card_virtual_drive["object_type"] = "sdcard.Drivers"
                                kwargs_sd_card_virtual_drive["class_id"] = "sdcard.Drivers"
                            elif virtual_drive["object_type"] == "Host_Upgrade_Utility":
                                kwargs_sd_card_virtual_drive["object_type"] = "sdcard.HostUpgradeUtility"
                                kwargs_sd_card_virtual_drive["class_id"] = "sdcard.HostUpgradeUtility"
                            elif virtual_drive["object_type"] == "Server_Configuration_Utility":
                                kwargs_sd_card_virtual_drive["object_type"] = "sdcard.ServerConfigurationUtility"
                                kwargs_sd_card_virtual_drive["class_id"] = "sdcard.ServerConfigurationUtility"
                            elif virtual_drive["object_type"] == "User_Partition":
                                kwargs_sd_card_virtual_drive["object_type"] = "sdcard.UserPartition"
                                kwargs_sd_card_virtual_drive["class_id"] = "sdcard.UserPartition"
                        if virtual_drive["name"] is not None:
                            kwargs_sd_card_virtual_drive["name"] = virtual_drive["name"]
                        if virtual_drive["enable"] is not None:
                            kwargs_sd_card_virtual_drive["enable"] = virtual_drive["enable"]
                        kwargs_sd_card_partition["virtual_drives"].append(
                            SdcardVirtualDrive(**kwargs_sd_card_virtual_drive))

                kwargs["partitions"].append(
                    SdcardPartition(**kwargs_sd_card_partition))

        sdcard_policy = SdcardPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=sdcard_policy, detail=self.name):
            return False

        return True


class IntersightSerialOverLanPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Serial over LAN Policy"
    _CONFIG_SECTION_NAME = "serial_over_lan_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "sol.Policy"

    def __init__(self, parent=None, sol_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=sol_policy)

        self.baud_rate = self.get_attribute(attribute_name="baud_rate")
        self.com_port = self.get_attribute(attribute_name="com_port")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enabled = self.get_attribute(attribute_name="enabled")
        self.name = self.get_attribute(attribute_name="name")
        self.ssh_port = self.get_attribute(attribute_name="ssh_port")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.sol_policy import SolPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enabled is not None:
            kwargs["enabled"] = self.enabled
        if self.baud_rate is not None:
            kwargs["baud_rate"] = self.baud_rate
        if self.com_port is not None:
            kwargs["com_port"] = self.com_port
        if self.ssh_port is not None:
            kwargs["ssh_port"] = self.ssh_port

        sol_policy = SolPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=sol_policy, detail=self.name):
            return False

        return True


class IntersightSmtpPolicy(IntersightConfigObject):
    _CONFIG_NAME = "SMTP Policy"
    _CONFIG_SECTION_NAME = "smtp_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "smtp.Policy"

    def __init__(self, parent=None, smtp_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=smtp_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enabled = None
        self.min_severity = None
        self.name = self.get_attribute(attribute_name="name")
        self.sender_email = None
        self.smtp_port = None
        self.smtp_recipients = None
        self.smtp_server_address = None

        if self._config.load_from == "live":
            if hasattr(self._object, "enabled"):
                self.enabled = self._object.enabled
                if getattr(self._object, "enabled") is True:
                    if hasattr(self._object, "smtp_server"):
                        self.smtp_server_address = self._object.smtp_server
                    if hasattr(self._object, "smtp_port"):
                        self.smtp_port = self._object.smtp_port
                    if hasattr(self._object, "min_severity"):
                        self.min_severity = self._object.min_severity
                    if hasattr(self._object, "sender_email"):
                        self.sender_email = self._object.sender_email
                    if hasattr(self._object, "smtp_recipients"):
                        if self._object.smtp_recipients:
                            self.smtp_recipients = []
                            for smtp_recipient in self._object.smtp_recipients:
                                self.smtp_recipients.append(smtp_recipient)

        elif self._config.load_from == "file":
            for attribute in ["enabled", "min_severity", "sender_email", "smtp_port", "smtp_recipients",
                              "smtp_server_address"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.smtp_policy import SmtpPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enabled is not None:
            kwargs["enabled"] = self.enabled
        if self.smtp_server_address is not None:
            kwargs['smtp_server'] = self.smtp_server_address
        if self.smtp_port is not None:
            kwargs['smtp_port'] = self.smtp_port
        if self.min_severity is not None:
            kwargs['min_severity'] = self.min_severity
        if self.sender_email is not None:
            kwargs['sender_email'] = self.sender_email
        if self.smtp_recipients is not None:
            kwargs["smtp_recipients"] = []
            for smtp_recipient in self.smtp_recipients:
                kwargs["smtp_recipients"].append(smtp_recipient)

        smtp_policy = SmtpPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=smtp_policy, detail=self.name):
            return False

        return True


class IntersightSnmpPolicy(IntersightConfigObject):
    _CONFIG_NAME = "SNMP Policy"
    _CONFIG_SECTION_NAME = "snmp_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "snmp.Policy"

    def __init__(self, parent=None, snmp_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=snmp_policy)

        self.access_community_string = self.get_attribute(attribute_name="access_community_string")
        self.community_access = self.get_attribute(attribute_name="community_access")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enabled = self.get_attribute(attribute_name="enabled")
        self.engine_input_id = self.get_attribute(attribute_name="engine_id",
                                                  attribute_secondary_name="engine_input_id")
        self.name = self.get_attribute(attribute_name="name")
        self.port = self.get_attribute(attribute_name="snmp_port", attribute_secondary_name="port")
        self.system_contact = self.get_attribute(attribute_name="sys_contact",
                                                 attribute_secondary_name="system_contact")
        self.system_location = self.get_attribute(attribute_name="sys_location",
                                                  attribute_secondary_name="system_location")
        self.trap_community_string = self.get_attribute(attribute_name="trap_community",
                                                        attribute_secondary_name="trap_community_string")
        self.trap_destinations = None
        self.users = None

        if self._config.load_from == "live":
            self.trap_destinations = self._get_trap_destinations()
            self.users = self._get_users()

        elif self._config.load_from == "file":
            for attribute in ["trap_destinations", "users"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a Trap Destination are set to None if they are not present
        if self.trap_destinations:
            for trap_destination in self.trap_destinations:
                for attribute in ["community", "destination_address", "enabled", "port", "trap_type", "user",
                                  "version"]:
                    if attribute not in trap_destination:
                        trap_destination[attribute] = None

        # We use this to make sure all options of a User are set to None if they are not present
        if self.users:
            for user in self.users:
                for attribute in ["auth_password", "auth_type", "name", "privacy_password", "privacy_type",
                                  "security_level"]:
                    if attribute not in user:
                        user[attribute] = None

    def _get_trap_destinations(self):
        if hasattr(self._object, "snmp_traps"):
            if self._object.snmp_traps is not None:
                snmp_traps_list = []

                for snmp_trap in self._object.snmp_traps:
                    snmp_traps_list.append({"enabled": snmp_trap.enabled,
                                            "version": snmp_trap.version,
                                            "user": snmp_trap.user,
                                            "community": snmp_trap.community,
                                            "trap_type": snmp_trap.type,
                                            "destination_address": snmp_trap.destination,
                                            "port": snmp_trap.port})

                return snmp_traps_list

        return None

    def _get_users(self):
        if hasattr(self._object, "snmp_users"):
            if self._object.snmp_users is not None:
                snmp_users_list = []

                for snmp_user in self._object.snmp_users:
                    snmp_users_list.append({"name": snmp_user.name,
                                            "security_level": snmp_user.security_level,
                                            "auth_type": snmp_user.auth_type,
                                            "privacy_type": snmp_user.privacy_type})
                    if snmp_user.is_auth_password_set:
                        self.logger(level="warning",
                                    message="Auth Password of " + self._CONFIG_NAME + " '" + self.name +
                                            "' - User '" + snmp_user.name + "' can't be exported")
                    if snmp_user.is_privacy_password_set:
                        self.logger(level="warning",
                                    message="Priv Password of " + self._CONFIG_NAME + " '" + self.name +
                                            "' - User '" + snmp_user.name + "' can't be exported")

                return snmp_users_list

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.snmp_policy import SnmpPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enabled is not None:
            kwargs["enabled"] = self.enabled
        if self.access_community_string is not None:
            kwargs["access_community_string"] = self.access_community_string
        if self.community_access is not None:
            kwargs["community_access"] = self.community_access
        if self.engine_input_id is not None:
            kwargs["engine_id"] = self.engine_input_id
        if self.port is not None:
            kwargs["snmp_port"] = self.port
        if self.system_contact is not None:
            kwargs["sys_contact"] = self.system_contact
        if self.system_location is not None:
            kwargs["sys_location"] = self.system_location
        if self.trap_community_string is not None:
            kwargs["trap_community"] = self.trap_community_string

        if self.trap_destinations is not None:
            from intersight.model.snmp_trap import SnmpTrap
            trap_destinations = []
            for trap_destination in self.trap_destinations:
                trap_destination_kwargs = {
                    "object_type": "snmp.Trap",
                    "class_id": "snmp.Trap",
                }
                if trap_destination.get("destination_address"):
                    trap_destination_kwargs["destination"] = trap_destination["destination_address"]
                if trap_destination.get("community"):
                    trap_destination_kwargs["community"] = trap_destination["community"]
                if trap_destination.get("enabled"):
                    trap_destination_kwargs["enabled"] = trap_destination["enabled"]
                if trap_destination.get("port"):
                    trap_destination_kwargs["port"] = trap_destination["port"]
                if trap_destination.get("trap_type"):
                    trap_destination_kwargs["type"] = trap_destination["trap_type"]
                if trap_destination.get("user"):
                    trap_destination_kwargs["user"] = trap_destination["user"]
                if trap_destination.get("version"):
                    trap_destination_kwargs["version"] = trap_destination["version"]

                trap_destinations.append(SnmpTrap(**trap_destination_kwargs))

            kwargs["snmp_traps"] = trap_destinations

        if self.users is not None:
            from intersight.model.snmp_user import SnmpUser
            users = []
            for user in self.users:
                user_kwargs = {
                    "object_type": "snmp.User",
                    "class_id": "snmp.User",
                }
                if user.get("auth_password"):
                    user_kwargs["auth_password"] = user["auth_password"]
                else:
                    self.logger(
                        level="warning",
                        message="No password provided for field 'auth_password' of object snmp.User"
                    )
                if user.get("auth_type"):
                    user_kwargs["auth_type"] = user["auth_type"]
                if user.get("name"):
                    user_kwargs["name"] = user["name"]
                if user.get("privacy_password"):
                    user_kwargs["privacy_password"] = user["privacy_password"]
                else:
                    self.logger(
                        level="warning",
                        message="No password provided for field 'privacy_password' of object snmp.User"
                    )
                if user.get("privacy_type"):
                    user_kwargs["privacy_type"] = user["privacy_type"]
                if user.get("security_level"):
                    user_kwargs["security_level"] = user["security_level"]

                users.append(SnmpUser(**user_kwargs))

            kwargs["snmp_users"] = users

        snmp_policy = SnmpPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=snmp_policy, detail=self.name):
            return False

        return True


class IntersightSshPolicy(IntersightConfigObject):
    _CONFIG_NAME = "SSH Policy"
    _CONFIG_SECTION_NAME = "ssh_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "ssh.Policy"

    def __init__(self, parent=None, ssh_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=ssh_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enabled = self.get_attribute(attribute_name="enabled")
        self.name = self.get_attribute(attribute_name="name")
        self.port = self.get_attribute(attribute_name="port")
        self.timeout = self.get_attribute(attribute_name="timeout")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.ssh_policy import SshPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enabled is not None:
            kwargs["enabled"] = self.enabled
        if self.port is not None:
            kwargs["port"] = self.port
        if self.timeout is not None:
            kwargs["timeout"] = self.timeout

        ssh_policy = SshPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=ssh_policy, detail=self.name):
            return False

        return True


class IntersightStoragePolicy(IntersightConfigObject):
    _CONFIG_NAME = "Storage Policy"
    _CONFIG_SECTION_NAME = "storage_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "storage.StoragePolicy"

    def __init__(self, parent=None, storage_storage_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=storage_storage_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.use_jbod_for_vd_creation = self.get_attribute(attribute_name="use_jbod_for_vd_creation")
        self.unused_disks_state = self.get_attribute(attribute_name="unused_disks_state")
        self.default_drive_state = self.get_attribute(attribute_name="default_drive_mode",
                                                      attribute_secondary_name="default_drive_state")
        self.secure_jbod_disk_slots = self.get_attribute(attribute_name="secure_jbods",
                                                         attribute_secondary_name="secure_jbod_disk_slots")
        self.m2_configuration = None
        self.hybrid_slot_configuration = None
        self.global_hot_spares = self.get_attribute(attribute_name="global_hot_spares")
        self.drive_group = None
        self.single_drive_raid_configuration = None

        if self._config.load_from == "live":
            # Renaming Unused Disk State to be more user-friendly
            self.unused_disks_state = self._format_parameter_values(policy="unused_disks_state",
                                                                    param_value=self.unused_disks_state,
                                                                    param_type="file")
            # Renaming Default Drive State to be more user-friendly
            self.default_drive_state = self._format_parameter_values(policy="default_drive_state",
                                                                     param_value=self.default_drive_state,
                                                                     param_type="file")

            if (getattr(self._object, "direct_attached_nvme_slots", None) or
                    getattr(self._object, "controller_attached_nvme_slots", None)):
                hybrid_slot_configuration = {}
                if getattr(self._object, "direct_attached_nvme_slots", None):
                    hybrid_slot_configuration["direct_attached_nvme_slots"] = self._object.direct_attached_nvme_slots
                if getattr(self._object, "controller_attached_nvme_slots", None):
                    hybrid_slot_configuration["controller_attached_nvme_slots"] = \
                        self._object.controller_attached_nvme_slots
                self.hybrid_slot_configuration = hybrid_slot_configuration

            if hasattr(self._object, "m2_virtual_drive"):
                if self._object.m2_virtual_drive:
                    self.m2_configuration = {
                        "enable": self._object.m2_virtual_drive.enable,
                        "controller_slot": self._object.m2_virtual_drive.controller_slot,
                        "name": self._object.m2_virtual_drive.name if self._object.m2_virtual_drive.name else None
                    }

            if hasattr(self._object, "drive_group"):
                if self._object.drive_group:
                    self.drive_group = []
                    drive_groups = self._get_storage_drive_groups(self._object.drive_group)
                    for drive_group in drive_groups:
                        if drive_group:
                            dg = {
                                "drive_group_name": drive_group.get("name"),
                                "raid_level": (drive_group.get("raid_level")).upper(),
                                "secure_drive_group": drive_group.get("secure_drive_group")
                            }

                            if hasattr(drive_group, "manual_drive_group"):
                                if drive_group.manual_drive_group:
                                    manual_drive_selection = {
                                        "dedicated_hot_spares": drive_group.manual_drive_group.dedicated_hot_spares,
                                        "drive_array_spans": None
                                    }

                                    if hasattr(drive_group.manual_drive_group, "span_groups"):
                                        if drive_group.manual_drive_group.span_groups:
                                            manual_drive_selection["drive_array_spans"] = []
                                            for span_group in drive_group.manual_drive_group.span_groups:
                                                drive_array_span = {
                                                    "slots": span_group.slots
                                                }
                                                manual_drive_selection["drive_array_spans"].append(drive_array_span)

                                    dg["manual_drive_selection"] = manual_drive_selection

                            if hasattr(drive_group, "virtual_drives"):
                                if drive_group.virtual_drives:
                                    virtual_drives = []
                                    for virtual_drive in drive_group.virtual_drives:
                                        vd = {
                                            "vd_name": virtual_drive.name,
                                            "boot_drive": virtual_drive.boot_drive,
                                            "expand_to_available": virtual_drive.expand_to_available,
                                            "size": int(virtual_drive.size)
                                        }

                                        if hasattr(virtual_drive, "virtual_drive_policy"):
                                            if virtual_drive.virtual_drive_policy:
                                                if virtual_drive.virtual_drive_policy.strip_size in [64, 128, 256, 512]:
                                                    vd["strip_size"] = str(
                                                        virtual_drive.virtual_drive_policy.strip_size) + "KiB"
                                                elif virtual_drive.virtual_drive_policy.strip_size in [1024]:
                                                    vd["strip_size"] = str(int(
                                                        virtual_drive.virtual_drive_policy.strip_size / 1024)) + "MiB"
                                                vd["access_policy"] = self._format_parameter_values(
                                                    policy="access_policy",
                                                    param_value=virtual_drive.virtual_drive_policy.access_policy,
                                                    param_type="file")
                                                vd["read_policy"] = self._format_parameter_values(
                                                    policy="read_policy",
                                                    param_value=virtual_drive.virtual_drive_policy.read_policy,
                                                    param_type="file")
                                                vd["write_policy"] = self._format_parameter_values(
                                                    policy="write_policy",
                                                    param_value=virtual_drive.virtual_drive_policy.write_policy,
                                                    param_type="file")
                                                vd["disk_cache"] = self._format_parameter_values(
                                                    policy="drive_cache",
                                                    param_value=virtual_drive.virtual_drive_policy.drive_cache,
                                                    param_type="file")

                                        virtual_drives.append(vd)
                                    dg["virtual_drives"] = virtual_drives
                            self.drive_group.append(dg)

            if hasattr(self._object, "raid0_drive"):
                if self._object.raid0_drive:
                    self.single_drive_raid_configuration = {
                        "enable": self._object.raid0_drive.enable,
                        "drive_slots": self._object.raid0_drive.drive_slots
                    }
                    if hasattr(self._object.raid0_drive, "virtual_drive_policy"):
                        if self._object.raid0_drive.virtual_drive_policy:
                            if self._object.raid0_drive.virtual_drive_policy.strip_size in [64, 128, 256, 512]:
                                self.single_drive_raid_configuration["strip_size"] = str(
                                    self._object.raid0_drive.virtual_drive_policy.strip_size) + "KiB"
                            elif self._object.raid0_drive.virtual_drive_policy.strip_size in [1024]:
                                self.single_drive_raid_configuration["strip_size"] = str(
                                    int(self._object.raid0_drive.virtual_drive_policy.strip_size/1024)) + "MiB"
                            self.single_drive_raid_configuration["access_policy"] = self._format_parameter_values(
                                policy="access_policy",
                                param_value=self._object.raid0_drive.virtual_drive_policy.access_policy,
                                param_type="file")
                            self.single_drive_raid_configuration["read_policy"] = self._format_parameter_values(
                                policy="read_policy",
                                param_value=self._object.raid0_drive.virtual_drive_policy.read_policy,
                                param_type="file")
                            self.single_drive_raid_configuration["write_policy"] = self._format_parameter_values(
                                policy="write_policy",
                                param_value=self._object.raid0_drive.virtual_drive_policy.write_policy,
                                param_type="file")
                            self.single_drive_raid_configuration["disk_cache"] = self._format_parameter_values(
                                policy="drive_cache",
                                param_value=self._object.raid0_drive.virtual_drive_policy.drive_cache,
                                param_type="file")

        elif self._config.load_from == "file":
            for attribute in ["drive_group", "hybrid_slot_configuration", "m2_configuration",
                              "single_drive_raid_configuration"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # Attribute "raid_attached_nvme_slots" is now deprecated in favor of "controller_attached_nvme_slots"
            if self.hybrid_slot_configuration:
                if self.hybrid_slot_configuration.get("raid_attached_nvme_slots"):
                    self.hybrid_slot_configuration["controller_attached_nvme_slots"] = \
                        self.hybrid_slot_configuration.get("raid_attached_nvme_slots")

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all attributes of M.2 Virtual Drive are set to None
        # if they are not present

        if self.hybrid_slot_configuration:
            for hsc_attribute in ["controller_attached_nvme_slots", "direct_attached_nvme_slots",
                                  "raid_attached_nvme_slots"]:
                if hsc_attribute not in self.hybrid_slot_configuration:
                    self.hybrid_slot_configuration[hsc_attribute] = None

        if self.m2_configuration:
            for m2_attribute in ["controller_slot", "enable", "name"]:
                if m2_attribute not in self.m2_configuration:
                    self.m2_configuration[m2_attribute] = None

        if self.drive_group:
            for drive_group in self.drive_group:
                for dg_attribute in ["drive_group_name", "raid_level", "manual_drive_selection", "secure_drive_group",
                                     "virtual_drives"]:
                    if dg_attribute not in drive_group:
                        drive_group[dg_attribute] = None

                    if drive_group.get("manual_drive_selection"):
                        for mds_attribute in ["dedicated_hot_spares", "drive_array_spans"]:
                            if mds_attribute not in drive_group["manual_drive_selection"]:
                                drive_group["manual_drive_selection"][mds_attribute] = None

                            if drive_group["manual_drive_selection"].get("drive_array_spans"):
                                for drive_array_span in drive_group["manual_drive_selection"]["drive_array_spans"]:
                                    for das_attribute in ["slots"]:
                                        if das_attribute not in drive_array_span:
                                            drive_array_span[das_attribute] = None

                    if drive_group.get("virtual_drives"):
                        for virtual_drive in drive_group["virtual_drives"]:
                            for vd_attribute in ["vd_name", "size", "strip_size", "access_policy", "read_policy",
                                                 "write_policy", "disk_cache"]:
                                if vd_attribute not in virtual_drive:
                                    virtual_drive[vd_attribute] = None

        if self.single_drive_raid_configuration:
            for sdrc_attribute in ["drive_slots", "strip_size", "access_policy", "read_policy", "write_policy",
                                   "disk_cache"]:
                if sdrc_attribute not in self.single_drive_raid_configuration:
                    self.single_drive_raid_configuration[sdrc_attribute] = None

    @staticmethod
    def _format_parameter_values(policy=None, param_value=None, param_type="file"):
        """Formats the Parameter value to be more user-friendly and readable in JSON
        Args:
            param_value ([int, str]): Attribute values of an Object
            param_type (["file", "live"]): Type of parameter expected. "file" returns
            user-friendly parameter value whereas "live" returns SDK compatible
            parameter value.
        Returns:
            Returns user-friendly or SDK compatible parameter value based on parameter type
        """
        unused_disks_state_dict = {
            "No Change": "NoChange",
            "Unconfigured Good": "UnconfiguredGood",
            "JBOD": "Jbod"
        }
        default_drive_state_dict = {
            "RAID0": "RAID0",
            "Unconfigured Good": "UnconfiguredGood",
            "JBOD": "Jbod"
        }
        access_policy_dict = {
            "Default": "Default",
            "Read Write": "ReadWrite",
            "Read Only": "ReadOnly",
            "Blocked": "Blocked"
        }
        drive_cache_dict = {
            "Default": "Default",
            "Unchanged": "NoChange",
            "Enabled": "Enable",
            "Disabled": "Disable"
        }
        read_policy_dict = {
            "Default": "Default",
            "Always Read Ahead": "ReadAhead",
            "No Read Ahead": "NoReadAhead"
        }
        write_policy_dict = {
            "Default": "Default",
            "Write Through": "WriteThrough",
            "Write Back Good BBU": "WriteBackGoodBbu",
            "Always Write Back": "AlwaysWriteBack"
        }

        param_dict = {}
        if policy == "unused_disks_state":
            param_dict = unused_disks_state_dict
        elif policy == "default_drive_state":
            param_dict = default_drive_state_dict
        elif policy == "access_policy":
            param_dict = access_policy_dict
        elif policy == "drive_cache":
            param_dict = drive_cache_dict
        elif policy == "read_policy":
            param_dict = read_policy_dict
        elif policy == "write_policy":
            param_dict = write_policy_dict

        if param_type == "live":
            return param_dict.get(param_value)
        elif param_type == "file":
            return next((live for live, file in param_dict.items() if file == param_value), None)

    def _get_storage_drive_groups(self, drive_group_refs):
        """This function returns the list of Drive Groups associated with a Storage Policy
        Args:
            drive_group_refs (drive_group_objects): Drive Group Objects
        Returns:
            drive_groups [list]: Returns the list of Drive Groups associated with a Storage Policy
        """
        if not drive_group_refs:
            self.logger(level="error", message="Missing Drive group Reference objects")
            return []
        drive_groups = self.get_config_objects_from_ref(ref=drive_group_refs)
        if not drive_groups:
            self.logger(level="debug", message=f"Could not find the appropriate {str(drive_group_refs[0].object_type)}"
                                               f"(s) for storage.StoragePolicy with MOID {str(self._object.moid)}")
        # We return all the attributes of the matching Storage Drive Groups
        return drive_groups

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.storage_storage_policy import StorageStoragePolicy
        import re

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.use_jbod_for_vd_creation is not None:
            kwargs["use_jbod_for_vd_creation"] = self.use_jbod_for_vd_creation
        if self.unused_disks_state is not None:
            kwargs["unused_disks_state"] = self._format_parameter_values(policy="unused_disks_state",
                                                                         param_value=self.unused_disks_state,
                                                                         param_type="live")
        if self.default_drive_state is not None:
            kwargs["default_drive_mode"] = self._format_parameter_values(policy="default_drive_state",
                                                                         param_value=self.default_drive_state,
                                                                         param_type="live")
        if self.secure_jbod_disk_slots is not None:
            kwargs["secure_jbods"] = self.secure_jbod_disk_slots
        if self.global_hot_spares is not None:
            kwargs["global_hot_spares"] = self.global_hot_spares

        if self.hybrid_slot_configuration:
            if self.hybrid_slot_configuration.get("direct_attached_nvme_slots"):
                kwargs["direct_attached_nvme_slots"] = self.hybrid_slot_configuration.get("direct_attached_nvme_slots")
            if self.hybrid_slot_configuration.get("controller_attached_nvme_slots"):
                kwargs["controller_attached_nvme_slots"] = \
                    self.hybrid_slot_configuration.get("controller_attached_nvme_slots")

        if self.m2_configuration is not None and self.m2_configuration.get("enable"):
            from intersight.model.storage_m2_virtual_drive_config import StorageM2VirtualDriveConfig
            m2_configuration_kwargs = {
                "object_type": "storage.M2VirtualDriveConfig",
                "class_id": "storage.M2VirtualDriveConfig",
            }
            if self.m2_configuration.get("enable"):
                m2_configuration_kwargs["enable"] = self.m2_configuration["enable"]
            if self.m2_configuration.get("controller_slot"):
                m2_configuration_kwargs["controller_slot"] = self.m2_configuration["controller_slot"]
            if self.m2_configuration.get("name"):
                m2_configuration_kwargs["name"] = self.m2_configuration["name"]
            kwargs["m2_virtual_drive"] = StorageM2VirtualDriveConfig(**m2_configuration_kwargs)
        if self.single_drive_raid_configuration is not None and self.single_drive_raid_configuration.get("enable"):
            from intersight.model.storage_r0_drive import StorageR0Drive
            storage_r0_drive_kwargs = {
                "object_type": "storage.R0Drive",
                "class_id": "storage.R0Drive",
            }
            if self.single_drive_raid_configuration.get("drive_slots"):
                storage_r0_drive_kwargs["drive_slots"] = self.single_drive_raid_configuration["drive_slots"]
            if self.single_drive_raid_configuration.get("enable"):
                storage_r0_drive_kwargs["enable"] = self.single_drive_raid_configuration["enable"]
            if self.single_drive_raid_configuration.get("strip_size"):
                from intersight.model.storage_virtual_drive_policy import StorageVirtualDrivePolicy
                virtual_drive_policy_kwargs = {
                    "object_type": "storage.VirtualDrivePolicy",
                    "class_id": "storage.VirtualDrivePolicy",
                }
                if self.single_drive_raid_configuration["strip_size"] in ["64KiB", "128KiB", "256KiB", "512KiB"]:
                    virtual_drive_policy_kwargs["strip_size"] = int(
                        re.findall(r'[0-9]+', self.single_drive_raid_configuration["strip_size"])[0])
                elif self.single_drive_raid_configuration["strip_size"] in ["1MiB"]:
                    virtual_drive_policy_kwargs["strip_size"] = int(
                        re.findall(r'[0-9]+', self.single_drive_raid_configuration["strip_size"])[0]) * 1024

                if self.single_drive_raid_configuration.get("access_policy"):
                    virtual_drive_policy_kwargs["access_policy"] = self._format_parameter_values(
                        policy="access_policy",
                        param_value=self.single_drive_raid_configuration["access_policy"], param_type="live")
                if self.single_drive_raid_configuration.get("read_policy"):
                    virtual_drive_policy_kwargs["read_policy"] = self._format_parameter_values(
                        policy="read_policy",
                        param_value=self.single_drive_raid_configuration["read_policy"], param_type="live")
                if self.single_drive_raid_configuration.get("write_policy"):
                    virtual_drive_policy_kwargs["write_policy"] = self._format_parameter_values(
                        policy="write_policy",
                        param_value=self.single_drive_raid_configuration["write_policy"], param_type="live")
                if self.single_drive_raid_configuration.get("disk_cache"):
                    virtual_drive_policy_kwargs["drive_cache"] = self._format_parameter_values(
                        policy="drive_cache",
                        param_value=self.single_drive_raid_configuration["disk_cache"], param_type="live")
                storage_r0_drive_kwargs["virtual_drive_policy"] = \
                    StorageVirtualDrivePolicy(**virtual_drive_policy_kwargs)

            kwargs["raid0_drive"] = StorageR0Drive(**storage_r0_drive_kwargs)

        storage_storage_policy = StorageStoragePolicy(**kwargs)
        storage_storage_policy_obj = self.commit(
            object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
            payload=storage_storage_policy,
            detail=self.name,
            return_relationship=True
        )
        if not storage_storage_policy_obj:
            return False

        if self.drive_group is not None:
            from intersight.model.storage_drive_group import StorageDriveGroup
            for drive_group in self.drive_group:
                drive_group_kwargs = {
                    "object_type": "storage.DriveGroup",
                    "class_id": "storage.DriveGroup",
                    "name": drive_group.get("drive_group_name"),
                    "storage_policy": storage_storage_policy_obj
                }
                if drive_group.get("raid_level"):
                    drive_group_kwargs["raid_level"] = (drive_group["raid_level"]).capitalize()
                if drive_group.get("secure_drive_group"):
                    drive_group_kwargs["secure_drive_group"] = drive_group["secure_drive_group"]
                # ToDo - Only Manual method is currently supported. Automated method needs to be added
                if drive_group.get("manual_drive_selection"):
                    # 0 for Manual and 1 for Automated (Intersight SDK has 0 as default value)
                    # drive_group_kwargs["type"] = 0
                    from intersight.model.storage_manual_drive_group import StorageManualDriveGroup
                    manual_dg_kwargs = {
                        "object_type": "storage.ManualDriveGroup",
                        "class_id": "storage.ManualDriveGroup",
                    }
                    if drive_group["manual_drive_selection"].get("dedicated_hot_spares"):
                        manual_dg_kwargs["dedicated_hot_spares"] = drive_group["manual_drive_selection"][
                            "dedicated_hot_spares"]
                    if drive_group["manual_drive_selection"].get("drive_array_spans"):
                        from intersight.model.storage_span_drives import StorageSpanDrives
                        drive_array_spans = []
                        for drive_array_span in drive_group["manual_drive_selection"]["drive_array_spans"]:
                            drive_array_span_kwargs = {
                                "object_type": "storage.SpanDrives",
                                "class_id": "storage.SpanDrives",
                            }
                            if drive_array_span.get("slots"):
                                drive_array_span_kwargs["slots"] = drive_array_span["slots"]

                            drive_array_spans.append(StorageSpanDrives(**drive_array_span_kwargs))

                        manual_dg_kwargs["span_groups"] = drive_array_spans

                    drive_group_kwargs["manual_drive_group"] = StorageManualDriveGroup(**manual_dg_kwargs)
                if drive_group.get("virtual_drives"):
                    from intersight.model.storage_virtual_drive_configuration import StorageVirtualDriveConfiguration
                    virtual_drives = []
                    for virtual_drive in drive_group["virtual_drives"]:
                        virtual_drive_kwargs = {
                            "object_type": "storage.VirtualDriveConfiguration",
                            "class_id": "storage.VirtualDriveConfiguration",
                        }
                        if virtual_drive.get("vd_name"):
                            virtual_drive_kwargs["name"] = virtual_drive["vd_name"]
                        if virtual_drive.get("boot_drive"):
                            virtual_drive_kwargs["boot_drive"] = virtual_drive["boot_drive"]
                        if virtual_drive.get("expand_to_available"):
                            virtual_drive_kwargs["expand_to_available"] = virtual_drive["expand_to_available"]
                        if virtual_drive.get("size"):
                            virtual_drive_kwargs["size"] = virtual_drive["size"]
                        if virtual_drive.get("strip_size"):
                            from intersight.model.storage_virtual_drive_policy import StorageVirtualDrivePolicy
                            virtual_drive_policy_kwargs = {
                                "object_type": "storage.VirtualDrivePolicy",
                                "class_id": "storage.VirtualDrivePolicy",
                            }
                            if virtual_drive["strip_size"] in ["64KiB", "128KiB", "256KiB", "512KiB"]:
                                virtual_drive_policy_kwargs["strip_size"] = int(
                                    re.findall(r'[0-9]+', virtual_drive["strip_size"])[0])
                            elif virtual_drive["strip_size"] in ["1MiB"]:
                                virtual_drive_policy_kwargs["strip_size"] = int(
                                    re.findall(r'[0-9]+', virtual_drive["strip_size"])[0]) * 1024

                            if virtual_drive.get("access_policy"):
                                virtual_drive_policy_kwargs["access_policy"] = self._format_parameter_values(
                                    policy="access_policy",
                                    param_value=virtual_drive["access_policy"],
                                    param_type="live"
                                )
                            if virtual_drive.get("read_policy"):
                                virtual_drive_policy_kwargs["read_policy"] = self._format_parameter_values(
                                    policy="read_policy",
                                    param_value=virtual_drive["read_policy"],
                                    param_type="live"
                                )
                            if virtual_drive.get("write_policy"):
                                virtual_drive_policy_kwargs["write_policy"] = self._format_parameter_values(
                                    policy="write_policy",
                                    param_value=virtual_drive["write_policy"],
                                    param_type="live"
                                )
                            if virtual_drive.get("disk_cache"):
                                virtual_drive_policy_kwargs["drive_cache"] = self._format_parameter_values(
                                    policy="drive_cache",
                                    param_value=virtual_drive["disk_cache"],
                                    param_type="live"
                                )

                            virtual_drive_kwargs["virtual_drive_policy"] = StorageVirtualDrivePolicy(
                                **virtual_drive_policy_kwargs)

                        virtual_drives.append(StorageVirtualDriveConfiguration(**virtual_drive_kwargs))

                    drive_group_kwargs["virtual_drives"] = virtual_drives
                storage_drive_group_policy = StorageDriveGroup(**drive_group_kwargs)

                self.commit(object_type="storage.DriveGroup", payload=storage_drive_group_policy,
                            detail=self.name + " - Drive Group " + str(drive_group_kwargs["name"]),
                            key_attributes=["name", "storage_storage_policy"])

        return True


class IntersightSyslogPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Syslog Policy"
    _CONFIG_SECTION_NAME = "syslog_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "syslog.Policy"

    def __init__(self, parent=None, syslog_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=syslog_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.local_logging = None
        self.name = self.get_attribute(attribute_name="name")
        self.remote_logging = None

        if self._config.load_from == "live":
            if hasattr(self._object, "local_clients"):
                if self._object.local_clients:
                    if len(self._object.local_clients) == 1:
                        self.local_logging = {"file": {"min_severity": self._object.local_clients[0].min_severity}}

            if hasattr(self._object, "remote_clients"):
                if self._object.remote_clients:
                    self.remote_logging = {}
                    counter = 1
                    for remote_client in self._object.remote_clients:
                        syslog_server = "server" + str(counter)
                        self.remote_logging[syslog_server] = {"enable": remote_client.enabled,
                                                              "hostname": remote_client.hostname,
                                                              "port": remote_client.port,
                                                              "protocol": remote_client.protocol,
                                                              "min_severity": remote_client.min_severity}
                        counter += 1

        elif self._config.load_from == "file":
            for attribute in ["local_logging", "remote_logging"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # We use this to make sure all options of Local Logging are set to None if they are not present
            if self.local_logging:
                for attribute in ["file"]:
                    if attribute not in self.local_logging:
                        self.local_logging[attribute] = None
                    else:
                        for sub_attribute in ["min_severity"]:
                            if sub_attribute not in self.local_logging[attribute]:
                                self.local_logging[attribute][sub_attribute] = None

            # We use this to make sure all options of Remote Logging are set to None if they are not present
            if self.remote_logging:
                for attribute in ["server1", "server2"]:
                    if attribute not in self.remote_logging:
                        self.remote_logging[attribute] = None
                    else:
                        for sub_attribute in ["enable", "hostname", "port", "protocol", "min_severity"]:
                            if sub_attribute not in self.remote_logging[attribute]:
                                self.remote_logging[attribute][sub_attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.syslog_policy import SyslogPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        if self.local_logging is not None:
            if "file" in self.local_logging:
                from intersight.model.syslog_local_file_logging_client import SyslogLocalFileLoggingClient

                local_logging_kwargs = {
                    "object_type": "syslog.LocalFileLoggingClient",
                    "class_id": "syslog.LocalFileLoggingClient",
                }
                if self.local_logging["file"]["min_severity"] is not None:
                    local_logging_kwargs["min_severity"] = self.local_logging["file"]["min_severity"]
                kwargs["local_clients"] = [SyslogLocalFileLoggingClient(**local_logging_kwargs)]

        if self.remote_logging is not None:
            from intersight.model.syslog_remote_logging_client import SyslogRemoteLoggingClient

            remote_clients = []
            for server in ["server1", "server2"]:
                if self.remote_logging.get(server, None) is not None:
                    remote_logging_kwargs = {
                        "object_type": "syslog.RemoteLoggingClient",
                        "class_id": "syslog.RemoteLoggingClient",
                    }
                    if self.remote_logging[server].get("enable", None) is not None:
                        remote_logging_kwargs["enabled"] = self.remote_logging[server]["enable"]
                    if self.remote_logging[server].get("hostname", None) is not None:
                        remote_logging_kwargs["hostname"] = self.remote_logging[server]["hostname"]
                    if self.remote_logging[server].get("port", None) is not None:
                        remote_logging_kwargs["port"] = self.remote_logging[server]["port"]
                    if self.remote_logging[server].get("protocol", None) is not None:
                        remote_logging_kwargs["protocol"] = self.remote_logging[server]["protocol"]
                    if self.remote_logging[server].get("min_severity", None) is not None:
                        remote_logging_kwargs["min_severity"] = self.remote_logging[server]["min_severity"]
                    remote_clients.append(SyslogRemoteLoggingClient(**remote_logging_kwargs))

            if len(remote_clients) != 0:
                kwargs["remote_clients"] = remote_clients

        syslog_policy = SyslogPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=syslog_policy, detail=self.name):
            return False

        return True


class IntersightThermalPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Thermal Policy"
    _CONFIG_SECTION_NAME = "thermal_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "thermal.Policy"

    def __init__(self, parent=None, thermal_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=thermal_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.fan_control_mode = self.get_attribute(attribute_name="fan_control_mode")

        if self._config.load_from == "live":
            self.fan_control_mode = self._get_fan_control_mode(mode=self.fan_control_mode, mode_type="file")

    @staticmethod
    def _get_fan_control_mode(mode="Balanced", mode_type="live"):
        mode_dict = {
            "Balanced": "Balanced",
            "LowPower": "Low Power",
            "HighPower": "High Power",
            "MaximumCooling": "Maximum Cooling",
            "MaximumPower": "Maximum Power",
            "Acoustic": "Acoustic"
        }

        if mode_type == "file":
            return mode_dict.get(mode)
        elif mode_type == "live":
            return next((live for live, file in mode_dict.items() if file == mode), None)

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.thermal_policy import ThermalPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.fan_control_mode is not None:
            kwargs["fan_control_mode"] = self._get_fan_control_mode(mode=self.fan_control_mode)

        thermal_policy = ThermalPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=thermal_policy, detail=self.name):
            return False

        return True


class IntersightVirtualKvmPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Virtual KVM Policy"
    _CONFIG_SECTION_NAME = "virtual_kvm_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "kvm.Policy"

    def __init__(self, parent=None, kvm_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=kvm_policy)

        self.allow_tunneled_vkvm = self.get_attribute(attribute_name="tunneled_kvm_enabled",
                                                      attribute_secondary_name="allow_tunneled_vkvm")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_local_server_video = self.get_attribute(attribute_name="enable_local_server_video")
        self.enable_video_encryption = self.get_attribute(attribute_name="enable_video_encryption")
        self.enable_virtual_kvm = self.get_attribute(attribute_name="enabled",
                                                     attribute_secondary_name="enable_virtual_kvm")
        self.max_sessions = self.get_attribute(attribute_name="maximum_sessions",
                                               attribute_secondary_name="max_sessions")
        self.name = self.get_attribute(attribute_name="name")
        self.remote_port = self.get_attribute(attribute_name="remote_port")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.kvm_policy import KvmPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enable_virtual_kvm is not None:
            kwargs["enabled"] = self.enable_virtual_kvm
        if self.remote_port is not None:
            kwargs["remote_port"] = self.remote_port
        if self.max_sessions is not None:
            kwargs["maximum_sessions"] = self.max_sessions
        if self.enable_video_encryption is not None:
            kwargs["enable_video_encryption"] = self.enable_video_encryption
        if self.enable_local_server_video is not None:
            kwargs["enable_local_server_video"] = self.enable_local_server_video

        kvm_policy = KvmPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=kvm_policy, detail=self.name):
            return False

        return True


class IntersightVirtualMediaPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Virtual Media Policy"
    _CONFIG_SECTION_NAME = "virtual_media_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "vmedia.Policy"

    def __init__(self, parent=None, vmedia_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=vmedia_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_low_power_usb = self.get_attribute(attribute_name="low_power_usb",
                                                       attribute_secondary_name="enable_low_power_usb")
        self.enable_virtual_media = self.get_attribute(attribute_name="enabled",
                                                       attribute_secondary_name="enable_virtual_media")
        self.enable_virtual_media_encryption = \
            self.get_attribute(attribute_name="encryption",
                               attribute_secondary_name="enable_virtual_media_encryption")
        self.name = self.get_attribute(attribute_name="name")
        self.vmedia_mounts = None

        if self._config.load_from == "live":
            if hasattr(self._object, "mappings"):
                if self._object.mappings:
                    self.vmedia_mounts = []
                    for mapping in self._object.mappings:
                        vmedia_mount = {
                            "name": mapping.volume_name,
                            "device_type": mapping.device_type,
                            "protocol": mapping.mount_protocol,
                            "file_location": mapping.file_location
                        }
                        if mapping.mount_options:
                            vmedia_mount["mount_options"] = mapping.mount_options
                        if mapping.username:
                            vmedia_mount["username"] = mapping.username
                        if mapping.is_password_set:
                            self.logger(level="warning",
                                        message="Password of " + self._CONFIG_NAME + " '" + self.name +
                                                "' - vMedia Mount '" + mapping.volume_name + "' can't be exported")
                        if mapping.mount_protocol in ["cifs"]:
                            if mapping.authentication_protocol:
                                vmedia_mount["authentication_protocol"] = mapping.authentication_protocol
                        self.vmedia_mounts.append(vmedia_mount)

        elif self._config.load_from == "file":
            for attribute in ["vmedia_mounts"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a vMedia Mount are set to None if they are not present
        if self.vmedia_mounts:
            for vmedia_mount in self.vmedia_mounts:
                for attribute in ["authentication_protocol", "device_type", "file_location", "hostname",
                                  "mount_options", "name", "password", "protocol", "remote_file", "remote_path",
                                  "username"]:
                    if attribute not in vmedia_mount:
                        vmedia_mount[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vmedia_policy import VmediaPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enable_virtual_media is not None:
            kwargs["enabled"] = self.enable_virtual_media
        if self.enable_virtual_media_encryption is not None:
            kwargs["encryption"] = self.enable_virtual_media_encryption
        if self.enable_low_power_usb is not None:
            kwargs["low_power_usb"] = self.enable_low_power_usb

        if self.vmedia_mounts is not None:
            from intersight.model.vmedia_mapping import VmediaMapping
            kwargs["mappings"] = []
            for vmedia_mount in self.vmedia_mounts:
                kwargs_vmedia_mount = {
                    "object_type": "vmedia.Mapping",
                    "class_id": "vmedia.Mapping"
                }
                if vmedia_mount["name"] is not None:
                    kwargs_vmedia_mount["volume_name"] = vmedia_mount["name"]
                if vmedia_mount["device_type"] is not None:
                    kwargs_vmedia_mount["device_type"] = vmedia_mount["device_type"]
                if vmedia_mount["protocol"] is not None:
                    kwargs_vmedia_mount["mount_protocol"] = vmedia_mount["protocol"]
                if vmedia_mount["file_location"] is not None:
                    kwargs_vmedia_mount["file_location"] = vmedia_mount["file_location"]
                else:
                    if vmedia_mount["hostname"] is not None:
                        kwargs_vmedia_mount["host_name"] = vmedia_mount["hostname"]
                    if vmedia_mount["remote_file"] is not None:
                        kwargs_vmedia_mount["remote_file"] = vmedia_mount["remote_file"]
                    if vmedia_mount["remote_path"] is not None:
                        kwargs_vmedia_mount["remote_path"] = vmedia_mount["remote_path"]
                if vmedia_mount["mount_options"] is not None:
                    kwargs_vmedia_mount["mount_options"] = vmedia_mount["mount_options"]
                if vmedia_mount["username"] is not None:
                    kwargs_vmedia_mount["username"] = vmedia_mount["username"]
                if vmedia_mount.get("password") is not None:
                    kwargs_vmedia_mount["password"] = vmedia_mount["password"]
                elif vmedia_mount.get("username") is not None:
                    self.logger(
                        level="warning",
                        message="No password provided for field 'password' of object vmedia.Mapping"
                    )
                if vmedia_mount["authentication_protocol"] is not None:
                    kwargs_vmedia_mount["authentication_protocol"] = vmedia_mount["authentication_protocol"]

                kwargs["mappings"].append(VmediaMapping(**kwargs_vmedia_mount))

        vmedia_policy = VmediaPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=vmedia_policy, detail=self.name):
            return False

        return True


class IntersightMemoryPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Memory Policy"
    _CONFIG_SECTION_NAME = "memory_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "memory.Policy"

    def __init__(self, parent=None, memory_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=memory_policy)

        self.name = self.get_attribute(attribute_name="name")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_dimm_blocklisting = self.get_attribute(attribute_name="enable_dimm_blocklisting")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.memory_policy import MemoryPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enable_dimm_blocklisting is not None:
            kwargs["enable_dimm_blocklisting"] = self.enable_dimm_blocklisting

        memory_policy = MemoryPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=memory_policy,
                           detail=self.name):
            return False

        return True
