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

    def AppendFire(self, year, inventory_workspace, layer_name, fire_year_field, disturbanceType):

        filterConfig = self.tilerConfig.CreateSliceValueFilterConfig(
            year, slice_len=4)

        attributeConfig = self.tilerConfig.CreateAttributeConfig(
            fire_year_field, filterConfig)

        vectorLayerConfig =  self.tilerConfig.CreateVectorLayerConfig(
            "fire_{}".format(year),
            inventory_workspace,
            attributeConfig,
            layer=layer_name)

        transitionConfig = self.tilerConfig.CreateTransitionRuleConfig(
            regen_delay = 0, age_after = 0)

        disturbanceLayerConfig = self.tilerConfig.CreateDisturbanceLayerConfig(
                vectorLayerConfig, year, disturbanceType, transitionConfig)

        self.tilerConfig.AppendLayer("HistoricFire", disturbanceLayerConfig)

    def AppendHarvest(self, tilerConfig):
        pass

    def AppendSlashburn(self, tilerConfig):
        pass

    def AppendInsect(self, tilerConfig):
        pass






