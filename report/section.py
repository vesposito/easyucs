# coding: utf-8
# !/usr/bin/env python

""" section.py: Easy UCS Deployment Tool """
from __init__ import __author__, __copyright__,  __version__, __status__


from docx.shared import Cm, Pt
from report.content import *
from report.content_table import *
from PIL import Image
from pathlib import Path
import os.path
import json


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
            self.content_list.append(InfraRackUcsReportSection(order_id=self.report.get_current_order_id(),
                                                               parent=self,
                                                               title=_("UCS Rack #") + rack.id, rack=rack))


class InfraRackUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, rack):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        path = self.report.img_path + "infra_" + "rack_" + rack.id + ".png"
        if os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path,
                                   centered=True, size=18))

            self.content_list.append(
                UcsReportRackConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                               fis=self.report.inventory.fabric_interconnects,
                                               fexs=self.report.inventory.fabric_extenders, rack=rack,
                                               centered=True)
            )
        else:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("This device is not connected to any FI or FEX")))


class InfraChassisEquipmentUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Chassis Internal Infrastructure cabling")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for chassis in self.report.inventory.chassis:
            self.content_list.append(InfraChassisUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                  parent=self,
                                                                  title=_("UCS Chassis #") + chassis.id,
                                                                  chassis=chassis))


class InfraChassisUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, chassis):
        GenericReportSection.__init__(self,order_id=order_id, parent=parent, title=title)

        path = self.report.img_path + "infra_" + "chassis_" + chassis.id + ".png"
        if os.path.exists(path):
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
        else:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("This device is not connected to any FI or FEX")))


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
        descr = _("This section details the inventory: FIs, FEXs, rack Servers, chassis and their components.")
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))
        self.content_list.append(FabricInventoryUcsReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(ChassisInventoryUcsReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(RackInventoryUcsReportSection(self.report.get_current_order_id(), parent=self))
        # self.content_list.append(RecapUcsReportSection(self.report.get_current_order_id(), parent=self))


class EquipmentInventoryUcsImcReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Equipment Inventory")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        descr = _("This section details the inventory.")
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))
        self.content_list.append(RackInventoryUcsReportSection(self.report.get_current_order_id(), parent=self))
        # self.content_list.append(RecapUcsImcReportSection(self.report.get_current_order_id(), parent=self))


class ChassisInventoryUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Chassis Inventory")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.chassis:
            descr = ""  # TODO
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        blade_list = []
        for chassis in self.report.inventory.chassis:
            self.content_list.append(ChassisUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title="Chassis #"+chassis.id, chassis=chassis))
            if chassis.blades:
                blade_list = blade_list + chassis.blades

        if blade_list:
            self.content_list.append(BladesUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                               title=_("Blade Servers Summary"),
                                                               blades=blade_list))


class BladesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, blades):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            BladesSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                           blades=blades, centered=True))



class RackInventoryUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Inventory")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.rack_units:
            descr = ""  # TODO
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        for rack in self.report.inventory.rack_units:
            self.content_list.append(RackUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                          title="Rack #" + rack.id, rack=rack))

        if self.report.device.device_type == "UCS System":
            if self.report.inventory.rack_units:
                self.content_list.append(RackUnitsUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                                title=_("Rack Servers Summary"),
                                                                rack_units=self.report.inventory.rack_units))


class RackUnitsUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, rack_units):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            RackUnitsSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                           rack_units=rack_units, centered=True))


class FabricInventoryUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Fabric Inventory")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.fabric_interconnects or self.report.inventory.fabric_extenders:
            descr = _("The Fabric inventory gives information about the " +
                      str(len(self.report.inventory.fabric_interconnects)) +
                      " FIs, " + str(len(self.report.inventory.fabric_extenders)) +
                      " FEXs, PSUs and Expansion Modules.")
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        for fi in self.report.inventory.fabric_interconnects:
            self.content_list.append(FiUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title="Fabric Interconnect " + fi.id, fi=fi))

        for fex in self.report.inventory.fabric_extenders:
            self.content_list.append(FexUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                            title="Fabric Extender " + fex.id, fex=fex))


class FiUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, fi):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = _("The FI " + fi.id + " (" + fi.model + ") has " + str(len(fi.expansion_modules)) +
                  " expansion modules and " + str(len(fi.power_supplies)) + " power supplies.")
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))
        if fi.model in ["UCS-FI-M-6324"]:
            # UCS Mini FI only has a rear picture
            path_rear = self.report.img_path + "fi_" + fi.id + "_rear_clear.png"
            if os.path.exists(path_rear):
                # rotate and create an horizontal picture of the FI from UCS Mini
                image = Image.open(path_rear).rotate(90, expand=True)
                path_rear = self.report.img_path + "fi_" + fi.id + "_rear_clear_horizontal.png"
                image.save(path_rear)
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, spacing_after=2))
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("Rear View")), centered=True, italicized=True, font_size=8))

        else:
            path_front = self.report.img_path + "fi_" + fi.id + "_front.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                                   centered=True, spacing_after=2))
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("Front View")), centered=True, italicized=True, font_size=8))

            path_rear = self.report.img_path + "fi_" + fi.id + "_rear_clear.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, spacing_after=2))
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("Rear View")), centered=True, italicized=True, font_size=8))
        self.content_list.append(
            FiUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi, centered=True))

        if fi.power_supplies:
            self.content_list.append(PsuUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title=_("Power Supplies"), device=fi))

        if fi.expansion_modules:
            self.content_list.append(GemUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title=_("Expansion Modules"), fi=fi))


class GemUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, fi):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                GemSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                             gem=fi.expansion_modules, centered=True))


class FexUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, fex):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = _("The FEX " + fex.id + " (" + fex.model + ") has " + str(len(fex.power_supplies)) + " power supplies.")
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        path_front = self.report.img_path + "fex_" + fex.id + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Front View")), centered=True, italicized=True, font_size=8))

        path_rear = self.report.img_path + "fex_" + fex.id + "_rear_clear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Rear View")), centered=True, italicized=True, font_size=8))
        self.content_list.append(
            FexUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, fex=fex, centered=True))

        if fex.power_supplies:
            self.content_list.append(PsuUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("Power Supplies"), device=fex))

class RackUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, rack):
        GenericReportSection.__init__(self,order_id=order_id, parent=parent ,title=title)

        descr = ""  # TODO
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        path_front = self.report.img_path + "rack_" + rack.id + "_front.png"
        path_rear = self.report.img_path + "rack_" + rack.id + "_rear_clear.png"
        if self.report.device.device_type == "UCS IMC":
            path_front = self.report.img_path + "rack_front.png"
            path_rear = self.report.img_path + "rack_rear.png"

        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Front View")), centered=True, italicized=True, font_size=8))

        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Rear View")), centered=True, italicized=True, font_size=8))

        if self.report.size == "full":
            self.content_list.append(
                RackUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, rack=rack, centered=True))

        if rack.power_supplies:
            self.content_list.append(PsuUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("Power Supplies"), device=rack))
        if rack.storage_controllers:
            for storage_controller in rack.storage_controllers:
                key = GenericReportTable.get_name_and_sku(storage_controller)
                self.content_list.append(StorageControllerUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                           parent=self,
                                                                           title=_(
                                                                               "Storage Controller " +
                                                                               storage_controller.id +
                                                                               ' - ' + key),
                                                                           device=storage_controller))
        if rack.nvme_drives:
            self.content_list.append(NvmeDrivesUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                       parent=self,
                                                                       title=_(
                                                                           "NVMe Drives"),
                                                                       device=rack))


class ChassisUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, chassis):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ""  # TODO
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        path_front = self.report.img_path + "chassis_" + chassis.id + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Front View")), centered=True, italicized=True, font_size=8))

        path_rear = self.report.img_path + "chassis_" + chassis.id + "_rear_clear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Rear View")), centered=True, italicized=True, font_size=8))
        self.content_list.append(
            ChassisUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, chassis=chassis,
                               centered=True))

        if chassis.io_modules:
            self.content_list.append(IomUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("IO Modules"), chassis=chassis))
        if chassis.power_supplies:
            self.content_list.append(PsuUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("Power Supplies"), device=chassis))
        if chassis.blades:
            self.content_list.append(BladeServersUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("Blade Servers"), chassis=chassis))


class BladeServersUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, chassis):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                BladesSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                    blades=chassis.blades, centered=True))

            for blade in chassis.blades:
                self.content_list.append(BladeUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                               title=_("Blade Server " + blade.id + " details"),
                                                               blade=blade))


class BladeUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, blade):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                BladeUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                        blade=blade, centered=True))

            if blade.storage_controllers:
                for storage_controller in blade.storage_controllers:
                    key=GenericReportTable.get_name_and_sku(storage_controller)
                    self.content_list.append(StorageControllerUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                               parent=self,
                                                                               title=_(
                                                                                   "Storage Controller " +
                                                                                   storage_controller.id +
                                                                                   ' - ' + key),
                                                          device=storage_controller))

            if blade.nvme_drives:
                self.content_list.append(NvmeDrivesUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                    parent=self,
                                                                    title=_(
                                                                        "NVMe Drives"),
                                                                    device=blade))


class IomUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, chassis):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                IomSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                             iom=chassis.io_modules, centered=True))


class PsuUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, device):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                PsuSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                             psu=device.power_supplies, centered=True))


class StorageControllerUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, device):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            if device.disks:
                self.content_list.append(
                    DiskSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                 disks=device.disks, centered=True))


class NvmeDrivesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, device):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            if device.nvme_drives:
                self.content_list.append(
                    DiskSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                 disks=device.nvme_drives, centered=True))


class InfraLanNeighborsUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("LAN Neighbors")
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
            title = _("SAN Neighbors")
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
                                                        vlans=self.report.config.vlans, centered=True))


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
                                                        vsans=self.report.config.vsans, centered=True))


class ServiceProfilesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profile allocation")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.chassis:
            self.content_list.append(
                InfraChassisServiceProfileUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))

        if self.report.inventory.rack_units:
            self.content_list.append(
                InfraRackServiceProfileUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))


class InfraRackServiceProfileUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profile on Racks")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        i = 1
        path = self.report.img_path + "infra_service_profile_" + "rack_" + str(i) + ".png"
        while os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path, centered=True,
                                   size=18))
            i += 1
            path = self.report.img_path + "infra_service_profile_" + "rack_" + str(i) + ".png"

        flag = False
        for rack in self.report.inventory.rack_units:
            if rack.service_profile_name:
                flag = True
        if flag:
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
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path, centered=True,
                                   size=18))
            i += 1
            path = self.report.img_path + "infra_service_profile_" + "chassis_" + str(i) + ".png"

        flag = False
        for chassis in self.report.inventory.chassis:
            for blade in chassis.blades:
                if blade.service_profile_name:
                    flag = True
        if flag:
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


class RecapUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Detailed Specifications")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        # FI
        if self.report.inventory.fabric_interconnects or self.report.inventory.fabric_extenders:
            fabric_model_list = []
            for fabric in self.report.inventory.fabric_interconnects:
                key = fabric.sku
                if key not in fabric_model_list:
                    fabric_model_list.append(key)

            if fabric_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="FI", recap=fabric_model_list,
                                                              title=_("Fabric Interconnect Details")))

        # FEX
        if self.report.inventory.fabric_extenders:
            fabric_model_list = []
            for fabric in self.report.inventory.fabric_extenders:
                key = fabric.sku
                if key not in fabric_model_list:
                    fabric_model_list.append(key)

            if fabric_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="FEX", recap=fabric_model_list,
                                                              title=_("FEX Details")))

        # Chassis / Blades
        if self.report.inventory.chassis:
            chassis_model_list = []
            blade_model_list = []
            for chassis in self.report.inventory.chassis:
                if chassis.blades:
                    for blade in chassis.blades:
                        if blade.sku_scaled:
                            key = blade.sku_scaled
                        else:
                            key = blade.sku
                        if key not in blade_model_list:
                            blade_model_list.append(key)
                key = chassis.sku
                if key not in chassis_model_list:
                    chassis_model_list.append(key)
            if chassis_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Chassis", recap=chassis_model_list,
                                                              title=_("Chassis Details")))
            if blade_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Blades", recap=blade_model_list,
                                                              title=_("Blades Details")))

        # Racks
        if self.report.inventory.rack_units:
            rack_model_list = []
            for rack in self.report.inventory.rack_units:
                key = rack.sku
                if key not in rack_model_list:
                    rack_model_list.append(key)

            if rack_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Rack", recap=rack_model_list,
                                                              title=_("Racks Details")))


class RecapUcsImcReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Detailed Specifications")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        # Racks
        if self.report.inventory.rack_units:
            rack_model_list = []
            for rack in self.report.inventory.rack_units:
                key = rack.sku
                if key not in rack_model_list:
                    rack_model_list.append(key)

            if rack_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Rack", recap=rack_model_list,
                                                              title=_("Racks Details")))

class ReportInventoryRecap(GenericReportSection):
    def __init__(self, order_id, parent, title, recap, type):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.rows = []

        self.title = title
        self.recap = recap
        self.parent = parent

        for sku in recap:
            json_file = self._get_json_file(sku)
            name = type + " " + sku
            if json_file:
                spec_sheet_url = "Not Found"
                descr = "Not defined"
                dimensions = ""
                weight = ""
                if "spec_sheet_url" in json_file:
                    spec_sheet_url = json_file['spec_sheet_url']
                if "specs" in json_file:
                    specs = json_file["specs"]
                    if "descr" in specs:
                        descr = specs['descr']
                    if 'dimensions' in specs:
                        dimensions = specs['dimensions']
                    if 'weight' in specs:
                        weight = specs['weight']
                if "model_short_name" in json_file:
                    name = type + " " + json_file["model_short_name"] + ' (' + sku + ')'

                self.rows.append([name, descr, spec_sheet_url, dimensions, weight])

        if self.rows:
            for row in self.rows:
                self.content_list.append(ReportInventoryDeviceRecap(order_id=self.report.get_current_order_id(),
                                                                    parent=self, row=row))

    def _get_json_file(self, sku):
        file_name = str(sku) + ".json"
        folder_path = self._find_folder_path(file_name=file_name)
        try:
            json_file = open(folder_path / str(file_name))
            json_string = json_file.read()
            json_file.close()
            return json.loads(json_string)
        except FileNotFoundError:
            self.logger(level="error", message="JSON file " + folder_path + file_name + " not found")

        return False

    def _find_folder_path(self, file_name):
        for directory, sub_dirs, files in os.walk("catalog"):
            for file in files:
                if file == file_name:
                    return Path(directory)
        self.logger(level="error", message="Could not find catalog folder path for " + file_name)
        return Path('')


class ReportInventoryDeviceRecap(GenericReportSection):
    def __init__(self, order_id, parent, row, title=""):
        if not title:
            title = row[0]
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.title = title

        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=_("Description: "), italicized=True, bolded=True))
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=row[1], new_paragraph=False))

        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=_("SpecSheet: "), italicized=True, bolded=True))
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=_("specsheet"), hyper_link=row[2], new_paragraph=False,
                                                   color="blue",
                                                   underlined=True))
        # Dimensions
        if row[3]:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("Dimensions: \n"), italicized=True, bolded=True))
            dim = ""
            for key, value in row[3].items():
                if type(value) is dict:
                    data = key.title() + " (H x W x D): "
                    for subkey, subvalue in value.items():
                        data = data + str(subvalue) + " x "
                    data = data[:-2]  # remove the last " x "
                    dim = dim + "    " + data + "\n"
                else:
                    data = key.title().replace('_', ' ') + ": " + str(value)
                    dim = dim + "    " + data + "\n"
            dim = dim[:-1]  # remove the last "\n"
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=dim, new_paragraph=False))

            # Weight
            if row[4]:
                self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                           string=_("Weight: \n"), italicized=True, bolded=True))
                weight = ""
                for key, value in row[4].items():
                    data = key.title().replace('_', ' ') + ": " + str(value)
                    weight = weight + "    " + data + "\n"
                weight = weight[:-1]  # remove the last "\n"
                self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                           string=weight, new_paragraph=False))
