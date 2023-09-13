# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

from report.manager import GenericReportManager


class IntersightReportManager(GenericReportManager):
    def __init__(self, parent=None):
        GenericReportManager.__init__(self, parent=parent)
