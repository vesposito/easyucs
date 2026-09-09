# coding: utf-8
# !/usr/bin/env python

""" profiles.py: Easy UCS Deployment Tool """

from config.object import GenericConfigObject


class GenericUcsServiceProfile(GenericConfigObject):

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

        # Get the full "readable" org path of the org this template belongs to (e.g. "root/Org1").
        # We rely on the org object's own get_org_path() rather than manually parsing the template's DN,
        # since manually taking only the first "org-" segment of the DN would incorrectly return just the
        # top-level org (e.g. "root") for templates that actually live in a nested sub-org (e.g. "root/Org1"),
        # causing this method to never match any bound profiles in that case.
        referenced_template_org_path = None
        if hasattr(self._parent, "get_org_path"):
            referenced_template_org_path = self._parent.get_org_path()

        # Gather all service profiles under this organization
        all_service_profiles = self._gather_all_service_profiles(self._parent)
        # Now filter only those profiles that are explicitly bound to this template
        bound_profiles = []
        for profile in all_service_profiles:
            # Every profile may have a reference to its template in operational_state
            template_ref = getattr(profile, "operational_state", {}).get("service_profile_template")

            # Match both template name and org path to confirm binding
            if template_ref is not None and \
                    template_ref.get("name") == referenced_template_name and \
                    template_ref.get("org") == referenced_template_org_path:
                bound_profiles.append(profile)

        return bound_profiles

