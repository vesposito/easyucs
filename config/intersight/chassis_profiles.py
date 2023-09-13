# coding: utf-8
# !/usr/bin/env python

""" chassis_profiles.py: Easy UCS Deployment Tool """

from config.intersight.object import IntersightConfigObject


class IntersightUcsChassisProfile(IntersightConfigObject):
    _CONFIG_NAME = "UCS Chassis Profile"
    _CONFIG_SECTION_NAME = "ucs_chassis_profiles"
    _INTERSIGHT_SDK_OBJECT_NAME = "chassis.Profile"

    def __init__(self, parent=None, chassis_profile=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=chassis_profile)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        # ToDo
        # self.assigned_chassis = None
        # self.associated_chassis = None
        self.imc_access_policy = None
        self.power_policy = None
        self.snmp_policy = None
        self.thermal_policy = None

        if self._config.load_from == "live":
            for policy in self._object.policy_bucket:
                if policy.object_type == "access.Policy":
                    self.imc_access_policy = self._get_policy(policy)
                elif policy.object_type == "power.Policy":
                    self.power_policy = self._get_policy(policy)
                elif policy.object_type == "snmp.Policy":
                    self.snmp_policy = self._get_policy(policy)
                elif policy.object_type == "thermal.Policy":
                    self.thermal_policy = self._get_policy(policy)
                
        elif self._config.load_from == "file":
            for attribute in ["imc_access_policy", "power_policy", "snmp_policy", "thermal_policy"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    # Fetches policy name with MOID
    def _get_policy(self, policy):
        policy_list = self.get_config_objects_from_ref(ref=policy)
        
        if (len(policy_list)) != 1:
            self.logger(level="debug", message="Could not find the appropriate" + str(policy.object_type) +
                                               " for Policy with MOID " + str(policy.moid))
            return None
        else:
            # We return the name attribute of the matching Policy
            return policy_list[0].name

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.chassis_profile import ChassisProfile

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We identify the parent organization as it will be used many times
        org = self.get_parent_org_relationship()
        if not org:
            return False

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": org
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        kwargs["policy_bucket"] = []
        if self.imc_access_policy is not None:
            imc_access_policy = self.get_live_object(object_name=self.imc_access_policy, object_type="access.Policy")
            if imc_access_policy:
                kwargs["policy_bucket"].append(imc_access_policy)
        if self.power_policy is not None:
            power_policy = self.get_live_object(object_name=self.power_policy, object_type="power.Policy")
            if power_policy:
                kwargs["policy_bucket"].append(power_policy)
        if self.snmp_policy is not None:
            snmp_policy = self.get_live_object(object_name=self.snmp_policy, object_type="snmp.Policy")
            if snmp_policy:
                kwargs["policy_bucket"].append(snmp_policy)
        if self.thermal_policy is not None:
            thermal_policy = self.get_live_object(object_name=self.thermal_policy, object_type="thermal.Policy")
            if thermal_policy:
                kwargs["policy_bucket"].append(thermal_policy)

        # ToDo: Code Pending for mapping Assigned and Associated Chassis to Chassis Profile
        chassis_profile = ChassisProfile(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=chassis_profile, detail=self.name):
            return False

        return True