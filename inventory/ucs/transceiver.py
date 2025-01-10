# coding: utf-8
# !/usr/bin/env python

""" transceiver.py: Easy UCS Deployment Tool """
from inventory.generic.transceiver import GenericTransceiver
from inventory.ucs.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsTransceiver(GenericTransceiver, GenericUcsInventoryObject):
    def __init__(self, parent=None, transceiver=None):
        GenericTransceiver.__init__(self, parent=parent)
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=transceiver)

        self.type = self.get_attribute(ucs_sdk_object=transceiver, attribute_name="type")
        self.vendor = self.get_attribute(ucs_sdk_object=transceiver, attribute_name="vendor")


class UcsSystemTransceiver(UcsTransceiver, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentXcvr"

    def __init__(self, parent=None, equipment_xcvr=None):
        UcsTransceiver.__init__(self, parent=parent, transceiver=equipment_xcvr)

        self.model = self.get_attribute(ucs_sdk_object=equipment_xcvr, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=equipment_xcvr, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_xcvr, attribute_name="serial")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_xcvr)

        # Getting SKU info from catalog types file
        self._get_sku_info()

        if not self.sku:
            # Trying to determine SKU manually
            self._determine_sku_manually()

        # Getting length info from catalog file
        self._get_length_info()


class UcsImcTransceiver(UcsTransceiver, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "adaptorConnectorInfo"

    def __init__(self, parent=None, adaptor_connector_info=None):
        UcsTransceiver.__init__(self, parent=parent, transceiver=adaptor_connector_info)

        self.model = self.get_attribute(ucs_sdk_object=adaptor_connector_info, attribute_name="part_number",
                                        attribute_secondary_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=adaptor_connector_info, attribute_name="part_revision",
                                           attribute_secondary_name="revision")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_connector_info)
