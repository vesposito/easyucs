# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

import time
import urllib

from imcsdk.imcexception import ImcException
from ucscsdk.ucscexception import UcscException
from ucsmsdk.ucsexception import UcsException


class GenericConfigObject:
    def __init__(self, parent=None):
        self._parent = parent
        self._parent_having_logger = self._find_logger()

        self._config = self.__find_config()
        self._device = None
        if self._config:
            self._device = self._config.parent.parent

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
        return self.__class__.__name__ + "\n" +\
               str({key: value for key, value in vars(self).items() if not key.startswith('_')})

    def __find_config(self):
        # Method to find the Config object - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, '_parent') and not hasattr(current_object, 'timestamp'):
            current_object = current_object._parent
        if hasattr(current_object, 'timestamp'):
            return current_object
        else:
            return None


class GenericUcsConfigObject(GenericConfigObject):
    def __init__(self, parent=None):
        GenericConfigObject.__init__(self, parent=parent)
        self._dn = None
        self._handle = self._config.parent.parent.handle

    def get_attributes_from_json(self, json_content=None):
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
        return True

    def clean_object(self):
        """
        Clean the NA or N/A or None or none or empty values of a config object

        :return:
        """

        if self.__class__.__name__ in ["UcsSystemBiosPolicy", "UcsSystemDefaultVhbaBehavior",
                                       "UcsSystemDefaultVnicBehavior"]:
            # We do not clean "None" values in a BIOS Policy because some parameters are using the string "None"
            # Default vHBA / vNIC Behavior can also contain the string "None" as the default value for "action"
            str_to_avoid = ["N/A", "", "NA"]
        else:
            str_to_avoid = ["N/A", "", "NA", "none", "None"]

        for key in self.__dict__.keys():
            if getattr(self, key) in str_to_avoid:
                # self.logger(level="debug",
                #             message="In " + self._CONFIG_NAME + ", key '" + key + "' with value " +
                #                     (getattr(self, key) if getattr(self, key) != "" else "''") + " cleaned")
                setattr(self, key, None)

            elif getattr(self, key).__class__.__name__ == "list":
                for item in getattr(self, key):
                    if item.__class__.__name__ == "dict":
                        for item_key, value in item.items():
                            if value in str_to_avoid:
                                # self.logger(level="debug",
                                #             message="In " + self._CONFIG_NAME + ", in " + key + ": key '" + item_key +
                                #                     "' with value " +
                                #                     (item[item_key] if item[item_key] != "" else "''") + " cleaned")
                                item[item_key] = None


class UcsSystemConfigObject(GenericUcsConfigObject):
    def __init__(self, parent=None):
        GenericUcsConfigObject.__init__(self, parent=parent)

    def commit(self, detail="", show=True, retry=True):
        try:
            self._handle.commit()
            if show:
                if detail:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME + " - " + detail)
                else:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME)
            return True

        except UcsException as err:
            if retry:
                if err.error_descr == "Authorization required":
                    self.logger(level="debug", message="Fail to commit: " + err.error_descr + " " + detail +
                                                       ". Trying to commit again")
                    if self.retry_commit(detail=detail, show=show):
                        return True
                self._handle.commit_buffer_discard()
                self._config.refresh_config_handle()
            if show:
                if detail:
                    self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + " - " + detail +
                                                       " - " + err.error_descr)
                else:
                    self.logger(level="error",
                                message="Error in configuring " + self._CONFIG_NAME + ": " + err.error_descr)
            return err

        except urllib.error.URLError as err:
            if retry:
                self.logger(level="debug", message="Fail to commit: " + "Timeout error" + " " + detail +
                                                   ". Trying to commit again")
                if self.retry_commit(detail=detail, show=show):
                    return True
                self._handle.commit_buffer_discard()
            if show:
                self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + ": " + "Timeout error")
            return err

        except Exception as err:
            # We first discard the commit buffer in order to avoid resending the bad buffer content in the next commit
            self._handle.commit_buffer_discard()
            if show:
                self.logger(level="error", message="Unknown error in configuring " + self._CONFIG_NAME)
            return err

    def retry_commit(self, detail="", show=True):
        for i in range(self._device.push_attempts):
            if detail:
                self.logger(level="warning",
                            message="Trying to push again the " + self._CONFIG_NAME + " " + detail + " configuration")
            else:
                self.logger(level="warning", message="Trying to push again the " + self._CONFIG_NAME + " configuration")
            if self._device.is_connected():
                if self.commit(retry=False, show=False):
                    if show:
                        if detail:
                            self.logger(level="debug",
                                        message="Successfully configured " + self._CONFIG_NAME + " - " + detail)
                        else:
                            self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME)
                    return True
            else:
                self.logger(level="error", message="Not successfully connected. Trying to reconnect")
                self._device.connect()
            time.sleep(self._device.push_interval_after_fail)

        # Only accessible if the retries failed to push the commit
        if self._device.push_attempts:
            self.logger(level="error",
                        message="Impossible to push the " + self._CONFIG_NAME +
                                " configuration even after multiple attempts. Thus, the buffer will be discarded.")
        return False


