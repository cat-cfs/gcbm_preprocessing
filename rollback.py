from loghelper import *
from preprocess_tools.licensemanager import *
import argparse
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.preprocessorconfig import PreprocessorConfig

from rollback.merge_disturbances import MergeDisturbances
from rollback.intersect_disturbances_inventory import IntersectDisturbancesInventory
from rollback.update_inventory import CalculateDistDEdifference
from rollback.update_inventory import CalculateNewDistYr
from rollback.update_inventory import updateInvRollback
from rollback.rollback_tiler_config import RollbackTilerConfig

class Rollback(object):

    def __init__(self, config):
        self.config = config

    def Process(self, subRegionConfig, subRegionNames=None):
        regions = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]

        for r in regions:
            region_path = r["PathName"]
            inventoryMeta = self.RunRollback(region_path = region_path)

            tilerPath = self.config.GetRollbackTilerConfigPath(region_path = region_path)
            rollbackDisturbancePath = self.config.GetRollbackDisturbancesOutputDir(region_path)
            tilerConfig = RollbackTilerConfig()
            dist_lookup = self.config.GetRollbackOutputDisturbanceTypes()

            tilerConfig.Generate(outPath=tilerPath,
                inventoryMeta = inventoryMeta,
                resolution = self.config.GetResolution(),
                rollback_disturbances_path=rollbackDisturbancePath,
                rollback_range=[
                    self.config.GetRollbackRange()["StartYear"],
                    self.config.GetRollbackRange()["EndYear"]],
                dist_lookup=dist_lookup)

    def RunRollback(self, region_path):
        inventory_workspace = self.config.GetInventoryWorkspace(region_path)
        inventory_year = int(self.config.GetInventoryYear())
        inventory_field_names = self.config.GetInventoryFieldNames()
        inventory_classifiers = self.config.GetInventoryClassifiers()
        rollback_range = [
                    self.config.GetRollbackRange()["StartYear"],
                    self.config.GetRollbackRange()["EndYear"]]
        harvest_year_field = self.config.GetHistoricHarvestYearField()
        inventory_raster_output_dir = self.config.GetInventoryRasterOutputDir(region_path)
        rollback_disturbances_output = self.config.GetRollbackDisturbancesOutputDir(region_path)
        resolution = self.config.GetResolution()
        slashburnpercent = self.config.GetSlashBurnPercent()
        reportingclassifiers = self.config.GetReportingClassifiers()
        disturbances = self.config.GetRollbackInputLayers(region_path)

        with arc_license(Products.ARC) as arcpy:
            mergeDist = MergeDisturbances(arcpy, inventory_workspace, disturbances)
            intersect = IntersectDisturbancesInventory(arcpy, 
                                                       inventory_workspace,
                                                       inventory_year, 
                                                       inventory_field_names,
                                                       rollback_range[0])

            calcDistDEdiff = CalculateDistDEdifference(arcpy,
                                                       inventory_workspace,
                                                       inventory_year,
                                                       inventory_field_names)
            calcNewDistYr = CalculateNewDistYr(arcpy,
                                               inventory_workspace,
                                               inventory_year,
                                               inventory_field_names,
                                               rollback_range[0],harvest_year_field,
                                               self.config.GetDistAgeProportionFilePath())

            updateInv = updateInvRollback(arcpy, inventory_workspace,
                                          inventory_year,
                                          inventory_field_names,
                                          inventory_classifiers,
                                          inventory_raster_output_dir,
                                          rollback_disturbances_output,
                                          rollback_range,
                                          resolution,
                                          slashburnpercent,
                                          reportingclassifiers)

            mergeDist.runMergeDisturbances()
            intersect.runIntersectDisturbancesInventory()
            calcDistDEdiff.calculateDistDEdifference()
            calcNewDistYr.calculateNewDistYr()
            raster_metadata = updateInv.updateInvRollback()
            return raster_metadata

def main():

    create_script_log(sys.argv[0])
    try:
        parser = argparse.ArgumentParser(description="rollback")
        parser.add_argument("--pathRegistry", help="path to file registry data")
        parser.add_argument("--preprocessorConfig", help="path to preprocessor configuration")
        parser.add_argument("--subRegionConfig", help="path to sub region data")
        parser.add_argument("--subRegionNames", help="optional comma delimited "+
                            "string of sub region names (as defined in "+
                            "subRegionConfig) to process, if unspecified all "+
                            "regions will be processed")

        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        preprocessorconfig = PreprocessorConfig(os.path.abspath(args.preprocessorConfig), pathRegistry)
        subRegionConfig = SubRegionConfig(os.path.abspath(args.subRegionConfig))

        subRegionNames = args.subRegionNames.split(",") \
            if args.subRegionNames else None

        r = Rollback(preprocessorconfig)
        r.Process(subRegionConfig, subRegionNames)

    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

    logging.info("all rollup tasks finished")

if __name__ == "__main__":
    main()