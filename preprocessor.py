### GCBM Preprocessing

## Imports
import archook
archook.get_arcpy()
import arcpy
import os
import preprocess_tools
import cPickle
gridGeneration = __import__("01_grid_generation")
rollback = __import__("02_rollback")
tiler = __import__("03_tiler")
recliner2GCBM = __import__("04_recliner2GCBM")
GCBMconfig = __import__("05_GCBM_config")

def save_inputs():
    try:
        print "---------------------\nSaving inputs...",
        if not os.path.exists('inputs'):
            os.mkdir('inputs')
        cPickle.dump(inventory, open(r'inputs\inventory.pkl', 'wb'))
        cPickle.dump(historicFire1, open(r'inputs\historicFire1.pkl', 'wb'))
        cPickle.dump(historicFire2, open(r'inputs\historicFire2.pkl', 'wb'))
        cPickle.dump(historicHarvest, open(r'inputs\historicHarvest.pkl', 'wb'))
        cPickle.dump(historicMPB, open(r'inputs\historicMPB.pkl', 'wb'))
        cPickle.dump(projectedDistBase, open(r'inputs\projectedDistBase.pkl', 'wb'))
        cPickle.dump(rollbackDisturbances, open(r'inputs\rollbackDisturbances.pkl', 'wb'))
        cPickle.dump(spatialBoundaries, open(r'inputs\spatialBoundaries.pkl', 'wb'))
        cPickle.dump(NAmat, open(r'inputs\NAmat.pkl', 'wb'))
        cPickle.dump(transitionRules, open(r'inputs\transitionRules.pkl', 'wb'))
        cPickle.dump(yieldTable, open(r'inputs\yieldTable.pkl', 'wb'))
        cPickle.dump(AIDB, open(r'inputs\AIDB.pkl', 'wb'))
        cPickle.dump(resolution, open(r'inputs\resolution.pkl', 'wb'))
        cPickle.dump(rollback_enabled, open(r'inputs\rollback_enabled.pkl', 'wb'))
        cPickle.dump(historic_range, open(r'inputs\historic_range.pkl', 'wb'))
        cPickle.dump(rollback_range, open(r'inputs\rollback_range.pkl', 'wb'))
        cPickle.dump(future_range, open(r'inputs\future_range.pkl', 'wb'))
        cPickle.dump(activity_start_year, open(r'inputs\activity_start_year.pkl', 'wb'))
        cPickle.dump(inventory_raster_out, open(r'inputs\inventory_raster_out.pkl', 'wb'))
        cPickle.dump(tiler_scenarios, open(r'inputs\tiler_scenarios.pkl', 'wb'))
        cPickle.dump(GCBM_scenarios, open(r'inputs\GCBM_scenarios.pkl', 'wb'))
        cPickle.dump(tiler_output_dir, open(r'inputs\tiler_output_dir.pkl', 'wb'))
        cPickle.dump(recliner2gcbm_config_dir, open(r'inputs\recliner2gcbm_config_dir.pkl', 'wb'))
        cPickle.dump(recliner2gcbm_output_path, open(r'inputs\recliner2gcbm_output_path.pkl', 'wb'))
        cPickle.dump(future_dist_input_dir, open(r'inputs\future_dist_input_dir.pkl', 'wb'))
        cPickle.dump(gcbm_raw_output_dir, open(r'inputs\gcbm_raw_output_dir.pkl', 'wb'))
        cPickle.dump(gcbm_configs_dir, open(r'inputs\gcbm_configs_dir.pkl', 'wb'))
        cPickle.dump(reportingIndicators, open(r'inputs\reportingIndicators.pkl', 'wb'))
        cPickle.dump(gcbm_exe, open(r'inputs\gcbm_exe.pkl', 'wb'))
        print "Done\n---------------------"
    except:
        print "Failed to save inputs."
        raise

