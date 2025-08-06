# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import datetime
import threading
from queue import Queue

from __init__ import __version__
from api.api_server import perform_action
from common import read_json_file
from repository.metadata import TaskMetadata
from task.task import Task


class TaskManager:
    def __init__(self, parent=None):
        self.task_list = []
        self.parent = parent

        # Number of concurrent tasks. Should always be less than queue size of "pending_tasks".
        self.available_tokens_count = 10
        self.available_tokens = Queue(maxsize=self.available_tokens_count)
        # We fill the available_tokens queue with tokens
        for i in range(self.available_tokens_count):
            self.available_tokens.put(1)

        # Number of total pending tasks is 50 times the number of concurrent tasks
        self.pending_tasks = Queue(maxsize=self.available_tokens_count * 50)

        self._parent_having_logger = self._find_logger()

        self._clear_in_progress_tasks()
        self.scheduler_thread = threading.Thread(target=self.task_scheduler, name="task_scheduler")
        self.scheduler_thread.start()

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in Task Manager")
            return None

    def add_task(self, metadata=None, uuid=None, name=None, description=None, config_uuid=None, device_name=None,
                 device_uuid=None, inventory_uuid=None, repo_file_path=None, repo_file_uuid=None, report_uuid=None,
                 target_device_uuid=None):
        """
        Adds a task to the list of tasks
        :param metadata: The metadata object of to the task to be added (if no task details provided)
        :param uuid: The UUID of the task to be added
        :param name: The name of the task
        :param description: The description of the task
        :param config_uuid: The UUID of the config related to the task (optional)
        :param device_name: The name of the device related to the task (optional)
        :param device_uuid: The UUID of the device related to the task (optional)
        :param inventory_uuid: The UUID of the inventory related to the task (optional)
        :param repo_file_path: The Path to the repo file related to the task (optional)
        :param repo_file_uuid: The UUID of the repo file related to the task (optional)
        :param report_uuid: The UUID of the report related to the task (optional)
        :param target_device_uuid: The UUID of the target device related to the task (optional)
        :return: UUID of task if add is successful, False otherwise
        """
        if isinstance(metadata, TaskMetadata):
            uuid = metadata.uuid
            name = metadata.name
            description = metadata.description

        if name is None:
            self.logger(level="error", message="Missing name in task add request!")
            return False

        task = Task(parent=self, uuid=uuid, name=name, description=description)
        task.metadata.easyucs_version = __version__

        # Retrieve device_endpoint_id using device_uuid and update task metadata
        device = self.parent.device_manager.find_device_by_uuid(uuid=device_uuid)
        if device and device.metadata.device_endpoint_id:
            task.metadata.device_endpoint_id = device.metadata.device_endpoint_id

        for attribute in ["config_uuid", "device_name", "device_uuid", "inventory_uuid", "repo_file_path",
                          "repo_file_uuid", "report_uuid", "target_device_uuid"]:
            if eval(attribute):
                setattr(task.metadata, attribute, eval(attribute))

        # We now need to add the task steps corresponding to this task
        task_library = read_json_file(file_path="task/task_library.json", logger=self)
        if task_library:
            for task_library_key, task_library_value in task_library.items():
                if task_library_key == name:
                    # We add the default description from the task library in case none is set
                    if not task.metadata.description:
                        task.metadata.description = task_library_value["description"]
                    for task_library_step in task_library_value["steps"]:
                        task.taskstep_manager.add_taskstep(name=task_library_step["name"],
                                                           optional=task_library_step.get("optional", False),
                                                           order=task_library_step["order"],
                                                           weight=task_library_step["weight"])
                    break

        self.logger(level="debug", message="Adding task with UUID " + str(task.uuid) + " to the list of tasks")
        self.task_list.append(task)

        # We save the task to the repository
        self.parent.repository_manager.save_metadata(task.metadata)

        return task.uuid

    def add_to_pending_tasks(self, pending_task_dict=None):
        """
        Adds the task to the system's/device's/repo's task queue
        :param pending_task_dict: Dictionary containing the details of the task pending to be executed
        :return: True if successful, False otherwise
        """
        if pending_task_dict is None:
            self.logger(level="error", message="Missing pending task dictionary argument")
            return False

        task = self.find_task_by_uuid(uuid=pending_task_dict.get("task_uuid", None))
        if not task:
            self.logger(level="error", message="The task that needs to be added to the Queue could not be found")
            return False

        # Flag to track if multiple devices with same endpoint ID exist AND one of them has an active task
        active_task_on_endpoint_id = False

        if task.metadata.device_uuid:
            obj = self.parent.device_manager.find_device_by_uuid(uuid=task.metadata.device_uuid)

            # Find all devices with the same endpoint ID (may exist with different API keys/credentials)
            devices = self.parent.device_manager.find_devices_by_endpoint_id(
                endpoint_id=task.metadata.device_endpoint_id
            )
            # If multiple devices point to same endpoint ID, check if any of them is currently running a task
            if devices and len(devices) > 1:
                # If a task is running on any device with same endpoint ID, set flag
                for device in devices:
                    if device.task is not None:
                        active_task_on_endpoint_id = True
                        break
        else:
            obj = self.parent.repository_manager.repo
        if obj:
            # Check if a task is already running on this device OR on another device with the same endpoint ID
            if obj.task is not None or active_task_on_endpoint_id:

                # Device/Repo is already busy. We put the task in the device's/repo's queued tasks queue.
                if not active_task_on_endpoint_id:
                    self.logger(
                        level="info",
                        message=f"{'Device ' + str(obj.uuid) if hasattr(obj, 'uuid') else 'Repo'} already has a task "
                                f"running: {obj.task.uuid}. Waiting for device to be available for task {str(task.uuid)}."
                    )
                else:
                    self.logger(
                        level="info",
                        message=f"Device {task.metadata.device_uuid} is already running a task using a different "
                                f"credential/API key. Waiting for the device to become available to run task "
                                f"{str(task.uuid)}."
                    )

                if not obj.queued_tasks.full():
                    # Adding task to the device's tasks queue
                    obj.queued_tasks.put(pending_task_dict, timeout=10)
                else:
                    self.logger(level="error", message=f"Device's/Repo's tasks queue is full with "
                                                       f"{obj.queued_tasks.qsize()} queued tasks!")
                    return False
            else:
                if not self.pending_tasks.full():
                    # Adding task to the system's (task manager's) pending tasks queue
                    self.pending_tasks.put(pending_task_dict, timeout=10)
                else:
                    self.logger(level="error", message=f"System's (task manager's) pending tasks queue is full with "
                                                       f"{self.pending_tasks.qsize()} pending tasks!")
                    return False
            return True
        else:
            return False

    def _clear_in_progress_tasks(self):
        """
        Checks for any task or task step that is "in_progress" from earlier runs of EasyUCS
        If found, they will be marked as "failed"
        :return: True if successful, False otherwise
        """
        task_metadata_list = self.parent.repository_manager.get_metadata(object_type="task")
        for task_metadata in task_metadata_list:
            if task_metadata.status in ["in_progress", "pending"]:
                if task_metadata.status in "pending":
                    # We reset the timestamp_start value to None since it was set artificially to +24h for sorting
                    task_metadata.timestamp_start = None
                task_metadata.status = "failed"
                if task_metadata.status_message is None:
                    task_metadata.status_message = "Marked as failed after EasyUCS restart"
                if task_metadata.timestamp_stop is None:
                    task_metadata.timestamp_stop = datetime.datetime.now()
                self.logger(level="debug", message="Cleared previously unfinished task " + task_metadata.name +
                                                   " with UUID " + str(task_metadata.uuid))
                self.parent.repository_manager.save_metadata(metadata=task_metadata)

        taskstep_metadata_list = self.parent.repository_manager.get_metadata(object_type="taskstep")
        for taskstep_metadata in taskstep_metadata_list:
            if taskstep_metadata.status == "in_progress":
                taskstep_metadata.status = "failed"
                if taskstep_metadata.status_message is None:
                    taskstep_metadata.status_message = "Marked as failed after EasyUCS restart"
                if taskstep_metadata.timestamp_stop is None:
                    taskstep_metadata.timestamp_stop = datetime.datetime.now()
                self.logger(level="debug", message="Cleared previously unfinished task step " + taskstep_metadata.name +
                                                   " with UUID " + str(taskstep_metadata.uuid))
                self.parent.repository_manager.save_metadata(metadata=taskstep_metadata)

        return True

    def clear_task_list(self):
        """
        Removes all the tasks from the task list
        :return: True
        """
        self.task_list.clear()
        return True

    def find_task_by_uuid(self, uuid=None):
        """
        Finds a task from the task list given a specific UUID
        :param uuid: UUID of the task to find
        :return: task if found, None otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No task UUID specified")
            return None

        task_list = [task for task in self.task_list if str(task.uuid) == str(uuid)]
        if len(task_list) != 1:
            self.logger(level="debug", message="Failed to locate task with UUID " + str(uuid))
            return None
        else:
            return task_list[0]

    def get_latest_task(self):
        """
        Returns the most recent task from the task list
        :return: Task, None if no task is found
        """
        if len(self.task_list) == 0:
            return None
        # return sorted(self.task_list, key=lambda task: task.metadata.timestamp)[-1]
        return self.task_list[-1]

    def is_any_taskstep_failed(self, uuid=None, ignore_optional=True):
        """
        Check if any of the tasksteps in a task have failed
        :param uuid: UUID of the task
        :param ignore_optional: Whether to ignore optional tasksteps while checking for failed taskstep
        :return: True if any taskstep failed, False otherwise
        """
        if uuid is None:
            self.logger(level="error", message="Missing UUID of task")
            return False

        # We find the task
        task = self.find_task_by_uuid(uuid=uuid)
        if task is None:
            self.logger(level="error", message="No task found with UUID " + str(uuid))
            return False

        for taskstep in task.taskstep_manager.taskstep_list:
            if taskstep.metadata.status in ["failed"]:
                # If we ignore optional tasksteps then we don't return True even when optional tasksteps have failed
                if ignore_optional and taskstep.metadata.optional:
                    continue
                return True

        return False

    def is_any_task_in_progress(self):
        """
        Check if any of the tasks is in-progress
        :return: True if any task is in-progress, False otherwise
        """
        for task in self.task_list:
            if task.metadata.status in ["in_progress", "pending"]:
                return True
        return False

    def remove_task(self, uuid=None):
        """
        Removes the specified task from the task list
        :param uuid: The UUID of the task to be deleted
        :return: True if delete is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No task UUID specified in remove task request.")
            return False

        # Find the task that needs to be removed
        task = self.find_task_by_uuid(uuid=uuid)
        if not task:
            return False
        else:
            task_to_remove = task

        # Remove the task from the list of tasks
        self.task_list.remove(task_to_remove)
        return True

    def set_task_progression(self, uuid=None, progress=None):
        """
        Sets the progression of the task in progress attribute
        :param uuid: UUID of the task
        :param progress: Set the progression to this value if provided, otherwise calculate it
        :return: True if successful, False otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No task UUID specified")
            return False

        # Find the task for which progression needs to be set
        task = self.find_task_by_uuid(uuid=uuid)
        if not task:
            return False

        if not task.taskstep_manager.taskstep_list:
            return False
        else:
            weight_sum = 0
            for step in task.taskstep_manager.taskstep_list:
                if step.metadata.weight:
                    weight_sum += step.metadata.weight

        current_taskstep = task.taskstep_manager.get_current_taskstep()
        if current_taskstep:
            if progress:
                task.metadata.progress = progress
            else:
                current_step_id = current_taskstep.metadata.order
                # If the task step is currently in status "successful" or "skipped", we count it as completed
                if current_taskstep.metadata.status in ["successful", "skipped"]:
                    current_step_id += 1

                completed_weight_sum = 0
                for step in task.taskstep_manager.taskstep_list[0:current_step_id - 1]:
                    if step.metadata.weight:
                        completed_weight_sum += step.metadata.weight

                task.metadata.progress = int(100 / weight_sum * completed_weight_sum)
        else:
            # There is no current task step running, so the task is either not started or completed/failed
            if all(step.metadata.status is None for step in task.taskstep_manager.taskstep_list):
                return False
            elif all(step.metadata.status in ["successful", "skipped"] for step in task.taskstep_manager.taskstep_list):
                task.metadata.progress = 100

        # We save the task to the repository
        self.parent.repository_manager.save_metadata(task.metadata)

        return True

    def start_task(self, uuid=None, description=None):
        """
        Starts task
        :param uuid: UUID of the task
        :param description: Description of the task - e.g. "Pushing Config <uuid> to UCS System <uuid>"
        :return: UUID of task if successful, None otherwise
        """
        if uuid is None:
            self.logger(level="error", message="Missing UUID of task")
            return None

        # We identify the task
        task = self.find_task_by_uuid(uuid=uuid)

        if task is None:
            self.logger(level="error", message="Could not find task with UUID " + str(uuid))
            return None

        # We start the task
        self.logger(level="debug", message="Starting task with UUID " + str(uuid))
        task.metadata.timestamp_start = datetime.datetime.now()
        task.metadata.status = "in_progress"
        if description:
            task.metadata.description = description
        task.metadata.progress = 0

        # We save the task to the repository
        self.parent.repository_manager.save_metadata(task.metadata)

        # We also save the task steps to the repository
        for taskstep in task.taskstep_manager.taskstep_list:
            self.parent.repository_manager.save_metadata(taskstep.metadata)

        return str(task.uuid)

    def stop_task(self, uuid=None, status=None, status_message=None):
        """
        Stops task
        :param uuid: UUID of the task
        :param status: Status of the task (successful/failed) - if not specified, will be determined by the steps
        :param status_message: Status message of the task - e.g. "Failed to push config"
        :return: UUID of task if successful, None otherwise
        """
        if uuid is None:
            self.logger(level="error", message="Missing UUID of task")
            return None

        if status not in [None, "successful", "failed"]:
            self.logger(level="error", message="Status is not valid")
            return None

        # We find the task to stop
        task = self.find_task_by_uuid(uuid=uuid)
        if task is None:
            self.logger(level="error", message="No task found with UUID " + str(uuid))
            return None

        # If the status is set to failed/successful, and we have a status message, we use those
        if status in ["failed", "successful"]:
            task.metadata.status = status
            task.metadata.status_message = status_message
            if status == "successful":
                task.metadata.progress = 100
        else:
            # We check if the task has actually been started before being stopped
            if task.metadata.status is None:
                task.metadata.status = "failed"
                task.metadata.status_message = "Failed to start the task"
            elif task.metadata.status in ["failed", "successful"]:
                if status_message:
                    task.metadata.status_message = status_message
            else:
                # If status is not provided and task status is not set then we set the task status based on the
                # task steps status
                failed_step = False
                failed_step_status_message = ""
                for taskstep in task.taskstep_manager.taskstep_list:
                    # We check for presence of failed non-optional step to determine whether the task is failed overall
                    if taskstep.metadata.status in [None, "in_progress"]:
                        task.taskstep_manager.stop_taskstep(
                            name=taskstep.metadata.name, status="failed",
                            status_message="Task stopped before completing the step")
                    if taskstep.metadata.status in [None, "failed", "in_progress"] and not taskstep.metadata.optional:
                        failed_step = True
                        failed_step_status_message = taskstep.metadata.status_message
                        break

                if failed_step:
                    task.metadata.status = "failed"
                    if failed_step_status_message:
                        task.metadata.status_message = failed_step_status_message
                    else:
                        task.metadata.status_message = "Failed to complete task"
                else:
                    task.metadata.status = "successful"
                    task.metadata.status_message = "Successfully completed task"
                    task.metadata.progress = 100

        # We stop the task
        self.logger(level="debug", message="Stopping task with UUID " + str(uuid))
        task.metadata.timestamp_stop = datetime.datetime.now()
        # task.metadata.status = status
        # task.metadata.status_message = status_message

        self.set_task_progression(uuid=uuid)

        # We save the task to the repository
        self.parent.repository_manager.save_metadata(task.metadata)

        return str(task.uuid)

    def task_scheduler(self):
        """
        Schedules all the tasks that need to be executed from the API
        Blocking Infinite loop running in a separate thread waiting for new tasks to schedule
        """
        self.logger(level="info", message="Successfully started task scheduler")
        while True:
            # The following 2 statements are blocking, which means that the execution stops here until we get a
            # value from the "pending_tasks" and "available_tokens" queues.
            pending_task = self.pending_tasks.get()
            # We take 1 token from the available tokens
            self.available_tokens.get()
            self.logger(level="debug",
                        message=f"Taken 1 token. {str(self.available_tokens.qsize())} token(s) left")

            task = self.find_task_by_uuid(uuid=pending_task.get("task_uuid", None))
            if task:
                if task.metadata.status not in ["pending"]:
                    self.logger(level="debug",
                                message="Skipping task with UUID " + str(task.uuid) + " as it is not pending")
                    # Releasing the token
                    self.available_tokens.put(1)
                    continue
            else:
                self.logger(level="error",
                            message="Unable to find task with UUID " + pending_task.get("task_uuid", "None"))
                # Releasing the token
                self.available_tokens.put(1)
                continue

            if not task.cancel:
                if task.metadata.device_uuid:
                    obj = self.parent.device_manager.find_device_by_uuid(uuid=task.metadata.device_uuid)
                else:
                    obj = self.parent.repository_manager.repo
                if obj:
                    if obj.task is not None:
                        # Device/Repo is already busy. We put the task back at the end of the device's/repo's
                        # queued tasks.
                        self.logger(
                            message=f"{'Device ' + str(obj.uuid) if hasattr(obj, 'uuid') else 'Repo'} already has a "
                                    f"task running: {obj.task.uuid}. Waiting for device/repo to be available "
                                    f"for task {str(task.uuid)}."
                        )
                        obj.queued_tasks.put(pending_task)
                    else:
                        kwargs = {
                            "action_type": pending_task.get("action_type", None),
                            "object_type": pending_task.get("object_type", None),
                            "task_uuid": str(task.uuid),
                            "timeout": pending_task.get("timeout", None),
                            "action_kwargs": pending_task.get("action_kwargs", None)
                        }
                        if task.metadata.device_uuid:
                            kwargs["device"] = obj
                        action_thread = threading.Thread(target=perform_action, kwargs=kwargs,
                                                         name="perform_action_" + str(task.uuid))
                        action_thread.start()
                        continue
                else:
                    if task.metadata.device_uuid:
                        err_message = "Unable to find device with UUID " + task.metadata.device_uuid
                    else:
                        err_message = "Unable to get repo attribute from Repository Manager"
                    self.logger(level="error", message=err_message)
                    self.stop_task(uuid=task.uuid, status="failed", status_message=err_message)

            # Release the token, if task did not execute for some reason
            self.available_tokens.put(1)
