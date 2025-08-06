# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import common
from __init__ import __version__

from config.intersight.config import IntersightConfig
from config.intersight.equipment import IntersightEquipment
from config.intersight.settings import IntersightAccountDetails, IntersightOrganization, \
    IntersightResourceGroup, IntersightRole, IntersightUser, IntersightUserGroup
from config.intersight.pools import IntersightMacPool, IntersightIqnPool, IntersightIpPool, IntersightUuidPool, \
    IntersightWwnnPool, IntersightWwpnPool
from config.intersight.server_policies import IntersightLdapPolicy
from config.manager import GenericConfigManager


class IntersightConfigManager(GenericConfigManager):
    def __init__(self, parent=None):
        GenericConfigManager.__init__(self, parent=parent)
        self.config_class_name = IntersightConfig

    def fetch_config(self, force=False):

        # We check if settings.json file is present
        from api.api_server import easyucs
        if easyucs:
            settings = easyucs.repository_manager.settings
        else:
            settings = common.read_json_file(file_path="settings.json", logger=self)
        if not settings:
            self.logger(level="error", message="Could not open settings file")
            return None

        # We verify that the settings JSON content is valid
        if not common.validate_json(json_data=settings, schema_path="schema/settings/settings.json", logger=self):
            self.logger(level="error", message="Can't import invalid settings JSON file")
            return None
        else:
            self.logger(message="Successfully validated settings file")

        if force:
            self.parent.task.taskstep_manager.skip_taskstep(name="ValidateIntersightLicense",
                                                            status_message="Skipped license validation since forced")
        elif not self.parent.validate_intersight_license():
            return False

        self.logger(message="Fetching config from live device (can take several minutes)")
        config = IntersightConfig(parent=self, settings=settings)
        config.metadata.origin = "live"
        config.metadata.easyucs_version = __version__
        config.load_from = "live"
        config._fetch_sdk_objects(force=force)

        # If any of the mandatory tasksteps fails then return None
        if easyucs and self.parent.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.parent.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more SDK objects. Stopping the config fetch.")
            return None

        self.logger(level="debug", message="Finished fetching Intersight SDK objects for config")

        for iam_account in config.sdk_objects["iam_account"]:
            config.account_details.append(IntersightAccountDetails(parent=config,
                                                                   iam_account=iam_account))
            # There should be only one iam.Account, so we take the first object we find
            break

        # Fetch Intersight Appliance LDAP/AD settings
        if self.parent.is_appliance:
            for ldap in config.sdk_objects["iam_ldap_policy"]:
                if ldap.organization is None and (any(tag.get("key") == "appliance.management" for tag in ldap.tags)):
                    config.ldap.append(IntersightLdapPolicy(parent=config, ldap_policy=ldap,
                                                            appliance_management_ldap=True))

        for iam_permission in config.sdk_objects["iam_permission"]:
            config.roles.append(IntersightRole(parent=config, iam_permission=iam_permission))

        for iam_user in config.sdk_objects["iam_user"]:
            config.users.append(IntersightUser(parent=config, iam_user=iam_user))

        for iam_user_group in config.sdk_objects["iam_user_group"]:
            config.user_groups.append(IntersightUserGroup(parent=config, iam_user_group=iam_user_group))

        for resource_group in config.sdk_objects["resource_group"]:
            # We don't fetch the system created "private-catalog-rg" RG if this is an Intersight Appliance device
            if self.parent.is_appliance and getattr(resource_group, "name", None) in ["private-catalog-rg"]:
                self.logger(level="debug", message="Skipping Resource Group 'private-catalog-rg'")
                continue
            # We don't fetch the system created License-based Resource Groups
            if getattr(resource_group, "name", None) not in ["License-Standard", "License-Essential",
                                                             "License-Advantage", "License-Premier"]:
                config.resource_groups.append(IntersightResourceGroup(parent=config, resource_group=resource_group))

        if config.sdk_objects["asset_device_registration"]:
            for asset_device_registration in config.sdk_objects["asset_device_registration"]:
                # Filtering to IMM domains and standalone rack servers claimed on the Intersight account.
                if asset_device_registration.platform_type == "UCSFIISM" or (asset_device_registration.platform_type in
                    ["IMC", "IMCM4", "IMCM5", "IMCRack"] and not asset_device_registration.parent_connection):
                    config.equipment.append(IntersightEquipment(parent=config, equipment=None))
                    break

        for organization_organization in config.sdk_objects["organization_organization"]:
            # We don't fetch the system created "private-catalog" org if this is an Intersight Appliance device
            if self.parent.is_appliance and getattr(organization_organization, "name", None) in ["private-catalog"]:
                self.logger(level="debug", message="Skipping Organization 'private-catalog'")
                continue
            config.orgs.append(IntersightOrganization(parent=config,
                                                      organization_organization=organization_organization))

        self.config_list.append(config)
        self.logger(message="Finished fetching config with UUID " + str(config.uuid) + " from live device")
        return config.uuid

    def _get_profiles(self, config_orgs, output_json_orgs):
        """
        Fetches all the server/chassis/domain profiles from all the orgs
        :returns: nothing
        """
        for org in config_orgs:
            json_org = {
                "org_name": org.name,
                "is_shared": False
            }
            if getattr(org, "shared_with_orgs", None):
                json_org["is_shared"] = True
            if org.descr:
                json_org["descr"] = org.descr
            json_org["profiles"] = []
            if org.ucs_server_profiles:
                for server_profile in org.ucs_server_profiles:
                    dict_server_profile = {
                        "name": getattr(server_profile, "name", None),
                        "type": "ucs_server_profile"
                    }
                    for field in ["descr", "ucs_server_profile_template"]:
                        if hasattr(server_profile, field) and getattr(server_profile, field):
                            dict_server_profile[field] = getattr(server_profile, field)
                    if getattr(server_profile, "operational_state", None):
                        for field in ["config_state", "profile_state"]:
                            if server_profile.operational_state.get(field):
                                dict_server_profile[field] = server_profile.operational_state.get(field)
                    json_org["profiles"].append(dict_server_profile)
            if org.ucs_server_profile_templates:
                for server_profile_template in org.ucs_server_profile_templates:
                    dict_server_profile_template = {
                        "name": getattr(server_profile_template, "name", None),
                        "type": "ucs_server_profile_template"
                    }
                    json_org["profiles"].append(dict_server_profile_template)

            if org.ucs_domain_profiles:
                for domain_profile in org.ucs_domain_profiles:
                    dict_domain_profile = {
                        "name": getattr(domain_profile, "name", None),
                        "type": "ucs_domain_profile"
                    }
                    for field in ["descr", "ucs_domain_profile_template"]:
                        if hasattr(domain_profile, field) and getattr(domain_profile, field):
                            dict_domain_profile[field] = getattr(domain_profile, field)
                    if getattr(domain_profile, "operational_state", None):
                        for field in ["config_state", "profile_state"]:
                            if domain_profile.operational_state.get(field):
                                dict_domain_profile[field] = domain_profile.operational_state.get(field)
                    json_org["profiles"].append(dict_domain_profile)
            
            if org.ucs_domain_profile_templates:
                for domain_profile_template in org.ucs_domain_profile_templates:
                    dict_domain_profile_template = {
                        "name": getattr(domain_profile_template, "name", None),
                        "type": "ucs_domain_profile_template"
                    }
                    json_org["profiles"].append(dict_domain_profile_template)

            if org.ucs_chassis_profiles:
                for chassis_profile in org.ucs_chassis_profiles:
                    dict_chassis_profile = {
                        "name": getattr(chassis_profile, "name", None),
                        "type": "ucs_chassis_profile"
                    }
                    for field in ["descr", "ucs_chassis_profile_template"]:
                        if hasattr(chassis_profile, field) and getattr(chassis_profile, field):
                            dict_chassis_profile[field] = getattr(chassis_profile, field)
                    if getattr(chassis_profile, "operational_state", None):
                        for field in ["config_state", "profile_state"]:
                            if chassis_profile.operational_state.get(field):
                                dict_chassis_profile[field] = chassis_profile.operational_state.get(field)
                    json_org["profiles"].append(dict_chassis_profile)

            if org.ucs_chassis_profile_templates:
                for chassis_profile_template in org.ucs_chassis_profile_templates:
                    dict_chassis_profile_template = {
                        "name": getattr(chassis_profile_template, "name", None),
                        "type": "ucs_chassis_profile_template"
                    }
                    json_org["profiles"].append(dict_chassis_profile_template)

            output_json_orgs.append(json_org)

    def get_profiles(self, config=None):
        """
        List all profiles (server/chassis/domain profiles) from a given config with some of their key attributes
        :param config: The config from which all the profiles/templates need to be obtained
        :return: All profiles/templates from the config, [] otherwise
        """
        if config is None:
            self.logger(level="error", message="Missing config in get profiles request!")
            return None

        profiles = []
        self._get_profiles(config.orgs, profiles)
        return profiles

    def push_config(self, uuid=None, reset=False, bypass_version_checks=False, force=False, push_equipment=False, push_equipment_only=False):
        """
        Push the specified config to the live system
        :param uuid: The UUID of the config to be pushed. If not specified, the most recent config will be used
        :param reset: Whether the device must be reset before pushing the config
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :param force: Force the push to proceed even in-case of critical errors. Eg: If we fail to push a source
        shared org then we will continue pushing target orgs (orgs with which the source org is shared)
        if and only if force is true, otherwise we will skip the push of the target orgs.
        :param push_equipment: Whether the equipment section of the configuration should be pushed alongside the rest of the configuration.
        :param push_equipment_only: Only the equipment section of the configuration should be pushed.
        that the domain or server profile deployment has been successfully completed.
        :return: True if config push was successful, False otherwise
        """
        if uuid is None:
            self.logger(level="debug", message="No config UUID specified in config push request. Using latest.")
            config = self.get_latest_config()
        else:
            # Find the config that needs to be pushed
            config_list = [config for config in self.config_list if str(config.uuid) == str(uuid)]
            if len(config_list) != 1:
                self.logger(level="error", message="Failed to locate config with UUID " + str(uuid) + " for push")
                return False
            else:
                config = config_list[0]

        if config:
            # Pushing configuration to the device
            # We first make sure we are connected to the device
            if not self.parent.connect(bypass_version_checks=bypass_version_checks):
                return False

            if force:
                self.parent.task.taskstep_manager.skip_taskstep(name="ValidateIntersightLicense",
                                                                status_message="Skipped license validation since "
                                                                               "forced")
            elif not self.parent.validate_intersight_license():
                return False

            self.parent.set_task_progression(50)
            self.logger(message="Pushing configuration " + str(config.uuid) + " to " + self.parent.target)

            is_pushed = True
            if not push_equipment_only:
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.start_taskstep(
                        name="PushOrgsSectionIntersight", description="Pushing Orgs section of config")

                # We push all config elements, in a specific optimized order
                self.logger(message="Now configuring Orgs/Policies/Profiles section")
                for resource_group in config.resource_groups:
                    is_pushed = resource_group.push_object() and is_pushed

                # We sort the organizations in an order where shared organizations are pushed first.
                config.orgs.sort(key=lambda o: len(getattr(o, 'shared_with_orgs', []) or []), reverse=True)

                # First we push the Orgs not including their sub policies/profiles/pools
                failed_orgs = []
                for org in config.orgs:
                    if org.name not in failed_orgs and not org.push_object():
                        # If we fail to push the organization object then we skip pushing its sub-objects, sharing rules
                        # and organizations which this organization is shared to.
                        is_pushed = False
                        failed_orgs.append(org.name)
                        if org.shared_with_orgs and not force:
                            failed_orgs += org.shared_with_orgs
                            self.logger(level="error",
                                        message=f"Failed to push the organization(s) {', '.join(org.shared_with_orgs)}. "
                                                f"As the organization '{org.name}' which is shared to the organization(s) "
                                                f"have failed to be pushed.")

                # Then we push the sharing rules between the orgs
                for org in config.orgs:
                    if org.name not in failed_orgs or force:
                        is_pushed = org.push_sharing_rules() and is_pushed

                # Finally we push the Organizations policies/profiles/pools in an order where shared organizations are
                # pushed first
                for org in config.orgs:
                    if org.name not in failed_orgs or force:
                        is_pushed = org.push_subobjects() and is_pushed

                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.stop_taskstep(
                        name="PushOrgsSectionIntersight", status="successful",
                        status_message="Successfully pushed Orgs section of config")

                self.parent.set_task_progression(75)

                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.start_taskstep(
                        name="PushAdminSectionIntersight", description="Pushing Admin section of config")

                # We push the entire admin section after the orgs because roles can be mapped to orgs
                self.logger(message="Now configuring Admin section")
                for account_details in config.account_details:
                    is_pushed = account_details.push_object() and is_pushed

                for role in config.roles:
                    is_pushed = role.push_object() and is_pushed

                for ldap in config.ldap:
                    is_pushed = ldap.push_object(appliance_management_ldap=True) and is_pushed

                for user in config.users:
                    is_pushed = user.push_object() and is_pushed

                for user_group in config.user_groups:
                    is_pushed = user_group.push_object() and is_pushed

                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.stop_taskstep(
                        name="PushAdminSectionIntersight", status="successful",
                        status_message="Successfully pushed Admin section of config")
                if not push_equipment:
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.skip_taskstep(
                            name="PushEquipmentSectionIntersight",
                            status_message="Skipped pushing equipment section of config"
                        )

                self.parent.set_task_progression(85)

            if push_equipment_only or push_equipment:
                if push_equipment_only:
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.skip_taskstep(
                            name="PushOrgsSectionIntersight",
                            status_message="Skipped pushing org section of config"
                        )
                        self.parent.task.taskstep_manager.skip_taskstep(
                            name="PushAdminSectionIntersight",
                            status_message="Skipped pushing admin section of config"
                        )
                if config.equipment:
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.start_taskstep(
                            name="PushEquipmentSectionIntersight", description="Pushing Equipment section of config")

                    # We push the entire equipment section after the orgs because profiles can be assigned to FIs
                    self.logger(message="Now configuring Equipment section")
                    is_pushed = config.equipment[0].push_subobjects() and is_pushed
                    
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="PushEquipmentSectionIntersight", status="successful",
                            status_message="Successfully pushed Equipment section of config")

                    self.parent.set_task_progression(90)
                else:
                    self.logger(level="error", message="No equipment section to push!")
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.skip_taskstep(
                            name="PushEquipmentSectionIntersight",
                            status_message="Skipped pushing equipment section of config"
                        )

            if is_pushed:
                # Checking the push summary failed count
                if config.push_summary_manager.push_summary.get("summary", {}).get("failed") == 0:
                    self.logger(message="Successfully pushed configuration " + str(config.uuid) +
                                        " to " + self.parent.target)

            # We disconnect from the device
            self.parent.disconnect()
            self.parent.set_task_progression(100)

            return True
        else:
            self.logger(level="error", message="No config to push!")
            return False

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

        if "account_details" in config_json:
            for account_details in config_json["account_details"]:
                config.account_details.append(IntersightAccountDetails(parent=config,
                                                                       iam_account=account_details))

        if "ldap" in config_json:
            for ldap in config_json["ldap"]:
                config.ldap.append(IntersightLdapPolicy(parent=config, ldap_policy=ldap))
                
        if "equipment" in config_json:
            config.equipment.append(IntersightEquipment(parent=config, equipment=config_json["equipment"][0]))

        if "roles" in config_json:
            for role in config_json["roles"]:
                config.roles.append(IntersightRole(parent=config, iam_permission=role))

        if "users" in config_json:
            for user in config_json["users"]:
                config.users.append(IntersightUser(parent=config, iam_user=user))

        if "user_groups" in config_json:
            for user_group in config_json["user_groups"]:
                config.user_groups.append(IntersightUserGroup(parent=config, iam_user_group=user_group))

        if "resource_groups" in config_json:
            for resource_group in config_json["resource_groups"]:
                config.resource_groups.append(IntersightResourceGroup(parent=config, resource_group=resource_group))

        if "orgs" in config_json:
            for org in config_json["orgs"]:
                config.orgs.append(IntersightOrganization(parent=config, organization_organization=org))

        return True
