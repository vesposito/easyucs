# coding: utf-8
# !/usr/bin/env python

""" server_profiles.py: Easy UCS Deployment Tool """

import copy

from config.intersight.object import IntersightConfigObject
from config.intersight.pools import (
    IntersightIqnPool,
    IntersightMacPool,
    IntersightResourcePool,
    IntersightUuidPool,
    IntersightWwnnPool,
    IntersightWwpnPool
)
from config.intersight.server_policies import (
    IntersightAdapterConfigurationPolicy,
    IntersightBiosPolicy,
    IntersightBootPolicy,
    IntersightCertificateManagementPolicy,
    IntersightDeviceConnectorPolicy,
    IntersightDriveSecurityPolicy,
    IntersightFirmwarePolicy,
    IntersightImcAccessPolicy,
    IntersightIpmiOverLanPolicy,
    IntersightIpPool,
    IntersightIscsiBootPolicy,
    IntersightLanConnectivityPolicy,
    IntersightLdapPolicy,
    IntersightLocalUserPolicy,
    IntersightNetworkConnectivityPolicy,
    IntersightNtpPolicy,
    IntersightPersistentMemoryPolicy,
    IntersightPowerPolicy,
    IntersightSanConnectivityPolicy,
    IntersightSdCardPolicy,
    IntersightSerialOverLanPolicy,
    IntersightSmtpPolicy,
    IntersightSnmpPolicy,
    IntersightSshPolicy,
    IntersightStoragePolicy,
    IntersightSyslogPolicy,
    IntersightThermalPolicy,
    IntersightVirtualKvmPolicy,
    IntersightVirtualMediaPolicy
)
from config.ucs.ucsc.profiles import UcsCentralServiceProfile
from config.ucs.ucsm.profiles import UcsSystemServiceProfile


class IntersightGenericUcsServerProfile(IntersightConfigObject):
    _POLICY_MAPPING_TABLE = {
        "adapter_configuration_policy": IntersightAdapterConfigurationPolicy,
        "bios_policy": IntersightBiosPolicy,
        "boot_policy": IntersightBootPolicy,
        "certificate_management_policy": IntersightCertificateManagementPolicy,
        "device_connector_policy": IntersightDeviceConnectorPolicy,
        "drive_security_policy": IntersightDriveSecurityPolicy,
        "firmware_policy": IntersightFirmwarePolicy,
        "imc_access_policy": IntersightImcAccessPolicy,
        "ipmi_over_lan_policy": IntersightIpmiOverLanPolicy,
        "lan_connectivity_policy": IntersightLanConnectivityPolicy,
        "ldap_policy": IntersightLdapPolicy,
        "local_user_policy": IntersightLocalUserPolicy,
        "network_connectivity_policy": IntersightNetworkConnectivityPolicy,
        "ntp_policy": IntersightNtpPolicy,
        "persistent_memory_policy": IntersightPersistentMemoryPolicy,
        "power_policy": IntersightPowerPolicy,
        "resource_pool": IntersightResourcePool,
        "san_connectivity_policy": IntersightSanConnectivityPolicy,
        "sd_card_policy": IntersightSdCardPolicy,
        "serial_over_lan_policy": IntersightSerialOverLanPolicy,
        "smtp_policy": IntersightSmtpPolicy,
        "snmp_policy": IntersightSnmpPolicy,
        "ssh_policy": IntersightSshPolicy,
        "storage_policy": IntersightStoragePolicy,
        "syslog_policy": IntersightSyslogPolicy,
        "thermal_policy": IntersightThermalPolicy,
        "uuid_pool": IntersightUuidPool,
        "virtual_kvm_policy": IntersightVirtualKvmPolicy,
        "virtual_media_policy": IntersightVirtualMediaPolicy
    }
    UCS_TO_INTERSIGHT_POOL_MAPPING_TABLE = {
        "inband_ipv4_pool": IntersightIpPool,
        "inband_ipv6_pool": IntersightIpPool,
        # UCSM iSCSI Boot Parameter IP Pool
        "initiator_ip_address_policy": IntersightIpPool,
        # UCS Central iSCSI interface IP Pool
        "ip_pool": IntersightIpPool,
        # IQN Pool from Individual iSCSI vNIC
        "iqn_pool": IntersightIqnPool,
        # IQN Pool from Global Identifier
        "iscsi_iqn_pool_name": IntersightIqnPool,
        "mac_address_pool": IntersightMacPool,
        "outband_ipv4_pool": IntersightIpPool,
        "server_pool": IntersightResourcePool,
        "uuid_pool": IntersightUuidPool,
        "wwnn_pool": IntersightWwnnPool,
        "wwpn_pool": IntersightWwpnPool
    }

    def __init__(self, parent, sdk_object):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=sdk_object)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.target_platform = self.get_attribute(attribute_name="target_platform")

        self.adapter_configuration_policy = None
        self.bios_policy = None
        self.boot_policy = None
        self.certificate_management_policy = None
        self.device_connector_policy = None
        self.drive_security_policy = None
        self.imc_access_policy = None
        self.ipmi_over_lan_policy = None
        self.lan_connectivity_policy = None
        self.ldap_policy = None
        self.local_user_policy = None
        self.network_connectivity_policy = None
        self.ntp_policy = None
        self.persistent_memory_policy = None
        self.power_policy = None
        self.san_connectivity_policy = None
        self.sd_card_policy = None
        self.serial_over_lan_policy = None
        self.smtp_policy = None
        self.snmp_policy = None
        self.ssh_policy = None
        self.storage_policy = None
        self.syslog_policy = None
        self.thermal_policy = None
        self.uuid_pool = None
        self.virtual_kvm_policy = None
        self.virtual_media_policy = None

    def _get_policy(self, policy):
        if not policy:
            self.logger(level="warning", message="No Policy/Pool Provided")
            return None
        policy_list = self.get_config_objects_from_ref(ref=policy)
        if (len(policy_list)) != 1:
            self.logger(level="debug", message="Could not find the appropriate " + str(policy.object_type) +
                                               " for access.Policy with MOID " + str(policy.moid))
            return None
        else:
            # We return the name attribute of the matching Policy
            return policy_list[0].name


