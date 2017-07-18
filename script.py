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

if __name__=="__main__":

    ### Data Prep
    # inpout = [
    #     ()
    # ]
    # for input, output in [()
    # print "Clipping...",
    # arcpy.Clip_analysis(r'G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\02_harvest\BC_cutblocks90_15.shp',
    #     r'G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\00_Workspace.gdb\inventory_gridded',
    #     r'G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\02_harvest\clipped\harvest_clipped.shp', "")
    # print "Done"

    ### Variables
    # Tile resolution in degrees
    resolution = 0.001
    # Deprecated ?
    tiles = 1

    rollback_enabled = True

    ## Inventory
    # Path the the inventory gdb workspace
    inventory_path = "G:\\Nick\\GCBM\\05_Test_Automation\\05_working\\02_layers\\01_external_spatial_data\\00_Workspace.gdb"
    # Layer name of the inventory in the gdb
    inventory_layer = "tsaTEST"
    # The age field name in the inventory layer
    inventory_age_field = "Age2011"
    # The starting year of the inventory
    inventory_year = 2011
    # A dictionary with the classifiers as keys and the associated field names (as
    # they appear in the inventory) as values.
    inv_classifier_attr = {
        "LdSpp": "LeadSpp",
        "AU": "AU"
    }
    # Reproject the inventory into WGS 1984
    reproject_inventory = True

    ## Disturbances
    NFDB_workspace = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\01_fire\shapefiles"
    NFDB_filter = "NFDB*.shp"
    NFDB_year_field = "YEAR_"
    NBAC_workspace = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\01_fire\shapefiles"
    NBAC_filter = "NBAC*.shp"
    NBAC_year_field = "EDATE"
    harvest_workspace = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\02_harvest\clipped"
    harvest_filter = "harvest_clipped.shp"
    harvest_year_field = "HARV_YR"
    MPB_workspace = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\03_MPB\BCMPB\shapefiles"
    MPB_filter = "mpb*.shp"

    projScenBase_workspace = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\02_future\projDist_BASE"
    projScenBase_filter = "TS_*.shp"
    projScenBase_lookuptable = {
        11: "Base CC",
        7: "Wild Fires",
        13: "SlashBurning",
        10: "Partial Cut",
        6: "Base Salvage",
        2: "Wild Fire",
        1: "Clearcut harvesting with salvage"
    }

    historic_range = [1990,2014]
    rollback_range = [1990,2010]
    future_range = [2010,2050]
    activity_start_year = 2018

    rollbackInvOut = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\02_inventory"
    rollbackDistOut = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\03_rollbackDisturbances\rollbackDist.shp"
    recliner2gcbm_config_dir = r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\config"
    recliner2gcbm_output_path = r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\gcbm.db"

    spatial_reference = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\01_spatial_reference"
    spatial_boundaries_tsa = os.path.join(spatial_reference, "TSA_boundaries_2016.shp")
    spatial_boundaries_pspu = os.path.join(spatial_reference, "PSPUS_2016.shp")
    study_area_filter = {
        "field": "TSA_NUMBER",
        "code": "'Cranbrook TSA'"
    }
    spatial_boundaries_attr = {
        "Admin": "AdminBou_1",
        "Eco": "EcoBound_1"
    }

    NAmat_path = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\04_environment\NAmerica_MAT_1971_2000.tif"

    tiler_output_dir = r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\02_GCBM_tiled_input\SCEN_TEST"

    tilerScenarios = ['Base', 'B', 'C']
    GCBMScenarios = {'Base':'Base', 'A':'Base', 'B':'B', 'C':'C', 'D':'C'}

    ### Initialize inputs
    inventory = preprocess_tools.inputs.Inventory(path=inventory_path, layer=inventory_layer,
        age_field=inventory_age_field, year=inventory_year, classifiers_attr=inv_classifier_attr)
    if reproject_inventory == True:
        inventory.reproject("inv_reprojected")

    historicFire1 = preprocess_tools.inputs.HistoricDisturbance(NFDB_workspace, NFDB_filter, NFDB_year_field)
    historicFire2 = preprocess_tools.inputs.HistoricDisturbance(NBAC_workspace, NBAC_filter, NBAC_year_field)
    historicHarvest = preprocess_tools.inputs.HistoricDisturbance(harvest_workspace, harvest_filter, harvest_year_field)
    historicMPB = preprocess_tools.inputs.HistoricDisturbance(MPB_workspace, MPB_filter, None)
    # historicDisturbances = [historicFire1, historicFire2, historicHarvest, historicMPB]
    # standReplHistoricDisturbances = [historicFire1, historicFire2, historicHarvest]

    projectedDistBase = preprocess_tools.inputs.ProjectedDisturbance(projScenBase_workspace, projScenBase_filter, "Base", projScenBase_lookuptable)
    projectedDisturbances = []

    # historicHarvest = preprocess_tools.disturbance_manager.DisturbanceParser(
    #     path=r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\02_harvest\BC_cutblocks90_15.shp",
    #     multiple=False,type="shp",year_disp=0,year_attribute="HARV_YR",year_range=historic_range,extract_yr_re=None,
    #     filter_attribute="tsa_num",filter_code="05",dist_type="Clearcut harvesting with salvage", name="historicharvest", standReplacing=True
    # )
    # histHarvColl = historicHarvest.createDisturbanceCollection(r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\05_disturbance_collections\harvest.gdb")
    #
    #
    # historicFire = preprocess_tools.disturbance_manager.DisturbanceParser(
    #     path=r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\01_fire\shapefiles",
    #     multiple=True,type="shp",year_disp=0,year_range=historic_range,extract_yr_re=r"([0-9]+)\.shp$",
    #     filter_attribute=None,filter_code=None,dist_type="Wildfires", name="historicfire", standReplacing=True
    # )
    # histFireColl = historicFire.createDisturbanceCollection(r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\05_disturbance_collections\fire.gdb")


    spatialBoundaries = preprocess_tools.inputs.SpatialBoundaries(spatial_boundaries_tsa, spatial_boundaries_pspu,
        "shp", study_area_filter, spatial_boundaries_attr)

    NAmat = preprocess_tools.inputs.NAmericaMAT(NAmat_path)

    rollbackDisturbances = preprocess_tools.inputs.RollbackDisturbances(rollbackDistOut)

    transitionRules = preprocess_tools.inputs.TransitionRules(path=r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\transition_rules.csv",
        classifier_cols={"AU":None, "LDSPP":None}, header=True, cols={"NameCol":0, "AgeCol":2, "DelayCol":1})

    yieldTable = preprocess_tools.inputs.YieldTable(path=r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\yield.csv",
        classifier_cols={"AU":0, "LDSPP":1}, header=True, interval=10, cols={"SpeciesCol":2,"IncrementRange":[3,38]})

    AIDB = preprocess_tools.inputs.AIDB(path=r"G:\Nick\GCBM\05_Test_Automation\05_working\00_AIDB\ArchiveIndex_Beta_Install_BASE.mdb")

    inputs = {
        "inventory":inventory,
        # "histHarvColl":histHarvColl,
        # "histFireColl":histFireColl,
        "rollbackDisturbances":rollbackDisturbances,
        "spatialBoundaries":spatialBoundaries,
        "NAmat":NAmat,
        "transitionRules":transitionRules,
        "yieldTable":yieldTable,
        "AIDB":AIDB
    }
    ### Load previous configuration
    # for file in os.listdir("objects"):
    #     inp = os.path.basename(file).split(".")[0]
    #     if inp in inputs:
    #         with open(os.path.join("objects", file)) as obj:
    #           inputs[inp] = cPickle.load(obj)

    ### Initialize function classes
    PP = preprocess_tools.progressprinter.ProgressPrinter()
    fish1ha = gridGeneration.create_grid.Fishnet(inventory, resolution, PP)
    tileId = gridGeneration.create_grid.TileID(inventory.workspace, tiles, PP)
    inventoryGridder = gridGeneration.grid_inventory.GridInventory(inventory, PP)
    mergeDist = rollback.merge_disturbances.MergeDisturbances(inventory.workspace, [historicFire1, historicFire2, historicHarvest], PP)
    intersect = rollback.intersect_disturbances_inventory.IntersectDisturbancesInventory(inventory, spatialBoundaries, PP)
    calcDistDEdiff = rollback.update_inventory.CalculateDistDEdifference(inventory, PP)
    calcNewDistYr = rollback.update_inventory.CalculateNewDistYr(inventory, PP)
    updateInv = rollback.update_inventory.updateInvRollback(inventory, rollbackInvOut, rollbackDistOut, PP)
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


    ### Execute Functions
    try:
        # -- Grid generation
        # fish1ha.createFishnet()
        # tileId.runTileID()
        # -- Grid inventory
        # inventoryGridder.gridInventory()
        # -- Clip all inputs to inventory bbox
        # clipper.Clip(spatial_inputs)
        # -- Start of rollback
        # mergeDist.runMergeDisturbances()
        # intersect.runIntersectDisturbancesInventory()
        # calcDistDEdiff.calculateDistDEdifference()
        # calcNewDistYr.calculateNewDistYr()
        updateInv.updateInvRollback()
        # -- End of rollback
        # -- Prep Tiler
        # tiler.prepTiler()
        # -- Upload to S3
        # s3.upload()
    # ------------------------------------------------------------------------------
        # -- Run Tiler
        tiler.defineBoundingBox(tiler_output_dir)
        tiler.processGeneralLayers()
        # tiler.processRollbackDisturbances()
        # tiler.processHistoricFireDisturbances(historicFire1)
        # tiler.processHistoricFireDisturbances(historicFire2)
        tiler.processHistoricHarvestDisturbances(historicHarvest)
        # tiler.processHistoricMPBDisturbances(historicMPB)
        # tiler.processProjectedDisturbances(projectedDistBase)
        tiler.runTiler(tiler_output_dir)
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
    except:
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        if not os.path.exists('objects'):
            os.mkdir('objects')
        for inp in inputs:
            with open(r'objects\{}.pkl'.format(inp), 'wb') as out:
                cPickle.dump(inp, out)
        raise

