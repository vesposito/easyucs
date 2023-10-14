# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import common
from __init__ import __version__

from config.intersight.config import IntersightConfig
from config.intersight.settings import IntersightAccountDetails, IntersightOrganization, IntersightResourceGroup, \
    IntersightRole, IntersightUser, IntersightUserGroup
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

        for iam_session_limits in config.sdk_objects["iam_session_limits"]:
            # We make sure this iam.SessionLimits object is linked to an account, as in some rare cases there might
            # be more than one iam.SessionLimits object, only one of which is linked to the account
            if iam_session_limits.account:
                config.account_details.append(IntersightAccountDetails(parent=config,
                                                                       iam_session_limits=iam_session_limits))

        for iam_permission in config.sdk_objects["iam_permission"]:
            config.roles.append(IntersightRole(parent=config, iam_permission=iam_permission))

        for iam_user in config.sdk_objects["iam_user"]:
            config.users.append(IntersightUser(parent=config, iam_user=iam_user))

        for iam_user_group in config.sdk_objects["iam_user_group"]:
            config.user_groups.append(IntersightUserGroup(parent=config, iam_user_group=iam_user_group))

        for resource_group in config.sdk_objects["resource_group"]:
            # We don't fetch the system created License-based Resource Groups
            if getattr(resource_group, "name", None) not in ["License-Standard", "License-Essential",
                                                             "License-Advantage", "License-Premier"]:
                config.resource_groups.append(IntersightResourceGroup(parent=config, resource_group=resource_group))

        for organization_organization in config.sdk_objects["organization_organization"]:
            config.orgs.append(IntersightOrganization(parent=config,
                                                      organization_organization=organization_organization))

        self.config_list.append(config)
        self.logger(message="Finished fetching config with UUID " + str(config.uuid) + " from live device")
        return config.uuid

    def _get_server_profiles(self, config_orgs, output_json_orgs):
        """
        Fetches all the server profiles from all the orgs
        :returns: nothing
        """
        for org in config_orgs:
            json_org = {
                "org_name": org.name
            }
            if org.descr:
                json_org["descr"] = org.descr
            json_org["server_profiles"] = []
            if org.ucs_server_profiles:
                for server_profile in org.ucs_server_profiles:
                    dict_server_profile = {
                        "name": getattr(server_profile, "name", None),
                        "type": "ucs_server_profile"
                    }
                    for field in ["descr", "ucs_server_profile_template"]:
                        if hasattr(server_profile, field) and getattr(server_profile, field):
                            dict_server_profile[field] = getattr(server_profile, field)
                    json_org["server_profiles"].append(dict_server_profile)
            if org.ucs_server_profile_templates:
                for server_profile_template in org.ucs_server_profile_templates:
                    dict_server_profile_template = {
                        "name": getattr(server_profile_template, "name", None),
                        "type": "ucs_server_profile_template"
                    }
                    json_org["server_profiles"].append(dict_server_profile_template)

            output_json_orgs.append(json_org)

    def get_profiles(self, config=None):
        """
        List all Server Profiles from a given config with some of their key attributes
        :param config: The config from which all the server profiles/templates needs to be obtained
        :return: All server profiles/templates from the config, [] otherwise
        """
        if config is None:
            self.logger(level="error", message="Missing config in get service profiles request!")
            return None

        server_profiles = []
        self._get_server_profiles(config.orgs, server_profiles)

        return server_profiles

    def push_config(self, uuid=None, bypass_version_checks=False):
        """
        Push the specified config to the live system
        :param uuid: The UUID of the config to be pushed. If not specified, the most recent config will be used
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
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

            self.parent.set_task_progression(50)
            self.logger(message="Pushing configuration " + str(config.uuid) + " to " + self.parent.target)

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.start_taskstep(
                    name="PushOrgsSectionIntersight", description="Pushing Orgs section of config")

            # We push all config elements, in a specific optimized order
            self.logger(message="Now configuring Orgs/Policies/Profiles section")
            for resource_group in config.resource_groups:
                resource_group.push_object()
            for org in config.orgs:
                org.push_object()

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
                account_details.push_object()

            for role in config.roles:
                role.push_object()

            for user in config.users:
                user.push_object()

            for user_group in config.user_groups:
                user_group.push_object()

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="PushAdminSectionIntersight", status="successful",
                    status_message="Successfully pushed Admin section of config")

            self.parent.set_task_progression(90)

            self.logger(message="Successfully pushed configuration " + str(config.uuid) + " to " + self.parent.target)

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
                                                                       iam_session_limits=account_details))

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
