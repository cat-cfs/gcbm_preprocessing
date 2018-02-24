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

    def AppendHistoricInsectDisturbances(self):
        pass

    def AppendMergedDisturbanceLayer(self, year, inventory_workspace, layer_name,
                   year_field, name, disturbanceType):

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
            name="{0}_{1}".format(name, year),
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
            disturbance_type = disturbanceType,
            transition = transitionConfig)

        self.tilerConfig.AppendLayer("Historic_Fire", disturbanceLayerConfig)

    def AppendHarvest(self, tilerConfig):
        pass

    def AppendSlashburn(self, tilerConfig):
        pass

    def AppendInsect(self, tilerConfig):
        pass






