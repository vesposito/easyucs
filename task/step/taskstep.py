# coding: utf-8
# !/usr/bin/env python

""" taskstep.py: Easy UCS Deployment Tool """

import uuid as python_uuid

from repository.metadata import TaskStepMetadata


class TaskStep:
    def __init__(self, parent=None, uuid=None, name="", optional=False, order=None, description="", task_uuid=None,
                 weight=None):
        self.name = name
        self.parent = parent
        self.uuid = uuid

        if not self.uuid:
            self.uuid = python_uuid.uuid4()

        # Needs to be created after UUID
        self.metadata = TaskStepMetadata(parent=self, name=name, optional=optional, order=order,
                                         description=description, task_uuid=task_uuid, weight=weight)

    def __str__(self):
        return str(vars(self))
