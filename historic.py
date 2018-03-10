from loghelper import *
from preprocess_tools.licensemanager import *
import argparse
from historic.historic_tiler_config import HistoricTilerConfig
from historic.generate_historic_slashburn import GenerateSlashburn
class Historic(object):
    """
    computes historic slashburn as a proportion of the historical harvest
    appends to tiler configuration with the historical layers
    """
    def __init__(self, tilerConfigPath):
        self.tilerConfig = HistoricTilerConfig(tilerConfigPath)

    def ProcessHistoric(self, config):
        self.tilerConfig.AddMergedDisturbanceLayers(
            layerData = config["MergedLayerData"],
            inventory_workspace = config["InventoryWorkspace"],
            rollback_end_year = "",
            historic_end_year = "")
        
        self.tilerConfig.AddHistoricInsectDisturbance(
            name = "",
            filename = "",
            year = "",
            attribute = "",
            attribute_lookup = "",
            layerMeta = "")

        self.tilerConfig.AddSlashburn(
            year = "",
            path = "",
            yearField = "",
            name_filter = "",
            name = "",
            cbmDisturbanceTypeName = "",
            layerMeta = "")

    def GenerateHistoricSlashBurn(self):
        g = GenerateSlashBurn()
        g.generateSlashburn(
            inventory_workspace = "",
            inventory_disturbance_year_fieldname = "",
            harvest_shp = "",
            harvest_shp_year_field = "",
            year_range = "",
            sb_percent = "")

def main():
    parser = argparse.ArgumentParser(description="historic processor: processes inputs for the tiler for the historic portion of simulations")
    parser.add_argument("--pathRegistry", help="path to file registry data")
    parser.add_argument("--historicConfig", help="path to clip tasks data")
    parser.add_argument("--subRegionConfig", help="path to sub region data")
    parser.add_argument("--subRegionNames", help="optional comma delimited "+
                        "string of sub region names (as defined in "+
                        "subRegionConfig) to process, if unspecified all "+
                        "regions will be processed")

    try:
        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        historicConfig = HistoricConfig(os.path.abspath(args.historicConfig),
                                        pathRegistry)
        subRegionConfig = SubRegionConfig(os.path.abspath(args.subRegionConfig))

        subRegionNames = args.subRegionNames.split(",") \
            if args.subRegionNames else None

        r = Rollback(historicConfig)
        r.Process(subRegionConfig, subRegionNames)
    except Exception as ex:
        logging.exception("error")
        sys.exit(1)











