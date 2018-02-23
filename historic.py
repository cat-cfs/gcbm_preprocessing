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

    def AppendFireLayer(self, year, inventory_workspace, layer_name,
                   fire_year_field, disturbanceType):

        filterConfig = self.tilerConfig.CreateConfigItem(
            "SliceValueFilter",
            target_val=year,
            slice_len=4)

        attributeConfig = self.tilerConfig.CreateConfigItem(
            "Attribute",
            layer_name=fire_year_field,
            filter=filterConfig)

        vectorLayerConfig =  self.tilerConfig.CreateConfigItem(
            "VectorLayer",
            name="fire_{}".format(year),
            path=inventory_workspace,
            attributes=attributeConfig,
            layer=layer_name)

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

        self.tilerConfig.AppendLayer("HistoricFire", disturbanceLayerConfig)

    def AppendHarvest(self, tilerConfig):
        pass

    def AppendSlashburn(self, tilerConfig):
        pass

    def AppendInsect(self, tilerConfig):
        pass






