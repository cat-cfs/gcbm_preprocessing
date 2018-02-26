from loghelper import *
from preprocess_tools.licensemanager import *
import argparse
from configuration.tilerconfig import TilerConfig

class Historic(object):
    """
    computes historic slashburn as a proportion of the historical harvest
    appends to tiler configuration with the historical layers
    """
    def __init__(self, tilerConfigPath):
        self.tilerConfig = TilerConfig(tilerConfigPath)

    def GenerateSlashBurn(self):
        pass

    def AppendHistoricInsectDisturbance(self, nameFormat, filename,
                                        year, attribute, attribute_lookup,
                                        layerMeta):
        attributeConfig = self.tilerConfig.CreateConfigItem(
            "Attribute",
            layer_name=attribute,
            substitutions=attribute_lookup)

        vectorlayerConfig = self.tilerConfig.CreateConfigItem(
            "VectorLayer",
            name = nameFormat.format(year),
            path = filename,
            attributes = attributeConfig)

        transitionRuleConfig = self.tilerConfig.CreateConfigItem(
            "TransitionRule",
            regen_delay=0,
            age_after=-1)

        disturbanceLayerConfig = self.tilerConfig.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorlayerConfig,
            year = year,
            disturbance_type= self.tilerConfig.CreateConfigItem(
                "Attribute", layer_name=attribute),
            transition = transitionRuleConfig)

        self.tilerConfig.AppendLayer(layerMeta, disturbanceLayerConfig)

    def AppendMergedDisturbanceLayer(self, year, inventory_workspace,
                                     year_field, name, cbmDisturbanceTypeName,
                                     layerMeta):

        filterConfig = self.tilerConfig.CreateConfigItem(
            "SliceValueFilter",
            target_val=year,
            slice_len=4)

        attributeConfig = self.tilerConfig.CreateConfigItem(
            "Attribute",
            layer_name=year_field,
            filter=filterConfig)

        vectorLayerConfig =  self.tilerConfig.CreateConfigItem(
            "VectorLayer",
            name=name,
            path=inventory_workspace,
            attributes=attributeConfig,
            layer="MergedDisturbances")

        transitionConfig = self.tilerConfig.CreateConfigItem(
            "TransitionRule",
            regen_delay = 0,
            age_after = 0)

        disturbanceLayerConfig = self.tilerConfig.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorLayerConfig,
            year = year,
            disturbance_type = cbmDisturbanceTypeName,
            transition = transitionConfig)

        self.tilerConfig.AppendLayer(layerMeta,
                                     disturbanceLayerConfig)

    def AppendSlashburn(self, year, path, yearField, name_filter, name,
                        cbmDisturbanceTypeName, layerMeta):
        valueFilterConfig = self.tilerConfig.CreateConfigItem(
            "ValueFilter",
            target_val = year,
            str_comparison = True)

        attributeConfig = self.tilerConfig.CreateConfigItem(
            "Attribute",
            layer_name = yearField,
            filter = valueFilterConfig)

        vectorLayerConfig = self.tilerConfig.CreateConfigItem(
            "VectorLayer",
            name = name,
            path = path,
            attributes=attributeConfig)

        transitionConfig = self.tilerConfig.CreateConfigItem(
            regen_delay=0,
            age_after=0)

        disturbanceLayerConfig = self.tilerConfig.CreateConfigItem(
            "DisturbanceLayer",
            lyr = vectorLayerConfig,
            year = year,
            disturbance_type = cbmDisturbanceTypeName,
            transition = transitionConfig)

        self.tilerConfig.AppendLayer(layerMeta,
                                     disturbanceLayerConfig)








