# coding: utf-8
# !/usr/bin/env python

""" config.py: Easy UCS Deployment Tool """

from report.intersight.server_policies import (
    IntersightOrganizationsReportSection,
    IntersightBiosPoliciesReportSection,
    IntersightBootPoliciesReportSection,
    IntersightDriveSecurityPoliciesReportSection,
    IntersightEthAdapterPoliciesReportSection,
    IntersightEthNetworkControlPoliciesReportSection,
    IntersightEthNetworkGroupPoliciesReportSection,
    IntersightEthQosPoliciesReportSection,
    IntersightFcAdapterPoliciesReportSection,
    IntersightFcNetworkPoliciesReportSection,
    IntersightFcQosPoliciesReportSection,
    IntersightFcZonePoliciesReportSection,
    IntersightFirmwarePoliciesReportSection,
    IntersightImcAccessPoliciesReportSection,
    IntersightIpmiOverLanPoliciesReportSection,
    IntersightIscsiAdapterPoliciesReportSection,
    IntersightIscsiBootPoliciesReportSection,
    IntersightIscsiStaticTargetPoliciesReportSection,
    IntersightLanConnectivityPoliciesReportSection,
    IntersightLocalUserPoliciesReportSection,
    IntersightMemoryPoliciesReportSection,
    IntersightNetworkConnectivityPoliciesReportSection,
    IntersightNtpPoliciesReportSection,
    IntersightPowerPoliciesReportSection,
    IntersightSanConnectivityPoliciesReportSection,
    IntersightScrubPoliciesReportSection,
    IntersightSdCardPoliciesReportSection,
    IntersightSerialOverLanPoliciesReportSection,
    IntersightServerPoolQualificationPoliciesReportSection,
    IntersightStoragePoliciesReportSection,
    IntersightSyslogPoliciesReportSection,
    IntersightThermalPoliciesReportSection,
    IntersightVirtualKvmPoliciesReportSection,
    IntersightVirtualMediaPoliciesReportSection,
    IntersightVhbaTemplatesReportSection,
    IntersightVnicTemplatesReportSection
)
from report.intersight.pools import (
    IntersightIpPoolsReportSection,
    IntersightIqnPoolsReportSection,
    IntersightMacPoolsReportSection,
    IntersightResourcePoolsReportSection,
    IntersightUuidPoolsReportSection,
    IntersightWwnnPoolsReportSection,
    IntersightWwpnPoolsReportSection
)
from report.ucs.section import UcsReportSection


class IntersightConfigReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Configuration"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightOrganizationsReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightPoolsReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightPoliciesReportSection(self.report.get_current_order_id(), parent=self))


class IntersightPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Pools"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightIpPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightIqnPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightMacPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightResourcePoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightUuidPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightWwnnPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightWwpnPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))


class IntersightPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Policies"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightBiosPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightBootPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightDriveSecurityPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightEthAdapterPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightEthNetworkControlPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightEthNetworkGroupPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightEthQosPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightFcAdapterPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightFcNetworkPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightFcQosPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightFcZonePoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightFirmwarePoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightImcAccessPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightIpmiOverLanPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightIscsiAdapterPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightIscsiBootPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightIscsiStaticTargetPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightLanConnectivityPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightLocalUserPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightMemoryPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightNetworkConnectivityPoliciesReportSection(order_id=self.report.get_current_order_id(),
                                                               parent=self))
        self.content_list.append(
            IntersightNtpPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightPowerPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightSanConnectivityPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightScrubPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightSdCardPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightSerialOverLanPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightServerPoolQualificationPoliciesReportSection(order_id=self.report.get_current_order_id(),
                                                                   parent=self))
        self.content_list.append(
            IntersightStoragePoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightSyslogPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightThermalPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightVirtualKvmPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightVirtualMediaPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightVhbaTemplatesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightVnicTemplatesReportSection(order_id=self.report.get_current_order_id(), parent=self))
