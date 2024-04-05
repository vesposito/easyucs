# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import datetime

from __init__ import __version__
from repository.metadata import TaskStepMetadata
from task.step.taskstep import TaskStep


class TaskStepManager:
    def __init__(self, parent=None):
        self.taskstep_list = []
        self.parent = parent

        self._parent_having_logger = self._find_logger()

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
            print("WARNING: No logger found in Task Step Manager")
            return None

    def add_taskstep(self, metadata=None, uuid=None, name=None, description=None, optional=False, order=None,
                     weight=None):
        """
        Adds a task step to the list of task steps
        :param metadata: The metadata object of to the task step to be added (if no task step details provided)
        :param uuid: The UUID of the task step to be added
        :param name: The name of the task step
        :param description: The description of the task step
        :param optional: Whether the taskstep is optional or mandatory
        :param order: The order of the task step
        :param weight: The weight of the task step
        :return: UUID of task step if add is successful, False otherwise
        """
        if isinstance(metadata, TaskStepMetadata):
            uuid = metadata.uuid
            name = metadata.name
            optional = metadata.optional
            order = metadata.order
            description = metadata.description

        taskstep = TaskStep(parent=self, uuid=uuid, name=name, optional=optional, order=order, description=description,
                            task_uuid=self.parent.uuid, weight=weight)

        taskstep.metadata.easyucs_version = __version__
        self.logger(level="debug",
                    message="Adding task step with UUID " + str(taskstep.uuid) + " to the list of task steps")
        self.taskstep_list.append(taskstep)
        self.parent.parent.parent.repository_manager.save_metadata(taskstep.metadata)
        return taskstep.uuid

    def find_taskstep_by_uuid(self, uuid=None):
        """
        Finds a task step from the task step list given a specific UUID
        :param uuid: UUID of the task step to find
        :return: task step if found, None otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No task step UUID specified in find task step request.")
            return None

        taskstep_list = [taskstep for taskstep in self.taskstep_list if str(taskstep.uuid) == str(uuid)]
        if len(taskstep_list) != 1:
            self.logger(level="debug", message="Failed to locate task step with UUID " + str(uuid))
            return None
        else:
            return taskstep_list[0]

    def get_current_taskstep(self):
        """
        Returns the current task step from the task step list
        :return: TaskStep, None if no active task step is found
        """
        active_step = None
        for taskstep in self.taskstep_list:
            if taskstep.metadata.status in ["in_progress"]:
                if active_step is None:
                    active_step = taskstep
                else:
                    self.logger(level="error", message="Found multiple running task steps: " + str(active_step.name) +
                                                       ", " + str(taskstep.name))
                    return None

        if not active_step:
            # No step is currently in status "in_progress". There are multiple possibilities:
            # - The steps can all be in status None --> Task is not yet started
            # - The steps can all be in status "successful"/"skipped" --> Task is completed
            # - One step can be in status "failed" --> Task is failed
            # - Some steps can be ended, and other steps in status None --> Task is started but not actively running
            if all(step.metadata.status is None for step in self.taskstep_list):
                self.logger(level="debug", message="Task with UUID " + str(self.parent.uuid) + " has not yet started")
                return None
            elif all(step.metadata.status in ["successful", "skipped"] for step in self.taskstep_list):
                self.logger(level="debug",
                            message="Task with UUID " + str(self.parent.uuid) + " is terminated with success")
                return None
            elif any(step.metadata.status == "failed" for step in self.taskstep_list):
                self.logger(level="debug",
                            message="Task with UUID " + str(self.parent.uuid) + " is terminated with failure")
                return None
            else:
                x = 0
                while x < len(self.taskstep_list):
                    if self.taskstep_list[x].metadata.status is None:
                        return self.taskstep_list[x - 1]
                    x += 1

        return active_step

    def get_latest_taskstep(self):
        """
        Returns the most recent task step from the task step list
        :return: TaskStep, None if no task step is found
        """
        if len(self.taskstep_list) == 0:
            return None
        # return sorted(self.taskstep_list, key=lambda taskstep: taskstep.metadata.timestamp)[-1]
        return self.taskstep_list[-1]

    def get_next_taskstep(self):
        """
        Returns the next task step from the task step list
        :return: TaskStep, None if no next task step is found
        """
        active_step = None
        for taskstep in self.taskstep_list:
            if taskstep.metadata.status in ["in_progress"]:
                if active_step is None:
                    active_step = taskstep
                else:
                    self.logger(level="error", message="Found multiple running task steps: " + str(active_step.name) +
                                                       ", " + str(taskstep.name))
                    return None

        if not active_step:
            # No step is currently in status "in_progress". There are multiple possibilities:
            # - The steps can all be in status None --> Task is not yet started
            # - The steps can all be in status "successful"/"skipped" --> Task is completed
            # - One step can be in status "failed" --> Task is failed
            # - Some steps can be ended, and other steps in status None --> Task is started but not actively running
            if all(step.metadata.status is None for step in self.taskstep_list):
                return self.taskstep_list[0]
            elif all(step.metadata.status in ["successful", "skipped"] for step in self.taskstep_list):
                self.logger(level="debug",
                            message="Task with UUID " + str(self.parent.uuid) + " is terminated with success")
                return None
            elif any(step.metadata.status == "failed" for step in self.taskstep_list):
                self.logger(level="debug",
                            message="Task with UUID " + str(self.parent.uuid) + " is terminated with failure")
                return None
            else:
                x = 0
                while x < len(self.taskstep_list):
                    if self.taskstep_list[x].metadata.status is None:
                        return self.taskstep_list[x]
                    x += 1
        else:
            if active_step == self.taskstep_list[-1]:
                self.logger(level="debug", message="Currently running task step is the last step.")
                return None

        return self.taskstep_list[self.taskstep_list.index(active_step) + 1]
    
    def is_taskstep_optional(self, name=None):
        """
        Is the task step optional
        :param name: Name of the task step - e.g. "StepOne"
        :return: True if taskstep is optional, False otherwise
        """
        if name is None:
            self.logger(level="error", message="Missing name of task step")
            return False
        
        for taskstep in self.taskstep_list:
            if taskstep.metadata.name == name:
                if taskstep.metadata.optional:
                    return True
                else:
                    return False

        self.logger(level="error", message="Failed to find task step in taskstep list")
        return False

    def remove_taskstep(self, uuid=None):
        """
        Removes the specified task step from the task step list
        :param uuid: The UUID of the task step to be deleted
        :return: True if delete is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No task step UUID specified in remove task step request.")
            return False

        # Find the task step that needs to be removed
        taskstep = self.find_taskstep_by_uuid(uuid=uuid)
        if not taskstep:
            return False
        else:
            taskstep_to_remove = taskstep

        # Remove the task step from the list of task steps
        self.taskstep_list.remove(taskstep_to_remove)
        return True

    def skip_taskstep(self, name=None, status_message=None):
        """
        Skips task step (starts & stops immediately)
        :param name: Name of the task step - e.g. "StepOne"
        :param status_message: Status message for the skipped task step
        :return: UUID of task step if successful, None otherwise
        """
        if name is None:
            self.logger(level="error", message="Missing name of task step")
            return None

        # We check if there is already another task step running
        for taskstep in self.taskstep_list:
            if taskstep.metadata.status in ["in_progress"]:
                self.logger(level="error", message="Task step " + str(taskstep.name) + " is already running")
                return None

        # We identify the task step
        step = None
        for taskstep in self.taskstep_list:
            if taskstep.name == name:
                step = taskstep
                break

        if step is None:
            self.logger(level="error", message="Could not find task step " + str(name))
            return None

        # We skip the task step
        self.logger(level="debug", message="Skipping task step " + str(name) + " of task " + str(self.parent.uuid))
        step.metadata.timestamp_start = datetime.datetime.now()
        step.metadata.timestamp_stop = step.metadata.timestamp_start
        step.metadata.status = "skipped"
        step.metadata.status_message = status_message

        self.parent.parent.set_task_progression(uuid=self.parent.uuid)

        # We save the task step to the repository
        self.parent.parent.parent.repository_manager.save_metadata(step.metadata)

        return str(step.uuid)

    def start_taskstep(self, name=None, description=None):
        """
        Starts task step
        :param name: Name of the task step - e.g. "StepOne"
        :param description: Description of the task step
        :return: UUID of task step if successful, None otherwise
        """
        if name is None:
            self.logger(level="error", message="Missing name of task step")
            return None

        # We check if there is already another task step running
        for taskstep in self.taskstep_list:
            if taskstep.metadata.status in ["in_progress"]:
                self.logger(level="error", message="Task step " + str(taskstep.name) + " is already running")
                return None

        # We identify the task step which must match the name and the order ID of the next planned step
        step = None
        next_step = self.get_next_taskstep()
        next_step_id = 0
        if next_step:
            next_step_id = next_step.metadata.order
        for taskstep in self.taskstep_list:
            if taskstep.name == name and taskstep.metadata.order == next_step_id:
                step = taskstep
                break

        if step is None:
            self.logger(level="error", message="Could not find task step " + str(name))
            return None

        # We start the task step
        self.logger(level="debug", message="Starting task step " + str(name) + " of task " + str(self.parent.uuid))
        step.metadata.timestamp_start = datetime.datetime.now()
        step.metadata.status = "in_progress"
        step.metadata.description = description

        self.parent.parent.set_task_progression(uuid=self.parent.uuid)

        # We save the task step to the repository
        self.parent.parent.parent.repository_manager.save_metadata(step.metadata)

        return str(step.uuid)

    def stop_taskstep(self, name=None, status=None, status_message=None):
        """
        Stops task step
        :param name: Name of the task step - e.g. "StepOne"
        :param status: Status of the task step (successful/failed)
        :param status_message: Status message of the task step - e.g. "Failed to push Admin section of config"
        :return: UUID of task step if successful, None otherwise
        """
        if name is None:
            self.logger(level="error", message="Missing name of task step")
            return None

        if status not in ["successful", "failed"]:
            self.logger(level="error", message="Status is not valid")
            return None

        current_step = self.get_current_taskstep()
        if current_step is None:
            # If none of the task steps have started and we are trying to set the status of the first task step
            # then we set current_step to the first task step
            next_taskstep = self.get_next_taskstep()
            if next_taskstep and next_taskstep.name == name:
                current_step = self.get_next_taskstep()
            else:
                self.logger(level="error", message="No task step is currently running")
                return None

        # We check if the task step name matches the currently running task step
        if not current_step.name == name:
            next_taskstep = self.get_next_taskstep()
            if current_step.metadata.status in ["successful", "skipped"] and next_taskstep and \
                    next_taskstep.name == name:
                current_step = next_taskstep
            else:
                self.logger(level="error", message="Task step " + str(current_step.name) + " is already running")
                return None

        # We stop the task step
        self.logger(level="debug", message="Stopping task step " + str(name) + " of task " + str(self.parent.uuid))
        current_step.metadata.timestamp_stop = datetime.datetime.now()
        current_step.metadata.status = status
        current_step.metadata.status_message = status_message

        self.parent.parent.set_task_progression(uuid=self.parent.uuid)

        # We save the task step to the repository
        self.parent.parent.parent.repository_manager.save_metadata(current_step.metadata)

        return str(current_step.uuid)

    def update_taskstep_description(self, name=None, description=None):
        """
        Updates description of the task step given as argument (name). If no argument given, uses the current task step
        :param name: Name of the task step (optional)
        :param description: Description of the task step
        :return: True if description is updated, False otherwise
        """
        if description is None:
            self.logger(level="error", message="Missing description of task step")
            return False

        # We identify the task step
        if name is None:
            current_taskstep = self.get_current_taskstep()
        else:
            current_taskstep = None
            for taskstep in self.taskstep_list:
                if taskstep.name == name:
                    current_taskstep = taskstep
                    break

        if current_taskstep is None:
            if name:
                self.logger(level="error", message="Could not find task step " + str(name))
            else:
                self.logger(level="error", message="Could not find the current task step")
            return False

        current_taskstep.metadata.description = description

        # We save the task step to the repository
        self.parent.parent.parent.repository_manager.save_metadata(current_taskstep.metadata)

        return True
