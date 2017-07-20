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

def save_objects():
    try:
        if not os.path.exists('objects'):
            os.mkdir('objects')
        cPickle.dump(inventory, open(r'objects\inventory.pkl', 'wb'))
        cPickle.dump(rollbackDisturbances, open(r'objects\rollbackDisturbances.pkl', 'wb'))
        cPickle.dump(historicFire1, open(r'objects\historicFire1.pkl', 'wb'))
        cPickle.dump(historicFire2, open(r'objects\historicFire2.pkl', 'wb'))
        cPickle.dump(historicHarvest, open(r'objects\historicHarvest.pkl', 'wb'))
        cPickle.dump(historicMPB, open(r'objects\historicMPB.pkl', 'wb'))
        cPickle.dump(projectedDistBase, open(r'objects\projectedDistBase.pkl', 'wb'))
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


###############################################################################
#                            Required Inputs (BC)
#                                                     []: Restricting qualities
# Inventory [layer in a geodatabase]
# Historic Fire Disturbances (NFDB, NBAC) [shapefiles where year is the last 4
#    characters before file extention]
# Historic Harvest Disturbances (BC Cutblocks) [shapefile]
# Historic MPB Disturbances [shapefiles where year is the last 4 characters
#    before file extention]
# Projected Disturbances [shapefiles]
# Spatial Boundaries (TSA and PSPU) [shapefiles]
# NAmerica MAT (Mean Annual Temperature) [tiff]
# Yield Table (Growth Curves) [AIDB species matching column, classifier columns]
# AIDB [pre-setup with disturbance matrix values etc.]
###############################################################################

if __name__=="__main__":
    ### Variables
    # directory path to the working directory for relative paths
    working_directory = r'G:\Nick\GCBM\05_Test_Automation\05_working'
    # Tile resolution in degrees
    resolution = 0.001
    # Deprecated ?
    tiles = 1

    # Set true to enable rollback
    rollback_enabled = True

    ## Inventory
    # Path the the inventory gdb workspace
    inventory_workspace = r"{}\02_layers\01_external_spatial_data\00_Workspace.gdb".format(working_directory)
    # Layer name of the inventory in the gdb
    inventory_layer = "inv_reprojected"
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
    reproject_inventory = False

    ## Disturbances
    # directory or geodatabase
    NFDB_workspace = r"{}\02_layers\01_external_spatial_data\03_disturbances\01_historic\01_fire\shapefiles".format(working_directory)
    # filter to get all layers within the directory/geodatabase following glob syntax
    NFDB_filter = "NFDB*.shp"
    # the field from which the year can be extracted
    NFDB_year_field = "YEAR_"
    NBAC_workspace = r"{}\02_layers\01_external_spatial_data\03_disturbances\01_historic\01_fire\shapefiles".format(working_directory)
    NBAC_filter = "NBAC*.shp"
    NBAC_year_field = "EDATE"
    harvest_workspace = r"{}\02_layers\01_external_spatial_data\03_disturbances\01_historic\02_harvest\clipped".format(working_directory)
    harvest_filter = "harvest_clipped.shp"
    harvest_year_field = "HARV_YR"
    MPB_workspace = r"{}\02_layers\01_external_spatial_data\03_disturbances\01_historic\03_MPB\BCMPB\shapefiles".format(working_directory)
    MPB_filter = "mpb*.shp"

    projScenBase_workspace = r"{}\02_layers\01_external_spatial_data\03_disturbances\02_future\projDist_BASE".format(working_directory)
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

    ## Year ranges
    historic_range = [1990,2014]
    rollback_range = [1990,2010]
    future_range = [2010,2050]
    activity_start_year = 2018

    # directory path to the spatial reference directory containing the TSA and PSPU boundaries
    spatial_reference = r"{}\02_layers\01_external_spatial_data\01_spatial_reference".format(working_directory)
    # file name or filter to find the TSA boundaries in the spatial reference directory
    spatial_boundaries_tsa = "TSA_boundaries_2016.shp"
    # file name or filter to find the PSPU boundaries in the spatial reference directory
    spatial_boundaries_pspu = "PSPUS_2016.shp"
    # filter used to get the desired study area. change only the values for "field" and "code"
    study_area_filter = {
        "field": "TSA_NUMBER",
        "code": "'Cranbrook TSA'"
    }
    # field names for the Admin and Eco attributes in the PSPU boundaries file
    spatial_boundaries_attr = {
        "Admin": "AdminBou_1",
        "Eco": "EcoBound_1"
    }

    # path to NAmerica MAT (Mean Annual Temperature)
    NAmat_path = r"{}\02_layers\01_external_spatial_data\04_environment\NAmerica_MAT_1971_2000.tif".format(working_directory)

    # Different scenarios to be ran by the tiler (before Disturbance Matrix distinctions)
    tilerScenarios = ['Base']
    # GCBM scenarios (after Disturbance Matrix distinctions) with the associated tiler scenario as the key
    GCBMScenarios = {'Base':'Base'}

    ## Rollback disturbances
    rollbackInvOut = r"{}\02_layers\01_external_spatial_data\02_inventory".format(working_directory)
    rollbackDistOut = r"{}\02_layers\01_external_spatial_data\03_disturbances\03_rollbackDisturbances\rollbackDist.shp".format(working_directory)
    recliner2gcbm_config_dir = r"G:\Nick\GCBM\05_Test_Automation\05_working\01_configs\Recliner2GCBM"
    recliner2gcbm_output_path = r"G:\Nick\GCBM\05_Test_Automation\05_working\01_configs\GCBMinput.db"

    # directory where the tiler will output to
    tiler_output_dir = r"{}\02_layers\02_GCBM_tiled_input\SCEN_TEST".format(working_directory)

    ## Yield table
    # path to the yield table (recommened to be in the recliner2gcbm config directory)
    yieldTable_path = r"{}\yield.csv".format(recliner2gcbm_config_dir)
    # The classifiers as keys and the column as value
    yieldTable_classifier_cols = {"AU":0, "LDSPP":1}
    # True if the first row of the yield table is a header
    yieldTable_header = True
    # year interval between age increments
    yieldTable_interval = 10
    # species column and increment range
    yieldTable_cols = {"SpeciesCol":2,"IncrementRange":[3,38]}







