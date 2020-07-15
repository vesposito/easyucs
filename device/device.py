# coding: utf-8
# !/usr/bin/env python

""" device.py: Easy UCS Deployment Tool """

import datetime
import inspect
import json
import logging
import uuid

import export


class GenericDevice:
    def __init__(self, target="", user="", password="", logger_handle_log_level="info", log_file_path=None):
        self.device_type = "Generic"
        self.device_type_short = "generic"
        self.custom = None
        self.load_from = None
        self.name = None
        self.password = password
        self.target = target
        self.task_progression = 0
        self.username = user
        self.uuid = uuid.uuid4()
        self.version = None
        self.version_max_supported_by_sdk = None
        self.version_min_required = None

        self._logger_handle_log_level = logger_handle_log_level
        self._log_file_path = log_file_path
        self._logger_buffer = []
        self._logger_handle = None
        self._logger_keeper = {"error": [], "critical": [], "warning": [], "info": [], "debug": [], "all": []}
        self._logger_summary = ""

        self._init_logger()

        self.config_manager = None
        self.inventory_manager = None

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

    def _init_logger(self):
        # We need to avoid dot in the logger name because if there is more than one dot it will create multiple
        # logger handles
        self.logger_target = self.target.replace(".", "_")

        # We use a custom named logger
        self._logger_handle = logging.getLogger(self.logger_target)
        self._logger_handle.setLevel(logging.DEBUG)
        # Format of the output
        formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

        # create console handler for log
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        if self._logger_handle_log_level == "debug":
            ch.setLevel(logging.DEBUG)
        elif self._logger_handle_log_level == "info":
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

    def logger(self, level='info', message="No message"):
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

        log_string = self.target + " :: " + caller_file + " :: in " + caller_function + " :: " + message
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

        # Add to the keeper
        now = str(datetime.datetime.now()).replace('.', ',')[:-3]
        self._logger_keeper[level].append(now + " :: " + log_string)
        self._logger_keeper["all"].append(now + " :: " + level + " :: " + log_string)

        # Add to the buffer (for the GUI)
        self._logger_buffer.append(now + " :: " + level + " :: " + log_string)

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

    def connect(self):
        pass

    def disconnect(self):
        pass

    def generate_report(self, inventory=None, config=None, language="en", output_format="docx", page_layout="a4",
                        directory=None, filename=None, size="full"):
        pass

    def generate_config_plots(self, config=None, directory=None):
        pass

    def reset(self):
        pass

    def export_device(self, export_format="json", directory=None, filename=None):
        """
        Exports a device using the specified export format to a file
        :param export_format: Export format. Currently only supports JSON
        :param directory: Directory to store the export file
        :param filename: Name of the export file
        :return: True if export is successful, False otherwise
        """
        if export_format not in ["json"] or filename is None:
            return False
        if directory is None:
            directory = "."

        if export_format == "json":
            header_json = {}
            header_json["metadata"] = [export.generate_json_metadata_header(file_type="device", device=self)]
            device_json = {}
            device_json["easyucs"] = header_json
            device_json["device"] = {}

            device_json["device"]["target"] = self.target
            device_json["device"]["username"] = self.username
            device_json["device"]["password"] = self.password

            # Calculate hash of entire JSON file and adding it to header before exporting
            device_json = export.insert_json_metadata_hash(json_content=device_json)

            self.logger(message="Exporting device " + str(self.uuid) + " to file: " + directory + "/" + filename)
            with open(directory + '/' + filename, 'w') as device_json_file:
                json.dump(device_json, device_json_file, indent=3)
            device_json_file.close()
            return True

    def get_task_progression(self):
        """
        Gets the current progression of the EasyUCS deployment
        :return: (int) progress state (%) of the EasyUCS deployment
        """
        return self.task_progression

    def set_task_progression(self, value=None):
        """
        Sets the current progression of the EasyUCS deployment
        :param value: (int) progress state (%) of the EasyUCS deployment
        :return: True if successful, False otherwise

        00% :  all : At start
        01% :  all : Entering init_process

        05% :  all : Entering reset
        10% :  all : Reset command send to the device
        20% :  all : The device(s) is(/are) reachable after a reset command

        25% :  all : Entering initial_setup
        30% : ucsm : Initial setup configuration send to the FI A
        35% :  all : Initial setup configuration send to the FI B or IMC
        40% :  all : The IMC / VIP is reachable after an initial setup
        45% : ucsm : The FIs are both in UP state and in sync (for UCS System only)

        50% :  all : Entering push_config & Connected to the device

        60% : ucsm : Admin section configured
        65% : ucsm : Equipment section configured
        70% : ucsm : VLAN - VSAN section configured
        75% : ucsm : After checking if the FI(s) will be rebooted due to a port configuration
        80% : ucsm : Ports section configured (except Server ports)
        85% : ucsm : Server ports configured
        90% : ucsm : Now configuring orgs section

        60% : cimc : Admin section configured
        70% : cimc : Bunch of things configured
        80% : cimc : Other bunch of things configured
        90% : cimc : BIOS section configured

        100% :  all: At the end of init_process and push_config
        """
        if value is not None:
            self.task_progression = value
            return True
        else:
            return False

    def get_logs(self):
        """
        Gets the logs that are currently in the log buffer. Those logs are popped, meaning they are no longer in the
        buffer after being returned
        This method is used for displaying logs in the GUI
        :return: (str) a string containing the logs currently in the log buffer
        """
        log_str = ""
        while len(self._logger_buffer):
            log_str += self._logger_buffer[0]
            log_str += "\r"
            self._logger_buffer.pop(0)
        return log_str