def load_inputs():
    global inventory
    global historicFire1
    global historicFire2
    global historicHarvest
    global historicMPB
    global projectedDistBase
    global rollbackDisturbances
    global NAmat
    global spatialBoundaries
    global transitionRules
    global yieldTable
    global AIDB
    global resolution
    global rollback_enabled
    global historic_range
    global rollback_range
    global future_range
    global activity_start_year
    global inventory_raster_out
    global rollback_dist_out
    global tiler_scenarios
    global GCBM_scenarios
    global recliner2gcbm_config_dir
    global recliner2gcbm_output_path
    global tiler_output_dir
    global future_dist_input_dir
    global gcbm_raw_output_dir
    global gcbm_configs_dir
    global reportingIndicators
    global gcbm_exe
    try:
        print "----------------------\nLoading inputs...",
        inventory = cPickle.load(open(r'inputs\inventory.pkl'))
        historicFire1 = cPickle.load(open(r'inputs\historicFire1.pkl'))
        historicFire2 = cPickle.load(open(r'inputs\historicFire2.pkl'))
        historicHarvest = cPickle.load(open(r'inputs\historicHarvest.pkl'))
        historicMPB = cPickle.load(open(r'inputs\historicMPB.pkl'))
        projectedDistBase = cPickle.load(open(r'inputs\projectedDistBase.pkl'))
        rollbackDisturbances = cPickle.load(open(r'inputs\rollbackDisturbances.pkl'))
        NAmat = cPickle.load(open(r'inputs\NAmat.pkl'))
        spatialBoundaries = cPickle.load(open(r'inputs\spatialBoundaries.pkl'))
        transitionRules = cPickle.load(open(r'inputs\transitionRules.pkl'))
        yieldTable = cPickle.load(open(r'inputs\yieldTable.pkl'))
        AIDB = cPickle.load(open(r'inputs\AIDB.pkl'))
        resolution = cPickle.load(open(r'inputs\resolution.pkl'))
        rollback_enabled = cPickle.load(open(r'inputs\rollback_enabled.pkl'))
        historic_range = cPickle.load(open(r'inputs\historic_range.pkl'))
        rollback_range = cPickle.load(open(r'inputs\rollback_range.pkl'))
        future_range = cPickle.load(open(r'inputs\future_range.pkl'))
        activity_start_year = cPickle.load(open(r'inputs\activity_start_year.pkl'))
        inventory_raster_out = cPickle.load(open(r'inputs\inventory_raster_out.pkl'))
        tiler_scenarios = cPickle.load(open(r'inputs\tiler_scenarios.pkl'))
        GCBM_scenarios = cPickle.load(open(r'inputs\GCBM_scenarios.pkl'))
        tiler_output_dir = cPickle.load(open(r'inputs\tiler_output_dir.pkl'))
        recliner2gcbm_config_dir = cPickle.load(open(r'inputs\recliner2gcbm_config_dir.pkl'))
        recliner2gcbm_output_path = cPickle.load(open(r'inputs\recliner2gcbm_output_path.pkl'))
        future_dist_input_dir = cPickle.load(open(r'inputs\future_dist_input_dir.pkl'))
        gcbm_raw_output_dir = cPickle.load(open(r'inputs\gcbm_raw_output_dir.pkl'))
        gcbm_configs_dir = cPickle.load(open(r'inputs\gcbm_configs_dir.pkl'))
        reportingIndicators = cPickle.load(open(r'inputs\reportingIndicators.pkl'))
        gcbm_exe = cPickle.load(open(r'inputs\gcbm_exe.pkl'))
        print "Done\n----------------------"
    except:
        print "Failed to load inputs."
        raise

def save_objects():
    try:
        print 'Saving objects...',
        if not os.path.exists('objects'):
            os.mkdir('objects')
        cPickle.dump(inventory, open(r'objects\inventory.pkl', 'wb'))
        cPickle.dump(rollbackDisturbances, open(r'objects\rollbackDisturbances.pkl', 'wb'))
        cPickle.dump(historicFire1, open(r'objects\historicFire1.pkl', 'wb'))
        cPickle.dump(historicFire2, open(r'objects\historicFire2.pkl', 'wb'))
        cPickle.dump(historicHarvest, open(r'objects\historicHarvest.pkl', 'wb'))
        cPickle.dump(historicMPB, open(r'objects\historicMPB.pkl', 'wb'))
        cPickle.dump(projectedDistBase, open(r'objects\projectedDistBase.pkl', 'wb'))
        cPickle.dump(NAmat, open(r'objects\NAmat.pkl', 'wb'))
        cPickle.dump(spatialBoundaries, open(r'objects\spatialBoundaries.pkl', 'wb'))
        cPickle.dump(transitionRules, open(r'objects\transitionRules.pkl', 'wb'))
        cPickle.dump(yieldTable, open(r'objects\yieldTable.pkl', 'wb'))
        cPickle.dump(AIDB, open(r'objects\AIDB.pkl', 'wb'))
        print 'Done'
    except:
        print "Failed to save objects."
        raise

