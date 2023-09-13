# coding: utf-8
# !/usr/bin/env python

""" report.py: Easy UCS Deployment Tool """

from report.report import GenericReport


class PushSummaryReport(GenericReport):
    def __init__(self, parent, device, config, language, output_format, page_layout, directory, size):
        GenericReport.__init__(self, parent=parent, device=device, config=config, language=language,
                               output_format=output_format, page_layout=page_layout, directory=directory,
                               size=size, report_type="push_summary")

        if self.metadata.output_format == "json":
            self.document["report"] = config.push_summary_manager.export_push_summary_dict()
        else:
            self.logger(level="error", message=f"Invalid output format. '{self.metadata.output_format}' format not "
                                               "supported")
