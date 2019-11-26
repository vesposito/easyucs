# coding: utf-8
# !/usr/bin/env python

""" section.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from docx.shared import Cm, Pt
from easyucs.report.content import *
from easyucs.report.content_table import *
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

    def parse_org(self, org, element_list, element_to_parse):
        if eval("org." + element_to_parse) is not None:
            for element in eval("org." + element_to_parse):
                element_list.append(element)
        if hasattr(org, "orgs"):
            if org.orgs is not None:
                for suborg in org.orgs:
                    self.parse_org(suborg, element_list, element_to_parse)


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
            title = _("Internal Infrastructure cabling")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.chassis:
            if self.report.inventory.fabric_interconnects[0].model not in ["UCS-FI-M-6324"]:
                self.content_list.append(InfraChassisEquipmentUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                               parent=self))
            else:
                # Checking if we have a second chassis in UCS Mini, otherwise infra section is not needed
                if len(self.report.inventory.chassis) > 1:
                    self.content_list.append(
                        InfraChassisEquipmentUcsReportSection(order_id=self.report.get_current_order_id(),
                                                              parent=self))
        if self.report.inventory.rack_units:
            self.content_list.append(InfraRackEquipmentUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                        parent=self))


class InfraRackEquipmentUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Servers Internal Infrastructure cabling")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for rack in self.report.inventory.rack_units:
            rack_name = rack.id
            if rack.user_label:
                rack_name = rack.id + " - " + rack.user_label
            self.content_list.append(InfraRackUcsReportSection(order_id=self.report.get_current_order_id(),
                                                               parent=self,
                                                               title=_("Rack ") + rack_name, rack=rack))


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
            title = _("Chassis Internal Infrastructure cabling")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for chassis in self.report.inventory.chassis:
            if chassis.id == "1" and self.report.inventory.fabric_interconnects[0].model in ["UCS-FI-M-6324"]:
                # We do not create a section for chassis 1 in UCS Mini
                continue
            chassis_name = chassis.id
            if chassis.user_label:
                chassis_name = chassis.id + " - " + chassis.user_label
            self.content_list.append(InfraChassisUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                  parent=self,
                                                                  title=_("Chassis ") + chassis_name,
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
                                                       string=_("This device is not connected to any FI")))


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
            chassis_name = chassis.id
            if chassis.user_label:
                chassis_name = chassis.id + " - " + chassis.user_label
            self.content_list.append(ChassisUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title="Chassis " + chassis_name, chassis=chassis))
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
            title = _("Rack Servers Inventory")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.rack_units:
            descr = ""  # TODO
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        for rack in self.report.inventory.rack_units:
            rack_name = rack.id
            if rack.user_label:
                rack_name = rack.id + " - " + rack.user_label
            self.content_list.append(RackUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                          title="Rack " + rack_name, rack=rack))

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

        if fi.licenses:
            self.content_list.append(LicensesUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                              title=_("Port Licenses"), fi=fi))


class GemUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, fi):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                GemSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                             gem=fi.expansion_modules, centered=True))


class LicensesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, fi):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                LicensesSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                  fi=fi, centered=True))



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

        if chassis.storage_enclosures:
            self.content_list.append(StorageEnclosuresUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                       parent=self, title=_("Storage Enclosures"),
                                                                       chassis=chassis))

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
                blade_name = blade.id + " details"
                if blade.user_label:
                    blade_name = blade.id + " details - " + blade.user_label
                self.content_list.append(BladeUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                               title=_("Blade Server " + blade_name),
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


class StorageEnclosuresUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, chassis):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            for storage_enclosure in chassis.storage_enclosures:
                storage_enclosure_name = storage_enclosure.descr + " (" + storage_enclosure.num_slots + " slots)"
                self.content_list.append(EnclosureUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                   parent=self, title=storage_enclosure_name,
                                                                   storage_enclosure=storage_enclosure))


class EnclosureUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, storage_enclosure):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            if storage_enclosure.disks:
                self.content_list.append(
                    DiskSectionInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                  disks=storage_enclosure.disks, centered=True))


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
            title = _("Configuration")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(FiLogicalConfigurationUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                        parent=self))
        self.content_list.append(NetworkingUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(OrganizationUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(IdentitiesUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(ServiceProfilesUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                 parent=self))


class NetworkingUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Networking")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(VlanUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(VlanGroupUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(VsanUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(LanPortChannelUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                parent=self))
        self.content_list.append(SanPortChannelUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                parent=self))
        self.content_list.append(FcoePortChannelUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                parent=self))
        self.content_list.append(QosSystemClassUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))


class FiLogicalConfigurationUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Fabric Interconnect Ports Configuration")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        for fi in self.report.inventory.fabric_interconnects:
            self.content_list.append(FiPortsUcsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                        title="Fabric Interconnect " + fi.id +
                                                              " Ports Configuration", fi=fi))


class FiPortsUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title, fi):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if fi.model in ["UCS-FI-M-6324"]:
            # UCS Mini FI only has a rear picture
            path_rear = self.report.img_path + "fi_" + fi.id + "_rear.png"
            if os.path.exists(path_rear):
                # rotate and create an horizontal picture of the FI from UCS Mini
                image = Image.open(path_rear).rotate(90, expand=True)
                path_rear = self.report.img_path + "fi_" + fi.id + "_rear_horizontal.png"
                image.save(path_rear)
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, spacing_after=2))
        else:

            path_rear = self.report.img_path + "fi_" + fi.id + "_rear.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, spacing_after=2))

        self.content_list.append(
            FiPortsUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi, centered=True))


class VlanUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VLANs")
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
            title = _("VLAN Groups")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.config.vlan_groups:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("There is a total of ") + str(len(self.report.config.vlan_groups)) +
                                          _(" VLANs groups"))))
            self.content_list.append(
                VlanGroupUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                        vlan_groups=self.report.config.vlan_groups))


class VsanUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VSANs")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.config.vsans:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                   string=(_("There is a total of ") + str(len(self.report.config.vsans)) + " VSANs")))
            self.content_list.append(
                VsanUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                        vsans=self.report.config.vsans, centered=True))


class LanPortChannelUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("LAN Port-Channels")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.config.lan_port_channels:
            self.content_list.append(
                LanPortChannelUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                             lan_port_channels=self.report.config.lan_port_channels))


class SanPortChannelUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("SAN Port-Channels")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.config.san_port_channels:
            self.content_list.append(
                SanPortChannelUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                             san_port_channels=self.report.config.san_port_channels))


class FcoePortChannelUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("FCoE Port-Channels")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.config.fcoe_port_channels:
            self.content_list.append(
                FcoePortChannelUcsReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                              fcoe_port_channels=self.report.config.fcoe_port_channels))


class IpPoolUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("IP Pools")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        ip_pool_list = []
        # Searching for all IP Pools
        for org in self.report.config.orgs:
            self.parse_org(org, ip_pool_list, element_to_parse="ip_pools")

        if ip_pool_list:
            for ip_pool in ip_pool_list:
                self.content_list.append(
                    IpPoolDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                      parent=self,
                                                      ip_pool=ip_pool,
                                                      title=_("IP Pool ") + ip_pool.name))


class IpPoolDescriptionUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, ip_pool, title=""):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if ip_pool.ip_blocks:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(),
                                  parent=self,
                                  string=_("\nIPv4 Blocks :"), bolded=True)
            )
            self.content_list.append(
                IpPoolSectionInfoBlockUcsReportTable(order_id=self.report.get_current_order_id(),
                                                     parent=self, centered=True,
                                                     blocks_ipv4=ip_pool.ip_blocks))

        if ip_pool.ipv6_blocks:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(),
                                  parent=self,
                                  string=_("\nIPv6 Blocks :"), bolded=True)
            )
            self.content_list.append(
                IpPoolSectionInfoBlockv6UcsReportTable(order_id=self.report.get_current_order_id(),
                                                       parent=self, centered=True,
                                                       blocks_ipv6=ip_pool.ipv6_blocks))


class MacPoolUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("MAC Pools")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        mac_pool_list = []
        # Searching for all IP Pools
        for org in self.report.config.orgs:
            self.parse_org(org, mac_pool_list, element_to_parse="mac_pools")

        if mac_pool_list:
            for mac_pool in mac_pool_list:
                self.content_list.append(
                    MacPoolDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                       parent=self,
                                                       mac_pool=mac_pool,
                                                       title=_("MAC Pool ") + mac_pool.name))


class MacPoolDescriptionUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, mac_pool, title=""):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if mac_pool.mac_blocks:
            self.content_list.append(
                GenericSectionInfoBlockUcsReportTable(order_id=self.report.get_current_order_id(),
                                                      parent=self, centered=True,
                                                      blocks=mac_pool.mac_blocks))


class UuidPoolUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UUID Pools")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        uuid_pool_list = []
        # Searching for all UUID Pools
        for org in self.report.config.orgs:
            self.parse_org(org, uuid_pool_list, element_to_parse="uuid_pools")

        if uuid_pool_list:
            for uuid_pool in uuid_pool_list:
                self.content_list.append(
                    UuidPoolDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                        parent=self,
                                                        uuid_pool=uuid_pool,
                                                        title=_("UUID Pool ") + uuid_pool.name))


class UuidPoolDescriptionUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, uuid_pool, title=""):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=_("\nPrefix : "), bolded=False))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=_(uuid_pool.prefix), bolded=True, new_paragraph=False))

        if uuid_pool.uuid_blocks:
            self.content_list.append(
                GenericSectionInfoBlockUcsReportTable(order_id=self.report.get_current_order_id(),
                                                      parent=self, centered=True,
                                                      blocks=uuid_pool.uuid_blocks))
            
            
class WwnnPoolUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("WWNN Pools")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        wwnn_pool_list = []
        # Searching for all WWNN Pools
        for org in self.report.config.orgs:
            self.parse_org(org, wwnn_pool_list, element_to_parse="wwnn_pools")

        if wwnn_pool_list:
            for wwnn_pool in wwnn_pool_list:
                self.content_list.append(
                    WwnnPoolDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                        parent=self,
                                                        wwnn_pool=wwnn_pool,
                                                        title=_("WWNN Pool ") + wwnn_pool.name))


class WwnnPoolDescriptionUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, wwnn_pool, title=""):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if wwnn_pool.wwnn_blocks:
            self.content_list.append(
                GenericSectionInfoBlockUcsReportTable(order_id=self.report.get_current_order_id(),
                                                      parent=self, centered=True,
                                                      blocks=wwnn_pool.wwnn_blocks))


class WwpnPoolUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("WWPN Pools")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        wwpn_pool_list = []
        # Searching for all WWPN Pools
        for org in self.report.config.orgs:
            self.parse_org(org, wwpn_pool_list, element_to_parse="wwpn_pools")

        if wwpn_pool_list:
            for wwpn_pool in wwpn_pool_list:
                self.content_list.append(
                    WwpnPoolDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                        parent=self,
                                                        wwpn_pool=wwpn_pool,
                                                        title=_("WWPN Pool ") + wwpn_pool.name))


class WwpnPoolDescriptionUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, wwpn_pool, title=""):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if wwpn_pool.wwpn_blocks:
            self.content_list.append(
                GenericSectionInfoBlockUcsReportTable(order_id=self.report.get_current_order_id(),
                                                      parent=self, centered=True,
                                                      blocks=wwpn_pool.wwpn_blocks))


class WwxnPoolUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("WWxN Pools")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        wwxn_pool_list = []
        # Searching for all WWxN Pools
        for org in self.report.config.orgs:
            self.parse_org(org, wwxn_pool_list, element_to_parse="wwxn_pools")

        if wwxn_pool_list:
            for wwxn_pool in wwxn_pool_list:
                self.content_list.append(
                    WwxnPoolDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                        parent=self,
                                                        wwxn_pool=wwxn_pool,
                                                        title=_("WWxN Pool ") + wwxn_pool.name))


class WwxnPoolDescriptionUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, wwxn_pool, title=""):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=_("\nMax ports per Node : "), bolded=False))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=_(wwxn_pool.max_ports_per_node), bolded=True, new_paragraph=False))

        if wwxn_pool.wwxn_blocks:
            self.content_list.append(
                GenericSectionInfoBlockUcsReportTable(order_id=self.report.get_current_order_id(),
                                                      parent=self, centered=True,
                                                      blocks=wwxn_pool.wwxn_blocks))


class QosSystemClassUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("QoS System Class")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.config.qos_system_class:
            self.content_list.append(
                QosSystemClassUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                             centered=True,
                                             qos_system_class=self.report.config.qos_system_class))


class ServiceProfilesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profiles & Templates")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(ServiceProfilesTemplatesDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                           parent=self))
        self.content_list.append(ServiceProfilesDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                            parent=self))
        self.content_list.append(ServiceProfilesAllocationUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                           parent=self))


class ServiceProfilesDescriptionUcsReportSection(GenericReportSection):
    def parse_org(self, org, service_profile_list, element_to_parse="service_profiles"):
        if org.service_profiles is not None:
            for service_profile in org.service_profiles:
                if not service_profile.service_profile_template:
                    if not service_profile.type in ["updating-template", "initial-template"]:
                        service_profile_list.append(service_profile)
        if hasattr(org, "orgs"):
            if org.orgs is not None:
                for suborg in org.orgs:
                    self.parse_org(suborg, service_profile_list)

    def __init__(self, order_id, parent, title=""):

        if not title:
            title = _("Service Profiles")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        service_profile_list = []
        # Searching for all updating template Service Profile
        for org in self.report.config.orgs:
            self.parse_org(org, service_profile_list)

        for sp in service_profile_list:
            self.content_list.append(ServiceProfileDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                               parent=self,
                                                                               service_profile=sp,
                                                                               title=_("Service Profile " + sp.name)))


class ServiceProfilesTemplatesDescriptionUcsReportSection(GenericReportSection):
    def parse_org(self, org, service_profile_temp_list, service_profile_child_list, element_to_parse="service_profiles"):
        if org.service_profiles is not None:
            for service_profile in org.service_profiles:
                if not service_profile.service_profile_template:
                    if service_profile.type in ["updating-template", "initial-template"]:
                        service_profile_temp_list.append(service_profile)
                else:
                    service_profile_child_list.append(service_profile)

        if hasattr(org, "orgs"):
            if org.orgs is not None:
                for suborg in org.orgs:
                    self.parse_org(suborg, service_profile_temp_list, service_profile_child_list)

    def __init__(self, order_id, parent, title=""):

        if not title:
            title = _("Service Profiles Templates")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        service_profile_temp_list = []
        service_profile_child_list = []
        # Searching for all updating template Service Profile
        for org in self.report.config.orgs:
            self.parse_org(org, service_profile_temp_list, service_profile_child_list)

        for sp_temp in service_profile_temp_list:
            # Get the SP spawned from the template
            children = ""
            for child in service_profile_child_list:
                if child.service_profile_template == sp_temp.name:
                    if not children:
                        children = child.name
                    else:
                        children = children + ", " + child.name
            sp_temp.children = children

            self.content_list.append(ServiceProfileDescriptionUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                               parent=self,
                                                                               service_profile=sp_temp,
                                                                               title=_("Service Profile Template " +
                                                                                       sp_temp.name)))
            delattr(sp_temp, "children")


class ServiceProfileDescriptionUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, service_profile, title=""):

        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if "template" in service_profile.type:
            service_profile_path = self.report.img_path + service_profile._parent._dn.replace(
                "/", "_") + "_Service_Profile_Template_" + "_".join(service_profile.name.split(" ")) + '.png'
        else:
            service_profile_path = self.report.img_path + service_profile._parent._dn.replace(
                "/", "_") + "_Service_Profile_" + "_".join(service_profile.name.split(" ")) + '.png'
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=service_profile_path,
                               centered=True, size=18))

        self.content_list.append(ServiceProfileUcsReportTable(order_id=self.report.get_current_order_id(),
                                                              parent=self,
                                                              centered=True,
                                                              service_profile=service_profile))


class ServiceProfilesAllocationUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profiles associations")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.chassis:
            self.content_list.append(
                InfraChassisServiceProfileUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))

        if self.report.inventory.rack_units:
            self.content_list.append(
                InfraRackServiceProfileUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))

        if self.report.inventory.rack_enclosures:
            self.content_list.append(
                InfraRackEnclosureServiceProfileUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                 parent=self))


class OrganizationUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Organizations")

        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        org_list = []
        # Searching for all orgs
        for org in self.report.config.orgs:
            self.parse_org(org, org_list, element_to_parse="orgs")
        if org_list:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("There is a total of " + str(len(org_list)) +
                                                                " organizations (excluding 'root').")))
        if len(org_list) == 0:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("There are no organizations (other than 'root')."),
                                                       italicized=True, bolded=False))
        else:
            org_path = self.report.img_path + "orgs.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=org_path,
                                   centered=True, size=18))


class IdentitiesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Identities")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(IpPoolUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(MacPoolUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(UuidPoolUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(WwnnPoolUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(WwpnPoolUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(WwxnPoolUcsReportSection(order_id=self.report.get_current_order_id(), parent=self))


class InfraRackServiceProfileUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Servers associations")
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
                                                                        parent=self, centered=True,
                                                                        rack_units=self.report.inventory.rack_units))


class InfraRackEnclosureServiceProfileUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Enclosures Servers associations")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        i = 1
        path = self.report.img_path + "infra_service_profile_" + "rack_enclosure_" + str(i) + ".png"
        while os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path, centered=True,
                                   size=18))
            i += 1
            path = self.report.img_path + "infra_service_profile_" + "rack_enclosure_" + str(i) + ".png"

        flag = False
        for rack_enclosure in self.report.inventory.rack_enclosures:
            for server_node in rack_enclosure.server_nodes:
                if server_node.service_profile_name:
                    flag = True
        if flag:
            self.content_list.append(
                ServiceProfilesRackEnclosuresUcsReportTable(order_id=self.report.get_current_order_id(),
                                                            parent=self, centered=True,
                                                            rack_enclosures=self.report.inventory.rack_enclosures))


class InfraChassisServiceProfileUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Blade Servers associations")
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
                                                                          parent=self, centered=True,
                                                                          chassis=self.report.inventory.chassis))


class ClusterOverviewUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS System Overview")
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            ClusterInfoUcsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                      config=self.report.config, device=self.report.device, centered=True))
        self.content_list.append(ClusterCommServicesUcsReportSection(order_id=self.report.get_current_order_id(),
                                                                     parent=self))


class ClusterCommServicesUcsReportSection(GenericReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Communication Services")
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
