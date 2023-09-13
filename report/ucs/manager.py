# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

from report.manager import GenericReportManager
from report.ucs.report import UcsCentralReport, UcsImcReport, UcsSystemReport


class GenericUcsReportManager(GenericReportManager):
    def __init__(self, parent=None):
        GenericReportManager.__init__(self, parent=parent)


class UcsSystemReportManager(GenericUcsReportManager):
    def __init__(self, parent=None):
        GenericUcsReportManager.__init__(self, parent=parent)
        self.report_class_name = UcsSystemReport


class UcsImcReportManager(GenericUcsReportManager):
    def __init__(self, parent=None):
        GenericUcsReportManager.__init__(self, parent=parent)
        self.report_class_name = UcsImcReport


class UcsCentralReportManager(GenericUcsReportManager):
    def __init__(self, parent=None):
        GenericUcsReportManager.__init__(self, parent=parent)
        self.report_class_name = UcsCentralReport