class UcsImcConfigObject(GenericUcsConfigObject):
    def __init__(self, parent=None):
        GenericUcsConfigObject.__init__(self, parent=parent)

    def commit(self, mo=None, detail=""):
        try:
            if mo is not None:
                self._handle.set_mo(mo=mo)
                return True

        except ImcException as err:
            if detail:
                self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + " - " + detail +
                                                   " - " + err.error_descr)
            else:
                self.logger(level="error",
                            message="Error in configuring " + self._CONFIG_NAME + ": " + err.error_descr)

        except urllib.error.URLError:
            self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + ": " + "Timeout error")

        except TimeoutError:
            self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + ": " + "Timeout error")

        except Exception as err:
            self.logger(level="debug", message="Unknown error in configuring " + self._CONFIG_NAME + " " + str(err))
            self.logger(level="error", message="Unknown error in configuring " + self._CONFIG_NAME)
        return False


class UcsCentralConfigObject(GenericUcsConfigObject):
    def __init__(self, parent=None):
        GenericUcsConfigObject.__init__(self, parent=parent)

    def commit(self, detail="", show=True, retry=True):
        try:
            self._handle.commit()
            if show:
                if detail:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME + " - " + detail)
                else:
                    self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME)
            return True

        except UcscException as err:
            if retry:
                if err.error_descr == "Authorization required":
                    self.logger(level="debug", message="Fail to commit: " + err.error_descr + " " + detail +
                                                       ". Trying to commit again")
                    if self.retry_commit(detail=detail, show=show):
                        return True
                self._handle.commit_buffer_discard()
                self._config.refresh_config_handle()
            if show:
                if detail:
                    self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + " - " + detail +
                                                       " - " + err.error_descr)
                else:
                    self.logger(level="error",
                                message="Error in configuring " + self._CONFIG_NAME + ": " + err.error_descr)
            return err

        except urllib.error.URLError as err:
            if retry:
                self.logger(level="debug",
                            message="Fail to commit: " + "Timeout error" + " " + detail + ". Trying to commit again")
                if self.retry_commit(detail=detail, show=show):
                    return True
                self._handle.commit_buffer_discard()
            if show:
                self.logger(level="error", message="Error in configuring " + self._CONFIG_NAME + ": " + "Timeout error")
            return err

        except Exception as err:
            # We first discard the commit buffer in order to avoid resending the bad buffer content in the next commit
            self._handle.commit_buffer_discard()
            if show:
                self.logger(level="error", message="Unknown error in configuring " + self._CONFIG_NAME)
            return err

    def retry_commit(self, detail="", show=True):
        for i in range(self._device.push_attempts):
            if detail:
                self.logger(level="warning",
                            message="Trying to push again the " + self._CONFIG_NAME + " " + detail + " configuration")
            else:
                self.logger(level="warning", message="Trying to push again the " + self._CONFIG_NAME + " configuration")
            if self._device.is_connected():
                if self.commit(retry=False, show=False):
                    if show:
                        if detail:
                            self.logger(level="debug",
                                        message="Successfully configured " + self._CONFIG_NAME + " - " + detail)
                        else:
                            self.logger(level="debug", message="Successfully configured " + self._CONFIG_NAME)
                    return True
            else:
                self.logger(level="error", message="Not successfully connected. Trying to reconnect")
                self._device.connect()
            time.sleep(self._device.push_interval_after_fail)

        # Only accessible if the retries failed to push the commit
        if self._device.push_attempts:
            self.logger(level="error",
                        message="Impossible to push the " + self._CONFIG_NAME +
                                " configuration even after multiple attempts. Thus, the buffer will be discarded.")
        return False
