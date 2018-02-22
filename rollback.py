from loghelper import *
from preprocess_tools.licensemanager import *
import argparse
from configuration.pathregistry import PathRegistry
from configuration.subregionconfig import SubRegionConfig
from configuration.rollbackconfig import RollbackConfig
from configuration.tilerconfig import TilerConfig

from rollback.merge_disturbances import MergeDisturbances
from rollback.intersect_disturbances_inventory import IntersectDisturbancesInventory
from rollback.update_inventory import CalculateDistDEdifference
from rollback.update_inventory import CalculateNewDistYr
from rollback.update_inventory import updateInvRollback

class Rollback(object):

    def __init__(self, rollbackConfig):
        self.rollbackConfig = rollbackConfig

    def CreateTilerConfig(self, region_path, inventoryMeta, resolution):
        tilerPath = self.rollbackConfig.GetTilerConfigPath(region_path)
        t = TilerConfig()

        inventoryLayers = [
            t.CreateConfigItem(typename="RasterLayer", 
                               path=x["file_path"],
                               attributes=[x["attribute"]],
                               attribute_table=x["attribute_table"])
            for x in inventoryMeta]

        boundingbox = t.CreateConfigItem(typename="BoundingBox",
                                         layer=inventoryLayers[0],
                                         pixel_size=resolution)
        t.Initialize(
            t.CreateConfigItem(typeName="CompressingTiler2D",
                             bounding_box=boundingbox,
                             use_bounding_box_resolution=True))

        for i in inventoryLayers:
            t.AppendLayer("inventory", i)
        t.writeJson(tilerPath)

    def Process(self, subRegionConfig, resolution, subRegionNames=None):
        regions = subRegionConfig.GetRegions() if subRegionNames is None \
            else [subRegionConfig.GetRegion(x) for x in subRegionNames]

        for r in regions:
            inventoryMeta = self.RunRollback(region_path = r["PathName"])
            CreateTilerConfig(region_path = r["PathName"],
                              inventoryMeta = inventoryMeta,
                              resolution = self.rollbackConfig.GetResolution())

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
                                               self.rollbackConfig.GetDistAgeProportionFilePath())
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

def main():

    create_script_log(sys.argv[0])
    parser = argparse.ArgumentParser(description="rollback")
    parser.add_argument("--pathRegistry", help="path to file registry data")
    parser.add_argument("--rollbackConfig", help="path to rollback configuration")
    parser.add_argument("--subRegionConfig", help="path to sub region data")
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