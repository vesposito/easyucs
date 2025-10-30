# coding: utf-8
# !/usr/bin/env python

""" profiles.py: Easy UCS Deployment Tool """

from config.object import GenericConfigObject


class GenericUcsServiceProfile(GenericConfigObject):

    def analyze_vic_for_assigned_server(self, inventory_obj):
        """
        Analyze the VIC hardware configuration of the server assigned to this Service Profile.

        This function verifies whether the Service Profile is actively associated
        with a server and, if so, attempts to locate the corresponding server
        object in the UCS hardware inventory. Once the server is found, it inspects
        its network adapters to determine:
          - Whether the server has multiple VIC adapters.
          - Whether any of the adapters belong to the VIC 1300 series
            (e.g., VIC 1340, VIC 1380, VIC 1385).

        The results are stored as boolean attributes on the `service_profile`:
          - `_server_has_multiple_vic`: True if more than one VIC is installed.
          - `_server_has_vic_1300`: True if any VIC belongs to the 1300 series.

        :param inventory_obj: The source UCS inventory object (for checking VIC hardware configuration of the server)
        :return: True if successful, False otherwise
    """

        # If the hardware inventory is missing, exit
        if not inventory_obj:
            self.logger(level="error",
                        message=f"Missing inventory for analyzing VIC hardware configuration on profile {self.name}")
            return False

        if getattr(self, "type", "") != "instance":
            self.logger(
                level="error",
                message=f"Cannot perform VIC analysis;'{getattr(self, 'name', '')}' is not a service profile"
            )
            return False

        # Check operational state in config to skip unassociated profiles
        operational_state = getattr(self, "operational_state", {})
        profile_state = operational_state.get("profile_state")
        name = getattr(self, "name", "")
        assigned_server_info = operational_state.get("assigned_server")

        if profile_state == "unassociated":
            return False

        if not assigned_server_info:
            return False

        chassis_id = assigned_server_info.get("chassis_id")
        slot_id = assigned_server_info.get("slot_id")
        server_id = assigned_server_info.get("server_id")
        serial_number = assigned_server_info.get("serial_number")
        matching_chassis = None
        matching_server = None

        if chassis_id:
            if getattr(inventory_obj, "chassis", None):
                for chassis in inventory_obj.chassis:
                    chassis_id_val = chassis.get("id", "") if isinstance(chassis, dict) else getattr(chassis, "id", "")
                    if str(chassis_id_val) == str(chassis_id) and hasattr(chassis, "blades"):
                        matching_chassis = chassis
                        for blade in chassis.blades:
                            blade_slot_id = blade.get("slot_id") if isinstance(blade, dict) else getattr(blade,
                                                                                                         "slot_id",
                                                                                                         None)
                            blade_serial = blade.get("serial") if isinstance(blade, dict) else getattr(blade, "serial",
                                                                                                       None)
                            if str(blade_slot_id) == str(slot_id) and blade_serial == serial_number:
                                matching_server = blade
                                break

                        if not matching_server:
                            self.logger(level="warning",
                                        message="Unable to find server with serial " +
                                                str(serial_number) + " in slot " + str(slot_id) +
                                                " of chassis with ID " + str(chassis_id) +
                                                " in the inventory! Ignoring VIC analysis for profile " + name)

            if not matching_chassis:
                self.logger(level="warning", message="Unable to find chassis with ID " + str(
                    chassis_id) + " in the inventory! Ignoring VIC analysis for profile " + name)

        elif server_id:
            if getattr(inventory_obj, "rack_units", None):
                for ru in inventory_obj.rack_units:
                    ru_serial = ru.get("serial") if isinstance(ru, dict) else getattr(ru, "serial", None)
                    if ru_serial == serial_number:
                        matching_server = ru
                        break

            if not matching_server:
                self.logger(level="warning", message="Unable to find rack server with serial " + str(
                    serial_number) + " in the inventory! Ignoring VIC analysis for profile " + name)

        # If no matching server found, or server has no adapters info, exit
        if not matching_server or not getattr(matching_server, "adaptors", None):
            self.logger(
                level="warning",
                message=(
                    f"Unable to perform VIC analysis for profile {name} "
                    f"because no matching server was found or the server has no adapter information in the inventory!"
                )
            )
            return False

        # Get ONLY the VIC adapters from this server's adaptors
        vic_adapters = [a for a in matching_server.adaptors if getattr(a, "short_name", None) and "VIC" in a.short_name]

        vic_count = len(vic_adapters)
        self._server_has_multiple_vic = vic_count > 1
        self._server_has_vic_1300 = any(
            any(model in a.short_name for model in ["VIC 1340", "VIC 1380", "VIC 1385"])
            for a in vic_adapters
        )
        if self._server_has_multiple_vic or self._server_has_vic_1300:
            conditions = []
            if self._server_has_multiple_vic:
                conditions.append("has multiple VIC adapters")
            if self._server_has_vic_1300:
                conditions.append("includes a VIC 1300 series model")

            msg = f"Server assigned to profile '{name}' in org '{self._parent.name}' {' and '.join(conditions)}."
            self.logger(level="info", message=msg)

        return True

    def _gather_all_service_profiles(self, org):
        """
        Recursively collect all Service Profiles within a given UCS organization tree.

        This function traverses an organization (`org`) and all its sub-organizations
        to gather every Service Profile.
        Returns:
            list: A flat list of all Service Profile objects found within
                  the organization tree.
        """
        profiles = []
        if hasattr(org, "service_profiles") and org.service_profiles:
            profiles.extend(org.service_profiles)

        if hasattr(org, "orgs") and org.orgs:
            for suborg in org.orgs:
                profiles.extend(self._gather_all_service_profiles(suborg))
        return profiles

    def find_bound_profiles(self):
        """
        Find all UCS service profiles that are bound to this service profile template.

        Returns:
            list: A list of UCS service profile objects that are bound to the given template.
        """
        # Ensure self is indeed a Service Profile Template
        if not getattr(self, "type", None) in ("updating-template", "initial-template"):
            self.logger(level="error", message="Can only find Service Profiles bound to a Service Profile Template")
            return []

        # Get the template name
        referenced_template_name = getattr(self, "name", None)

        # Extract organization path from the template's distinguished name (_dn)
        dn = getattr(self, "_dn", None)
        referenced_template_org_path = None
        if dn:
            for part in dn.split("/"):
                if part.startswith("org-"):
                    # Store the org path without the "org-" prefix
                    referenced_template_org_path = part.replace("org-", "")
                    break

        # Gather all service profiles under this organization
        all_service_profiles = self._gather_all_service_profiles(self._parent)
        # Now filter only those profiles that are explicitly bound to this template
        bound_profiles = []
        for profile in all_service_profiles:
            # Every profile may have a reference to its template in operational_state
            template_ref = profile.operational_state.get("service_profile_template")

            # Match both template name and org path to confirm binding
            if template_ref is not None and \
                    template_ref.get("name") == referenced_template_name and \
                    template_ref.get("org") == referenced_template_org_path:
                bound_profiles.append(profile)

        return bound_profiles

