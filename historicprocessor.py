import argparse
import logging

from loghelper import create_script_log
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.preprocessorconfig import PreprocessorConfig
from historic.historic_tiler_config import HistoricTilerConfig
from historic.generate_historic_slashburn import generate_slashburn


class Historic(object):
    """
    computes historic slashburn as a proportion of the historical harvest
    appends to tiler configuration with the historical layers
    """
    def __init__(self, preprocessorConfig):
        self.preprocessorConfig = preprocessorConfig

    def Process(self, region_path):
        #load the rollback tiler config path. We will append to a copy of this.
        tilerConfig = HistoricTilerConfig(
            self.preprocessorConfig.GetRollbackTilerConfigPath(region_path))

        defaultSpatialBoundaries = self.preprocessorConfig.GetDefaultSpatialBoundaries(region_path)
        tilerConfig.AddAdminEcoLayers(
            spatial_boundaries_path= defaultSpatialBoundaries["Path"],
            attributes = defaultSpatialBoundaries["Attributes"])

        mat = climateLayerPath=self.preprocessorConfig.GetMeanAnnualTemp(region_path)
        tilerConfig.AddClimateLayer(mat["Path"], mat["Nodata_Value"])

        tilerConfig.AddMergedDisturbanceLayers(
            layerData = self.preprocessorConfig.GetHistoricMergedDisturbanceLayers(),
            inventory_workspace = self.preprocessorConfig.GetInventoryWorkspace(region_path),
            first_year = self.preprocessorConfig.GetRollbackRange()["EndYear"] + 1,
            last_year = self.preprocessorConfig.GetHistoricRange()["EndYear"])

        tilerConfig.AddHistoricInsectLayers(
           layerData = self.preprocessorConfig.GetInsectDisturbances(region_path),
           first_year = self.preprocessorConfig.GetHistoricRange()["StartYear"],
           last_year = self.preprocessorConfig.GetHistoricRange()["EndYear"] + 1)

        slashburn_year_range = range(self.preprocessorConfig.GetRollbackRange()["EndYear"] + 1,
                                     self.preprocessorConfig.GetHistoricRange()["EndYear"] + 1)

        if(slashburn_year_range):
            sbInput = self.preprocessorConfig.GetHistoricSlashburnInput(region_path)
            harvestLayer = sbInput["HarvestLayer"]
            harvest_shp = os.path.join(harvestLayer["Workspace"], harvestLayer["WorkspaceFilter"])
            harvest_shp_year_field = harvestLayer["YearField"]
            sb_percent = self.preprocessorConfig.GetSlashBurnPercent()

            slashburn_path = generate_slashburn(
                inventory_workspace=self.preprocessorConfig.GetInventoryWorkspace(
                    region_path),
                inventory_disturbance_year_fieldname=self.preprocessorConfig.GetInventoryField("disturbance_yr"),
                harvest_shp=harvest_shp,
                harvest_shp_year_field=harvest_shp_year_field,
                year_range=slashburn_year_range,
                sb_percent=sb_percent)

            for year in slashburn_year_range:
                tilerConfig.AddSlashburn(
                    year = year,
                    path = slashburn_path,
                    yearField = harvest_shp_year_field,
                    name = sbInput["Name"],
                    cbmDisturbanceTypeName = sbInput["CBM_Disturbance_Type"],
                    layerMeta = "historic_{}".format(sbInput["Name"]))

        tilerConfig.Save(self.preprocessorConfig.GetHistoricTilerConfigPath(region_path))
def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="historic processor: processes inputs for the tiler for the historic portion of simulations")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument("--preprocessorConfig", help="path to preprocessor config")
        parser.add_argument("--subRegionConfig", help="path to sub region data")
        parser.add_argument("--subRegionNames", help="optional comma delimited "+
                            "string of sub region names (as defined in "+
                            "subRegionConfig) to process, if unspecified all "+
                            "regions will be processed")

        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        preprocessorConfig = PreprocessorConfig(os.path.abspath(args.preprocessorConfig),
                                        pathRegistry)

        subRegionConfig = SubRegionConfig(os.path.abspath(args.subRegionConfig))

        subRegionNames = args.subRegionNames.split(",") \
            if args.subRegionNames else None

        historic = Historic(preprocessorConfig)

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