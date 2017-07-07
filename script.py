### GCBM Preprocessing

## Imports
import archook
archook.get_arcpy()
import preprocess_tools
gridGeneration = __import__("01_grid_generation")
rollback = __import__("02_rollback")
recliner2GCBM = __import__("04_recliner2GCBM")

if __name__=="__main__":
    ## Variables
    res = 100
    tiles = 16
    disturbances = [r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\02_harvest",  r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\01_fire\shapefiles"]
    rollbackInvOut = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\02_inventory"
    rollbackDistOut = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\03_rollbackDisturbances\rollbackDist.shp"
    recliner2gcbm_config_dir = r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\config"
    recliner2gcbm_output_path = r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\gcbm.db"

    ## Initialize inputs
    inventory = preprocess_tools.inventory.Inventory("G:\\Nick\\GCBM\\05_Test_Automation\\05_working\\02_layers\\01_external_spatial_data\\00_Workspace.gdb",
        "tsaTEST", "Age2011", 2011)

    transitionRules = preprocess_tools.inputs.TransitionRules(path=r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\transition_rules.csv",
        classifier_cols={"AU":None, "LDSPP":None}, header=True, cols={"NameCol":0, "AgeCol":2, "DelayCol":1})

    yieldTable = preprocess_tools.inputs.YieldTable(path=r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\yield.csv",
        classifier_cols={"AU":0, "LDSPP":1}, header=True, interval=10, cols={"SpeciesCol":2,"IncrementRange":[3,38]})

    AIDB = preprocess_tools.inputs.AIDB(path=r"G:\Nick\GCBM\05_Test_Automation\05_working\00_AIDB\ArchiveIndex_Beta_Install_BASE.mdb")

    ## Initialize function classes
    PP = preprocess_tools.progressprinter.ProgressPrinter()
    fish1ha = gridGeneration.create_grid.Fishnet(inventory, res, PP)
    tileId = gridGeneration.create_grid.TileID(inventory.workspace, tiles, PP)
    inventoryGridder = gridGeneration.grid_inventory.GridInventory(inventory, PP)
    merge_dist = rollback.merge_disturbances.MergeDisturbances(inventory.workspace, disturbances, PP)
    intersect = rollback.intersect_disturbances_inventory.IntersectDisturbancesInventory(inventory, PP)
    calcDistDEdiff = rollback.update_inventory.CalculateDistDEdifference(inventory, PP)
    calcNewDistYr = rollback.update_inventory.CalculateNewDistYr(inventory, PP)
    updateInv = rollback.update_inventory.updateInvRollback(inventory, rollbackInvOut, rollbackDistOut, PP)
    r2GCBM = recliner2GCBM.recliner2GCBM.Recliner2GCBM(config_dir=recliner2gcbm_config_dir,
        output_path=recliner2gcbm_output_path,transitionRules=transitionRules,yieldTable=yieldTable,aidb=AIDB,ProgressPrinter=PP)


    ## Execute Functions
    print "Start Script"
    # -- Grid generation
    fish1ha.createFishnet()
    tileId.runTileID()
    # -- Grid inventory
    inventoryGridder.gridInventory()
    # -- Start of rollback
    # merge_dist.runMergeDisturbances()
    intersect.runIntersectDisturbancesInventory()
    calcDistDEdiff.calculateDistDEdifference()
    calcNewDistYr.calculateNewDistYr()
    updateInv.updateInvRollback()
    # -- End of rollback
    # -- Prep Tiler

    # -- Upload to S3

    # -- Run Tiler

    # -- Prep and run recliner2GCBM
    # transitionRules = r2GCBM.prepTransitionRules(transitionRules)
    # r2GCBM.prepYieldTable(yieldTable)
    # r2GCBM.runRecliner2GCBM()
    # -- Configure GCBM

    # -- Run GCBM

    # -- Run CompileGCBM

    # -- Run CBM Rollup

    # -- Download from S3
