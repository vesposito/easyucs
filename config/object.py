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
                function(self, *args, **kwargs)
            return wrapper
        return decorator
