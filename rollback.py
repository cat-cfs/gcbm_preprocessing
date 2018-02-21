from loghelper import *
import argparse
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.rollbackconfig import RollbackConfig

from rollback.merge_disturbances import MergeDisturbances
from rollback.intersect_disturbances_inventory import IntersectDisturbancesInventory
from rollback.update_inventory import CalculateDistDEdifference
from rollback.update_inventory import CalculateNewDistYr
from rollback.update_inventory import updateInvRollback

class Rollback(object):

    def __init__(self, rollbackConfig):
        self.rollbackConfig = rollbackConfig

    def Process(self, subRegionConfig, subRegionNames=None):
        regions = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]

        for r in regions:
            self.RunRollback(region_path = r["PathName"])

    def RunRollback(self, region_path):
        inventory_workspace = self.rollbackConfig.GetInventoryWorkspace(region_path)
        inventory_year = int(self.rollbackConfig.GetInventoryYear())
        inventory_field_names = self.rollbackConfig.GetInventoryFieldNames()
        inventory_classifiers = self.rollbackConfig.GetInventoryClassifiers()
        rollback_range = self.rollbackConfig.GetRollbackRange()
        harvest_year_field = self.rollbackConfig.GetHistoricHarvestYearField()
        inventory_raster_output_dir = self.rollbackConfig.GetInventoryRasterOutputDir(region_path)
        rollback_disturbances_output = self.rollbackConfig.GetRollbackDisturbancesOutput(region_path)
        resolution = self.rollbackConfig.GetResolution()
        slashburnpercent = self.rollbackConfig.GetSlashBurnPercent()
        reportingclassifiers = self.rollbackConfig.GetReportingClassifiers()
        disturbances = self.rollbackConfig.GetRollbackDisturbances(region_path)

        mergeDist = MergeDisturbances(inventory_workspace, disturbances)
        intersect = IntersectDisturbancesInventory(inventory_workspace, inventory_year, inventory_field_names, rollback_range[0])
        calcDistDEdiff = CalculateDistDEdifference(inventory_workspace, inventory_year, inventory_field_names)
        calcNewDistYr = CalculateNewDistYr(inventory_workspace, inventory_year, inventory_field_names, rollback_range[0],harvest_year_field, self.rollbackConfig.GetDistAgeProportionFilePath())
        updateInv = updateInvRollback(inventory_workspace,
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

def main():

    create_script_log(sys.argv[0])
    parser = argparse.ArgumentParser(description="rollback")
    parser.add_argument("--pathRegistry", help="path to file registry data")
    parser.add_argument("--rollbackConfig", help="path to rollback configuration")
    parser.add_argument("--subRegionConfig", help="path to sub region data")
    parser.add_argument("--tilerConfigDir", help="path to the tilerConfig created by this process")
    parser.add_argument("--subRegionNames", help="optional comma delimited "+
                        "string of sub region names (as defined in "+
                        "subRegionConfig) to process, if unspecified all "+
                        "regions will be processed")
    try:
        args = parser.parse_args()

        pathRegistry = PathRegistry(os.path.abspath(args.pathRegistry))
        rollbackConfig = RollbackConfig(os.path.abspath(args.rollbackConfig), pathRegistry)
        subRegionConfig = SubRegionConfig(os.path.abspath(args.subRegionConfig))

        subRegionNames = args.subRegionNames.split(",") \
            if args.subRegionNames else None

        r = Rollback(rollbackConfig)
        r.Process(subRegionConfig, subRegionNames)
    except Exception as ex:
        logging.exception("error")
        sys.exit(1)

if __name__ == "__main__":
    main()