def save_objects():
    try:
        if not os.path.exists('objects'):
            os.mkdir('objects')
        cPickle.dump(inventory, open(r'objects\inventory.pkl'))
        cPickle.dump(rollbackDisturbances, open(r'objects\rollbackDisturbances.pkl'))
        cPickle.dump(historicFire1, open(r'objects\historicFire1.pkl'))
        cPickle.dump(historicFire2, open(r'objects\historicFire2.pkl'))
        cPickle.dump(historicHarvest, open(r'objects\historicHarvest.pkl'))
        cPickle.dump(historicMPB, open(r'objects\historicMPB.pkl'))
        cPickle.dump(projectedDistBase, open(r'objects\projectedDistBase.pkl'))
    except:
        print "Failed to save objects."
        raise

def load_objects():
    try:
        inventory = cPickle.load(open(r'objects\inventory.pkl'))
        rollbackDisturbances = cPickle.load(open(r'objects\rollbackDisturbances.pkl'))
        historicFire1 = cPickle.load(open(r'objects\historicFire1.pkl'))
        historicFire2 = cPickle.load(open(r'objects\historicFire2.pkl'))
        historicHarvest = cPickle.load(open(r'objects\historicHarvest.pkl'))
        historicMPB = cPickle.load(open(r'objects\historicMPB.pkl'))
        projectedDistBase = cPickle.load(open(r'objects\projectedDistBase.pkl'))
    except:
        print "Failed to load objects."
        raise
