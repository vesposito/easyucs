# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """
from report.intersight.report import IntersightReport
from report.manager import GenericReportManager


class IntersightReportManager(GenericReportManager):
    def __init__(self, parent=None):
        GenericReportManager.__init__(self, parent=parent)
        self.report_class_name = IntersightReport