class IntersightUcsServerProfile(IntersightGenericUcsServerProfile):
    _CONFIG_NAME = "UCS Server Profile"
    _CONFIG_SECTION_NAME = "ucs_server_profiles"
    _INTERSIGHT_SDK_OBJECT_NAME = "server.Profile"

    def __init__(self, parent=None, server_profile=None):
        IntersightGenericUcsServerProfile.__init__(self, parent=parent, sdk_object=server_profile)

        self.assigned_server = None
        self.server_pre_assign_by_serial = None
        self.server_pre_assign_by_slot = None
        # self.associated_server = None
        self.resource_pool = None
        self.ucs_server_profile_template = None
        self.uuid_allocation_type = None
        self.uuid_static = None
        # List containing the Reservation References to be assigned during creation of the Server Profile.
        self.reservations = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if self.target_platform == "FIAttached":
                self.target_platform = "FI-Attached"

            # If this UCS Server Profile is derived from a UCS Server Profile Template, we only get the source template
            if hasattr(self._object, "src_template"):
                if self._object.src_template:
                    self.ucs_server_profile_template = self._get_ucs_server_profile_template()

            if not self.ucs_server_profile_template:
                self.uuid_allocation_type = self.get_attribute(attribute_name="uuid_address_type",
                                                               attribute_secondary_name="uuid_allocation_type")
                # Renaming UUID Allocation Type to lowercase to be more user-friendly
                # (and aligned with other xxx_allocation_type)
                if self.uuid_allocation_type:
                    self.uuid_allocation_type = self.uuid_allocation_type.lower()

                self.uuid_static = self.get_attribute(attribute_name="static_uuid_address",
                                                      attribute_secondary_name="uuid_static")

                if hasattr(server_profile, "uuid_pool"):  # This line is needed until Intersight Appliance is updated
                    if server_profile.uuid_pool:
                        uuid_pool = self._get_policy_name(policy=server_profile.uuid_pool)
                        if uuid_pool:
                            self.uuid_pool = uuid_pool

                if server_profile.server_pool:
                    server_pool = self._get_policy_name(policy=server_profile.server_pool)
                    if server_pool:
                        self.resource_pool = server_pool

                for policy in self._object.policy_bucket:
                    for (policy_name, intersight_policy) in self._POLICY_MAPPING_TABLE.items():
                        if policy.object_type == getattr(intersight_policy, "_INTERSIGHT_SDK_OBJECT_NAME", None):
                            setattr(self, policy_name, self._get_policy_name(policy))
                            break

            # Fetching the identities which are already consumed by the profile
            self.operational_state.update(self._get_identities())

            # Fetching the identities (reservations) which are not yet consumed by the profile
            if hasattr(self._object, "reservation_references"):
                for reservation_reference in self._object.reservation_references:
                    # Getting the pool type. Ex: Getting 'iqn' from class_id "iqnpool.ReservationReference"
                    pool_type = reservation_reference.class_id.split(".")[0].rsplit("p", 1)[0]
                    target_reservation = None
                    target_pool = None
                    reservation = {
                        "reservation_type": pool_type,
                        "identity": None,
                        "pool_name": None
                    }

                    for pool_type_reservation in self._config.sdk_objects[pool_type + "pool_reservation"]:
                        if pool_type_reservation.moid == reservation_reference.reservation_moid:
                            target_reservation = pool_type_reservation
                            break

                    for pool in self._config.sdk_objects[pool_type + "pool_pool"]:
                        if getattr(pool, "reservations", None) is not None:
                            for pool_reservation in pool.reservations:
                                if pool_reservation.moid == reservation_reference.reservation_moid:
                                    target_pool = pool
                                    break

                    if target_reservation and target_pool is not None:
                        if pool_type in ["mac"]:
                            reservation.update({"vnic_name": reservation_reference.consumer_name})

                        elif pool_type in ["ip"]:
                            ip_type = "IPv4"
                            if "Inband" in reservation_reference.consumer_type:
                                reservation["management_type"] = "Inband"
                            elif "Outofband" in reservation_reference.consumer_type:
                                reservation["management_type"] = "OutOfBand"
                            elif "ISCSI" in reservation_reference.consumer_type:
                                reservation["management_type"] = "ISCSI"

                            if "Ipv6" in reservation_reference.consumer_type:
                                ip_type = "IPv6"

                            reservation.update({"ip_type": ip_type})

                        elif pool_type in ["fc"]:
                            if reservation_reference.consumer_type == "Vhba":
                                reservation.update({
                                    "reservation_type": "wwpn",
                                    "vhba_name": reservation_reference.consumer_name,
                                })

                            elif reservation_reference.consumer_type == "WWNN":
                                reservation.update({"reservation_type": "wwnn"})

                        # If target pool exists in an org different from the server profile org (in a shared org) then
                        # we make sure to name the pool as "{org_name}/{pool_name}"
                        pool_name = target_pool.name
                        if target_pool.organization.moid != self._parent._moid:
                            org = self.get_config_objects_from_ref(ref=target_pool.organization)
                            if org:
                                pool_name = f"{org[0].name}/{target_pool.name}"

                        reservation.update({"identity": target_reservation.identity,
                                            "pool_name": pool_name})

                    self.reservations.append(reservation)

            if hasattr(self._object, "assigned_server"):
                if self._object.assigned_server:
                    if self._object.assigned_server.object_type == "compute.Blade":
                        self.assigned_server = {"server_type": "Blade"}
                        server_details = self._get_server(self._object.assigned_server)
                        if server_details:
                            (
                                self.assigned_server["chassis_id"],
                                self.assigned_server["slot_id"],
                                self.assigned_server["model"],
                            ) = server_details
                    elif self._object.assigned_server.object_type == "compute.RackUnit":
                        self.assigned_server = {"server_type": "Rack"}
                        server_details = self._get_server(self._object.assigned_server)
                        if server_details:
                            (
                                self.assigned_server["server_id"],
                                self.assigned_server["model"],
                            ) = server_details

            if hasattr(self._object, "server_assignment_mode") and self._object.server_assignment_mode == "None":
                if hasattr(self._object, "config_context") and self._object.config_context:
                    if self._object.config_context.get("config_state", None) == "Waiting-for-resource":
                        if hasattr(self._object, "server_pre_assign_by_serial") and \
                                self._object.server_pre_assign_by_serial:
                            self.server_pre_assign_by_serial = self._object.server_pre_assign_by_serial

                        elif hasattr(self._object, "server_pre_assign_by_slot") and \
                                self._object.server_pre_assign_by_slot:
                            self.server_pre_assign_by_slot = {
                                "chassis_id": self._object.server_pre_assign_by_slot.chassis_id,
                                "domain_name": self._object.server_pre_assign_by_slot.domain_name,
                                "slot_id": self._object.server_pre_assign_by_slot.slot_id
                            }

            # if hasattr(self._object, "associated_server"):
            #     if self._object.associated_server:
            #         if self._object.associated_server.object_type == "compute.Blade":
            #             self.associated_server = {"server_type": "Blade"}
            #             server_details = self._get_server(
            #                 self._object.associated_server
            #             )
            #             if server_details:
            #                 (
            #                     self.associated_server["chassis_id"],
            #                     self.associated_server["slot_id"],
            #                     self.associated_server["model"],
            #                 ) = server_details
            #         elif (
            #             self._object.associated_server.object_type == "compute.RackUnit"
            #         ):
            #             self.associated_server = {"server_type": "Rack"}
            #             server_details = self._get_server(
            #                 self._object.associated_server
            #             )
            #             if server_details:
            #                 (
            #                     self.associated_server["server_id"],
            #                     self.associated_server["model"],
            #                 ) = server_details

        elif self._config.load_from == "file":
            for attribute in [
                "adapter_configuration_policy", "assigned_server", "bios_policy", "boot_policy",
                "certificate_management_policy", "device_connector_policy", "drive_security_policy", "firmware_policy",
                "imc_access_policy", "ipmi_over_lan_policy", "lan_connectivity_policy", "ldap_policy",
                "local_user_policy", "network_connectivity_policy", "ntp_policy", "operational_state",
                "persistent_memory_policy", "power_policy", "reservations", "resource_pool", "san_connectivity_policy",
                "sd_card_policy", "serial_over_lan_policy", "server_pre_assign_by_serial", "server_pre_assign_by_slot",
                "smtp_policy", "snmp_policy", "ssh_policy", "storage_policy", "syslog_policy", "thermal_policy",
                "ucs_server_profile_template", "uuid_allocation_type", "uuid_pool", "uuid_static", "virtual_kvm_policy",
                "virtual_media_policy"
            ]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # if self.associated_server:
            #     for attribute in [
            #         "model",
            #         "server_id",
            #         "chassis_id",
            #         "slot_id",
            #         "server_type",
            #     ]:
            #         if attribute not in self.associated_server:
            #             self.associated_server[attribute] = None

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all attributes of assigned_server, reservations and operational_state
        # are set to None if they are not present
        if self.assigned_server:
            for attribute in ["chassis_id", "model", "server_id", "server_type", "slot_id"]:
                if attribute not in self.assigned_server:
                    self.assigned_server[attribute] = None

        if self.reservations:
            for reservation in self.reservations:
                for attribute in ["identity", "ip_type", "management_type", "reservation_type", "pool_name",
                                  "vhba_name", "vnic_name"]:
                    if attribute not in reservation:
                        reservation[attribute] = None

        if self.operational_state:
            for attribute in ["identities"]:
                if attribute not in self.operational_state:
                    self.operational_state[attribute] = None

            if self.operational_state["identities"]:
                for identity in self.operational_state["identities"]:
                    for attribute in ["identity", "identity_type", "ip_type", "management_type", "pool_name",
                                      "vhba_name", "vnic_name"]:
                        if attribute not in identity:
                            identity[attribute] = None

        if self.server_pre_assign_by_slot:
            for attribute in ["chassis_id", "domain_name", "slot_id"]:
                if attribute not in self.server_pre_assign_by_slot:
                    self.server_pre_assign_by_slot[attribute] = None

    # Non-Working Code
    def _get_server(self, server_obj):
        server_obj_list = self.get_config_objects_from_ref(ref=server_obj)
        if (len(server_obj_list)) != 1:
            self.logger(
                level="debug",
                message="Could not find the appropriate " + str(server_obj.object_type) + " for Server with MOID " +
                        str(server_obj.moid),
            )
            return None
        else:
            if server_obj.object_type == "compute.Blade":
                return server_obj_list[0].chassis_id, server_obj_list[0].slot_id, server_obj_list[0].model
            elif server_obj.object_type == "compute.RackUnit":
                return server_obj_list[0].server_id, server_obj_list[0].model
        return None

    def _get_ucs_server_profile_template(self):
        # Fetches the source UCS Server Profile Template of a UCS Server Profile
        if "server_profile_template" in self._config.sdk_objects:
            for server_profile_template in self._config.sdk_objects["server_profile_template"]:
                if server_profile_template.moid == self._object.src_template.moid:
                    # If the referenced SPT exists in a shared org, then we return "<org_name>/<spt_name>"
                    if self._object.organization.moid != server_profile_template.organization.moid:
                        source_org_list = self.get_config_objects_from_ref(ref=server_profile_template.organization)
                        if len(source_org_list) != 1:
                            self.logger(level="debug",
                                        message=f"Could not find the appropriate "
                                                f"{str(server_profile_template.organization.object_type)}"
                                                f" with MOID {str(server_profile_template.organization.moid)}")
                        else:
                            return f"{source_org_list[0].name}/{server_profile_template.name}"
                    return server_profile_template.name

        return None

    def _get_management_type(self, pool_name=None):
        # EASYUCS-746: This method need to be removed once we get the support of "consumer_type" and "vnic_name"
        # from ip pool lease object in the Intersight backend
        if getattr(self._parent, "imc_access_policies") is not None:
            # To get the Server Profile/Template associated IMC Access Policy
            associated_imc_access_policy = self._get_imc_access_policy()
            imc_access_policy = next(
                (imc_access_policy for imc_access_policy in self._parent.imc_access_policies
                 if associated_imc_access_policy == imc_access_policy.name),
                None)
            if imc_access_policy:
                if getattr(imc_access_policy, "inband_ip_pool", None) or getattr(
                        imc_access_policy, "out_of_band_ip_pool", None):
                    # To check if same pool is used for both the Inband and OutOfBand configurations.
                    condition = [imc_access_policy.inband_ip_pool == pool_name,
                                 imc_access_policy.out_of_band_ip_pool == pool_name]
                    if all(condition):
                        self.logger(
                            level="warning",
                            message=f"Could not find the management type of '{pool_name}' since this pool is used " +
                                    f"for both Inband and OutOfBand configuration")
                        return None
                    if imc_access_policy.inband_ip_pool == pool_name:
                        return "Inband"
                    elif imc_access_policy.out_of_band_ip_pool == pool_name:
                        return "OutOfBand"
        return None

    def _get_imc_access_policy(self):
        # Get the IMC Access Policy from Template else from Profile level
        imc_access_policy = None
        if self.ucs_server_profile_template:
            ucs_server_profile_template = next(
                (ucs_server_profile_template
                 for ucs_server_profile_template in self._parent.ucs_server_profile_templates
                 if self.ucs_server_profile_template == ucs_server_profile_template.name),
                None)
            if ucs_server_profile_template is not None:
                imc_access_policy = ucs_server_profile_template.imc_access_policy
        else:
            imc_access_policy = self.imc_access_policy
        return imc_access_policy

    def _get_identities(self):
        # Function to call the get identities for each identity type
        identities = []
        identities = identities + list(self._get_ip_identities())
        identities = identities + list(self._get_iqn_identities())
        identities = identities + list(self._get_mac_identities())
        identities = identities + list(self._get_uuid_identities())
        identities = identities + list(self._get_wwnn_identities())
        identities = identities + list(self._get_wwpn_identities())

        return {"identities": identities}

    def _get_leased_ip_properties(self, ippool_lease=None):
        """ Fetches the IP Properties from the IP pool lease object Mo
        :param ippool_lease: Object to fetch the leased IP Properties from
        :return: reservation dict if successful, empty dict otherwise
        """
        reservation = {}
        if ippool_lease.ip_type == "IPv4":
            reservation["identity"] = ippool_lease.ip_v4_address
        else:
            reservation["identity"] = ippool_lease.ip_v6_address
        reservation["ip_type"] = ippool_lease.ip_type
        reservation["identity_type"] = "ip"
        # pool name is not required when allocation type is static
        if ippool_lease.allocation_type not in ["static"]:
            reservation["pool_name"] = self._get_policy_name(ippool_lease.pool)
        return reservation

    def _get_ip_identities(self):
        # Fetches the IP Identities associated with the Server Profile
        if "ippool_ip_lease" in self._config.sdk_objects:
            for ippool_lease in self._config.sdk_objects["ippool_ip_lease"]:
                reservation = {}
                if ippool_lease.assigned_to_entity and (ippool_lease.ip_v4_address or ippool_lease.ip_v6_address):
                    # The IP address can be leased from the vNIC interface
                    if ippool_lease.assigned_to_entity.object_type == "vnic.EthIf":
                        associated_vnic = None
                        # Get the associated vNIC object
                        for vnic_eth_if in self._config.sdk_objects["vnic_eth_if"]:
                            if vnic_eth_if.moid == ippool_lease.assigned_to_entity.moid:
                                associated_vnic = vnic_eth_if
                                break

                        if associated_vnic is not None:
                            if associated_vnic.profile.moid == self._moid:
                                reservation["vnic_name"] = associated_vnic.name
                                reservation["management_type"] = "ISCSI"
                                reservation.update(self._get_leased_ip_properties(ippool_lease))
                                yield reservation
                        else:
                            self.logger(
                                level="warning",
                                message=f"Could not find the appropriate 'vnic.EthIf'" +
                                f"object with Moid '{ippool_lease.assigned_to_entity.moid}'")

                    # The IP address can be leased from the server profile(Inband/OutOfBand)
                    if ippool_lease.assigned_to_entity.moid == self._moid:
                        reservation.update(self._get_leased_ip_properties(ippool_lease))
                        reservation["management_type"] = self._get_management_type(reservation["pool_name"])
                        yield reservation

    def _get_iqn_identities(self):
        # Fetches the IQN Identities associated with the Server Profile
        if "iqnpool_lease" in self._config.sdk_objects:
            for iqnpool_lease in self._config.sdk_objects["iqnpool_lease"]:
                reservation = {}
                if iqnpool_lease.assigned_to_entity and iqnpool_lease.iqn_address:
                    if iqnpool_lease.assigned_to_entity.moid == self._moid:
                        reservation["identity"] = iqnpool_lease.iqn_address
                        # pool name is not required when allocation type is static
                        if iqnpool_lease.allocation_type not in ["static"]:
                            reservation["pool_name"] = self._get_policy_name(iqnpool_lease.pool)
                        reservation["identity_type"] = "iqn"
                        yield reservation

    def _get_mac_identities(self):
        # Fetches the MAC Identities associated with the Server Profile
        if "vnic_eth_if" in self._config.sdk_objects:
            for vnic_eth_if in self._config.sdk_objects["vnic_eth_if"]:
                reservation = {}
                if vnic_eth_if.profile:
                    if vnic_eth_if.profile.moid == self._moid and vnic_eth_if.mac_address:
                        reservation["identity"] = vnic_eth_if.mac_address
                        # pool name is not required when allocation type is static
                        if vnic_eth_if.mac_address_type not in ["static"]:
                            reservation["pool_name"] = self._get_policy_name(vnic_eth_if.mac_pool)
                        reservation["identity_type"] = "mac"
                        reservation["vnic_name"] = vnic_eth_if.name
                        yield reservation

    def _get_uuid_identities(self):
        # Fetches the UUID Identities associated with the Server Profile
        if "uuidpool_uuid_lease" in self._config.sdk_objects:
            for uuidpool_lease in self._config.sdk_objects["uuidpool_uuid_lease"]:
                reservation = {}
                if uuidpool_lease.assigned_to_entity:
                    if uuidpool_lease.assigned_to_entity.moid == self._moid and uuidpool_lease.uuid:
                        reservation["identity"] = uuidpool_lease.uuid
                        # pool name is not required when allocation type is static
                        if uuidpool_lease.allocation_type not in ["static"]:
                            reservation["pool_name"] = self._get_policy_name(uuidpool_lease.pool)
                        reservation["identity_type"] = "uuid"
                        yield reservation

    def _get_wwnn_identities(self):
        # Fetches the WWNN Identities associated with the Server Profile
        if "fcpool_lease" in self._config.sdk_objects:
            for fcpool_lease in self._config.sdk_objects["fcpool_lease"]:
                reservation = {}
                if fcpool_lease.assigned_to_entity:
                    if fcpool_lease.assigned_to_entity.moid == self._moid and fcpool_lease.wwn_id:
                        reservation["identity"] = fcpool_lease.wwn_id
                        # pool name is not required when allocation type is static
                        if fcpool_lease.allocation_type not in ["static"]:
                            reservation["pool_name"] = self._get_policy_name(fcpool_lease.pool)
                        reservation["identity_type"] = "wwnn"
                        yield reservation

    def _get_wwpn_identities(self):
        # Fetches the WWPN Identities associated with the Server Profile
        if "vnic_fc_if" in self._config.sdk_objects:
            for vnic_fc_if in self._config.sdk_objects["vnic_fc_if"]:
                reservation = {}
                if vnic_fc_if.profile:
                    if vnic_fc_if.profile.moid == self._moid and vnic_fc_if.wwpn:
                        reservation["identity"] = vnic_fc_if.wwpn
                        # pool name is not required when allocation type is static
                        if vnic_fc_if.wwpn_address_type not in ["static"]:
                            reservation["pool_name"] = self._get_policy_name(vnic_fc_if.wwpn_pool)
                        reservation["identity_type"] = "wwpn"
                        reservation["vhba_name"] = vnic_fc_if.name
                        yield reservation

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.server_profile import ServerProfile
        from intersight.model.server_profile_template import ServerProfileTemplate

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We identify the parent organization as it will be used many times
        org = self.get_parent_org_relationship()
        if not org:
            return False

        # We first need to check if a UCS Server Profile with the same name already exists
        server_profile = self.get_live_object(object_name=self.name, object_type="server.Profile",
                                              return_reference=False, log=False)

        if not getattr(self._config, "update_existing_intersight_objects", False) and server_profile:
            message = f"Skipping push of object type {self._INTERSIGHT_SDK_OBJECT_NAME} with name={self.name} as " \
                      f"it already exists"
            self.logger(level="info", message=message)
            self._config.push_summary_manager.add_object_status(
                obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="skipped",
                message=message)
            return True

        # In case this UCS Server Profile needs to be bound to a Template, we use the 'derive' mechanism to create it
        if self.ucs_server_profile_template:
            if not server_profile:
                # No UCS Server Profile with the same name exists, so we can derive the UCS Server Profile Template
                from intersight.model.bulk_mo_cloner import BulkMoCloner

                kwargs_mo_cloner = {
                    "sources": [],
                    "targets": []
                }

                # We need to identify the Moid of the source UCS Server Profile Template
                ucs_server_profile_template = self.get_live_object(object_name=self.ucs_server_profile_template,
                                                                   object_type="server.ProfileTemplate",
                                                                   return_reference=False, log=False)
                if ucs_server_profile_template:
                    template_moid = ucs_server_profile_template.moid
                    source_template = {
                        "moid": template_moid,
                        "object_type": "server.ProfileTemplate"
                    }
                    kwargs_mo_cloner["sources"].append(ServerProfileTemplate(**source_template))
                else:
                    err_message = "Unable to locate source UCS Server Profile Template " + \
                                  self.ucs_server_profile_template + " to derive UCS Server Profile " + self.name
                    self.logger(level="error", message=err_message)
                    self._config.push_summary_manager.add_object_status(obj=self, obj_detail=self.name,
                                                                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                                                                        status="failed", message=err_message)
                    return False

                # We now need to specify the attribute of the target UCS Server Profile
                target_profile = {
                    "name": self.name,
                    "object_type": "server.Profile",
                    "organization": org
                }
                if self.descr is not None:
                    target_profile["description"] = self.descr
                if self.tags is not None:
                    target_profile["tags"] = self.create_tags()

                if self.resource_pool is not None:
                    # We need to identify the Resource Pool object reference
                    resource_pool = self.get_live_object(object_name=self.resource_pool,
                                                         object_type="resourcepool.Pool")
                    if resource_pool:
                        target_profile["server_pool"] = resource_pool
                        target_profile["server_assignment_mode"] = "Pool"
                    else:
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Resource Pool '{self.resource_pool}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Resource Pool '{self.resource_pool}'")

                elif self.server_pre_assign_by_serial:
                    target_profile["server_pre_assign_by_serial"] = self.server_pre_assign_by_serial

                elif self.server_pre_assign_by_slot:
                    target_profile["server_pre_assign_by_slot"] = copy.copy(self.server_pre_assign_by_slot)

                if self.reservations:
                    reservation_references_list = []

                    # We create a local cache of pools to avoid performing too many queries
                    reservation_pools_cache = {"ip": {}, "iqn": {}, "mac": {}, "uuid": {}, "wwnn": {}, "wwpn": {}}

                    for reservation in self.reservations:
                        if reservation["reservation_type"] == "ip":
                            # If pool name is not in the local cache, we query for it to get its moid
                            if reservation["pool_name"] not in reservation_pools_cache["ip"]:
                                pool = self.get_live_object(object_type="ippool.Pool",
                                                            object_name=reservation['pool_name'],
                                                            return_reference=False)
                                if pool:
                                    reservation_pools_cache["ip"][reservation['pool_name']] = pool.moid
                                else:
                                    err_message = "Could not find unique ippool.Pool with name " + reservation[
                                        'pool_name']
                                    self.logger(level="error", message=err_message)
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=f"IP Pool Reservation Ref '{reservation['identity']}'",
                                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                    continue

                            reservation_list = self._device.query(
                                object_type="ippool.Reservation",
                                filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                                       f"'{reservation_pools_cache['ip'][reservation['pool_name']]}'"
                            )
                            if len(reservation_list) == 1:
                                from intersight.model.ippool_reservation_reference import IppoolReservationReference

                                consumer_type = None
                                consumer_name = None
                                if reservation["ip_type"] == "IPv4":
                                    if reservation["management_type"] == "Inband":
                                        consumer_type = "InbandIpv4-Access"
                                    elif reservation["management_type"] == "OutOfBand":
                                        consumer_type = "OutofbandIpv4-Access"
                                    elif reservation["management_type"] == "ISCSI":
                                        consumer_type = "ISCSI"
                                        if reservation.get("vnic_name"):
                                            consumer_name = reservation["vnic_name"]
                                elif reservation["ip_type"] == "IPv6":
                                    if reservation["management_type"] == "Inband":
                                        consumer_type = "InbandIpv6-Access"
                                    elif reservation["management_type"] == "ISCSI":
                                        consumer_type = "ISCSI"
                                        if reservation.get("vnic_name"):
                                            consumer_name = reservation["vnic_name"]

                                reservation_reference_kwargs = {
                                    "class_id": "ippool.ReservationReference",
                                    "object_type": "ippool.ReservationReference",
                                    "reservation_moid": reservation_list[0].moid
                                }
                                if consumer_type:
                                    reservation_reference_kwargs["consumer_type"] = consumer_type
                                if consumer_name:
                                    reservation_reference_kwargs["consumer_name"] = consumer_name
                                reservation_references_list.append(
                                    IppoolReservationReference(**reservation_reference_kwargs))
                            else:
                                err_message = "Could not find unique ippool.Reservation with identity " + \
                                              reservation['identity']
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"IP Pool Reservation Ref '{reservation['identity']}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                continue

                        elif reservation["reservation_type"] == "iqn":
                            # If pool name is not in the local cache, we query for it to get its moid
                            if reservation["pool_name"] not in reservation_pools_cache["iqn"]:
                                pool = self.get_live_object(object_type="iqnpool.Pool",
                                                            object_name=reservation['pool_name'],
                                                            return_reference=False)
                                if pool:
                                    reservation_pools_cache["iqn"][reservation['pool_name']] = pool.moid
                                else:
                                    err_message = "Could not find unique iqnpool.Pool with name " + reservation[
                                        'pool_name']
                                    self.logger(level="error", message=err_message)
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=f"IQN Pool Reservation Ref '{reservation['identity']}'",
                                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                    continue

                            reservation_list = self._device.query(
                                object_type="iqnpool.Reservation",
                                filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                                       f"'{reservation_pools_cache['iqn'][reservation['pool_name']]}'"
                            )
                            if len(reservation_list) == 1:
                                from intersight.model.iqnpool_reservation_reference import IqnpoolReservationReference
                                reservation_reference_kwargs = {
                                    "class_id": "iqnpool.ReservationReference",
                                    "object_type": "iqnpool.ReservationReference",
                                    "reservation_moid": reservation_list[0].moid
                                }
                                reservation_references_list.append(
                                    IqnpoolReservationReference(**reservation_reference_kwargs))
                            else:
                                err_message = "Could not find unique iqnpool.Reservation with identity " + \
                                              reservation['identity']
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"IQN Pool Reservation Ref '{reservation['identity']}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                continue

                        elif reservation["reservation_type"] == "mac":
                            # If pool name is not in the local cache, we query for it to get its moid
                            if reservation["pool_name"] not in reservation_pools_cache["mac"]:
                                pool = self.get_live_object(object_type="macpool.Pool",
                                                            object_name=reservation['pool_name'],
                                                            return_reference=False)
                                if pool:
                                    reservation_pools_cache["mac"][reservation['pool_name']] = pool.moid
                                else:
                                    err_message = "Could not find unique macpool.Pool with name " + \
                                                  reservation['pool_name']
                                    self.logger(level="error", message=err_message)
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=f"MAC Pool Reservation Ref '{reservation['identity']}'",
                                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                    continue

                            reservation_list = self._device.query(
                                object_type="macpool.Reservation",
                                filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                                       f"'{reservation_pools_cache['mac'][reservation['pool_name']]}'"
                            )
                            if len(reservation_list) == 1:
                                from intersight.model.macpool_reservation_reference import MacpoolReservationReference
                                reservation_reference_kwargs = {
                                    "class_id": "macpool.ReservationReference",
                                    "object_type": "macpool.ReservationReference",
                                    "reservation_moid": reservation_list[0].moid,
                                    "consumer_type": "Vnic",
                                    "consumer_name": reservation["vnic_name"]
                                }
                                reservation_references_list.append(
                                    MacpoolReservationReference(**reservation_reference_kwargs))
                            else:
                                err_message = "Could not find unique macpool.Reservation with identity " + \
                                              reservation['identity']
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"MAC Pool Reservation Ref '{reservation['identity']}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                continue

                        elif reservation["reservation_type"] == "uuid":
                            # If pool name is not in the local cache, we query for it to get its moid
                            if reservation["pool_name"] not in reservation_pools_cache["uuid"]:
                                pool = self.get_live_object(object_type="uuidpool.Pool",
                                                            object_name=reservation['pool_name'],
                                                            return_reference=False)
                                if pool:
                                    reservation_pools_cache["uuid"][reservation['pool_name']] = pool.moid
                                else:
                                    err_message = "Could not find unique uuidpool.Pool with name " + reservation[
                                        'pool_name']
                                    self.logger(level="error", message=err_message)
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=f"UUID Pool Reservation Ref '{reservation['identity']}'",
                                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                    continue

                            reservation_list = self._device.query(
                                object_type="uuidpool.Reservation",
                                filter=f"Identity eq '{reservation['identity'].upper()}' and Pool.Moid eq " +
                                       f"'{reservation_pools_cache['uuid'][reservation['pool_name']]}'"
                            )
                            if len(reservation_list) == 1:
                                from intersight.model.uuidpool_reservation_reference import UuidpoolReservationReference
                                reservation_reference_kwargs = {
                                    "class_id": "uuidpool.ReservationReference",
                                    "object_type": "uuidpool.ReservationReference",
                                    "reservation_moid": reservation_list[0].moid
                                }
                                reservation_references_list.append(
                                    UuidpoolReservationReference(**reservation_reference_kwargs))
                            else:
                                err_message = "Could not find unique uuidpool.Reservation with identity " + \
                                              reservation['identity']
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"UUID Pool Reservation Ref '{reservation['identity']}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                continue

                        elif reservation["reservation_type"] == "wwpn":
                            # If pool name is not in the local cache, we query for it to get its moid
                            if reservation["pool_name"] not in reservation_pools_cache["wwpn"]:
                                pool = self.get_live_object(object_type="fcpool.Pool",
                                                            object_name=reservation['pool_name'],
                                                            return_reference=False)
                                if pool:
                                    reservation_pools_cache["wwpn"][reservation['pool_name']] = pool.moid
                                else:
                                    err_message = "Could not find unique fcpool.Pool with type 'WWPN' " + \
                                                  "and name " + reservation['pool_name']
                                    self.logger(level="error", message=err_message)
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=f"WWPN Pool Reservation Ref '{reservation['identity']}'",
                                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                    continue

                            reservation_list = self._device.query(
                                object_type="fcpool.Reservation",
                                filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                                       f"'{reservation_pools_cache['wwpn'][reservation['pool_name']]}'"
                            )
                            if len(reservation_list) == 1:
                                from intersight.model.fcpool_reservation_reference import FcpoolReservationReference
                                reservation_reference_kwargs = {
                                    "class_id": "fcpool.ReservationReference",
                                    "object_type": "fcpool.ReservationReference",
                                    "reservation_moid": reservation_list[0].moid,
                                    "consumer_type": "Vhba",
                                    "consumer_name": reservation["vhba_name"]
                                }
                                reservation_references_list.append(
                                    FcpoolReservationReference(**reservation_reference_kwargs))
                            else:
                                err_message = "Could not find unique fcpool.Reservation with identity " + \
                                              reservation['identity']
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"WWPN Pool Reservation Ref '{reservation['identity']}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                continue

                        elif reservation["reservation_type"] == "wwnn":
                            # If pool name is not in the local cache, we query for it to get its moid
                            if reservation["pool_name"] not in reservation_pools_cache["wwnn"]:
                                pool = self.get_live_object(object_type="fcpool.Pool",
                                                            object_name=reservation['pool_name'],
                                                            return_reference=False)
                                if pool:
                                    reservation_pools_cache["wwnn"][reservation['pool_name']] = pool.moid
                                else:
                                    err_message = "Could not find unique fcpool.Pool with type 'WWNN' " + \
                                                  "and name " + reservation['pool_name']
                                    self.logger(level="error", message=err_message)
                                    self._config.push_summary_manager.add_object_status(
                                        obj=self, obj_detail=f"WWNN Pool Reservation Ref '{reservation['identity']}'",
                                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                    continue

                            reservation_list = self._device.query(
                                object_type="fcpool.Reservation",
                                filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                                       f"'{reservation_pools_cache['wwnn'][reservation['pool_name']]}'"
                            )
                            if len(reservation_list) == 1:
                                # We first need to determine the SAN Connectivity Policy name
                                san_connectivity_policy = None
                                for policy in getattr(ucs_server_profile_template, "policy_bucket", []):
                                    if getattr(policy, "object_type", None) == "vnic.SanConnectivityPolicy":
                                        san_connectivity_policy = self.get_live_object(
                                            object_type="vnic.SanConnectivityPolicy",
                                            query_filter="Moid eq '" + policy.moid + "'",
                                            return_reference=False
                                        )
                                        break

                                if not san_connectivity_policy:
                                    self.logger(
                                        level="warning",
                                        message="UCS Server Profile Template '" + ucs_server_profile_template.name +
                                                "' is not using a SAN Connectivity Policy. Skipping WWNN reservation."
                                    )
                                    continue

                                from intersight.model.fcpool_reservation_reference import FcpoolReservationReference
                                reservation_reference_kwargs = {
                                    "class_id": "fcpool.ReservationReference",
                                    "object_type": "fcpool.ReservationReference",
                                    "reservation_moid": reservation_list[0].moid,
                                    "consumer_type": "WWNN"
                                }
                                reservation_references_list.append(
                                    FcpoolReservationReference(**reservation_reference_kwargs))
                            else:
                                err_message = "Could not find unique fcpool.Reservation with identity " + \
                                              reservation['identity']
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"WWNN Pool Reservation Ref '{reservation['identity']}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                                continue

                    if reservation_references_list:
                        target_profile["reservation_references"] = reservation_references_list

                kwargs_mo_cloner["targets"].append(ServerProfile(**target_profile))

                mo_cloner = BulkMoCloner(**kwargs_mo_cloner)

                if not self.commit(object_type="bulk.MoCloner", payload=mo_cloner, detail=self.name):
                    return False
                return True
            else:
                # We found a UCS Server Profile with the same name, we need to check if it is bound to a Template
                if server_profile.src_template:
                    src_template = self._device.query(
                        object_type="server.ProfileTemplate",
                        filter="Moid eq '" + server_profile.src_template.moid + "'"
                    )
                    if len(src_template) == 1:
                        if src_template[0].name == self.ucs_server_profile_template:
                            # UCS Server Profile is already derived from the same UCS Server Profile Template
                            info_message = "UCS Server Profile " + self.name + " exists and is already derived " + \
                                           "from UCS Server Profile Template " + self.ucs_server_profile_template
                            self.logger(level="info", message=info_message)
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                                status="skipped", message=info_message)
                            return True
                        else:
                            # UCS Server Profile is derived from another UCS Server Profile Template
                            # We will detach it from its Template and reattach it to the desired Template
                            self.logger(
                                level="info",
                                message="UCS Server Profile " + self.name +
                                        " exists and is derived from different UCS Server Profile Template " +
                                        src_template[0].name
                            )
                            self.logger(
                                level="info",
                                message="Detaching UCS Server Profile " + self.name +
                                        " from UCS Server Profile Template " + src_template[0].name
                            )
                            kwargs = {
                                "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
                                "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
                                "organization": org,
                                "name": self.name,
                                "src_template": None
                            }
                            server_profile = ServerProfile(**kwargs)

                            if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=server_profile,
                                               detail="Detaching from template " + src_template[0].name):
                                return False

                            self.logger(
                                level="info",
                                message="Attaching UCS Server Profile " + self.name +
                                        " to UCS Server Profile Template " + self.ucs_server_profile_template
                            )
                            # We need to identify the Moid of the UCS Server Profile Template
                            ucs_server_profile_template = self.get_live_object(
                                object_name=self.ucs_server_profile_template,
                                object_type="server.ProfileTemplate"
                            )
                            kwargs["src_template"] = ucs_server_profile_template
                            server_profile = ServerProfile(**kwargs)

                            if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=server_profile,
                                               detail="Attaching to template " + self.ucs_server_profile_template):
                                return False

                            return True
                    else:
                        err_message = "Could not find UCS Server Profile Template " + self.ucs_server_profile_template
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=err_message)
                        return False
                else:
                    # UCS Server Profile is not currently bound to a template. So we just need to bind it
                    # We need to identify the Moid of the UCS Server Profile Template
                    ucs_server_profile_template = self.get_live_object(
                        object_name=self.ucs_server_profile_template,
                        object_type="server.ProfileTemplate"
                    )
                    kwargs = {
                        "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
                        "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
                        "organization": org,
                        "name": self.name,
                        "src_template": ucs_server_profile_template
                    }
                    server_profile = ServerProfile(**kwargs)

                    if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=server_profile,
                                       detail="Attaching to template " + self.ucs_server_profile_template):
                        return False

                    return True

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": org,
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.uuid_allocation_type is not None:
            kwargs["uuid_address_type"] = self.uuid_allocation_type.upper()
        if self.target_platform is not None:
            if self.target_platform in ["FI-Attached"]:
                kwargs["target_platform"] = "FIAttached"
            else:
                kwargs["target_platform"] = self.target_platform

        if self.uuid_allocation_type in ["pool"]:
            if self.uuid_pool is not None:
                # We need to identify the UUID Pool object reference
                uuid_pool = self.get_live_object(object_name=self.uuid_pool, object_type="uuidpool.Pool")
                if uuid_pool:
                    kwargs["uuid_pool"] = uuid_pool
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching UUID Pool '{self.uuid_pool}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                        message=f"Failed to find UUID Pool '{self.uuid_pool}'")

        elif self.uuid_allocation_type in ["static"]:
            if self.uuid_static is not None:
                kwargs["static_uuid_address"] = self.uuid_static

        if self.resource_pool is not None:
            # We need to identify the Resource Pool object reference
            resource_pool = self.get_live_object(object_name=self.resource_pool, object_type="resourcepool.Pool")
            if resource_pool:
                kwargs["server_pool"] = resource_pool
                kwargs["server_assignment_mode"] = "Pool"
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Resource Pool '{self.resource_pool}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find Resource Pool '{self.resource_pool}'")

        elif self.server_pre_assign_by_serial:
            kwargs["server_pre_assign_by_serial"] = self.server_pre_assign_by_serial

        elif self.server_pre_assign_by_slot:
            kwargs["server_pre_assign_by_slot"] = copy.copy(self.server_pre_assign_by_slot)

        if self.reservations:
            reservation_references_list = []

            # We create a local cache of pools to avoid performing too many queries
            reservation_pools_cache = {"ip": {}, "iqn": {}, "mac": {}, "uuid": {}, "wwnn": {}, "wwpn": {}}

            for reservation in self.reservations:
                if reservation["reservation_type"] == "ip":
                    # If pool name is not in the local cache, we query for it to get its moid
                    if reservation["pool_name"] not in reservation_pools_cache["ip"]:
                        pool = self.get_live_object(object_type="ippool.Pool",
                                                    object_name=reservation['pool_name'],
                                                    return_reference=False)
                        if pool:
                            reservation_pools_cache["ip"][reservation['pool_name']] = pool.moid
                        else:
                            err_message = "Could not find unique ippool.Pool with name " + reservation['pool_name']
                            self.logger(level="error", message=err_message)
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"IP Pool Reservation Ref '{reservation['identity']}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                            continue

                    reservation_list = self._device.query(
                        object_type="ippool.Reservation",
                        filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                               f"'{reservation_pools_cache['ip'][reservation['pool_name']]}'"
                    )
                    if len(reservation_list) == 1:
                        from intersight.model.ippool_reservation_reference import IppoolReservationReference

                        consumer_type = None
                        consumer_name = None
                        if reservation["ip_type"] == "IPv4":
                            if reservation["management_type"] == "Inband":
                                consumer_type = "InbandIpv4-Access"
                            elif reservation["management_type"] == "OutOfBand":
                                consumer_type = "OutofbandIpv4-Access"
                            elif reservation["management_type"] == "ISCSI":
                                consumer_type = "ISCSI"
                                if reservation.get("vnic_name"):
                                    consumer_name = reservation["vnic_name"]
                        elif reservation["ip_type"] == "IPv6":
                            if reservation["management_type"] == "Inband":
                                consumer_type = "InbandIpv6-Access"
                            elif reservation["management_type"] == "ISCSI":
                                consumer_type = "ISCSI"
                                if reservation.get("vnic_name"):
                                    consumer_name = reservation["vnic_name"]

                        reservation_reference_kwargs = {
                            "class_id": "ippool.ReservationReference",
                            "object_type": "ippool.ReservationReference",
                            "reservation_moid": reservation_list[0].moid
                        }
                        if consumer_type:
                            reservation_reference_kwargs["consumer_type"] = consumer_type
                        if consumer_name:
                            reservation_reference_kwargs["consumer_name"] = consumer_name
                        reservation_references_list.append(IppoolReservationReference(**reservation_reference_kwargs))
                    else:
                        err_message = "Could not find unique ippool.Reservation with identity " + \
                                      reservation['identity']
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"IP Pool Reservation Ref '{reservation['identity']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                        continue

                elif reservation["reservation_type"] == "iqn":
                    # If pool name is not in the local cache, we query for it to get its moid
                    if reservation["pool_name"] not in reservation_pools_cache["iqn"]:
                        pool = self.get_live_object(object_type="iqnpool.Pool",
                                                    object_name=reservation['pool_name'],
                                                    return_reference=False)
                        if pool:
                            reservation_pools_cache["iqn"][reservation['pool_name']] = pool.moid
                        else:
                            err_message = "Could not find unique iqnpool.Pool with name " + reservation[
                                'pool_name']
                            self.logger(level="error", message=err_message)
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"IQN Pool Reservation Ref '{reservation['identity']}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                            continue

                    reservation_list = self._device.query(
                        object_type="iqnpool.Reservation",
                        filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                               f"'{reservation_pools_cache['iqn'][reservation['pool_name']]}'"
                    )
                    if len(reservation_list) == 1:
                        from intersight.model.iqnpool_reservation_reference import IqnpoolReservationReference
                        reservation_reference_kwargs = {
                            "class_id": "iqnpool.ReservationReference",
                            "object_type": "iqnpool.ReservationReference",
                            "reservation_moid": reservation_list[0].moid
                        }
                        reservation_references_list.append(IqnpoolReservationReference(**reservation_reference_kwargs))
                    else:
                        err_message = "Could not find unique iqnpool.Reservation with identity " + \
                                      reservation['identity']
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"IQN Pool Reservation Ref '{reservation['identity']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                        continue

                elif reservation["reservation_type"] == "mac":
                    # If pool name is not in the local cache, we query for it to get its moid
                    if reservation["pool_name"] not in reservation_pools_cache["mac"]:
                        pool = self.get_live_object(object_type="macpool.Pool",
                                                    object_name=reservation['pool_name'],
                                                    return_reference=False)
                        if pool:
                            reservation_pools_cache["mac"][reservation['pool_name']] = pool.moid
                        else:
                            err_message = "Could not find unique macpool.Pool with name " + \
                                          reservation['pool_name']
                            self.logger(level="error", message=err_message)
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"MAC Pool Reservation Ref '{reservation['identity']}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                            continue

                    reservation_list = self._device.query(
                        object_type="macpool.Reservation",
                        filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                               f"'{reservation_pools_cache['mac'][reservation['pool_name']]}'"
                    )
                    if len(reservation_list) == 1:
                        from intersight.model.macpool_reservation_reference import MacpoolReservationReference
                        reservation_reference_kwargs = {
                            "class_id": "macpool.ReservationReference",
                            "object_type": "macpool.ReservationReference",
                            "reservation_moid": reservation_list[0].moid,
                            "consumer_type": "Vnic",
                            "consumer_name": reservation["vnic_name"]
                        }
                        reservation_references_list.append(MacpoolReservationReference(**reservation_reference_kwargs))
                    else:
                        err_message = "Could not find unique macpool.Reservation with identity " + \
                                      reservation['identity']
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"MAC Pool Reservation Ref '{reservation['identity']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                        continue

                elif reservation["reservation_type"] == "uuid":
                    # If pool name is not in the local cache, we query for it to get its moid
                    if reservation["pool_name"] not in reservation_pools_cache["uuid"]:
                        pool = self.get_live_object(object_type="uuidpool.Pool",
                                                    object_name=reservation['pool_name'],
                                                    return_reference=False)
                        if pool:
                            reservation_pools_cache["uuid"][reservation['pool_name']] = pool.moid
                        else:
                            err_message = "Could not find unique uuidpool.Pool with name " + reservation[
                                'pool_name']
                            self.logger(level="error", message=err_message)
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"UUID Pool Reservation Ref '{reservation['identity']}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                            continue

                    reservation_list = self._device.query(
                        object_type="uuidpool.Reservation",
                        filter=f"Identity eq '{reservation['identity'].upper()}' and Pool.Moid eq " +
                               f"'{reservation_pools_cache['uuid'][reservation['pool_name']]}'"
                    )
                    if len(reservation_list) == 1:
                        from intersight.model.uuidpool_reservation_reference import UuidpoolReservationReference
                        reservation_reference_kwargs = {
                            "class_id": "uuidpool.ReservationReference",
                            "object_type": "uuidpool.ReservationReference",
                            "reservation_moid": reservation_list[0].moid
                        }
                        reservation_references_list.append(UuidpoolReservationReference(**reservation_reference_kwargs))
                    else:
                        err_message = "Could not find unique uuidpool.Reservation with identity " + \
                                      reservation['identity']
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"UUID Pool Reservation Ref '{reservation['identity']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                        continue

                elif reservation["reservation_type"] == "wwpn":
                    # If pool name is not in the local cache, we query for it to get its moid
                    if reservation["pool_name"] not in reservation_pools_cache["wwpn"]:
                        pool = self.get_live_object(object_type="fcpool.Pool",
                                                    object_name=reservation['pool_name'],
                                                    return_reference=False)
                        if pool:
                            reservation_pools_cache["wwpn"][reservation['pool_name']] = pool.moid
                        else:
                            err_message = "Could not find unique fcpool.Pool with type 'WWPN' " + \
                                          "and name " + reservation['pool_name']
                            self.logger(level="error", message=err_message)
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"WWPN Pool Reservation Ref '{reservation['identity']}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                            continue

                    reservation_list = self._device.query(
                        object_type="fcpool.Reservation",
                        filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                               f"'{reservation_pools_cache['wwpn'][reservation['pool_name']]}'"
                    )
                    if len(reservation_list) == 1:
                        from intersight.model.fcpool_reservation_reference import FcpoolReservationReference
                        reservation_reference_kwargs = {
                            "class_id": "fcpool.ReservationReference",
                            "object_type": "fcpool.ReservationReference",
                            "reservation_moid": reservation_list[0].moid,
                            "consumer_type": "Vhba",
                            "consumer_name": reservation["vhba_name"]
                        }
                        reservation_references_list.append(FcpoolReservationReference(**reservation_reference_kwargs))
                    else:
                        err_message = "Could not find unique fcpool.Reservation with identity " + \
                                      reservation['identity']
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"WWPN Pool Reservation Ref '{reservation['identity']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                        continue

                elif reservation["reservation_type"] == "wwnn":
                    # If pool name is not in the local cache, we query for it to get its moid
                    if reservation["pool_name"] not in reservation_pools_cache["wwnn"]:
                        pool = self.get_live_object(object_type="fcpool.Pool",
                                                    object_name=reservation['pool_name'],
                                                    return_reference=False)
                        if pool:
                            reservation_pools_cache["wwnn"][reservation['pool_name']] = pool.moid
                        else:
                            err_message = "Could not find unique fcpool.Pool with type 'WWNN' " + \
                                          "and name " + reservation['pool_name']
                            self.logger(level="error", message=err_message)
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"WWNN Pool Reservation Ref '{reservation['identity']}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                            continue

                    reservation_list = self._device.query(
                        object_type="fcpool.Reservation",
                        filter=f"Identity eq '{reservation['identity']}' and Pool.Moid eq " +
                               f"'{reservation_pools_cache['wwnn'][reservation['pool_name']]}'"
                    )
                    if len(reservation_list) == 1:
                        if self.san_connectivity_policy:
                            from intersight.model.fcpool_reservation_reference import FcpoolReservationReference
                            reservation_reference_kwargs = {
                                "class_id": "fcpool.ReservationReference",
                                "object_type": "fcpool.ReservationReference",
                                "reservation_moid": reservation_list[0].moid,
                                "consumer_type": "WWNN"
                            }
                            reservation_references_list.append(
                                FcpoolReservationReference(**reservation_reference_kwargs)
                            )
                        else:
                            self.logger(level="warning",
                                        message=self._CONFIG_NAME + " '" + self.name +
                                        "' is not using a SAN Connectivity Policy. Skipping WWNN reservation.")
                    else:
                        err_message = "Could not find unique fcpool.Reservation with identity " + \
                                      reservation['identity']
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"WWNN Pool Reservation Ref '{reservation['identity']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                        continue

            if reservation_references_list:
                kwargs["reservation_references"] = reservation_references_list

        kwargs["policy_bucket"] = []
        for policy_name in [
            "adapter_configuration_policy", "bios_policy", "boot_policy", "certificate_management_policy",
            "device_connector_policy", "drive_security_policy", "firmware_policy", "imc_access_policy",
            "ipmi_over_lan_policy", "lan_connectivity_policy", "ldap_policy", "local_user_policy",
            "network_connectivity_policy", "ntp_policy", "persistent_memory_policy", "power_policy",
            "san_connectivity_policy", "sd_card_policy", "serial_over_lan_policy", "smtp_policy", "snmp_policy",
            "ssh_policy", "storage_policy", "syslog_policy", "thermal_policy", "virtual_kvm_policy",
            "virtual_media_policy"
        ]:
            if getattr(self, policy_name, None) is not None:
                policy_type = self._POLICY_MAPPING_TABLE.get(policy_name)
                if policy_type:
                    object_type = getattr(policy_type, "_INTERSIGHT_SDK_OBJECT_NAME", None)
                    if object_type:
                        live_policy = self.get_live_object(
                            object_name=getattr(self, policy_name, None),
                            object_type=object_type
                        )
                        if live_policy:
                            kwargs["policy_bucket"].append(live_policy)
                        else:
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"Attaching {policy_name} '{getattr(self, policy_name)}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                                message=f"Failed to find {policy_name} '{getattr(self, policy_name)}'")
                    else:
                        err_message = "Missing _INTERSIGHT_SDK_OBJECT_NAME value for " + policy_name
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching {policy_name} '{getattr(self, policy_name)}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)
                else:
                    err_message = "Missing entry for " + policy_name + " in _POLICY_MAPPING_TABLE"
                    self.logger(level="error", message=err_message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching {policy_name} '{getattr(self, policy_name)}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)

        # ToDo: Code Pending for mapping Assigned and Associated Server to Server Profile
        server_profile = ServerProfile(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=server_profile, detail=self.name):
            return False

        return True


class IntersightUcsServerProfileTemplate(IntersightGenericUcsServerProfile):
    _CONFIG_NAME = "UCS Server Profile Template"
    _CONFIG_SECTION_NAME = "ucs_server_profile_templates"
    _INTERSIGHT_SDK_OBJECT_NAME = "server.ProfileTemplate"

    def __init__(self, parent=None, server_profile_template=None):
        IntersightGenericUcsServerProfile.__init__(self, parent=parent, sdk_object=server_profile_template)

        if self._config.load_from == "live":
            if self.target_platform == "FIAttached":
                self.target_platform = "FI-Attached"

            if hasattr(server_profile_template, "uuid_pool"):  # This line is needed until IS Appliance is updated
                if server_profile_template.uuid_pool:
                    uuid_pool = self._get_policy_name(policy=server_profile_template.uuid_pool)
                    if uuid_pool:
                        self.uuid_pool = uuid_pool

            for policy in self._object.policy_bucket:
                for (policy_name, intersight_policy) in self._POLICY_MAPPING_TABLE.items():
                    if policy.object_type == getattr(intersight_policy, "_INTERSIGHT_SDK_OBJECT_NAME", None):
                        setattr(self, policy_name, self._get_policy_name(policy))
                        break

        elif self._config.load_from == "file":
            for attribute in [
                "adapter_configuration_policy", "bios_policy", "boot_policy", "certificate_management_policy",
                "device_connector_policy", "drive_security_policy", "firmware_policy", "imc_access_policy",
                "ipmi_over_lan_policy", "lan_connectivity_policy", "ldap_policy", "local_user_policy",
                "network_connectivity_policy", "ntp_policy", "persistent_memory_policy", "power_policy",
                "san_connectivity_policy", "sd_card_policy", "serial_over_lan_policy", "smtp_policy", "snmp_policy",
                "ssh_policy", "storage_policy", "syslog_policy", "thermal_policy", "uuid_pool", "virtual_kvm_policy",
                "virtual_media_policy"
            ]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.server_profile_template import ServerProfileTemplate

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We identify the parent organization as it will be used many times
        org = self.get_parent_org_relationship()
        if not org:
            return False

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": org,
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

        if self.uuid_pool is not None:
            # We need to identify the UUID Pool object reference
            uuid_pool = self.get_live_object(object_name=self.uuid_pool, object_type="uuidpool.Pool")
            if uuid_pool:
                kwargs["uuid_address_type"] = "POOL"
                kwargs["uuid_pool"] = uuid_pool
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching UUID Pool '{self.uuid_pool}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find UUID Pool '{self.uuid_pool}'")

        kwargs["policy_bucket"] = []
        for policy_name in [
            "adapter_configuration_policy", "bios_policy", "boot_policy", "certificate_management_policy",
            "device_connector_policy", "drive_security_policy", "firmware_policy", "imc_access_policy",
            "ipmi_over_lan_policy", "lan_connectivity_policy", "ldap_policy", "local_user_policy",
            "network_connectivity_policy", "ntp_policy", "persistent_memory_policy", "power_policy",
            "san_connectivity_policy", "sd_card_policy", "serial_over_lan_policy", "smtp_policy", "snmp_policy",
            "ssh_policy", "storage_policy", "syslog_policy", "thermal_policy", "virtual_kvm_policy",
            "virtual_media_policy"
        ]:
            if getattr(self, policy_name, None) is not None:
                policy_type = self._POLICY_MAPPING_TABLE.get(policy_name)
                if policy_type:
                    object_type = getattr(policy_type, "_INTERSIGHT_SDK_OBJECT_NAME", None)
                    if object_type:
                        live_policy = self.get_live_object(
                            object_name=getattr(self, policy_name, None),
                            object_type=object_type
                        )
                        if live_policy:
                            kwargs["policy_bucket"].append(live_policy)
                        else:
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"Attaching {policy_name} '{getattr(self, policy_name)}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                                message=f"Failed to find {policy_name} '{getattr(self, policy_name)}'")
                    else:
                        err_message = "Missing _INTERSIGHT_SDK_OBJECT_NAME value for " + policy_name
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching {policy_name} '{getattr(self, policy_name)}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)

                else:
                    err_message = "Missing entry for " + policy_name + " in _POLICY_MAPPING_TABLE"
                    self.logger(level="error", message=err_message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching {policy_name} '{getattr(self, policy_name)}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)

        server_profile_template = ServerProfileTemplate(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=server_profile_template,
                           detail=self.name):
            return False

        return True
