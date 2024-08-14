# coding: utf-8
# !/usr/bin/env python

""" report.py: Easy UCS Deployment Tool """

from report.report import GenericReport


class DeleteSummaryReport(GenericReport):
    def __init__(self, parent, device, language, page_layout, directory, size, output_format):
        # Initialize the base class (GenericReport) with provided parameters
        GenericReport.__init__(self, parent=parent, device=device, language=language,
                               output_format=output_format, page_layout=page_layout,
                               directory=directory, size=size, report_type="delete_summary")

        # Check the output format specified in metadata
        if self.metadata.output_format == "json":
            # If output format is JSON, export the delete summary dictionary from the device's delete summary manager
            self.document["report"] = device.delete_summary_manager.export_delete_summary_dict()
        else:
            # Log an error if the output format is not supported
            self.logger(level="error",
                        message=f"Invalid output format. '{self.metadata.output_format}' format not supported")