def load_objects():
    global inventory
    global rollbackDisturbances
    global historicFire1
    global historicFire2
    global historicHarvest
    global historicMPB
    global projectedDistBase
    try:
        inventory = cPickle.load(open(r'objects\inventory.pkl'))
        rollbackDisturbances = cPickle.load(open(r'objects\rollbackDisturbances.pkl'))
        historicFire1 = cPickle.load(open(r'objects\historicFire1.pkl'))
        historicFire2 = cPickle.load(open(r'objects\historicFire2.pkl'))
        historicHarvest = cPickle.load(open(r'objects\historicHarvest.pkl'))
        historicMPB = cPickle.load(open(r'objects\historicMPB.pkl'))
        projectedDistBase = cPickle.load(open(r'objects\projectedDistBase.pkl'))
        NAmat = cPickle.load(open(r'objects\NAmat.pkl'))
        spatialBoundaries = cPickle.load(open(r'objects\spatialBoundaries.pkl'))
        transitionRules = cPickle.load(open(r'objects\transitionRules.pkl'))
        yieldTable = cPickle.load(open(r'objects\yieldTable.pkl'))
        AIDB = cPickle.load(open(r'objects\AIDB.pkl'))
    except:
        print "Failed to load objects."
        raise

if __name__=="__main__":

    load_inputs()

    ### Initialize function classes
    PP = preprocess_tools.progressprinter.ProgressPrinter()
    fishnet = gridGeneration.create_grid.Fishnet(inventory, resolution, PP)
    inventoryGridder = gridGeneration.grid_inventory.GridInventory(inventory, future_dist_input_dir, PP)
    mergeDist = rollback.merge_disturbances.MergeDisturbances(inventory, [historicFire1, historicFire2, historicHarvest], PP)
    intersect = rollback.intersect_disturbances_inventory.IntersectDisturbancesInventory(inventory, spatialBoundaries, rollback_range, PP)
    calcDistDEdiff = rollback.update_inventory.CalculateDistDEdifference(inventory, PP)
    calcNewDistYr = rollback.update_inventory.CalculateNewDistYr(inventory, rollback_range, historicHarvest.getYearField(), PP)
    updateInv = rollback.update_inventory.updateInvRollback(inventory, inventory_raster_out, rollbackDisturbances, resolution, PP)
    tiler = tiler.tiler.Tiler(
        spatialBoundaries=spatialBoundaries,
        inventory=inventory,
        historicFire=None,
        historicHarvest=None,
        rollbackDisturbances=rollbackDisturbances,
        projectedDisturbances=None,
        NAmat=NAmat,
        rollback_range=rollback_range, historic_range=historic_range, future_range=future_range,
        resolution=resolution, ProgressPrinter=PP
    )
    r2GCBM = recliner2GCBM.recliner2GCBM.Recliner2GCBM(config_dir=recliner2gcbm_config_dir,
        output_path=recliner2gcbm_output_path,transitionRules=transitionRules,yieldTable=yieldTable,aidb=AIDB,ProgressPrinter=PP)
    gcbmConfigurer = GCBMconfig.configure_gcbm.ConfigureGCBM(output_dir=gcbm_raw_output_dir, gcbm_configs_dir=gcbm_configs_dir,
        GCBM_scenarios=GCBM_scenarios, inventory=inventory, reportingIndicators=reportingIndicators, resolution=resolution,
        rollback_range=rollback_range,future_range=future_range,ProgressPrinter=PP)

    ### Execute Functions
    # -- Grid generation
    # fishnet.createFishnet()
    # -- Grid inventory
    # inventoryGridder.gridInventory()
    # if not rollback_enabled:
    #     inventoryGridder.exportInventory(inventory_raster_out, resolution)
    # else:
        # -- Start of rollback
        # mergeDist.runMergeDisturbances()
        # intersect.runIntersectDisturbancesInventory()
        # calcDistDEdiff.calculateDistDEdifference()
        # calcNewDistYr.calculateNewDistYr()
    updateInv.updateInvRollback()
        # -- End of rollback
    # -- Upload to S3
    # s3.upload()
# ------------------------------------------------------------------------------
    # -- Run Tiler
    tiler.defineBoundingBox(tiler_output_dir)
    general_lyrs = tiler.processGeneralLayers()
    tiler.processRollbackDisturbances()
    tiler.processHistoricFireDisturbances(historicFire1)
    tiler.processHistoricFireDisturbances(historicFire2)
    tiler.processHistoricHarvestDisturbances(historicHarvest)
    tiler.processHistoricInsectDisturbances(historicMPB)
    tiler.processProjectedDisturbances(projectedDistBase)
    transitionRules = tiler.runTiler(tiler_output_dir, 'TEST', True)
    # -- Prep and run recliner2GCBM
    r2GCBM.prepTransitionRules(transitionRules)
    r2GCBM.prepYieldTable(yieldTable)
    r2GCBM.runRecliner2GCBM()
    # -- Configure GCBM
    gcbmConfigurer.configureGCBM(recliner2gcbm_output_path, general_lyrs, tiler_output_dir)
    # -- Run GCBM
    # gcbm.runGCBM()
    # -- Run CompileGCBM
    # GCBMcompiler.compileGCBM()
    # -- Run CBM Rollup
    # CBMRollup.runCBMRollup()
    # -- Download from S3
