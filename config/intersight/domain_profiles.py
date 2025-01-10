# coding: utf-8
# !/usr/bin/env python

""" domain_profiles.py: Easy UCS Deployment Tool """

import copy

from config.intersight.object import IntersightConfigObject
from config.intersight.server_policies import IntersightNetworkConnectivityPolicy, IntersightNtpPolicy, \
    IntersightSnmpPolicy, IntersightSyslogPolicy
from config.intersight.fabric_policies import IntersightFabricPortPolicy, IntersightFabricSwitchControlPolicy, \
    IntersightFabricSystemQosPolicy, IntersightFabricVlanPolicy, IntersightFabricVsanPolicy


class IntersightGenericUcsDomainProfile(IntersightConfigObject):
    _POLICY_MAPPING_TABLE = {
        "network_connectivity_policy": IntersightNetworkConnectivityPolicy,
        "ntp_policy": IntersightNtpPolicy,
        "port_policies": {
            "fabric_a": IntersightFabricPortPolicy,
            "fabric_b": IntersightFabricPortPolicy
        },
        "snmp_policy": IntersightSnmpPolicy,
        "switch_control_policy": IntersightFabricSwitchControlPolicy,
        "syslog_policy": IntersightSyslogPolicy,
        "system_qos_policy": IntersightFabricSystemQosPolicy,
        "vlan_policies": {
            "fabric_a": IntersightFabricVlanPolicy,
            "fabric_b": IntersightFabricVlanPolicy
        },
        "vsan_policies": {
            "fabric_a": IntersightFabricVsanPolicy,
            "fabric_b": IntersightFabricVsanPolicy
        }
    }

    def __init__(self, parent, sdk_object):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=sdk_object)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.user_label = self.get_attribute(attribute_name="user_label")

        self.network_connectivity_policy = None
        self.ntp_policy = None
        self.port_policies = None
        self.snmp_policy = None
        self.switch_control_policy = None
        self.syslog_policy = None
        self.system_qos_policy = None
        self.vlan_policies = None
        self.vsan_policies = None

    def _get_port_policies(self, profiles_or_templates):
        # Fetches the Port Policies assigned to the UCS Domain Profile
        port_policies = {"fabric_a": None, "fabric_b": None}
        for switch_profile in profiles_or_templates:
            for policy in switch_profile.policy_bucket:
                if policy.object_type == getattr(IntersightFabricPortPolicy, "_INTERSIGHT_SDK_OBJECT_NAME", None):
                    if switch_profile.name[-2:] == "-A":
                        port_policies["fabric_a"] = self._get_policy_name(policy)
                    elif switch_profile.name[-2:] == "-B":
                        port_policies["fabric_b"] = self._get_policy_name(policy)

        if port_policies["fabric_a"] or port_policies["fabric_b"]:
            return port_policies
        else:
            return None

    def _get_vlan_policies(self, profiles_or_templates):
        # Fetches the VLAN Policies assigned to the UCS Domain Profile
        vlan_policies = {"fabric_a": None, "fabric_b": None}
        for switch_profile in profiles_or_templates:
            for policy in switch_profile.policy_bucket:
                if policy.object_type == getattr(IntersightFabricVlanPolicy, "_INTERSIGHT_SDK_OBJECT_NAME", None):
                    if switch_profile.name[-2:] == "-A":
                        vlan_policies["fabric_a"] = self._get_policy_name(policy)
                    elif switch_profile.name[-2:] == "-B":
                        vlan_policies["fabric_b"] = self._get_policy_name(policy)

        if vlan_policies["fabric_a"] or vlan_policies["fabric_b"]:
            return vlan_policies
        else:
            return None

    def _get_vsan_policies(self, profiles_or_templates):
        # Fetches the VSAN Policies assigned to the UCS Domain Profile
        vsan_policies = {"fabric_a": None, "fabric_b": None}
        for switch_profile in profiles_or_templates:
            for policy in switch_profile.policy_bucket:
                if policy.object_type == getattr(IntersightFabricVsanPolicy, "_INTERSIGHT_SDK_OBJECT_NAME", None):
                    if switch_profile.name[-2:] == "-A":
                        vsan_policies["fabric_a"] = self._get_policy_name(policy)
                    elif switch_profile.name[-2:] == "-B":
                        vsan_policies["fabric_b"] = self._get_policy_name(policy)

        if vsan_policies["fabric_a"] or vsan_policies["fabric_b"]:
            return vsan_policies
        else:
            return None


class IntersightUcsDomainProfile(IntersightGenericUcsDomainProfile):
    _CONFIG_NAME = "UCS Domain Profile"
    _CONFIG_SECTION_NAME = "ucs_domain_profiles"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.SwitchClusterProfile"

    def __init__(self, parent=None, fabric_switch_cluster_profile=None):
        IntersightGenericUcsDomainProfile.__init__(self, parent=parent, sdk_object=fabric_switch_cluster_profile)

        self.operational_state = {}
        self.ucs_domain_profile_template = None

        if self._config.load_from == "live":
            # If this UCS Domain Profile is derived from a UCS Domain Profile Template, we only get the source template
            if hasattr(self._object, "src_template"):
                if self._object.src_template:
                    self.ucs_domain_profile_template = self._get_policy_name(self._object.src_template)
            
            if not self.ucs_domain_profile_template:
                # We first need to identify the Moids of the fabric.SwitchProfile objects attached to the UCS Domain Profile
                self._switch_profiles = self.get_config_objects_from_ref(ref=self._object.switch_profiles)
                if self._switch_profiles:
                    for switch_profile in self._switch_profiles:
                        for policy in switch_profile.policy_bucket:
                            for (policy_name, intersight_policy) in self._POLICY_MAPPING_TABLE.items():
                                if not isinstance(intersight_policy, dict) and \
                                        policy.object_type == getattr(intersight_policy, "_INTERSIGHT_SDK_OBJECT_NAME",
                                                                    None):
                                    setattr(self, policy_name, self._get_policy_name(policy))
                                    break

                self.port_policies = self._get_port_policies(self._switch_profiles)
                self.vlan_policies = self._get_vlan_policies(self._switch_profiles)
                self.vsan_policies = self._get_vsan_policies(self._switch_profiles)

            # Fetching the status of the profile
            if hasattr(self._object, "config_context"):
                if hasattr(self._object.config_context, "config_state_summary"):
                    self.operational_state.update({
                        "config_state": getattr(self._object.config_context, "config_state_summary", None)
                    })
                if getattr(self._object.config_context, "oper_state", None):
                    self.operational_state.update({
                        "profile_state": getattr(self._object.config_context, "oper_state", None)
                    })

        elif self._config.load_from == "file":
            for attribute in ["network_connectivity_policy", "ntp_policy", "operational_state", "port_policies",
                              "snmp_policy", "switch_control_policy", "syslog_policy", "system_qos_policy",
                              "vlan_policies", "vsan_policies", "ucs_domain_profile_template"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of the Port Policies, VLAN Policies and VSAN Policies are set to
        # None if they are not present
        for parent_attribute in ["port_policies", "vlan_policies", "vsan_policies"]:
            for attribute in ["fabric_a", "fabric_b"]:
                if getattr(self, parent_attribute, None):
                    if attribute not in getattr(self, parent_attribute):
                        getattr(self, parent_attribute)[attribute] = None

        if self.operational_state:
            for attribute in ["config_state", "profile_state"]:
                if attribute not in self.operational_state:
                    self.operational_state[attribute] = None

    def deepcopy(self, new_parent=None):
        """
        Function creates a deep copy of a UCS Domain Profile. This is done to handle UCS Domain Profile Template
        references inside a Domain Profile.
        :param new_parent: Parent of the new Intersight object
        :returns: New Intersight UCS domain profile object
        """
        new_profile = IntersightGenericUcsDomainProfile.deepcopy(self, new_parent=new_parent)

        # If Domain Profile is attached to a template then deepcopy the template too.
        if self.ucs_domain_profile_template:
            source_template = self._config.get_object(name=self.ucs_domain_profile_template,
                                                      org_name=self._parent.name,
                                                      object_type=IntersightUcsDomainProfileTemplate)

            # If Template is already copied then return
            target_template = new_parent._config.get_object(name=self.ucs_domain_profile_template,
                                                            org_name=self._parent.name,
                                                            object_type=IntersightUcsDomainProfileTemplate,
                                                            debug=False)
            if target_template:
                return new_profile

            # If the Domain Profile Template is an object of a shared organization, then we make sure that the
            # copy of this Domain Profile Template exists in the copy of the shared organization of the target config.
            if "/" in self.ucs_domain_profile_template:
                new_parent = self.handle_shared_object_parent_creation(object_name=self.ucs_domain_profile_template,
                                                                       parent_object_type=self._parent.__class__,
                                                                       target_config=new_parent._config)
                if not new_parent:
                    self.logger(level="error",
                                message=f"Failed to clone '{self._CONFIG_NAME}' '{self.name}' as we "
                                        f"failed to deepcopy its domain profile template "
                                        f"{self.ucs_domain_profile_template} in shared org "
                                        f"'{self.ucs_domain_profile_template.split('/')[0]}'.")
                    return None

            new_template = source_template.deepcopy(new_parent=new_parent)
            if not getattr(new_parent, new_template._CONFIG_SECTION_NAME, None):
                setattr(new_parent, new_template._CONFIG_SECTION_NAME, [])
            getattr(new_parent, new_template._CONFIG_SECTION_NAME).append(new_template)

        return new_profile

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_switch_cluster_profile import FabricSwitchClusterProfile
        from intersight.model.fabric_switch_cluster_profile_template import FabricSwitchClusterProfileTemplate

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We identify the parent organization as it will be used many times
        org = self.get_parent_org_relationship()
        if not org:
            return False
        
        # We first need to check if a UCS Domain Profile with the same name already exists
        domain_profile = self.get_live_object(object_name=self.name, object_type="fabric.SwitchClusterProfile",
                                              return_reference=False, log=False)

        if not getattr(self._config, "update_existing_intersight_objects", False) and domain_profile:
            message = f"Skipping push of object type {self._INTERSIGHT_SDK_OBJECT_NAME} with name={self.name} as " \
                      f"it already exists"
            self.logger(level="info", message=message)
            self._config.push_summary_manager.add_object_status(
                obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="skipped",
                message=message)
            return True
        
        # In case this UCS Domain Profile needs to be bound to a Template, we use the 'derive' mechanism to create it
        if self.ucs_domain_profile_template:
            if not domain_profile:
                # No UCS Domain Profile with the same name exists, so we can derive the UCS Domain Profile Template
                from intersight.model.bulk_mo_cloner import BulkMoCloner

                kwargs_mo_cloner = {
                    "sources": [],
                    "targets": []
                }

                # We need to identify the Moid of the source UCS Domain Profile Template
                ucs_domain_profile_template = self.get_live_object(object_name=self.ucs_domain_profile_template,
                                                                   object_type="fabric.SwitchClusterProfileTemplate",
                                                                   return_reference=False, log=False)
                if ucs_domain_profile_template:
                    template_moid = ucs_domain_profile_template.moid
                    source_template = {
                        "moid": template_moid,
                        "object_type": "fabric.SwitchClusterProfileTemplate"
                    }
                    kwargs_mo_cloner["sources"].append(FabricSwitchClusterProfileTemplate(**source_template))
                else:
                    err_message = "Unable to locate source UCS Domain Profile Template " + \
                                  self.ucs_domain_profile_template + " to derive UCS Domain Profile " + self.name
                    self.logger(level="error", message=err_message)
                    self._config.push_summary_manager.add_object_status(obj=self, obj_detail=self.name,
                                                                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                                                                        status="failed", message=err_message)
                    return False

                # We now need to specify the attribute of the target UCS Domain Profile
                target_profile = {
                    "name": self.name,
                    "object_type": "fabric.SwitchClusterProfile",
                    "organization": org
                }
                if self.descr is not None:
                    target_profile["description"] = self.descr
                if self.tags is not None:
                    target_profile["tags"] = self.create_tags()
                
                kwargs_mo_cloner["targets"].append(FabricSwitchClusterProfile(**target_profile))

                mo_cloner = BulkMoCloner(**kwargs_mo_cloner)

                if not self.commit(object_type="bulk.MoCloner", payload=mo_cloner, detail=self.name):
                    return False
                return True
            else:
                # We found a UCS Domain Profile with the same name, we need to check if it is bound to a Template
                if domain_profile.src_template:
                    src_template = self._device.query(
                        object_type="fabric.SwitchClusterProfileTemplate",
                        filter="Moid eq '" + domain_profile.src_template.moid + "'"
                    )
                    if len(src_template) == 1:
                        if src_template[0].name == self.ucs_domain_profile_template:
                            # UCS Domain Profile is already derived from the same UCS Domain Profile Template
                            info_message = "UCS Domain Profile " + self.name + " exists and is already derived " + \
                                           "from UCS Domain Profile Template " + self.ucs_domain_profile_template
                            self.logger(level="info", message=info_message)
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                                status="skipped", message=info_message)
                            return True
                        else:
                            # UCS Domain Profile is derived from another UCS Domain Profile Template
                            # We will detach it from its Template and reattach it to the desired Template
                            self.logger(
                                level="info",
                                message="UCS Domain Profile " + self.name +
                                        " exists and is derived from different UCS Domain Profile Template " +
                                        src_template[0].name
                            )
                            self.logger(
                                level="info",
                                message="Detaching UCS Domain Profile " + self.name +
                                        " from UCS Domain Profile Template " + src_template[0].name
                            )
                            kwargs = {
                                "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
                                "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
                                "organization": org,
                                "name": self.name,
                                "src_template": None
                            }
                            domain_profile = FabricSwitchClusterProfile(**kwargs)

                            if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=domain_profile,
                                               detail="Detaching from template " + src_template[0].name):
                                return False

                            self.logger(
                                level="info",
                                message="Attaching UCS Domain Profile " + self.name +
                                        " to UCS Domain Profile Template " + self.ucs_domain_profile_template
                            )
                            # We need to identify the Moid of the UCS Domain Profile Template
                            ucs_domain_profile_template = self.get_live_object(
                                object_name=self.ucs_domain_profile_template,
                                object_type="fabric.SwitchClusterProfileTemplate"
                            )
                            kwargs["src_template"] = ucs_domain_profile_template
                            domain_profile = FabricSwitchClusterProfile(**kwargs)

                            if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=domain_profile,
                                               detail="Attaching to template " + self.ucs_domain_profile_template):
                                return False

                            return True
                    else:
                        err_message = "Could not find UCS Domain Profile Template " + self.ucs_domain_profile_template
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=err_message)
                        return False
                else:
                    # UCS Domain Profile is not currently bound to a template. So we just need to bind it
                    # We need to identify the Moid of the UCS Domain Profile Template
                    ucs_domain_profile_template = self.get_live_object(
                        object_name=self.ucs_domain_profile_template,
                        object_type="fabric.SwitchClusterProfileTemplate"
                    )
                    kwargs = {
                        "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
                        "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
                        "organization": org,
                        "name": self.name,
                        "src_template": ucs_domain_profile_template
                    }
                    domain_profile = FabricSwitchClusterProfile(**kwargs)

                    if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=domain_profile,
                                       detail="Attaching to template " + self.ucs_domain_profile_template):
                        return False

                    return True

        # We first need to push the main fabric.SwitchClusterProfile object
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
        if self.user_label is not None:
            kwargs["user_label"] = self.user_label

        fabric_switch_cluster_profile = FabricSwitchClusterProfile(**kwargs)

        fscp = self.commit(
            object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
            payload=fabric_switch_cluster_profile,
            detail=self.name,
            return_relationship=True
        )
        if not fscp:
            return False

        # We now need to push the fabric.SwitchProfile objects for both Fabric Interconnects
        # FIXME: Add support for single Fabric Interconnect
        from intersight.model.fabric_switch_profile import FabricSwitchProfile
        switch_profile_a_kwargs = {
            "object_type": "fabric.SwitchProfile",
            "class_id": "fabric.SwitchProfile",
            "switch_cluster_profile": fscp,
            "policy_bucket": []
        }
        if self.name is not None:
            switch_profile_a_kwargs["name"] = self.name + "-A"
        if self.descr is not None:
            switch_profile_a_kwargs["description"] = self.descr

        switch_profile_b_kwargs = copy.deepcopy(switch_profile_a_kwargs)
        if self.name is not None:
            switch_profile_b_kwargs["name"] = self.name + "-B"

        for policy_section in ["network_connectivity_policy", "ntp_policy", "port_policies", "snmp_policy",
                               "switch_control_policy", "syslog_policy", "system_qos_policy", "vlan_policies",
                               "vsan_policies"]:
            if getattr(self, policy_section, None):
                if isinstance(getattr(self, policy_section, {}), dict):
                    policy_type = self._POLICY_MAPPING_TABLE.get(policy_section, {}).get("fabric_a")
                    fsp_a_policy_name = getattr(self, policy_section, {}).get("fabric_a")
                    fsp_b_policy_name = getattr(self, policy_section, {}).get("fabric_b")
                else:
                    policy_type = self._POLICY_MAPPING_TABLE.get(policy_section, None)
                    fsp_a_policy_name = fsp_b_policy_name = getattr(self, policy_section, None)

                if policy_type:
                    object_type = getattr(policy_type, "_INTERSIGHT_SDK_OBJECT_NAME", None)
                    if object_type:
                        # If fabric A policy name is missing then skip adding it to policy bucket.
                        if fsp_a_policy_name:
                            fsp_a_live_policy = self.get_live_object(object_name=fsp_a_policy_name, object_type=object_type)
                            if fsp_a_live_policy:
                                switch_profile_a_kwargs["policy_bucket"].append(fsp_a_live_policy)
                            else:
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"Attaching {policy_section} '{fsp_a_policy_name}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                                    message=f"Failed to find {policy_section} '{fsp_a_policy_name}'")

                        # If fabric B policy name is missing then skip adding it to policy bucket.
                        if fsp_b_policy_name:
                            fsp_b_live_policy = self.get_live_object(object_name=fsp_b_policy_name, object_type=object_type)
                            if fsp_b_live_policy:
                                switch_profile_b_kwargs["policy_bucket"].append(fsp_b_live_policy)
                            else:
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"Attaching {policy_section} '{fsp_b_policy_name}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                                    message=f"Failed to find {policy_section} '{fsp_b_policy_name}'")
                    else:
                        err_message = "Missing _INTERSIGHT_SDK_OBJECT_NAME value for " + policy_section
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching {policy_section} '{getattr(self, policy_section)}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)

                else:
                    err_message = "Missing entry for " + policy_section + " in _POLICY_MAPPING_TABLE"
                    self.logger(level="error", message=err_message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching {policy_section} '{getattr(self, policy_section)}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)

        fabric_switch_profile_a = FabricSwitchProfile(**switch_profile_a_kwargs)

        fspa = self.commit(
            object_type="fabric.SwitchProfile",
            payload=fabric_switch_profile_a,
            detail=self.name + " - Switch Profile FI A",
            key_attributes=["name", "switch_cluster_profile"]
        )
        if not fspa:
            return False

        fabric_switch_profile_b = FabricSwitchProfile(**switch_profile_b_kwargs)

        fspb = self.commit(
            object_type="fabric.SwitchProfile",
            payload=fabric_switch_profile_b,
            detail=self.name + " - Switch Profile FI B",
            key_attributes=["name", "switch_cluster_profile"]
        )
        if not fspb:
            return False

        return True
    

class IntersightUcsDomainProfileTemplate(IntersightGenericUcsDomainProfile):
    _CONFIG_NAME = "UCS Domain Profile Template"
    _CONFIG_SECTION_NAME = "ucs_domain_profile_templates"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.SwitchClusterProfileTemplate"

    def __init__(self, parent=None, fabric_switch_cluster_profile_template=None):
        IntersightGenericUcsDomainProfile.__init__(self, parent=parent, sdk_object=fabric_switch_cluster_profile_template)

        if self._config.load_from == "live":
            # We first need to identify the Moids of the fabric.SwitchProfileTemplate objects attached to the UCS Domain Profile Template
            self._switch_profile_templates = self.get_config_objects_from_ref(ref=self._object.switch_profile_templates)
            if self._switch_profile_templates:
                for switch_profile_template in self._switch_profile_templates:
                    for policy in switch_profile_template.policy_bucket:
                        for (policy_name, intersight_policy) in self._POLICY_MAPPING_TABLE.items():
                            if not isinstance(intersight_policy, dict) and \
                                    policy.object_type == getattr(intersight_policy, "_INTERSIGHT_SDK_OBJECT_NAME",
                                                                  None):
                                setattr(self, policy_name, self._get_policy_name(policy))
                                break

            self.port_policies = self._get_port_policies(self._switch_profile_templates)
            self.vlan_policies = self._get_vlan_policies(self._switch_profile_templates)
            self.vsan_policies = self._get_vsan_policies(self._switch_profile_templates)

        elif self._config.load_from == "file":
            for attribute in self._POLICY_MAPPING_TABLE.keys():
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of the Port Policies, VLAN Policies and VSAN Policies are set to
        # None if they are not present
        for parent_attribute in ["port_policies", "vlan_policies", "vsan_policies"]:
            for attribute in ["fabric_a", "fabric_b"]:
                if getattr(self, parent_attribute, None):
                    if attribute not in getattr(self, parent_attribute):
                        getattr(self, parent_attribute)[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_switch_cluster_profile_template import FabricSwitchClusterProfileTemplate

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We identify the parent organization as it will be used many times
        org = self.get_parent_org_relationship()
        if not org:
            return False

        # We first need to push the main fabric.SwitchClusterProfileTemplate object
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

        fabric_switch_cluster_profile_template = FabricSwitchClusterProfileTemplate(**kwargs)

        fscpt = self.commit(
            object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
            payload=fabric_switch_cluster_profile_template,
            detail=self.name,
            return_relationship=True
        )
        if not fscpt:
            return False
        
        # We now need to push the fabric.SwitchProfileTemplate objects for both Fabric Interconnects
        # FIXME: Add support for single Fabric Interconnect
        from intersight.model.fabric_switch_profile_template import FabricSwitchProfileTemplate
        switch_profile_template_a_kwargs = {
            "object_type": "fabric.SwitchProfileTemplate",
            "class_id": "fabric.SwitchProfileTemplate",
            "switch_cluster_profile_template": fscpt,
            "policy_bucket": []
        }
        if self.name is not None:
            switch_profile_template_a_kwargs["name"] = self.name + "-A"
        if self.descr is not None:
            switch_profile_template_a_kwargs["description"] = self.descr

        switch_profile_template_b_kwargs = copy.deepcopy(switch_profile_template_a_kwargs)
        if self.name is not None:
            switch_profile_template_b_kwargs["name"] = self.name + "-B"

        for policy_section in ["network_connectivity_policy", "ntp_policy", "port_policies", "snmp_policy",
                               "switch_control_policy", "syslog_policy", "system_qos_policy", "vlan_policies",
                               "vsan_policies"]:
            if getattr(self, policy_section, None):
                if isinstance(getattr(self, policy_section, {}), dict):
                    policy_type = self._POLICY_MAPPING_TABLE.get(policy_section, {}).get("fabric_a")
                    fspt_a_policy_name = getattr(self, policy_section, {}).get("fabric_a")
                    fspt_b_policy_name = getattr(self, policy_section, {}).get("fabric_b")
                else:
                    policy_type = self._POLICY_MAPPING_TABLE.get(policy_section, None)
                    fspt_a_policy_name = fspt_b_policy_name = getattr(self, policy_section, None)

                if policy_type:
                    object_type = getattr(policy_type, "_INTERSIGHT_SDK_OBJECT_NAME", None)
                    if object_type:
                        # If fabric A policy name is missing then skip adding it to policy bucket.
                        if fspt_a_policy_name:
                            fspt_a_live_policy = self.get_live_object(object_name=fspt_a_policy_name, object_type=object_type)
                            if fspt_a_live_policy:
                                switch_profile_template_a_kwargs["policy_bucket"].append(fspt_a_live_policy)
                            else:
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"Attaching {policy_section} '{fspt_a_policy_name}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                                    message=f"Failed to find {policy_section} '{fspt_a_policy_name}'")

                        # If fabric B policy name is missing then skip adding it to policy bucket.
                        if fspt_b_policy_name:
                            fspt_b_live_policy = self.get_live_object(object_name=fspt_b_policy_name, object_type=object_type)
                            if fspt_b_live_policy:
                                switch_profile_template_b_kwargs["policy_bucket"].append(fspt_b_live_policy)
                            else:
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, obj_detail=f"Attaching {policy_section} '{fspt_b_policy_name}'",
                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                                    message=f"Failed to find {policy_section} '{fspt_b_policy_name}'")
                    else:
                        err_message = "Missing _INTERSIGHT_SDK_OBJECT_NAME value for " + policy_section
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching {policy_section} '{getattr(self, policy_section)}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)

                else:
                    err_message = "Missing entry for " + policy_section + " in _POLICY_MAPPING_TABLE"
                    self.logger(level="error", message=err_message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching {policy_section} '{getattr(self, policy_section)}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed", message=err_message)

        fabric_switch_profile_template_a = FabricSwitchProfileTemplate(**switch_profile_template_a_kwargs)

        fspta = self.commit(
            object_type="fabric.SwitchProfileTemplate",
            payload=fabric_switch_profile_template_a,
            detail=self.name + " - Switch Profile Template FI A"
        )
        if not fspta:
            return False

        fabric_switch_profile_template_b = FabricSwitchProfileTemplate(**switch_profile_template_b_kwargs)

        fsptb = self.commit(
            object_type="fabric.SwitchProfileTemplate",
            payload=fabric_switch_profile_template_b,
            detail=self.name + " - Switch Profile Template FI B"
        )
        if not fsptb:
            return False

        return True
