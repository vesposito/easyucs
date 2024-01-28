# coding: utf-8
# !/usr/bin/env python

""" push_summary_manager.py: Easy UCS Deployment Tool """
from config.object import GenericConfigObject


class PushSummaryManager:
    def __init__(self, parent=None):
        """
        Initializes all the necessary attributes
        """
        self.parent = parent
        self._init_push_summary()
        self._parent_having_logger = self._find_logger()

    def _init_push_summary(self):
        """
        Initialize the Push Summary in Dictionary format for capturing different types of
        messages - Error, Warnings, Info related to different attributes of a Policy,
        fabric attributes and variables
        """
        self.push_summary = {
            "summary": {
                "success": 0,
                "skipped": 0,
                "failed": 0,
                "total": 0
            },
            "pushed_objects": {}
        }

    def add_object_message(self, obj=None, message=None):
        """Adds push object success message to push summary dict
        Args:
            obj: EasyUCS object which calls the 'commit()'
            message (str): Message in case of success push
        Returns:
            True is successful, False otherwise
        """
        if obj._commit_status:
            obj._commit_status[-1]["message"] = message
            return True
        return False

    def add_object_status(self, obj=None, obj_detail=None, obj_type=None, status="", message=""):
        """Adds object's push status to the Push Summary Dict
        Args:
            obj: EasyUCS object which calls the 'commit()'
            obj_detail (str): Detail of the object being pushed
            obj_type (str): Type of the sdk object being pushed
            status (str): Status of the push (success, failed, skipped)
            message (str): Message in case of skipped or failed push
        Returns:
            True is successful, False otherwise
        """
        if not obj_detail:
            # TODO: Make sure that all `commit()` methods have a proper `detail` attribute. Especially for UCSM and
            #  UCSC devices
            self.logger(level="error", message="Invalid Object detail")
            return False
        if not obj_type:
            # TODO: Handled the scenario for empty `obj_type`. This can happen for UCSC and UCSM when we are calling
            #  `commit()`, without calling any `add_mo()`.
            self.logger(level="error", message="Invalid Object type")
            return False
        if status not in ["success", "skipped", "failed"]:
            self.logger(level="error", message="Invalid object push status")
            return False

        if obj._commit_status:
            if status == "failed":
                # In case of commit(retry=True), if the push fails both the times then we prevent adding the same
                # object twice
                if obj._commit_status[-1]["status"] == "failed" and obj_detail == obj._commit_status[-1]["detail"] and \
                        obj_type == obj._commit_status[-1]["sdk_object_type"]:
                    self.logger(level="debug", message="Object already present in Push Summary")
                    return True

                # In case of we are trying to commit the same object twice, and it fails to commit it the end time.
                # In this case we change the status of previous commit to failed.
                # Eg: While committing IntersightFabricSystemQosPolicy, we call commit() twice. There is a chance that
                # the 2nd commit fails.
                elif obj._commit_status[-1]["status"] == "success" and obj_detail == obj._commit_status[-1]["detail"] \
                        and obj_type == obj._commit_status[-1]["sdk_object_type"]:
                    obj._commit_status[-1]["status"] = status
                    if message:
                        obj._commit_status[-1]["message"] = message
                    self.push_summary["summary"]["failed"] += 1
                    self.push_summary["summary"]["success"] -= 1
                    return True

            elif status == "success":
                # In case of commit(retry=True), if push fails on first try and succeeds on second then we remove
                # the last failed status from the summary
                if obj._commit_status[-1]["status"] == "failed" and obj_detail == obj._commit_status[-1]["detail"] and \
                        obj_type == obj._commit_status[-1]["sdk_object_type"]:
                    obj._commit_status.pop()
                    self.push_summary["summary"]["total"] -= 1
                    self.push_summary["summary"]["failed"] -= 1

                # Only occurs when we are trying to push the same object twice and both the times the status was
                # success. In this case we don't add the same summary twice.
                elif obj._commit_status[-1]["status"] == "success" and obj_detail == obj._commit_status[-1]["detail"] \
                        and obj_type == obj._commit_status[-1]["sdk_object_type"]:
                    self.logger(level="debug", message="Object already present in Push Summary")
                    return True

        commit_status = {
            "detail": obj_detail,
            "status": status,
            "sdk_object_type": obj_type
        }
        if message:
            commit_status["message"] = message

        obj._commit_status.append(commit_status)

        self.push_summary["summary"]["total"] += 1
        if status == "success":
            self.push_summary["summary"]["success"] += 1
        elif status == "skipped":
            self.push_summary["summary"]["skipped"] += 1
        elif status == "failed":
            self.push_summary["summary"]["failed"] += 1

        return True

    @staticmethod
    def add_push_obj_status(current_object, push_summary_pointer):
        """
        Adds the push object status of all objects and sub-objects
        Args:
            current_object: EasyUCS object from where push summary is fetched
            push_summary_pointer: Dictionary that holds the details of all pushed objects
        """
        if not isinstance(current_object, dict):
            # We have an EasyUCS object
            if getattr(current_object, "_commit_status", None):
                push_summary_pointer["commit_status"] = current_object._commit_status
                push_summary_pointer["easyucs_object_type"] = current_object.__class__.__name__
                push_summary_pointer["easyucs_object_name"] = current_object._CONFIG_NAME
                if any([status["status"] == "failed" for status in current_object._commit_status]):
                    push_summary_pointer["push_status"] = "failed"
                elif all([status["status"] == "skipped" for status in current_object._commit_status]):
                    push_summary_pointer["push_status"] = "skipped"
                else:
                    push_summary_pointer["push_status"] = "success"
                if getattr(current_object, "name", None):
                    push_summary_pointer["name"] = current_object.name
            else:
                # This implies that commit() was not called for this EasyUCS object. Very unlikely to happen.
                if getattr(current_object, "name", None):
                    push_summary_pointer["name"] = current_object.name
                push_summary_pointer["push_status"] = "not_committed"
                push_summary_pointer["easyucs_object_type"] = current_object.__class__.__name__
                push_summary_pointer["easyucs_object_name"] = current_object._CONFIG_NAME

            for attribute in sorted(vars(current_object)):
                if not attribute.startswith('_') and not attribute == "dn" \
                        and getattr(current_object, attribute) is not None:
                    if any(isinstance(getattr(current_object, attribute), x) for x in [GenericConfigObject]):
                        # Attribute of EasyUCS object is an EasyUCS object
                        push_summary_pointer[attribute] = {}
                        PushSummaryManager.add_push_obj_status(getattr(current_object, attribute),
                                                               push_summary_pointer[attribute])
                    elif isinstance(getattr(current_object, attribute), list):
                        # Attribute of EasyUCS object is a list
                        if len(getattr(current_object, attribute)) == 0:
                            continue
                        element_count = 0
                        for element in getattr(current_object, attribute):
                            if isinstance(element, GenericConfigObject):
                                attribute_name = current_object._CONFIG_SECTION_ATTRIBUTES_MAP[attribute]
                                # Element of the list is an EasyUCS object
                                if attribute_name not in push_summary_pointer:
                                    push_summary_pointer[attribute_name] = []
                                push_summary_pointer[attribute_name].append({})
                                PushSummaryManager.add_push_obj_status(element,
                                                                       push_summary_pointer[attribute_name][
                                                                           element_count])
                                element_count += 1

    def _find_logger(self):
        """
        Method to find the object having a logger - it can be high up in the hierarchy of objects
        Returns:
            EasyUCS object having a logger if found, None otherwise
        """
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in config")
            return None

    @staticmethod
    def get_last_object_status(obj=None):
        """Gets the last object status from the Push Summary
        Args:
            obj: EasyUCS object which calls the 'commit()'
        Returns:
            "success", "failed", "skipped" or None
        """
        if obj._commit_status:
            return obj._commit_status[-1]["status"]
        return None

    def export_push_summary_dict(self):
        """Returns Push Summary Dictionary

        Returns:
            Dict: Returns Push Summary Dictionary
        """
        for export_attribute in self.parent.export_list:
            # We check if the attribute to be exported is an empty list, in which case, we don't export it
            if isinstance(getattr(self.parent, export_attribute), list):
                if len(getattr(self.parent, export_attribute)) == 0:
                    continue
            export_attribute_name = self.parent._CONFIG_SECTION_ATTRIBUTES_MAP[export_attribute]
            self.push_summary["pushed_objects"][export_attribute_name] = []
            if isinstance(getattr(self.parent, export_attribute), list):
                count = 0
                for config_object in getattr(self.parent, export_attribute):
                    self.push_summary["pushed_objects"][export_attribute_name].append({})
                    self.add_push_obj_status(config_object,
                                             self.push_summary["pushed_objects"][export_attribute_name][count])
                    count += 1

        return self.push_summary

    def logger(self, level='info', message="No message"):
        """
        Logger method to print log messages
        Args:
            level: Log level to be assigned
            message: Log message to be printed
        """
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def reset_commit_status(self, current_object):
        """
        Resetting the commit status of all EasyUCS objects and sub-objects
        Args:
            current_object: EasyUCS object whose commit status will be reset
        """
        # Clearing commit status of all objects and sub-objects
        if not isinstance(current_object, dict):
            # We have an EasyUCS object
            if getattr(current_object, "_commit_status", None):
                current_object._commit_status = []

            for attribute in sorted(vars(current_object)):
                if not attribute.startswith('_') and not attribute == "dn" \
                        and getattr(current_object, attribute) is not None:
                    if any(isinstance(getattr(current_object, attribute), x) for x in [GenericConfigObject]):
                        # Attribute of EasyUCS object is an EasyUCS object
                        self.reset_commit_status(current_object)
                    elif isinstance(getattr(current_object, attribute), list):
                        # Attribute of EasyUCS object is a list
                        if len(getattr(current_object, attribute)) == 0:
                            continue
                        for element in getattr(current_object, attribute):
                            if isinstance(element, GenericConfigObject):
                                self.reset_commit_status(element)

    def reset_push_summary(self):
        """
        Resetting the push summary of the config. This is done to avoid having legacy data when
        pushing the same config multiple times.
        """
        if self.push_summary.get("summary", {}).get("total", 0) != 0:
            self._init_push_summary()
            # Clearing commit status of each config object
            for export_attribute in self.parent.export_list:
                # We check if the attribute is an empty list, in which case, we don't reset the status
                if isinstance(getattr(self.parent, export_attribute), list):
                    if len(getattr(self.parent, export_attribute)) == 0:
                        continue
                    for config_object in getattr(self.parent, export_attribute):
                        self.reset_commit_status(config_object)
