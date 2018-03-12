from loghelper import *
from preprocess_tools.licensemanager import *
import argparse
from configuration.historicconfig import HistoricConfig
from historic.historic_tiler_config import HistoricTilerConfig
from historic.generate_historic_slashburn import GenerateSlashburn
class Historic(object):
    """
    computes historic slashburn as a proportion of the historical harvest
    appends to tiler configuration with the historical layers
    """
    def __init__(self, historicConfig):
        self.historicConfig = historicConfig


    def Process(self, region_path):
        tilerConfig = HistoricTilerConfig(
            historicConfig.GetHistoricTilerConfigPath(region_path))

        tilerConfig.AddMergedDisturbanceLayers(
            layerData = self.historicConfig.GetRollbackDisturbances(),
            inventory_workspace = self.historicConfig.GetInventoryWorkspace(region_path),
            rollback_end_year = self.historicConfig.GetRollbackRange()["End_Year"] + 1,
            historic_end_year = self.historicConfig.GetHistoricRange()["End_Year"])

        tilerConfig.AddHistoricInsectLayers(
            layerData, first_year, last_year)

        self.GenerateHistoricSlashBurn(
            inventory_workspace = self.historicConfig.GetInventoryWorkspace(),
            inventory_disturbance_year_fieldname = self.historicConfig.GetInventoryField("age"),
            harvest_shp = harvest_shp,
            harvest_shp_year_field = harvest_shp_year_field,
            year_range = year_range,
            sb_percent = sb_percent)

        tilerConfig.AddSlashburn(
            year = "",
            path = "",
            yearField = "",
            name_filter = "",
            name = "",
            cbmDisturbanceTypeName = "",
            layerMeta = "")

    def GenerateHistoricSlashBurn(self, inventory_workspace,
                                  inventory_disturbance_year_fieldname,
                                  harvest_shp, harvest_shp_year_field,
                                  year_range, sb_percent):
        g = GenerateSlashburn()
        g.generateSlashburn(
            inventory_workspace = inventory_workspace,
            inventory_disturbance_year_fieldname = inventory_disturbance_year_fieldname,
            harvest_shp = harvest_shp,
            harvest_shp_year_field = harvest_shp_year_field,
            year_range = year_range,
            sb_percent = sb_percent)

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

        r = Historic(historicConfig)

        regions = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]

        for r in regions:
            region_path = r["PathName"]
            r.Process(region_path)

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)
