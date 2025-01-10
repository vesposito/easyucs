class GenericCache:
    def __init__(self, parent=None):
        self.device = parent.parent
        self.parent = parent
        self._parent_having_logger = self._find_logger()

    def logger(self, level='info', message="No message", set_api_error_message=True):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message, set_api_error_message=set_api_error_message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in config")
            return None

    def __str__(self):
        return str(vars(self))
