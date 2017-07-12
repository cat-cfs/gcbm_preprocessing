### GCBM Preprocessing

## Imports
import archook
archook.get_arcpy()
import preprocess_tools
gridGeneration = __import__("01_grid_generation")
rollback = __import__("02_rollback")
tiler = __import__("03_tiler")
recliner2GCBM = __import__("04_recliner2GCBM")

if __name__=="__main__":
    ### Variables
    res = 100
    tiles = 16

    ## Inventory
    inventory_path = "G:\\Nick\\GCBM\\05_Test_Automation\\05_working\\02_layers\\01_external_spatial_data\\00_Workspace.gdb"
    inventory_layer = "tsaTEST"
    inventory_age_field = "Age2011"
    inventory_age = 2011
    # A dictionary with the classifiers as keys and the associated field names as
    # they appear in the inventory as values.
    inv_classifier_attr = {
        "LdSpp": "LeadSpp",
        "AU": "AU"
    }

    disturbances = [r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\02_harvest",  r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\01_fire\shapefiles"]
    rollbackInvOut = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\02_inventory"
    rollbackDistOut = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\03_rollbackDisturbances\rollbackDist.shp"
    recliner2gcbm_config_dir = r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\config"
    recliner2gcbm_output_path = r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\gcbm.db"

    ### Initialize inputs
    inventory = preprocess_tools.inputs.Inventory(path=inventory_path, layer=inventory_layer,
        age_field=inventory_age_field, age=iventory_age, classifiers_attr=inv_classifier_attr)

    transitionRules = preprocess_tools.inputs.TransitionRules(path=r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\transition_rules.csv",
        classifier_cols={"AU":None, "LDSPP":None}, header=True, cols={"NameCol":0, "AgeCol":2, "DelayCol":1})

    yieldTable = preprocess_tools.inputs.YieldTable(path=r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\yield.csv",
        classifier_cols={"AU":0, "LDSPP":1}, header=True, interval=10, cols={"SpeciesCol":2,"IncrementRange":[3,38]})

    AIDB = preprocess_tools.inputs.AIDB(path=r"G:\Nick\GCBM\05_Test_Automation\05_working\00_AIDB\ArchiveIndex_Beta_Install_BASE.mdb")

    ### Initialize function classes
    PP = preprocess_tools.progressprinter.ProgressPrinter()
    fish1ha = gridGeneration.create_grid.Fishnet(inventory, res, PP)
    tileId = gridGeneration.create_grid.TileID(inventory.workspace, tiles, PP)
    inventoryGridder = gridGeneration.grid_inventory.GridInventory(inventory, PP)
    mergeDist = rollback.merge_disturbances.MergeDisturbances(inventory.workspace, disturbances, PP)
    intersect = rollback.intersect_disturbances_inventory.IntersectDisturbancesInventory(inventory, PP)
    calcDistDEdiff = rollback.update_inventory.CalculateDistDEdifference(inventory, PP)
    calcNewDistYr = rollback.update_inventory.CalculateNewDistYr(inventory, PP)
    updateInv = rollback.update_inventory.updateInvRollback(inventory, rollbackInvOut, rollbackDistOut, PP)
    r2GCBM = recliner2GCBM.recliner2GCBM.Recliner2GCBM(config_dir=recliner2gcbm_config_dir,
        output_path=recliner2gcbm_output_path,transitionRules=transitionRules,yieldTable=yieldTable,aidb=AIDB,ProgressPrinter=PP)


    ### Execute Functions

    # -- Grid generation
    fish1ha.createFishnet()
    tileId.runTileID()
    # -- Grid inventory
    inventoryGridder.gridInventory()
    # -- Start of rollback
    mergeDist.runMergeDisturbances()
    intersect.runIntersectDisturbancesInventory()
    calcDistDEdiff.calculateDistDEdifference()
    calcNewDistYr.calculateNewDistYr()
    updateInv.updateInvRollback()
    # -- End of rollback
    # -- Prep Tiler
    # tiler.prepTiler()
    # -- Upload to S3
    # s3.upload()
# ------------------------------------------------------------------------------
    # -- Run Tiler
    # tiler.runTiler()
    # -- Prep and run recliner2GCBM
    # transitionRules = r2GCBM.prepTransitionRules(transitionRules)
    # r2GCBM.prepYieldTable(yieldTable)
    # r2GCBM.runRecliner2GCBM()
    # -- Configure GCBM
    # gcbmConfigurer.configureGCBM()
    # -- Run GCBM
    # gcbm.runGCBM()
    # -- Run CompileGCBM
    # GCBMcompiler.compileGCBM()
    # -- Run CBM Rollup
    # CBMRollup.runCBMRollup()
    # -- Download from S3
