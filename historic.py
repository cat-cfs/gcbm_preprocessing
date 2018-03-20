from loghelper import *
from preprocess_tools.licensemanager import *
import argparse
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
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
        #load the rollback tiler config path. We will append to a copy of this.
        tilerConfig = HistoricTilerConfig(
            self.historicConfig.GetRollbackTilerConfigPath(region_path))

        defaultSpatialBoundaries = self.historicConfig.GetDefaultSpatialBoundaries(region_path)
        tilerConfig.AddAdminEcoLayers(
            spatial_boundaries_path= defaultSpatialBoundaries["Layer"],
            attributes = defaultSpatialBoundaries["Attributes"])

        tilerConfig.AddClimateLayer(
            climateLayerPath=self.historicConfig.GetMeanAnnualTempPath(region_path), )
        tilerConfig.AddMergedDisturbanceLayers(
            layerData = self.historicConfig.GetRollbackInputLayers(region_path),
            inventory_workspace = self.historicConfig.GetInventoryWorkspace(region_path),
            first_year = self.historicConfig.GetRollbackRange()["EndYear"] + 1,
            last_year = self.historicConfig.GetHistoricRange()["EndYear"])

        tilerConfig.AddHistoricInsectLayers(
           layerData = self.historicConfig.GetInsectDisturbances(region_path),
           first_year = self.historicConfig.GetHistoricRange()["StartYear"],
           last_year = self.historicConfig.GetHistoricRange()["EndYear"] + 1)

        slashburn_year_range = range(self.historicConfig.GetRollbackRange()["EndYear"] + 1,
                                     self.historicConfig.GetHistoricRange()["EndYear"] + 1)

        if(slashburn_year_range):
            harvestLayer = [x for x in 
                            self.historicConfig.GetRollbackInputLayers(region_path)
                            if x["Name"] == "harvest"]
            if len(harvestLayer) != 1:
                raise ValueError("expected a single harvest layer")

            harvest_shp = os.path.join(harvestLayer[0]["Workspace"], harvestLayer[0]["WorkspaceFilter"])
            harvest_shp_year_field = harvestLayer[0]["YearField"]
            sb_info = self.historicConfig.GetSlashBurnInfo()
            with arc_license(Products.ARC) as arcpy:
                g = GenerateSlashburn(arcpy)
                slashburn_path = g.generateSlashburn(
                    inventory_workspace = self.historicConfig.GetInventoryWorkspace(region_path),
                    inventory_disturbance_year_fieldname = self.historicConfig.GetInventoryField("disturbance_yr"),
                    harvest_shp = harvest_shp,
                    harvest_shp_year_field = harvest_shp_year_field,
                    year_range = slashburn_year_range,
                    sb_percent = sb_info["Percent"])

            for year in slashburn_year_range:
                tilerConfig.AddSlashburn(
                    year = year,
                    path = slashburn_path,
                    yearField = harvest_shp_year_field,
                    name = sb_info["Name"],
                    cbmDisturbanceTypeName = sb_info["CBM_Disturbance_Type"],
                    layerMeta = "historic_{}".format(sb_info["Name"]))

        tilerConfig.Save(self.historicConfig.GetHistoricTilerConfigPath(region_path))
def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="historic processor: processes inputs for the tiler for the historic portion of simulations")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument("--historicConfig", help="path to clip tasks data")
        parser.add_argument("--subRegionConfig", help="path to sub region data")
        parser.add_argument("--subRegionNames", help="optional comma delimited "+
                            "string of sub region names (as defined in "+
                            "subRegionConfig) to process, if unspecified all "+
                            "regions will be processed")

        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        historicConfig = HistoricConfig(os.path.abspath(args.historicConfig),
                                        pathRegistry)
        
        subRegionConfig = SubRegionConfig(os.path.abspath(args.subRegionConfig))

        subRegionNames = args.subRegionNames.split(",") \
            if args.subRegionNames else None

        historic = Historic(historicConfig)

        regions = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]

        for r in regions:
            region_path = r["PathName"]
            historic.Process(region_path)

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all historic tasks finished")

if __name__ == "__main__":
    main()