# ----------------------------------------------------------------------------------------------------

    ### Initialize inputs
    inventory = preprocess_tools.inputs.Inventory(workspace=inventory_workspace, filter=inventory_layer,
        year=inventory_year, classifiers_attr=inv_classifier_attr)
    if reproject_inventory == True:
        inventory.reproject("inv_reprojected")

    historicFire1 = preprocess_tools.inputs.HistoricDisturbance(NFDB_workspace, NFDB_filter, NFDB_year_field)
    historicFire2 = preprocess_tools.inputs.HistoricDisturbance(NBAC_workspace, NBAC_filter, NBAC_year_field)
    historicHarvest = preprocess_tools.inputs.HistoricDisturbance(harvest_workspace, harvest_filter, harvest_year_field)
    historicMPB = preprocess_tools.inputs.HistoricDisturbance(MPB_workspace, MPB_filter, None)

    projectedDistBase = preprocess_tools.inputs.ProjectedDisturbance(projScenBase_workspace, projScenBase_filter, "Base", projScenBase_lookuptable)
    projectedDisturbances = []

    # historicHarvest = preprocess_tools.disturbance_manager.DisturbanceParser(
    #     path=r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\02_harvest\BC_cutblocks90_15.shp",
    #     multiple=False,type="shp",year_disp=0,year_attribute="HARV_YR",year_range=historic_range,extract_yr_re=None,
    #     filter_attribute="tsa_num",filter_code="05",dist_type="Clearcut harvesting with salvage", name="historicharvest", standReplacing=True
    # )
    # histHarvColl = historicHarvest.createDisturbanceCollection(r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\05_disturbance_collections\harvest.gdb")
    #
    # historicFire = preprocess_tools.disturbance_manager.DisturbanceParser(
    #     path=r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\03_disturbances\01_historic\01_fire\shapefiles",
    #     multiple=True,type="shp",year_disp=0,year_range=historic_range,extract_yr_re=r"([0-9]+)\.shp$",
    #     filter_attribute=None,filter_code=None,dist_type="Wildfires", name="historicfire", standReplacing=True
    # )
    # histFireColl = historicFire.createDisturbanceCollection(r"G:\Nick\GCBM\05_Test_Automation\05_working\02_layers\01_external_spatial_data\05_disturbance_collections\fire.gdb")


    spatialBoundaries = preprocess_tools.inputs.SpatialBoundaries(spatial_reference, spatial_boundaries_tsa, spatial_boundaries_pspu,
        "shp", study_area_filter, spatial_boundaries_attr)

    NAmat = preprocess_tools.inputs.NAmericaMAT(os.path.dirname(NAmat_path), os.path.basename(NAmat_path))

    rollbackDisturbances = preprocess_tools.inputs.RollbackDisturbances(rollbackDistOut)

    # transitionRules = preprocess_tools.inputs.TransitionRules(path=r"G:\Nick\GCBM\05_Test_Automation\03_tools\00_PreprocessingScript\transition_rules.csv",
    #     classifier_cols={"AU":None, "LDSPP":None}, header=True, cols={"NameCol":0, "AgeCol":2, "DelayCol":1})
    transitionRules = None

    yieldTable = preprocess_tools.inputs.YieldTable(path=yieldTable_path, classifier_cols=yieldTable_classifier_cols,
        header=yieldTable_header, interval=yieldTable_interval, cols=yieldTable_cols)

    AIDB = preprocess_tools.inputs.AIDB(path=r"{}\00_AIDB\ArchiveIndex_Beta_Install_BASE.mdb".format(working_directory))

    ### Initialize function classes
    PP = preprocess_tools.progressprinter.ProgressPrinter()
    fish1ha = gridGeneration.create_grid.Fishnet(inventory, resolution, PP)
    tileId = gridGeneration.create_grid.TileID(inventory.getWorkspace(), tiles, PP)
    inventoryGridder = gridGeneration.grid_inventory.GridInventory(inventory, PP)
    mergeDist = rollback.merge_disturbances.MergeDisturbances(inventory.getWorkspace(), [historicFire1, historicFire2, historicHarvest], PP)
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
    tiler.defineBoundingBox(tiler_output_dir)
    tiler.processGeneralLayers()
    tiler.processRollbackDisturbances()
    tiler.processHistoricFireDisturbances(historicFire1)
    tiler.processHistoricFireDisturbances(historicFire2)
    tiler.processHistoricHarvestDisturbances(historicHarvest)
    # tiler.processHistoricMPBDisturbances(historicMPB)
    tiler.processProjectedDisturbances(projectedDistBase)
    transitionRules = tiler.runTiler(tiler_output_dir)
    # -- Prep and run recliner2GCBM
    r2GCBM.prepTransitionRules(transitionRules)
    r2GCBM.prepYieldTable(yieldTable)
    r2GCBM.runRecliner2GCBM()
    # -- Configure GCBM
    # gcbmConfigurer.configureGCBM()
    # -- Run GCBM
    # gcbm.runGCBM()
    # -- Run CompileGCBM
    # GCBMcompiler.compileGCBM()
    # -- Run CBM Rollup
    # CBMRollup.runCBMRollup()
    # -- Download from S3
