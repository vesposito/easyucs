# coding: utf-8
# !/usr/bin/env python

""" section.py: Easy UCS Deployment Tool """

from report.content import *

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer


class GenericReportSection(GenericReportElement):
    # A section has a list of img, string and table (all called content) (content can even be other sections)
    def __init__(self, order_id, parent, title):
        GenericReportElement.__init__(self, order_id=order_id, parent=parent)
        self.content_list = []
        self.title = title
        self.indent = self.__find_indent()  # Heading 1 for example

    def add_in_word_report(self):
        # self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        self.report.document.add_heading(text=self.title, level=self.indent)

    def add_in_json_report(self, content):
        content["Title"] = self.title.replace("\n", "")

    def create_pdf_heading(self, text, sty):
        from hashlib import sha1
        # create bookmarkname
        bn = sha1(str(text + sty.name).encode('utf-8')).hexdigest()
        # modify paragraph text to include an anchor point with name bn
        h = Paragraph(text + '<a name="%s"/>' % bn, sty)
        # store the bookmark name on the flowable so afterFlowable can see this
        h._bookmarkName = bn
        self.report.pdf_element_list.append(h)

    def add_in_pdf_report(self):
        self.report.pdf_element_list.append(Spacer(1, 10))
        h1 = ParagraphStyle(name='Heading1', fontSize=14, textColor='#375b92', leading=20)
        h2 = ParagraphStyle(name='Heading2', fontSize=12, textColor='#6a88c1', leftIndent=20, leading=20)
        h3 = ParagraphStyle(name='Heading3', fontSize=10, textColor='#6a88c1', leftIndent=40, leading=20)
        h4 = ParagraphStyle(name='Heading4', fontSize=9, textColor='#6a88c1', leftIndent=50,
                            fontName='Helvetica-Oblique', leading=10)
        h5 = ParagraphStyle(name='Heading5', fontSize=8, textColor='#6a88c1', leftIndent=60,
                            fontName='Helvetica-Oblique', leading=10)
        h6 = ParagraphStyle(name='Heading6', fontSize=7, textColor='#6a88c1', leftIndent=70,
                            fontName='Helvetica-Oblique', leading=10)
        h7 = ParagraphStyle(name='Heading7', fontSize=7, textColor='#6a88c1', leftIndent=80,
                            fontName='Helvetica-Oblique', leading=10)
        heading = {
            1: "<seq id='h1'/>.<seqreset id='h2'/><seqreset id='h3'/><seqreset id='h4'/><seqreset id='h5'/><seqreset id='h6'/><seqreset id='h7'/> {}",
            2: "<seq id='h1' inc='no'/>.<seq id='h2'/><seqreset id='h3'/> {}",
            3: "<seq id='h1' inc='no'/>.<seq id='h2' inc='no'/>.<seq id='h3'/><seqreset id='h4'/> {}",
            4: "<seq id='h1' inc='no'/>.<seq id='h2' inc='no'/>.<seq id='h3' inc='no'/>.<seq id='h4'/>"
               "<seqreset id='h5'/> {}",
            5: "<seq id='h1' inc='no'/>.<seq id='h2' inc='no'/>.<seq id='h3' inc='no'/>.<seq id='h4' inc='no'/>."
               "<seq id='h5'/><seqreset id='h6'/> {}",
            6: "<seq id='h1' inc='no'/>.<seq id='h2' inc='no'/>.<seq id='h3' inc='no'/>.<seq id='h4' inc='no'/>."
               "<seq id='h5' inc='no'/>.<seq id='h6'/><seqreset id='h7'/> {}",
            7: "<seq id='h1' inc='no'/>.<seq id='h2' inc='no'/>.<seq id='h3' inc='no'/>.<seq id='h4' inc='no'/>."
               "<seq id='h5' inc='no'/>.<seq id='h6' inc='no'/>.<seq id='h7'/> {}",
        }
        if self.indent == 1:
            self.report.pdf_element_list.append(PageBreak())
            self.create_pdf_heading(heading[1].format(self.title), h1)
        if self.indent == 2:
            self.create_pdf_heading(heading[2].format(self.title), h2)
        if self.indent == 3:
            self.create_pdf_heading(heading[3].format(self.title), h3)
        if self.indent == 4:
            self.create_pdf_heading(heading[4].format(self.title), h4)
        if self.indent == 5:
            self.create_pdf_heading(heading[5].format(self.title), h5)
        if self.indent == 6:
            self.create_pdf_heading(heading[6].format(self.title), h6)
        if self.indent == 7:
            self.create_pdf_heading(heading[7].format(self.title), h7)

    def __find_indent(self):
        indent = 1
        current_object = self.parent
        while hasattr(current_object, 'parent') and not hasattr(current_object, 'uuid'):
            current_object = current_object.parent
            indent += 1
        if hasattr(current_object, 'uuid'):
            return indent
        else:
            return None
