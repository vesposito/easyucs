# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import json
import os

from __init__ import __version__
from report.push_summary.report import PushSummaryReport
from report.delete_summary.report import DeleteSummaryReport
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER


class GenericReportManager:
    def __init__(self, parent=None):
        self.report_class_name = None
        self.push_summary_report_class_name = PushSummaryReport
        self.delete_summary_report_class_name = DeleteSummaryReport
        self.report_list = []
        self.parent = parent

        self._parent_having_logger = self._find_logger()

    def clear_report_list(self):
        """
        Removes all the reports from the report list
        :return: True
        """
        self.report_list.clear()
        return True

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
            print("WARNING: No logger found in Report Manager")
            return None

    def _header_footer(self, canvas, doc):
        report = self.get_latest_report()
        title_list = report.title.split()
        table = []

        # Save the state of our canvas, so we can draw on it
        canvas.saveState()
        canvas.setFillColorRGB(0.5078125, 0.515625, 0.51171875)

        # Header
        description_style = ParagraphStyle('description', alignment=TA_CENTER, textColor='#828483')
        table.append([Paragraph("Created with EasyUCS " + __version__ + " - " + title_list[0], description_style)])
        if len(title_list) == 4:
            table.append([Paragraph(title_list[1] + " " + title_list[2] + " " + title_list[3], description_style)])
        tables = Table(table)
        header = tables
        table_style = TableStyle([("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                  ("VALIGN", (0, 0), (-1, -1), "BOTTOM")])
        tables.setStyle(table_style)
        w, h = header.wrap(doc.width, doc.topMargin)
        header.drawOn(canvas, doc.leftMargin - 10, doc.height + doc.topMargin + h - 15)

        # Footer
        footer = Paragraph("")
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin - 40, h)

        # Add the page number
        page_num = canvas.getPageNumber()
        text = "%s" % page_num
        # text.drawOn(canvas, doc.rightMargin, h)
        canvas.drawRightString(100 * mm, 10 * mm, text)

        # Release the canvas
        canvas.restoreState()

    def export_report(self, uuid=None, export_format=None, directory=None, filename=None):
        """
        Exports the specified report in the specified export format to the specified filename
        :param uuid: The UUID of the report to be exported. If not specified, the most recent report will be used
        :param export_format: The export format (e.g. "docx"). If not specified, will use metadata's output_format
        :param directory: The directory containing the export file
        :param filename: The name of the file containing the exported content
        :return: True if export is successful, False otherwise
        """
        if export_format not in [None, "docx", "json", "pdf"]:
            self.logger(level="error", message="Requested report export format not supported!")
            return False
        if filename is None:
            self.logger(level="error", message="Missing filename in report export request!")
            return False
        if not directory:
            self.logger(level="debug",
                        message="No directory specified in report export request. Using local folder.")
            directory = "."

        if uuid is None:
            self.logger(level="debug", message="No report UUID specified in report export request. Using latest.")
            report = self.get_latest_report()
        else:
            # Find the report that needs to be exported
            report_list = [report for report in self.report_list if report.uuid == uuid]
            if len(report_list) != 1:
                self.logger(level="error", message="Failed to locate report with UUID " + str(uuid) + " for export")
                return False
            else:
                report = report_list[0]

        if report is None:
            # We could not find any report
            self.logger(level="error", message="Could not find any report to export!")
            return False

        self.logger(level="debug", message="Using report " + str(report.uuid) + " for export")

        if export_format is None:
            export_format = report.metadata.output_format

        if not filename.endswith('.' + export_format):
            filename += '.' + export_format

        if not os.path.exists(directory):
            self.logger(message="Creating directory " + directory)
            os.makedirs(directory)

        self.logger(message="Exporting report " + str(report.uuid) + " to file: " + directory + "/" + filename)

        if export_format == "docx":
            self.logger(level="debug", message="Requested report export format is Word (docx)")

            try:
                report.document.save(directory + '/' + filename)

                # Update the ToC (Windows only)
                # Not used
                # report.toc.update_toc(full_filename=full_filename)

                self.logger(message="Successfully exported report to: " + directory + '/' + filename)
                return True
            except PermissionError:
                self.logger(level="error",
                            message="Report has not been exported. Permission denied. Please close existing document.")
                return False
            except Exception as err:
                self.logger(level="error", message="Error while exporting Word report: " + str(err))
                return False

        elif export_format == "pdf":
            self.logger(level="debug", message="Requested report export format is PDF")

            try:
                if report.metadata.page_layout == "a4":
                    doc = report.document(directory + '/' + filename, pagesize=A4, leftMargine=25.4 * mm,
                                          rightMargin=25.4 * mm, title=filename)
                else:
                    doc = report.document(directory + '/' + filename, pagesize=LETTER, title=filename)
                doc.multiBuild(story=report.pdf_element_list, onFirstPage=self._header_footer,
                               onLaterPages=self._header_footer)
                self.logger(message="Successfully exported report to: " + directory + '/' + filename)
                return True
            except PermissionError:
                self.logger(level="error",
                            message="Report has not been exported. Permission denied. Please close existing document.")
                return False
            except Exception as err:
                self.logger(level="error", message="Error while exporting PDF report: " + str(err))
                return False

        elif export_format == "json":
            self.logger(level="debug", message="Requested report export format is JSON")

            try:
                with open(directory + '/' + filename, "w") as f:
                    json.dump(report.document, f, indent=4)

                self.logger(message="Successfully exported report to: " + directory + '/' + filename)
                return True
            except PermissionError:
                self.logger(level="error",
                            message="Report has not been exported. Permission denied. Please close existing document.")
                return False
            except Exception as err:
                self.logger(level="error", message="Error while exporting JSON report: " + str(err))
                return False

    def generate_report(self, inventory=None, config=None, language="en", output_formats=["docx"], page_layout="a4",
                        directory=None, size="full", report_type="classic"):
        """
        Generates a report of a device using given inventory and config
        :param inventory: inventory to be used to generate the report from
        :param config: config to be used to generate the report from
        :param language: language of the report (e.g. en/fr)
        :param output_formats: list of output formats of each report to be generated (e.g. docx/json)
        :param page_layout: page layout of the report (e.g. a4/letter)
        :param directory: directory where the pictures are located for integrating into the report
        :param size: the "size" of the report (e.g. full/short)
        :param report_type: the type of report (e.g. classic/delete_summary/push_summary)
        :return: True if successful, False otherwise
        """
        if inventory is None and report_type not in ["push_summary", "delete_summary"]:
            self.logger(level="debug",
                        message="No inventory UUID specified in generate report request. Using latest.")
            inventory = self.parent.inventory_manager.get_latest_inventory()

            if inventory is None:
                self.logger(level="error", message="No inventory found. Unable to generate report.")
                return False

        if config is None and report_type not in ["delete_summary"]:
            config = self.parent.config_manager.get_latest_config()
            self.logger(level="debug", message="No config UUID specified in generate report request. Using latest.")

            if config is None:
                self.logger(level="error", message="No config found. Unable to generate report.")
                return False

        if directory is None:
            if self.parent.metadata.images_path is not None:
                self.logger(level="debug", message="Using device metadata images_path as pictures directory")
                directory = self.parent.metadata.images_path
            else:
                self.logger(level="debug", message="No pictures directory specified. Using local folder.")
                directory = "."

        # We make sure there are no duplicates in the list of output formats
        output_formats = list(set(output_formats))

        # Added condition to handle delete_summary report separately since it does not require config or inventory.
        if report_type in ["delete_summary"]:
            message_str = f"Generating {' & '.join(output_formats)} delete summary report(s) for device " \
                          f"{self.parent.target}"
        elif report_type in ["push_summary"]:
            message_str = f"Generating {' & '.join(output_formats)} {report_type} report(s) for device " \
                          f"{self.parent.target} using config UUID {str(config.uuid)}"
        else:
            message_str = f"Generating {' & '.join(output_formats)} {report_type} report(s) for device " \
                          f"{self.parent.target} using config UUID {str(config.uuid)} and inventory UUID " \
                          f"{str(inventory.uuid)}"

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.start_taskstep(
                name="GenerateReportDevice",
                description=message_str)
        self.logger(message=message_str)
        self.logger(level="debug",
                    message="Generating report(s) in " + " & ".join(output_formats) + " format(s) with layout " +
                            page_layout.upper() + " in language " + language.upper())

        for output_format in output_formats:
            if report_type == "classic":
                if self.report_class_name:
                    report = self.report_class_name(parent=self, device=self.parent, inventory=inventory, config=config,
                                                    language=language, output_format=output_format,
                                                    page_layout=page_layout, directory=directory, size=size)
                    report.metadata.easyucs_version = __version__
                    report.metadata.report_type = report_type
                    self.logger(
                        message="Finished generating report with UUID " + str(report.uuid) + " using config UUID " +
                                str(config.uuid) + " and inventory UUID " + str(inventory.uuid))
                    self.report_list.append(report)
                else:
                    message_str = "Unable to generate classic report for this device type!"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(name="GenerateReportDevice", status="failed",
                                                                        status_message=message_str)
                    self.logger(level="error", message=message_str)
                    return False

            elif report_type == "delete_summary":
                if self.delete_summary_report_class_name:
                    report = self.delete_summary_report_class_name(parent=self, device=self.parent,
                                                                   language=language,
                                                                   output_format=output_format,
                                                                   page_layout=page_layout, directory=directory,
                                                                   size=size)
                    report.metadata.easyucs_version = __version__
                    report.metadata.report_type = report_type
                    self.logger(message=f"Finished generating {output_format} delete summary report with UUID "
                                        f"{str(report.uuid)} ")
                    self.report_list.append(report)
                else:
                    message_str = "Unable to generate delete summary report."
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(name="GenerateReportDevice",
                                                                        status="failed",
                                                                        status_message=message_str)
                    self.logger(level="error", message=message_str)
                    return False

            elif report_type == "push_summary":
                # We make sure to generate the push summary report only for intersight, ucsm and ucsc devices.
                if config.device.metadata.device_type not in ["intersight", "ucsm", "ucsc"]:
                    self.logger(
                        level="info",
                        message=f"Push summary report is not yet supported to for device type "
                                f"{config.device.metadata.device_type}"
                    )
                    return False

                # We check if push_summary is present in the config, only then we proceed with generating the
                # push summary report
                if not config.push_summary_manager.push_summary:
                    self.logger(
                        level="error",
                        message="Config has no Push Summary. Unable to generate push summary report."
                    )
                    return False

                if self.push_summary_report_class_name:
                    report = self.push_summary_report_class_name(parent=self, device=self.parent, config=config,
                                                                 language=language, output_format=output_format,
                                                                 page_layout=page_layout, directory=directory,
                                                                 size=size)
                    report.metadata.easyucs_version = __version__
                    report.metadata.report_type = report_type
                    self.logger(
                        message=f"Finished generating {output_format} push summary report with UUID {str(report.uuid)} "
                                f"using config UUID {str(config.uuid)}")
                    self.report_list.append(report)
                else:
                    message_str = "Unable to generate push summary report for this device type!"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(name="GenerateReportDevice", status="failed",
                                                                        status_message=message_str)
                    self.logger(level="error", message=message_str)
                    return False

            else:
                self.logger(level="error", message="Invalid report type.")
                continue

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.stop_taskstep(
                name="GenerateReportDevice", status="successful",
                status_message="Finished generating " + str(report_type) + " report(s)")
        return True

    def get_latest_report(self):
        """
        Returns the most recent report from the report list
        :return: GenericReport (or subclass), None if no report is found
        """
        if len(self.report_list) == 0:
            return None
        # return sorted(self.report_list, key=lambda report: report.metadata.timestamp)[-1]
        return self.report_list[-1]

    def find_report_by_uuid(self, uuid=None):
        """
        Finds a report from the report list given a specific UUID
        :param uuid: UUID of the report to find
        :return: report if found, None otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No report UUID specified in find report request.")
            return None

        report_list = [report for report in self.report_list if str(report.uuid) == str(uuid)]
        if len(report_list) != 1:
            self.logger(level="debug", message="Failed to locate report with UUID " + str(uuid))
            return None
        else:
            return report_list[0]

    def remove_report(self, uuid=None):
        """
        Removes the specified report from the report list
        :param uuid: The UUID of the report to be deleted
        :return: True if delete is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No report UUID specified in remove report request.")
            return False

        # Find the report that needs to be removed
        report = self.find_report_by_uuid(uuid=uuid)
        if not report:
            return False
        else:
            report_to_remove = report

        # Remove the report from the list of reports
        self.report_list.remove(report_to_remove)
        return True
