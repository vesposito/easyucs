# coding: utf-8
# !/usr/bin/env python

""" task.py: Easy UCS Deployment Tool """

import uuid as python_uuid

from repository.metadata import TaskMetadata
from task.step.manager import TaskStepManager


class Task:
    def __init__(self, parent=None, uuid=None, name="", description=""):
        self.name = name
        self.parent = parent
        self.uuid = uuid
        self.cancel = False

        if not self.uuid:
            self.uuid = python_uuid.uuid4()

        # Needs to be created after UUID
        self.metadata = TaskMetadata(parent=self, name=name, description=description)

        self.taskstep_manager = TaskStepManager(parent=self)

    def __str__(self):
        return str(vars(self))
