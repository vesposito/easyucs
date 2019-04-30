# coding: utf-8
# !/usr/bin/env python

""" section.py: Easy UCS Deployment Tool """
from __init__ import __author__, __copyright__,  __version__, __status__


from docx.shared import Cm, Pt
from report.content import *
from report.content_table import *
import os.path


class GenericReportSection(GenericReportElement):
    # A section has a list of img, string and table (all called content) (content can even be other sections)
    def __init__(self, order_id, parent, title):
        GenericReportElement.__init__(self, order_id=order_id, parent=parent)
        self.content_list = []
        self.title = title
        self.indent = self.__find_indent() # Heading 1 for example

    def add_in_word_report(self):
        #self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        self.report.document.add_heading(text=self.title, level=self.indent)

    def __find_indent(self):
        indent = 1
        current_object = self.parent
        while hasattr(current_object, 'parent') and not hasattr(current_object, 'timestamp'):
            current_object = current_object.parent
            indent += 1
        if hasattr(current_object, 'timestamp'):
            return indent
        else:
            return None


class ArchitectureUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Architecture")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(InfraCablingUcsReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(InfraNeighborsUcsReportSection(self.report.get_current_order_id(), parent=self))


class InfraCablingUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Internal Infrastructure cabling")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.chassis:
            if self.report.inventory.fabric_interconnects[0].model not in ["UCS-FI-M-6324"]:
                self.content_list.append(InfraChassisEquipmentUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                               parent=self))
        if self.report.inventory.rack_units:
            self.content_list.append(InfraRackEquipmentUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                        parent=self))


class InfraRackEquipmentUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Rack Servers Internal Infrastructure cabling")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for rack in self.report.inventory.rack_units:
            if rack._draw_infra:
                self.content_list.append(InfraRackUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                   parent=self,
                                                                   title=_("UCS Rack #") + rack.id, rack=rack))


class InfraRackUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, rack):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        path = self.report.img_path + "infra_" + "rack_" + rack.id + ".png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path,
                               centered=True, size=18))

        self.content_list.append(
            UcsReportRackConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                           fis=self.report.inventory.fabric_interconnects,
                                           fexs=self.report.inventory.fabric_extenders, rack=rack,
                                           centered=True)
        )


class InfraChassisEquipmentUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Chassis Internal Infrastructure cabling")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for chassis in self.report.inventory.chassis:
            if chassis._draw_infra:
                self.content_list.append(InfraChassisUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                      parent=self,
                                                                      title=_("UCS Chassis #") + chassis.id,
                                                                      chassis=chassis))


class InfraChassisUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, chassis):
        GenericReportSection.__init__(self,order_id=order_id, parent=parent, title=title)

        path = self.report.img_path + "infra_" + "chassis_" + chassis.id + ".png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path,
                               centered=True, size=18)
        )

        self.content_list.append(
            UcsReportChassisConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                              fis=self.report.inventory.fabric_interconnects,
                                              fexs=self.report.inventory.fabric_extenders, chassis=chassis,
                                              centered=True)
        )


class InfraNeighborsUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Network Neighbors")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.lan_neighbors:
            self.content_list.append(
                InfraLanNeighborsUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        if self.report.inventory.san_neighbors:
            self.content_list.append(
                InfraSanNeighborsUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))


class EquipmentInventoryUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Equipment Inventory")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(FabricInventoryUcsReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(RackInventoryUcsReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(ChassisInventoryUcsReportSection(self.report.get_current_order_id(), parent=self))


class RackInventoryUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Inventory")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for rack in self.report.inventory.rack_units:
            self.content_list.append(RackUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                          title="Rack #"+rack.id, rack=rack))


class ChassisInventoryUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Chassis Inventory")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for chassis in self.report.inventory.chassis:
            self.content_list.append(ChassisUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title="Chassis #"+chassis.id, chassis=chassis))


class FabricInventoryUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Fabric Inventory")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for fi in self.report.inventory.fabric_interconnects:
            self.content_list.append(FiUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title="Fabric Interconnect "+fi.id, fi=fi))

        for fex in self.report.inventory.fabric_extenders:
            self.content_list.append(FexUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                            title="Fabric Extenders " + fex.id, fex=fex))


class FiUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, fi):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if fi.model in ["UCS-FI-M-6324"]:
            # If UCS Mini
            path_rear = self.report.img_path + "fi_" + fi.id + "_rear.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, size=2))
        else:
            path_front = self.report.img_path + "fi_" + fi.id + "_front.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                                   centered=True))

            path_rear = self.report.img_path + "fi_" + fi.id + "_rear.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True))
        self.content_list.append(
            FiUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi, centered=True))

        if fi.expansion_modules:
            self.content_list.append(GemUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("GEM Section"), fi=fi))


class GemUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, fi):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            GemSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                         gem=fi.expansion_modules, centered=True))


class FexUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, fex):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        path_front = self.report.img_path + "fex_" + fex.id + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True))

        path_rear = self.report.img_path + "fex_" + fex.id + "_rear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True))
        self.content_list.append(
            FexUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, fex=fex, centered=True))

class RackUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, rack):
        GenericReportSection.__init__(self,order_id=order_id, parent=parent ,title=title)

        path_front = self.report.img_path + "rack_" + rack.id + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True))

        path_rear = self.report.img_path + "rack_" + rack.id + "_rear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True))
        self.content_list.append(
            RackUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, rack=rack, centered=True))

        if rack.power_supplies:
            self.content_list.append(PsuUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("PSU Section"), device=rack))


class ChassisUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, chassis):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        path_front = self.report.img_path + "chassis_" + chassis.id + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True))

        path_rear = self.report.img_path + "chassis_" + chassis.id + "_rear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True))
        self.content_list.append(
            ChassisUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, chassis=chassis,
                               centered=True))

        if chassis.blades:
            self.content_list.append(BladesUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("Blades Section"), chassis=chassis))
        if chassis.io_modules:
            self.content_list.append(IomUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("IOM Section"), chassis=chassis))
        if chassis.power_supplies:
            self.content_list.append(PsuUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("PSU Section"), device=chassis))


class BladesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, chassis):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            BladesSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                blades=chassis.blades, centered=True))

        for blade in chassis.blades:
            self.content_list.append(BladeUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                           title="Blade #" + blade.id, blade=blade))


class BladeUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, blade):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            BladeUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                    blade=blade, centered=True))


class IomUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, chassis):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IomSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                         iom=chassis.io_modules, centered=True))


class PsuUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, device):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            PsuSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                         psu=device.power_supplies, centered=True))


class InfraLanNeighborsUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Lan Neighbors")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        lan_neighbors_path = self.report.img_path + "infra_lan_neighbors.png"
        self.content_list.append(GenericReportImage(order_id=self.report.get_current_order_id(), parent=self,
                                                    path=lan_neighbors_path, centered=True, size=18))

        self.content_list.append(
            UcsReportLanNeighborsConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                              fis=self.report.inventory.fabric_interconnects, centered=False)
        )


class InfraSanNeighborsUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("San Neighbors")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        san_neighbors_path = self.report.img_path + "infra_san_neighbors.png"
        self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=san_neighbors_path,
                                   centered=True, size=18))

        self.content_list.append(
            UcsReportSanNeighborsConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                                   fis=self.report.inventory.fabric_interconnects, centered=False)
        )


class LogicalConfigurationUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Logical Configuration")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(VlanUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(VsanUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(VlanGroupUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(ServiceProfilesUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))


class VlanUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VLAN Information")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.config.vlans:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("There is a total of ") + str(len(self.report.config.vlans)) + " VLANs")))
            self.content_list.append(
                VlanUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                        vlans=self.report.config.vlans))


class VlanGroupUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VLAN Group Information")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.config.vlan_groups:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("There is a total of ") + str(len(self.report.config.vlan_groups)) +
                                          _(" VLANs groups"))))
            self.content_list.append(
                VlanGroupUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                        vlan_groups=self.report.config.vlan_groups))


class VsanUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VSAN Information")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.config.vsans:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                   string=(_("There is a total of ") + str(len(self.report.config.vsans)) + " VSANs")))
            self.content_list.append(
                VsanUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                        vsans=self.report.config.vsans))


class ServiceProfilesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profile allocation")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.rack_units:
            self.content_list.append(
                InfraRackServiceProfileUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))

        if self.report.inventory.chassis:
            self.content_list.append(
                InfraChassisServiceProfileUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))


class InfraRackServiceProfileUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profile on Racks")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        i = 1
        path = self.report.img_path + "infra_service_profile_" + "rack_" + str(i) + ".png"
        while os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path, centered=True, size=18))
            i += 1
            path = self.report.img_path + "infra_service_profile_" + "rack_" + str(i) + ".png"

        self.content_list.append(ServiceProfilesRacksUcsReportTable(order_id=self.report.get_current_order_id(),
                                                                    parent=self,
                                                                    rack_units=self.report.inventory.rack_units))


class InfraChassisServiceProfileUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profile on Chassis")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        i = 1
        path = self.report.img_path + "infra_service_profile_" + "chassis_" + str(i) + ".png"
        while os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path, centered=True, size=18))
            i += 1
            path = self.report.img_path + "infra_service_profile_" + "chassis_" + str(i) + ".png"

        self.content_list.append(ServiceProfilesChassisUcsReportTable(order_id=self.report.get_current_order_id(),
                                                                      parent=self,
                                                                      chassis=self.report.inventory.chassis))


class ClusterOverviewUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Fabric Interconnect - Cluster Overview")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            ClusterInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                      config=self.report.config, device=self.report.device, centered=True))
        self.content_list.append(ClusterCommServicesUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                     parent=self))


class ClusterCommServicesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Communications Services")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            CommServicesInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                           config=self.report.config, device=self.report.device, centered=True))

