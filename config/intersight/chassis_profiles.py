# coding: utf-8
# !/usr/bin/env python

""" chassis_profiles.py: Easy UCS Deployment Tool """

from config.intersight.object import IntersightConfigObject
from config.intersight.server_policies import IntersightThermalPolicy, IntersightSnmpPolicy, IntersightPowerPolicy, \
    IntersightImcAccessPolicy


class IntersightGenericUcsChassisProfile(IntersightConfigObject):
    _POLICY_MAPPING_TABLE = {
        "imc_access_policy": IntersightImcAccessPolicy,
        "power_policy": IntersightPowerPolicy,
        "snmp_policy": IntersightSnmpPolicy,
        "thermal_policy": IntersightThermalPolicy
    }

    def __init__(self, parent=None, sdk_object=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=sdk_object)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.user_label = self.get_attribute(attribute_name="user_label")

        self.imc_access_policy = None
        self.power_policy = None
        self.snmp_policy = None
        self.thermal_policy = None


class IntersightUcsChassisProfile(IntersightGenericUcsChassisProfile):
    _CONFIG_NAME = "UCS Chassis Profile"
    _CONFIG_SECTION_NAME = "ucs_chassis_profiles"
    _INTERSIGHT_SDK_OBJECT_NAME = "chassis.Profile"
    
    def __init__(self, parent=None, chassis_profile=None):
        IntersightGenericUcsChassisProfile.__init__(self, parent=parent, sdk_object=chassis_profile)

        # operational_state consist the assigned chassis details
        # self.assigned_chassis = None
        # self.associated_chassis = None
        self.chassis_pre_assign_by_serial = None
        self.ucs_chassis_profile_template = None
        self.operational_state = {}
        
        if "chassis_pre_assign_by_serial" in self._object and self._object["chassis_pre_assign_by_serial"]:
            self.chassis_pre_assign_by_serial = self._object["chassis_pre_assign_by_serial"]

        if self._config.load_from == "live":
            if hasattr(self._object, "assigned_chassis"):
                if self._object.assigned_chassis:
                    if self._object.assigned_chassis.object_type == "equipment.Chassis":
                        self.operational_state["assigned_chassis"] = {}
                        chassis_details = self._get_chassis(self._object.assigned_chassis)
                        if chassis_details:
                            (
                                self.operational_state["assigned_chassis"]["serial_number"],
                                self.operational_state["assigned_chassis"]["chassis_id"],
                                self.operational_state["assigned_chassis"]["model"],
                            ) = chassis_details

            # If this UCS Chassis Profile is derived from a UCS Chassis Profile Template,
            # we only get the source template
            if hasattr(self._object, "src_template"):
                if self._object.src_template:
                    self.ucs_chassis_profile_template = self._get_policy_name(self._object.src_template)

            if not self.ucs_chassis_profile_template:
                for policy in self._object.policy_bucket:
                    for (policy_name, intersight_policy) in self._POLICY_MAPPING_TABLE.items():
                        if policy.object_type == getattr(intersight_policy, "_INTERSIGHT_SDK_OBJECT_NAME", None):
                            setattr(self, policy_name, self._get_policy_name(policy))
                            break

            # Fetching the status of the profile
            if hasattr(self._object, "config_context"):
                if hasattr(self._object.config_context, "config_state"):
                    self.operational_state.update({
                        "config_state": getattr(self._object.config_context, "config_state", None)
                    })
                if getattr(self._object.config_context, "oper_state", None):
                    self.operational_state.update({
                        "profile_state": getattr(self._object.config_context, "oper_state", None)
                    })

        elif self._config.load_from == "file":
            for attribute in ["chassis_pre_assign_by_serial", "imc_access_policy", "operational_state",
                              "power_policy", "snmp_policy", "thermal_policy", "ucs_chassis_profile_template"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
        
        self.clean_object()

    def clean_object(self):
        if self.operational_state:
            for attribute in ["assigned_chassis", "config_state", "profile_state"]:
                if attribute not in self.operational_state:
                    self.operational_state[attribute] = None

            if self.operational_state.get("assigned_chassis", None):
                for attribute in ["chassis_id", "model", "serial_number"]:
                    if attribute not in self.operational_state["assigned_chassis"]:
                        self.operational_state["assigned_chassis"][attribute] = None

    def _get_chassis(self, chassis_obj):
        chassis_obj_list = self.get_config_objects_from_ref(ref=chassis_obj)
        if (len(chassis_obj_list)) != 1:
            self.logger(
                level="debug",
                message="Could not find the appropriate " + str(chassis_obj.object_type) + " for Chassis with MOID " +
                        str(chassis_obj.moid),
            )
        else:
            if chassis_obj.object_type == "equipment.Chassis":
                return chassis_obj_list[0].serial, chassis_obj_list[0].chassis_id, chassis_obj_list[0].model
        return None
        
    def _update_chassis_pre_assignment(self, chassis_profile=None):
        from intersight.api.chassis_api import ChassisApi
        from intersight.model.chassis_profile import ChassisProfile

        if not chassis_profile:
            live_chassis_profile = self.get_live_object(
                object_name=self.name,
                object_type="chassis.Profile",
                return_reference=False
            )
            if not live_chassis_profile:
                if not self.chassis_pre_assign_by_serial:
                    return True
                self.logger(
                    level="error",
                    message=f"Unable to find Chassis Profile {self.name}"
                )
                return False
            chassis_profile = live_chassis_profile

        if getattr(chassis_profile, "chassis_pre_assign_by_serial", None) == self.chassis_pre_assign_by_serial:
            return True

        profile_update = ChassisProfile(
            object_type="chassis.Profile",
            class_id="chassis.Profile",
            chassis_pre_assign_by_serial=self.chassis_pre_assign_by_serial or "", 
            chassis_assignment_mode='None'
        )

        try:
            chassis_api = ChassisApi(self._device.handle)

            chassis_api.patch_chassis_profile(
                moid=chassis_profile.moid,
                chassis_profile=profile_update
            )

            self.logger(
                level="info",
                message=f"{'Updated' if self.chassis_pre_assign_by_serial else 'Cleared'} pre-assigned serial "
                        f"for chassis profile {self.name}"
            )

            return True

        except Exception as err:
            self.logger(
                level="error",
                message=f"Failed to update chassis pre-assignment: {err}"
            )
            return False

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.chassis_profile import ChassisProfile
        from intersight.model.chassis_profile_template import ChassisProfileTemplate

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        assigned_chassis = (self.operational_state or {}).get("assigned_chassis") or {}
        serial_number = assigned_chassis.get("serial_number")
        if serial_number:
            self.chassis_pre_assign_by_serial = serial_number

        # We identify the parent organization as it will be used many times
        org = self.get_parent_org_relationship()
        if not org:
            return False
        
        # We first need to check if a UCS Chassis Profile with the same name already exists
        chassis_profile = self.get_live_object(object_name=self.name, object_type="chassis.Profile",
                                               return_reference=False, log=False)

        if not getattr(self._config, "update_existing_intersight_objects", False) and chassis_profile:
            message = f"Skipping push of object type {self._INTERSIGHT_SDK_OBJECT_NAME} with name={self.name} as " \
                      f"it already exists"
            self.logger(level="info", message=message)
            self._config.push_summary_manager.add_object_status(
                obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="skipped",
                message=message)
            return True
        
        # In case this UCS Chassis Profile needs to be bound to a Template, we use the 'derive' mechanism to create it
        if self.ucs_chassis_profile_template:
            template_org = org
            template_name = self.ucs_chassis_profile_template
            if "/" in template_name:
                shared_org_name = template_name.split("/", 1)[0]
                template_org = self.get_org_relationship(org_name=shared_org_name)
                template_name = template_name.split("/", 1)[1]
                if not template_org:
                    err_message = (f"Unable to locate organization '{shared_org_name}' of UCS Chassis Profile Template "
                                   f"'{self.ucs_chassis_profile_template}' to derive UCS Chassis Profile {self.name}")
                    self.logger(level="error", message=err_message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                        status="failed", message=err_message)
                    return False

            template_full_path = self.ucs_chassis_profile_template
            if "/" not in template_full_path:
                template_full_path = f"{self._parent.name}/{template_name}"
            ucs_chassis_profile_template = self.get_live_object(
                object_name=template_name,
                object_type="chassis.ProfileTemplate", return_reference=False, log=False,
                query_filter=f"Name eq '{template_name}' and Organization.Moid eq '{template_org.moid}'")
            if not ucs_chassis_profile_template:
                err_message = "Unable to locate source UCS Chassis Profile Template " + \
                              template_full_path + " to derive UCS Chassis Profile " + self.name
                self.logger(level="error", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                    status="failed", message=err_message)
                return False
            template_reference = self.create_relationship_equivalent(sdk_object=ucs_chassis_profile_template)
            if not template_reference:
                err_message = "Unable to locate source UCS Chassis Profile Template " + \
                              template_full_path + " to derive UCS Chassis Profile " + self.name
                self.logger(level="error", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                    status="failed", message=err_message)
                return False

            if not chassis_profile:
                # No UCS Chassis Profile with the same name exists, so we can derive the UCS Chassis Profile Template
                from intersight.model.bulk_mo_cloner import BulkMoCloner

                kwargs_mo_cloner = {
                    "sources": [],
                    "targets": []
                }

                # We need to identify the Moid of the source UCS Chassis Profile Template
                template_moid = ucs_chassis_profile_template.moid
                source_template = {
                    "moid": template_moid,
                    "object_type": "chassis.ProfileTemplate"
                }
                kwargs_mo_cloner["sources"].append(ChassisProfileTemplate(**source_template))

                # We now need to specify the attribute of the target UCS Chassis Profile
                target_profile = {
                    "name": self.name,
                    "object_type": "chassis.Profile",
                    "organization": org
                }
                if self.descr is not None:
                    target_profile["description"] = self.descr
                if self.tags is not None:
                    target_profile["tags"] = self.create_tags()
                if self.user_label is not None:
                    target_profile["user_label"] = self.user_label
                kwargs_mo_cloner["targets"].append(ChassisProfile(**target_profile))

                mo_cloner = BulkMoCloner(**kwargs_mo_cloner)

                if not self.commit(object_type="bulk.MoCloner", payload=mo_cloner, detail=self.name):
                    return False
                return self._update_chassis_pre_assignment()
            else:
                # We found a UCS Chassis Profile with the same name, we need to check if it is bound to a Template
                if chassis_profile.src_template:
                    src_template = self._device.query(
                        object_type="chassis.ProfileTemplate",
                        filter="Moid eq '" + chassis_profile.src_template.moid + "'"
                    )
                    if len(src_template) == 1:
                        if chassis_profile.src_template.moid == ucs_chassis_profile_template.moid:
                            # UCS Chassis Profile is already derived from the same UCS Chassis Profile Template
                            info_message = "UCS Chassis Profile " + self.name + " exists and is already derived " + \
                                           "from UCS Chassis Profile Template " + template_full_path
                            self.logger(level="info", message=info_message)
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                                status="skipped", message=info_message)
                            if (getattr(self._config, "update_existing_intersight_objects", False) and
                                    not getattr(chassis_profile, "assigned_chassis", None)):
                                return self._update_chassis_pre_assignment(chassis_profile=chassis_profile)
                            return True
                        else:
                            # UCS Chassis Profile is derived from another UCS Chassis Profile Template
                            # We will detach it from its Template and reattach it to the desired Template
                            source_orgs = self._device.query(
                                object_type="organization.Organization",
                                filter=f"Moid eq '{src_template[0].organization.moid}'"
                            )
                            source_org_name = (source_orgs[0].name if len(source_orgs) == 1
                                               else src_template[0].organization.moid)
                            source_template_full_path = f"{source_org_name}/{src_template[0].name}"
                            self.logger(
                                level="info",
                                message="UCS Chassis Profile " + self.name +
                                        " exists and is derived from different UCS Chassis Profile Template " +
                                        source_template_full_path
                            )
                            self.logger(
                                level="info",
                                message="Detaching UCS Chassis Profile " + self.name +
                                        " from UCS Chassis Profile Template " + source_template_full_path
                            )
                            kwargs = {
                                "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
                                "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
                                "organization": org,
                                "name": self.name,
                                "src_template": None
                            }
                            update_profile = ChassisProfile(**kwargs)

                            if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=update_profile,
                                               detail="Detaching from template " + src_template[0].name):
                                return False

                            self.logger(
                                level="info",
                                message="Attaching UCS Chassis Profile " + self.name +
                                        " to UCS Chassis Profile Template " + template_full_path
                            )
                            # We need to identify the Moid of the UCS Chassis Profile Template
                            kwargs["src_template"] = template_reference
                            if self.chassis_pre_assign_by_serial:
                                kwargs["chassis_pre_assign_by_serial"] = self.chassis_pre_assign_by_serial
                                kwargs["chassis_assignment_mode"] = "None"
                            else:
                                kwargs["chassis_pre_assign_by_serial"] = ''
                            update_profile = ChassisProfile(**kwargs)

                            if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=update_profile,
                                               detail="Attaching to template " + self.ucs_chassis_profile_template):
                                return False

                            return True
                    else:
                        err_message = "Could not find UCS Chassis Profile Template " + template_full_path
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=self.name, obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=err_message)
                        return False
                else:
                    # UCS Chassis Profile is not currently bound to a template. So we just need to bind it
                    # We need to identify the Moid of the UCS Chassis Profile Template
                    kwargs = {
                        "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
                        "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
                        "organization": org,
                        "name": self.name,
                        "src_template": template_reference
                    }
                    if self.chassis_pre_assign_by_serial:
                        kwargs["chassis_pre_assign_by_serial"] = self.chassis_pre_assign_by_serial
                        kwargs["chassis_assignment_mode"] = "None"
                    else:
                        kwargs["chassis_pre_assign_by_serial"] = ''
                    update_profile = ChassisProfile(**kwargs)

                    if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=update_profile,
                                       detail="Attaching to template " + self.ucs_chassis_profile_template):
                        return False

                    return True

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

        kwargs["policy_bucket"] = []
        for policy_name in self._POLICY_MAPPING_TABLE.keys():
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
                                message=f"Failed to find {policy_name} '{getattr(self, policy_name)}''")
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

        profile_payload = ChassisProfile(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=profile_payload, detail=self.name):
            return False

        return self._update_chassis_pre_assignment(chassis_profile=chassis_profile)


