# coding: utf8
# !/usr/bin/env python

""" easyucs_api.py: Easy UCS Deployment Tool """
import datetime
import inspect
import logging

from werkzeug.middleware.dispatcher import \
    DispatcherMiddleware  # use to combine each Flask app into a larger one that is dispatched based on prefix
from werkzeug.serving import run_simple  # werkzeug development server
from werkzeug.local import Local

from api.api_server import app as easyucs_backend
from api.api_server import start
from device.manager import DeviceManager
from urls.gui import app as easyucs_frontend
from urls.repo import app as easyucs_repo
from urls.repo import start as repo_start
from repository.manager import RepositoryManager
from task.manager import TaskManager

application = DispatcherMiddleware(
    easyucs_frontend, 
    {
        '/api/v1': easyucs_backend,
        '/repo': easyucs_repo
    }
)


class Easyucs:
    def __init__(self, logger_handle_log_level="info", log_file_path=None):
        self.logger_handle_log_level = logger_handle_log_level
        self._log_file_path = log_file_path
        self._logger_buffer = []
        self._logger_handle = None
        self._logger_keeper = {"error": [], "critical": [], "warning": [], "info": [], "debug": [], "all": []}
        self._logger_summary = ""

        self._init_logger()

        # We create an object of werkzeug.local.Local. This helps us use context-local variables. A context local is
        # defined/imported globally, but the data it contains is specific to the current thread, asyncio task, or
        # greenlet. You won’t accidentally get or overwrite another worker’s data.
        # Refer: https://werkzeug.palletsprojects.com/en/2.2.x/local/
        self._thread_local = Local()

        self.device_manager = DeviceManager(parent=self)
        self.repository_manager = RepositoryManager(parent=self)
        self.task_manager = TaskManager(parent=self)

    # We override __getstate__ and __setstate__. These functions are component of pickle.
    # When multi-threading : in order to get from the main operational task to multiple thread, python uses them
    # Each time a thread is created or destroyed, the code goes through __get__ and then __set__
    #
    #   Main                         |  __getstate__                                             ^    __setstate__
    #   ------Creating the thread ---|--------------------------------Terminating the thread-----|-------------------
    #   Thread                       v  __setstate__                                             |    __getstate__
    #
    # While multi-threading all the info are serialized so it's impossible with the logger to multi-threading a device
    # We need to override these functions because a stream object like a logger can not be serialize
    # We change the logger by it's name during the __getstate__ so it's just a string an not a stream
    # In __setstate__  we create a new logger handle or get back to the root logger depending on the situation
    # In the Thread, the memory is not shared so it's impossible the find the previously created root logger
    # But when we get back to the Main, the root logger will be recovered
    #
    def __getstate__(self):
        d = self.__dict__.copy()
        if '_logger_handle' in d.keys():
            d['_logger_handle'] = d['_logger_handle'].name
        return d

    def __setstate__(self, d):
        if '_logger_handle' in d.keys():
            d['_logger_handle'] = logging.getLogger(d['_logger_handle'])
        self.__dict__.update(d)
        self._init_logger()

    @property
    def api_error_message(self):
        # Property 'api_error_message' is a thread local attribute (which means it's unique for each thread/request).
        # This method defines is a getter() method to get field 'api_error_message' from the thread local storage.
        if hasattr(self._thread_local, "api_error_message"):
            return self._thread_local.api_error_message
        return ""

    @api_error_message.setter
    def api_error_message(self, err_message=""):
        # This method defines is a setter() method to set the field 'api_error_message' in the thread local storage.
        self._thread_local.api_error_message = err_message

    def _init_logger(self):
        # We need to avoid dot in the logger name because if there is more than one dot it will create multiple
        # logger handles
        self.logger_target = "EasyUCS"

        # We use a custom named logger
        self._logger_handle = logging.getLogger(self.logger_target)
        self._logger_handle.setLevel(logging.DEBUG)
        # Format of the output
        formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

        # create console handler for log
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        if self.logger_handle_log_level == "debug":
            ch.setLevel(logging.DEBUG)
        elif self.logger_handle_log_level == "info":
            ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)

        if self._logger_handle.hasHandlers():
            self._logger_handle.handlers = []
            self._logger_handle.addHandler(ch)
        else:
            self._logger_handle.addHandler(ch)
        # if not self._logger_handle.hasHandlers():
        #     self._logger_handle.addHandler(ch)

        # create file handler for log if a file is needed
        if self._log_file_path:
            fh = logging.FileHandler(self._log_file_path)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            self._logger_handle.addHandler(fh)

    def logger(self, level='info', message="No message", set_api_error_message=True):
        """
        Function to write a logger message
        :param level: Logger level
        :param message: Logger message
        :param set_api_error_message: If true then set the 'api_error_message' field in the thread local storage. This
        helps the APIs to get access to the last significant error message.
        """
        # Sanity check:
        if not self._logger_handle:
            self._init_logger()

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        this_frame_info = calframe[0]

        # caller_frame_info = calframe[1]
        # caller_file = caller_frame_info.filename.split("/")[-1]
        # caller_file = caller_file.split("\\")[-1]
        # caller_function = caller_frame_info[3]

        i = 1
        while i:
            caller_frame_info = calframe[i]
            # To prevent the use of "/" or "\" in file path
            caller_file = caller_frame_info.filename.split("/")[-1]
            caller_file = caller_file.split("\\")[-1]
            caller_function = caller_frame_info[3]
            if caller_function != "logger":
                break
            i += 1

        log_string = "EasyUCS :: " + caller_file + " :: in " + caller_function + " :: " + message
        if level == "debug":
            self._logger_handle.debug(log_string)
        if level == "info":
            self._logger_handle.info(log_string)
        if level == "warning":
            self._logger_handle.warning(log_string)
        if level == "critical":
            self._logger_handle.critical(log_string)
        if level == "error":
            self._logger_handle.error(log_string)
            # If set_api_error_message is true then we set the 'api_error_message' field in the thread local storage.
            # This helps the APIs to get access to the last relevant error message.
            if set_api_error_message:
                self._thread_local.api_error_message = message

        # Add to the keeper
        now = str(datetime.datetime.now()).replace('.', ',')[:-3]
        self._logger_keeper[level].append(now + " :: " + log_string)
        self._logger_keeper["all"].append(now + " :: " + level + " :: " + log_string)

        # Add to the buffer (for the GUI)
        self._logger_buffer.append(now + " :: " + level + " :: " + log_string)

    def get_log_message(self, level="all", index=-1):
        """
        Get a log message of a particular level and at a particular index from the log buffer.
        :param level: log level
        :param index: the position of the log entry
        :return: (str) a string containing the log
        """
        if level not in ["error", "critical", "warning", "info", "debug", "all"]:
            return ""
        if not isinstance(index, int):
            return ""
        # The index provided must be present in self._logger_keeper["level"]
        if (index < 0 and abs(index) > len(self._logger_keeper[level])) or \
                (index >= 0 and index + 1 > len(self._logger_keeper[level])):
            return ""
        return self._logger_keeper[level][index]

    def clear_logger_summary(self):
        self._logger_keeper = {"error": [], "critical": [], "warning": [], "info": [], "debug": [], "all": []}
        self._logger_summary = ""

    def add_to_summary(self, message="", tab=0):
        tab_str = "   "
        for i in range(tab):
            self._logger_summary = self._logger_summary + tab_str
        self._logger_summary = self._logger_summary + message
        self._logger_summary = self._logger_summary + "\n"

    def print_logger_summary(self, full_list=False, by_level=True, count=True, debug=False, info=False, clear=False,
                             display="logger"):
        """
        Print the log summary

        :param full_list: Print the full list of logs in time order
        :param by_level: Print the list of logs ordered by level and time
        :param count: Print the number of logs by each level
        :param debug: Add the "debug" level to the list of level to consider in the summary
        :param info: Add the "info" level to the list of level to consider in the summary
        :param clear: Call the function "clear_logger_summary" and delete the summary and the record of all the logs
        :param display: The type of display for the summary, can be "logger" or "print" FIXME: more type
        :return:
        """

        log_level = ["warning", "critical", "error"]
        if info:
            log_level.insert(0, "info")
        if debug:
            log_level.insert(0, "debug")

        self.add_to_summary("\n" + "\n" + "Summary :")
        if count:
            self.add_to_summary("Counting number of log by level:", tab=1)
            for level in log_level:
                self.add_to_summary(message="There are " + str(len(self._logger_keeper[level])) + " logs of level: "
                                            + level, tab=2)

        if by_level:
            for level in log_level:
                if self._logger_keeper[level]:
                    self.add_to_summary("All logs for level : " + level, tab=1)
                    for log in self._logger_keeper[level]:
                        self.add_to_summary(log, tab=2)

        if full_list:
            if self._logger_keeper['all']:
                self.add_to_summary("All logs in time order :", tab=1)
                for log in self._logger_keeper['all']:
                    self.add_to_summary(log, tab=2)

        if display == "logger":
            self.logger(level="info", message=self._logger_summary)
            # We remove the last element in list because it is the summary
            self._logger_keeper['info'].pop()
        elif display == "print":
            print(self._logger_summary)

        if clear:
            self.clear_logger_summary()

    def __str__(self):
        return str(vars(self))


def main():
    easyucs = Easyucs(logger_handle_log_level="debug")
    repo_start(easyucs_object=easyucs)
    start(easyucs_object=easyucs)


if __name__ == '__main__':
    main()
    run_simple('localhost', 5001, application, use_debugger=False, use_reloader=False, threaded=True)
