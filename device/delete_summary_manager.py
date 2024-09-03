# coding: utf-8
# !/usr/bin/env python
from intersight.api.organization_api import OrganizationApi


class DeleteSummaryManager:
    def __init__(self, parent=None):
        # Initialize the delete summary dictionary to keep track of deletion statistics and details
        self.parent = parent
        self._init_delete_summary()
        self.orgs_mapping = None

    def _init_delete_summary(self):
        """
        Initialize the Delete Summary in Dictionary format for capturing different types of
        messages - Error, Warnings, Info related to different attributes of a Policy,
        fabric attributes and variables
        """
        self.delete_summary = {
            "summary": {
                "success": 0,  # Count of successful deletions
                "failed": 0,  # Count of failed deletions
                "skipped": 0,  # Count skipped deletions
                "total": 0  # Total count of deletions attempted
            },
            "deleted_objects": {}
        }

    def add_obj_status(self, obj, status="success", message=None):
        """
        Adds a deletion record to the summary.

        Args:
            obj (object): The object being deleted.
            status (str, optional): The status of the deletion, either "success", "failed", or "skipped".
            message (str, optional): Message in case of skipped or failed push
        Returns:
            bool: returns True.
        """
        # Generating organization moid-to-name mapping
        if self.orgs_mapping is None:
            self.orgs_mapping = {}
            org_objects = self.parent.query(api_class=OrganizationApi, sdk_object_type="organization_organization")
            for org in org_objects:
                self.orgs_mapping[org.moid] = org.name

        # Extract details from the object
        object_type = getattr(obj, 'object_type', None)
        object_name = getattr(obj, 'name', None)
        organization_moid = getattr(obj.organization, 'moid', None) if hasattr(obj, 'organization') else None

        # Fetch organization name using moid from the mapping
        organization_name = None
        if organization_moid and organization_moid in self.orgs_mapping:
            organization_name = self.orgs_mapping[organization_moid]

        # Update the summary counts based on the status of the deletion
        if status == "success":
            self.delete_summary["summary"]["success"] += 1
        elif status == "failed":
            self.delete_summary["summary"]["failed"] += 1
        elif status == "skipped":
            self.delete_summary["summary"]["skipped"] += 1  # Handle skipped status
        self.delete_summary["summary"]["total"] += 1

        # Create a dictionary to store information about the deletion
        deletion_info = {
            "object_type": object_type,
            "status": status,
        }
        if object_name:
            deletion_info["name"] = object_name
        if message:
            deletion_info["message"] = message

        # Add the deletion information under the appropriate organization
        # or directly under "deleted_objects" if not associated with any organization.
        if organization_name:
            org_info = next((org for org in self.delete_summary["deleted_objects"].get("organization.Organization", [])
                             if org["name"] == organization_name), None)
            if not org_info:
                org_info = {
                    "name": organization_name,
                    "status": status,
                    "object_type": "organization.Organization",
                }
                if message:  # message field to be added in case organization deletion fails.
                    org_info["message"] = message
                self.delete_summary["deleted_objects"].setdefault("organization.Organization", []).append(org_info)
            org_info.setdefault(object_type, []).append(deletion_info)
        else:
            if object_type != "organization.Organization":
                self.delete_summary["deleted_objects"].setdefault(object_type, []).append(deletion_info)

            # This condition ensures that the organization object itself is not added redundantly
            if object_type == "organization.Organization":
                org_info = next((org for org in self.delete_summary["deleted_objects"].get(object_type, []) if
                                 org["name"] == object_name), None)
                if not org_info:
                    self.delete_summary["deleted_objects"].setdefault(object_type, []).append(deletion_info)
                else:
                    # Update the existing organization info status
                    org_info["status"] = status
                    if message:
                        org_info["message"] = message
        return True

    def export_delete_summary_dict(self):
        """
        Returns the delete summary dictionary.

        Returns:
            dict: The delete summary dictionary containing deletion statistics and details.
        """
        return self.delete_summary