class IntersightUcsChassisProfileTemplate(IntersightGenericUcsChassisProfile):
    _CONFIG_NAME = "UCS Chassis Profile Template"
    _CONFIG_SECTION_NAME = "ucs_chassis_profile_templates"
    _INTERSIGHT_SDK_OBJECT_NAME = "chassis.ProfileTemplate"

    def __init__(self, parent=None, chassis_profile_template=None):
        IntersightGenericUcsChassisProfile.__init__(self, parent=parent, sdk_object=chassis_profile_template)

        if self._config.load_from == "live":
            for policy in self._object.policy_bucket:
                for (policy_name, intersight_policy) in self._POLICY_MAPPING_TABLE.items():
                    if policy.object_type == getattr(intersight_policy, "_INTERSIGHT_SDK_OBJECT_NAME", None):
                        setattr(self, policy_name, self._get_policy_name(policy))
                        break

        elif self._config.load_from == "file":
            for attribute in ["imc_access_policy", "power_policy", "snmp_policy",
                              "thermal_policy"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.chassis_profile_template import ChassisProfileTemplate

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
        for policy_name in self._POLICY_MAPPING_TABLE.keys():
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
                                message=f"Failed to find {policy_name} '{getattr(self, policy_name)}''")
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

        chassis_profile_template = ChassisProfileTemplate(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=chassis_profile_template,
                           detail=self.name):
            return False

        return True
