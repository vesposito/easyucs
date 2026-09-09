# coding: utf-8
# !/usr/bin/env python

""" equipment.py: Easy UCS Deployment Tool """

from report.content import GenericReportAdmonition, GenericReportText
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class IntersightEquipmentReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Equipment")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        config = self.report.config
        if not config or not config.equipment:
            return

        equipment = config.equipment[0] if config.equipment else {}

        descr = _("The following sections detail the equipment objects:")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr)
        )

        if equipment.get("imm_domains"):
            self.content_list.append(
                IntersightImmDomainsReportSection(self.report.get_current_order_id(), parent=self)
            )
        if equipment.get("rack_units"):
            self.content_list.append(
                IntersightRackUnitsReportSection(self.report.get_current_order_id(), parent=self)
            )


class IntersightImmDomainsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("IMM Domains")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        config = self.report.config
        if not config or not config.equipment:
            return

        descr = _("The following sections detail the IMM domain equipment objects:")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr)
        )

        for imm_domain in config.equipment[0].get("imm_domains", []):
            for chassis in imm_domain.chassis:
                self.content_list.append(
                    IntersightImmDomainChassisReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        chassis=chassis,
                        title=_("Chassis"),
                    )
                )
            for fex in imm_domain.fabric_extenders:
                self.content_list.append(
                    IntersightImmDomainFabricExtendersReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fex=fex,
                        title=_("Fabric Extenders"),
                    )
                )
            for fi in imm_domain.fabric_interconnects:
                self.content_list.append(
                    IntersightImmDomainFabricInterconnectsReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fi=fi,
                        title=_("Fabric Interconnects"),
                    )
                )
            for rack in imm_domain.rack_units:
                self.content_list.append(
                    IntersightImmDomainRackUnitReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        rack_unit=rack,
                        title=_("Rack Units"),
                    )
                )


class IntersightRackUnitsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Units")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        config = self.report.config
        if not config or not config.equipment:
            return

        descr = _("The following sections detail the rack unit equipment objects:")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr)
        )

        for rack_unit in config.equipment[0].get("rack_units", []):
            self.content_list.append(
                IntersightRackUnitReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    rack_unit=rack_unit,
                    title=_("Rack Unit"),
                )
            )


class IntersightImmDomainChassisReportSection(UcsReportSection):
    def __init__(self, order_id, parent, chassis, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightImmDomainChassisReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                chassis=chassis,
            )
        )
        if chassis.get("blades"):
            for blade in chassis.get("blades", []):
                self.content_list.append(
                    IntersightImmDomainBladeReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        blade=blade,
                        title=_("Blade"),
                    )
                )


class IntersightImmDomainChassisReportTable(UcsReportTable):
    def __init__(self, order_id, parent, chassis, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), chassis.get("name")],
            [_("ID"), chassis.get("id")],
            [_("Serial"), chassis.get("serial")],
            [_("User Label"), chassis.get("user_label")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightImmDomainBladeReportSection(UcsReportSection):
    def __init__(self, order_id, parent, blade, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightImmDomainBladeReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                blade=blade,
            )
        )


class IntersightImmDomainBladeReportTable(UcsReportTable):
    def __init__(self, order_id, parent, blade, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), blade.get("name")],
            [_("Slot ID"), blade.get("slot_id")],
            [_("Serial"), blade.get("serial")],
            [_("User Label"), blade.get("user_label")],
            [_("Asset Tag"), blade.get("asset_tag")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightImmDomainFabricExtendersReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fex, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightImmDomainFabricExtendersReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                fex=fex,
            )
        )


class IntersightImmDomainFabricExtendersReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fex, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), fex.get("name")],
            [_("ID"), fex.get("id")],
            [_("Serial"), fex.get("serial")],
            [_("Switch ID"), fex.get("switch_id")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightImmDomainFabricInterconnectsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fi, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightImmDomainFabricInterconnectsReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                fi=fi,
            )
        )

        if fi.get("ports"):
            if fi["ports"].get("ethernet_port_channels"):
                self.content_list.append(
                    IntersightImmDomainFabricInterconnectEthFcPortReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fi=fi,
                        ports=fi["ports"].get("ethernet_port_channels"),
                        title=_("Ethernet Port Channels"),
                    )
                )
            if fi["ports"].get("fc_port_channels"):
                self.content_list.append(
                    IntersightImmDomainFabricInterconnectEthFcPortReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fi=fi,
                        ports=fi["ports"].get("fc_port_channels"),
                        title=_("FC Port Channels"),
                    )
                )
            if fi["ports"].get("ethernet_ports"):
                self.content_list.append(
                    IntersightImmDomainFabricInterconnectEthFcPortReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fi=fi,
                        ports=fi["ports"].get("ethernet_ports"),
                        title=_("Ethernet Ports"),
                    )
                )
            if fi["ports"].get("fc_ports"):
                self.content_list.append(
                    IntersightImmDomainFabricInterconnectEthFcPortReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fi=fi,
                        ports=fi["ports"].get("fc_ports"),
                        title=_("FC Ports"),
                    )
                )


class IntersightImmDomainFabricInterconnectsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fi, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), fi.get("name")],
            [_("Serial"), fi.get("serial")],
            [_("Switch ID"), fi.get("switch_id")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightImmDomainRackUnitReportSection(UcsReportSection):
    def __init__(self, order_id, parent, rack_unit, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightImmDomainRackUnitsReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                rack_units=rack_unit,
            )
        )


class IntersightRackUnitReportSection(UcsReportSection):
    def __init__(self, order_id, parent, rack_unit, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightImmDomainRackUnitsReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                rack_units=rack_unit,
            )
        )


class IntersightImmDomainRackUnitsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack_units, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), rack_units.get("name")],
            [_("ID"), rack_units.get("id")],
            [_("Serial"), rack_units.get("serial")],
            [_("User Label"), rack_units.get("user_label")],
            [_("Asset Tag"), rack_units.get("asset_tag")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightImmDomainFabricInterconnectEthFcPortReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fi, ports, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if title in [_("Ethernet Ports"), _("FC Ports"), "Ethernet Ports", "FC Ports"]:
            self.content_list.append(
                IntersightImmDomainFabricInterconnectPortsReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    ports=ports,
                )
            )
        else:
            self.content_list.append(
                IntersightImmDomainFabricInterconnectPortChannelsReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    ports=ports,
                )
            )


class IntersightImmDomainFabricInterconnectPortsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ports, centered=False):
        rows = [[_("Slot ID"), _("Port ID"), _("Aggr ID"), _("User Label")]]

        for port in ports:
            rows.append([port.get("slot_id"), port.get("port_id"), port.get("aggr_id"), port.get("user_label")])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightImmDomainFabricInterconnectPortChannelsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ports, centered=False):
        rows = [[_("PC ID"), _("User Label")]]

        for port in ports:
            rows.append([port.get("id"), port.get("user_label")])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )

