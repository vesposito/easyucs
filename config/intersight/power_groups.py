# coding: utf-8
# !/usr/bin/env python

""" power_groups.py: Easy UCS Deployment Tool """

import math
from config.intersight.object import IntersightConfigObject


class IntersightPowerGroup(IntersightConfigObject):
    _CONFIG_NAME = "Power Group"
    _CONFIG_SECTION_NAME = "power_groups"
    _INTERSIGHT_SDK_OBJECT_NAME = "power.PowerGroup"

    # Attribute name used to cache capability.NetworkEquipmentPowerDef objects directly on the Intersight device
    # object (indexed by (device_type, pid)). This static reference data is queried once per device and reused
    # across all Power Groups being pushed, instead of issuing one filtered query per FI/FEX member. We store it
    # on the device instance (rather than as a class attribute keyed by device uuid) so its lifetime follows the
    # device object instead of the whole process - once the device is garbage collected/reconnected, the cache
    # naturally goes away with it instead of persisting (and potentially growing stale) for the process lifetime.
    _CAPABILITY_POWER_DEF_CACHE_ATTR = "_capability_power_def_cache"

    def __init__(self, parent=None, power_power_group=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=power_power_group)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.admin_state = self.get_attribute(attribute_name="admin_state")
        self.power_group_budget = self.get_attribute(attribute_name="power_budget",
                                                     attribute_secondary_name="power_group_budget")
        self.power_group_devices = None

        if self._config.load_from == "live":
            self._get_power_group_devices()

        elif self._config.load_from == "file":
            for attribute in ["power_group_devices"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def _get_power_group_devices(self):
        # Get the devices belonging to this Power Group, grouped by device type
        # We read the power_power_group_member objects to find members that reference this Power Group
        power_group_moid = getattr(self._object, "moid", None)

        for member in self._config.sdk_objects.get("power_power_group_member", []):
            power_group_parent = getattr(member, "power_group_parent", None)
            if getattr(power_group_parent, "moid", None) != power_group_moid:
                continue

            if self.power_group_devices is None:
                self.power_group_devices = {
                    "chassis": [],
                    "fabric_interconnects": [],
                    "fabric_extenders": [],
                }

            member_type = getattr(member, "member_type", None)
            inventory_device_ref = getattr(member, "inventory_device", None)
            inventory_device_moid = getattr(inventory_device_ref, "moid", None) if inventory_device_ref else None

            if member_type == "Chassis":
                serial = name = None
                # We need to retrieve the equipment.Chassis object to get the serial and name
                if "equipment_chassis" in self._config.sdk_objects:
                    for sdk_obj in self._config.sdk_objects["equipment_chassis"]:
                        if getattr(sdk_obj, "moid", None) == inventory_device_moid:
                            serial = getattr(sdk_obj, "serial", None)
                            name = getattr(sdk_obj, "name", None)
                            break
                self.power_group_devices["chassis"].append({"serial": serial, "name": name})

            elif member_type == "FabricInterconnect":
                serial = switch_id = None
                # We need to retrieve the network.Element object to get the serial and switch_id
                if "network_element" in self._config.sdk_objects:
                    for sdk_obj in self._config.sdk_objects["network_element"]:
                        if getattr(sdk_obj, "moid", None) == inventory_device_moid:
                            serial = getattr(sdk_obj, "serial", None)
                            switch_id = getattr(sdk_obj, "switch_id", None)
                            break
                self.power_group_devices["fabric_interconnects"].append(
                    {"serial": serial, "switch_id": switch_id})

            elif member_type == "Fex":
                serial = connection_path = None
                # We need to retrieve the equipment.Fex object to get the serial and connection_path
                if "equipment_fex" in self._config.sdk_objects:
                    for sdk_obj in self._config.sdk_objects["equipment_fex"]:
                        if getattr(sdk_obj, "moid", None) == inventory_device_moid:
                            serial = getattr(sdk_obj, "serial", None)
                            connection_path = getattr(sdk_obj, "connection_path", None)
                            break
                self.power_group_devices["fabric_extenders"].append(
                    {"serial": serial, "connection_path": connection_path})

    def clean_object(self):
        # We use this to make sure all options of a Power Group Device are set to None if not present
        if self.power_group_devices:
            for attribute in ["chassis", "fabric_interconnects", "fabric_extenders"]:
                if attribute not in self.power_group_devices:
                    self.power_group_devices[attribute] = []

            # We use this to make sure all options of a chassis are set to None if not present
            for chassis in self.power_group_devices.get("chassis", []):
                for attribute in ["serial", "name"]:
                    if attribute not in chassis:
                        chassis[attribute] = None

            # We use this to make sure all options of a fabric interconnect are set to None if not present
            for fi in self.power_group_devices.get("fabric_interconnects", []):
                for attribute in ["serial", "switch_id"]:
                    if attribute not in fi:
                        fi[attribute] = None

            # We use this to make sure all options of a fabric extender are set to None if not present
            for fex in self.power_group_devices.get("fabric_extenders", []):
                for attribute in ["serial", "connection_path"]:
                    if attribute not in fex:
                        fex[attribute] = None

    def _get_network_equipment_power_defs(self, device):
        """
        Returns a dict of all capability.NetworkEquipmentPowerDef objects known by Intersight, indexed by
        (device_type, pid). This static reference data is queried once (unfiltered) per device and then cached
        on the device object itself (shared by all Power Group instances using that device), instead of
        issuing a separate filtered query for every FI/FEX member of every Power Group being pushed.
        :param device: The Intersight device used to query the objects
        :return: dict of capability.NetworkEquipmentPowerDef objects indexed by (device_type, pid) tuple
        """
        cache = getattr(device, self._CAPABILITY_POWER_DEF_CACHE_ATTR, None)
        if not cache:
            # We only cache a non-empty result. device.query() swallows API errors (after an internal retry)
            # and returns [] the same way it would for a device that genuinely has no capability data, so a
            # transient failure is indistinguishable from "no results". Caching an empty result here would
            # turn that transient failure into a permanent empty cache entry for the lifetime of the device
            # object, silently skipping live budget validation for every subsequent Power Group push involving
            # this device. Not caching empty results means the next lookup simply retries the query instead.
            capability_list = device.query(object_type="capability.NetworkEquipmentPowerDef")
            if not capability_list:
                return {}
            cache = {
                (getattr(capability, "device_type", None), getattr(capability, "pid", None)): capability
                for capability in capability_list
            }
            setattr(device, self._CAPABILITY_POWER_DEF_CACHE_ATTR, cache)
        return cache

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.power_power_group import PowerPowerGroup

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.admin_state is not None:
            kwargs["admin_state"] = self.admin_state
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        inventory_device_members = []
        chassis_min_required_power_total = 0
        fi_fex_typical_power_total = 0
        live_data_complete = True

        # We use a mapping of device types to their SDK object type
        device_type_map = {
            "chassis":              "equipment.Chassis",
            "fabric_interconnects": "network.Element",
            "fabric_extenders":     "equipment.Fex",
        }
        # Maps each FI/FEX devices_key to the DeviceType value expected by capability.NetworkEquipmentPowerDef
        capability_device_type_map = {
            "fabric_interconnects": "FabricInterconnect",
            "fabric_extenders":     "Fex",
        }

        if self.power_group_devices is not None:
            for devices_key, object_type in device_type_map.items():
                for device in self.power_group_devices.get(devices_key, []):
                    serial = device.get("serial")
                    if serial:
                        # We need to retrieve the device object to get its moid for the relationship
                        device_list = self._device.query(object_type=object_type,
                                                         filter="Serial eq '%s'" % serial)
                        if len(device_list) == 1:
                            inventory_device_members.append(
                                self.create_relationship_equivalent(sdk_object=device_list[0]))

                            if devices_key == "chassis":
                                # We query the live power.ControlState object of this chassis in Intersight to
                                # get its actual MinRequiredPower, instead of relying on the value reported by
                                # UCSM at conversion time
                                chassis_moid = getattr(device_list[0], "moid", None)
                                if chassis_moid:
                                    control_state_list = self._device.query(
                                        object_type="power.ControlState",
                                        filter=f"Parent.Moid eq '{chassis_moid}'")
                                    if control_state_list:
                                        min_required_power = getattr(
                                            control_state_list[0], "min_required_power", None)
                                        if min_required_power is not None:
                                            chassis_min_required_power_total += int(min_required_power)
                                        else:
                                            live_data_complete = False
                                            self.logger(
                                                level="warning",
                                                message=f"Could not find MinRequiredPower value in live "
                                                        f"power.ControlState object for Chassis with serial "
                                                        f"'{serial}' - unable to validate minimum power "
                                                        f"requirement for this device in {self._CONFIG_NAME} "
                                                        f"'{self.name}'")
                                    else:
                                        live_data_complete = False
                                        self.logger(
                                            level="warning",
                                            message=f"Could not find live power.ControlState object for "
                                                    f"Chassis with serial '{serial}' - unable to validate "
                                                    f"minimum power requirement for this device in "
                                                    f"{self._CONFIG_NAME} '{self.name}'")
                                else:
                                    live_data_complete = False
                                    self.logger(
                                        level="warning",
                                        message=f"Could not find Moid for Chassis with serial '{serial}' - "
                                                f"unable to validate minimum power requirement for "
                                                f"this device in {self._CONFIG_NAME} '{self.name}'")

                            elif devices_key in capability_device_type_map:
                                # We look up the (cached) static capability.NetworkEquipmentPowerDef object
                                # matching this device's PID to get its TypicalPower (used as an approximation
                                # of the minimum power Intersight expects for this FI/FEX)
                                pid = getattr(device_list[0], "model", None)
                                if pid:
                                    capability_index = self._get_network_equipment_power_defs(self._device)
                                    capability = capability_index.get(
                                        (capability_device_type_map[devices_key], pid))
                                    if capability:
                                        typical_power = getattr(capability, "typical_power", None)
                                        if typical_power is not None:
                                            fi_fex_typical_power_total += int(typical_power)
                                        else:
                                            live_data_complete = False
                                            self.logger(
                                                level="warning",
                                                message=f"Could not find TypicalPower value in power "
                                                        f"capability data for PID '{pid}' - unable to "
                                                        f"validate minimum power requirement for this device "
                                                        f"in {self._CONFIG_NAME} '{self.name}'")
                                    else:
                                        live_data_complete = False
                                        self.logger(
                                            level="warning",
                                            message=f"Could not find power capability data for PID '{pid}' - "
                                                    f"unable to validate minimum power requirement for this "
                                                    f"device in {self._CONFIG_NAME} '{self.name}'")
                                else:
                                    live_data_complete = False
                                    self.logger(
                                        level="warning",
                                        message=f"Could not find PID for device with serial '{serial}' - "
                                                f"unable to validate minimum power requirement for this "
                                                f"device in {self._CONFIG_NAME} '{self.name}'")

                        else:
                            live_data_complete = False
                            self.logger(level="warning",
                                        message="Could not find device with serial '" + serial +
                                                "' to assign to " + self._CONFIG_NAME + " '" + self.name + "'")
                    else:
                        live_data_complete = False
                        self.logger(level="warning",
                                    message="Could not assign device to " + self._CONFIG_NAME + " '" +
                                            self.name + "' as no serial number is available")

            if inventory_device_members:
                kwargs["inventory_device_member"] = inventory_device_members

        # We compute the live minimum power Intersight requires for this Power Group, based on the currently
        # assigned Chassis/FI/FEX members: Min = SUM(chassis MinRequiredPower) + 10% buffer + SUM(FI/FEX
        # TypicalPower). A budget below the live minimum is raised to it (avoids "Insufficient power budget"
        # errors) - this is the only case we log, since it is the only case where we actually change something.
        power_group_budget = self.power_group_budget

        if live_data_complete:
            intersight_min_required_budget = None
            if chassis_min_required_power_total > 0 or fi_fex_typical_power_total > 0:
                intersight_min_required_budget = (
                    chassis_min_required_power_total +
                    int(math.ceil(chassis_min_required_power_total * 0.10)) +
                    fi_fex_typical_power_total
                )

            if intersight_min_required_budget is not None and power_group_budget is not None and \
                    power_group_budget < intersight_min_required_budget:
                # The configured budget is below the live minimum required power - it must be raised to avoid
                # "Insufficient power budget" errors when the Power Group is pushed
                self.logger(
                    level="warning",
                    message=f"{self._CONFIG_NAME} '{self.name}' configured budget ({power_group_budget}W) is "
                            f"below the minimum power required live by Intersight for its assigned "
                            f"Chassis/FI/FEX members (Min: {intersight_min_required_budget}W) - budget has "
                            f"been automatically increased to {intersight_min_required_budget}W")
                power_group_budget = intersight_min_required_budget

        if power_group_budget is not None:
            # Intersight does not support a power budget greater than 1,000,000W
            kwargs["power_budget"] = min(power_group_budget, 1000000)

        power_group = PowerPowerGroup(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, key_attributes=["name"],
                           payload=power_group, detail=self.name):
            return False

        return True
