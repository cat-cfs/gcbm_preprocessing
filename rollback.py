from rollback.merge_disturbances import MergeDisturbances
from rollback.intersect_disturbances_inventory import IntersectDisturbancesInventory
from rollback.update_inventory import CalculateDistDEdifference
from rollback.update_inventory import CalculateNewDistYr
from rollback.update_inventory import updateInvRollback

class Rollback(object):

    def RunRollback(self,
                    inventory_workspace,
                    inventory_year,
                    inventory_field_names,
                    inventory_classifiers,
                    spatial_boundaries_area_filter,
                    rollback_range,
                    harvest_year_field,
                    rollback_out_dir,
                    rollback_disturbances,
                    resolution,
                    sbpercent,
                    reportingIndicators,
                    disturbances):

        mergeDist = MergeDisturbances(inventory_workspace, disturbances)
        intersect = IntersectDisturbancesInventory(inventory_workspace, inventory_year, inventory_field_names, spatial_boundaries_area_filter, rollback_range[0])
        calcDistDEdiff = CalculateDistDEdifference(inventory_workspace, inventory_year, inventory_field_names)
        calcNewDistYr = CalculateNewDistYr(inventory_workspace, inventory_year, inventory_field_names, rollback_range[0],harvest_year_field)
        updateInv = updateInvRollback(inventory_workspace, inventory_year, inventory_field_names, inventory_classifiers, rollback_out_dir, rollback_disturbances, rollback_range, resolution, sbpercent, reportingIndicators )

        mergeDist.runMergeDisturbances()
        intersect.runIntersectDisturbancesInventory()
        calcDistDEdiff.calculateDistDEdifference()
        calcNewDistYr.calculateNewDistYr()
        raster_metadata = updateInv.updateInvRollback()

def main():
    r = Rollback()
    
if __name__ == "__main__":
    main()