# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """
from functools import wraps


class GenericConfigObject:
    def __init__(self, parent=None):
        self._parent = parent
        self._commit_status = []
        self._parent_having_logger = self._find_logger()

        self._config = self.__find_config()
        self._device = None
        if self._config:
            self._device = self._config.parent.parent  # noqa

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self

        while hasattr(current_object, '_parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object._parent

        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in config object")
            return None

    def __str__(self):
        return self.__class__.__name__ + "\n" + \
               str({key: value for key, value in vars(self).items() if not key.startswith('_')})

    def __find_config(self):
        # Method to find the Config object - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, '_parent') and not hasattr(current_object, 'metadata'):
            current_object = current_object._parent
        if hasattr(current_object, 'metadata'):
            return current_object
        else:
            return None

    def copy(self, new_parent=None, hierarchical=True):
        """
        This function creates a copy of a Generic Config Object.
        :param new_parent: Parent of the new (copied) config object
        :param hierarchical: Whether to copy EasyUCS objects which comes under the hierarchy of current object (self).
        E.g. When copying an Org:
        - hierarchical=True will copy all its fields including the list of EasyUCS objects
        policies/pools/profiles/templates
        - hierarchical=False will only copy non EasyUCS objects fields ('name','descr','resource_groups')
        :return: New (copied) config object if successful
        """
        def copy_subobject(source_subobject, subobject_parent=None):
            """
            Returns a copy of a sub-object of an EasyUCS object. Should be used if sub-object is list or dict.
            :param source_subobject: Source sub-object which needs to be copied (list or dict). It usually refers to
            vNICs, boot devices, etc.
            :param subobject_parent: Parent of the new (copied) sub-object.
            :return: New (copied) sub-object
            """
            if isinstance(source_subobject, dict):
                new_object = {}
                for key in source_subobject:
                    if isinstance(source_subobject[key], (list, dict)):
                        new_object[key] = copy_subobject(source_subobject[key], subobject_parent=subobject_parent)
                    elif isinstance(source_subobject[key], GenericConfigObject):
                        if hierarchical:
                            new_object[key] = source_subobject[key].copy(new_parent=subobject_parent)
                    else:
                        new_object[key] = source_subobject[key]
            else:
                new_object = []
                for element in source_subobject:
                    if isinstance(element, (list, dict)):
                        new_object.append(copy_subobject(element, subobject_parent=subobject_parent))
                    elif isinstance(element, GenericConfigObject):
                        if hierarchical:
                            new_object.append(element.copy(new_parent=subobject_parent))
                    else:
                        new_object.append(element)
            return new_object

        new_object = self.__class__(parent=new_parent)
        for attribute in vars(self):
            if not attribute.startswith('_') and getattr(self, attribute) is not None:
                if isinstance(getattr(self, attribute), (dict, list)):
                    # Attribute of EasyUCS object is a list or dictionary
                    setattr(new_object, attribute, copy_subobject(getattr(self, attribute),
                                                                  subobject_parent=new_object))
                elif isinstance(getattr(self, attribute), GenericConfigObject):
                    if hierarchical:
                        # Attribute of EasyUCS object is an EasyUCS object
                        new_copied_object = getattr(self, attribute).copy(new_parent=new_object)
                        setattr(new_object, attribute, new_copied_object)
                else:
                    # Attribute of EasyUCS object is a regular value
                    setattr(new_object, attribute, getattr(self, attribute))

        return new_object

    def get_attributes_from_json(self, json_content=None, allow_int=False, allow_bool=False):
        if json_content is None:
            return False

        for attribute in json_content.keys():
            if isinstance(json_content[attribute], str):
                setattr(self, attribute, json_content[attribute])
            # Support list of values (like for NTP entries)
            elif isinstance(json_content[attribute], list):
                setattr(self, attribute, [])
                for element in json_content[attribute]:
                    if isinstance(element, (str, dict)):
                        getattr(self, attribute).append(element)
            # Support dict of values (like for operational_state)
            elif isinstance(json_content[attribute], dict):
                setattr(self, attribute, json_content[attribute])
            elif isinstance(json_content[attribute], int) and allow_int:
                setattr(self, attribute, json_content[attribute])
            elif isinstance(json_content[attribute], bool) and allow_bool:
                setattr(self, attribute, json_content[attribute])
        return True

    @staticmethod
    def update_taskstep_description(attribute_name="name"):
        """
        Decorator to update the current task step description
        :param attribute_name: Attribute name which needs to added to the description
        :return: decorator function
        """
        def decorator(function):
            @wraps(function)
            def wrapper(self, *args, **kwargs):
                if self._device.task is not None:
                    if attribute_name and getattr(self, attribute_name, None) and getattr(self, "_CONFIG_NAME", None):
                        self._device.task.taskstep_manager.update_taskstep_description(
                            description=f"Pushing {self._CONFIG_NAME} with {attribute_name} "
                                        f"'{getattr(self, attribute_name)}'")
                return function(self, *args, **kwargs)
            return wrapper
        return decorator
