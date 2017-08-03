### GCBM Preprocessing

## Imports
import archook
archook.get_arcpy()
import arcpy
import os
import preprocess_tools
import cPickle
import shutil

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


###############################################################################
#                            Required Inputs (BC)
#                                                     []: Restricting qualities
# Inventory [feature layer in geodatabase]
# Historic Fire Disturbances (NFDB, NBAC) [shapefiles where year is the last 4
#    characters before file extention]
# Historic Harvest Disturbances (BC Cutblocks) [shapefile]
# Historic MPB Disturbances [shapefiles where year is the last 4 characters
#    before file extention]
# Projected Disturbances [shapefiles]
# Spatial Boundaries (TSA and PSPU) [shapefiles]
# NAmerica MAT (Mean Annual Temperature) [tiff]
# Yield Table (Growth Curves) [AIDB species matching column, classifier columns,
#    csv format]
# AIDB [pre-setup with disturbance matrix values etc.]
###############################################################################


if __name__=="__main__":
    #### Variables
    # directory path to the working directory for relative paths
    working_directory = r'G:\Nick\GCBM\05_Test_Automation\05_working_new\TSA_05'
    # directory path to the external data directory for relative paths
    external_data = r'G:\Nick\BC_ON_1ha\05_working_BC\00_external_data'
    # TSA number as a string
    TSA = '05'
    # Tile resolution in degrees
    resolution = 0.001

    # Set true to enable rollback
    rollback_enabled = True

    ## Year ranges
    historic_range = [1990,2014]
    rollback_range = [1990,2010]
    future_range = [2010,2050]
    activity_start_year = 2018


    #### Spatial Inputs

    ## Inventory
    # Path the the inventory gdb workspace
    inventory_workspace = r"{}\01_spatial\02_inventory\Processed.gdb".format(external_data)
    # Layer name of the inventory in the gdb
    inventory_layer = "inv_reprojected"
    # The age field name in the inventory layer
    inventory_age_field = "Age2015"
    # The starting year of the inventory
    inventory_year = 2015
    # A dictionary with the classifiers as keys and the associated field names (as
    # they appear in the inventory) as values.
    inventory_classifier_attr = {
        "LdSpp": "LdSpp",
        "AU": "AU"
    }
    inventory_field_names = {
        "age": "Age2015",
        "species": "LdSpp"
    }

    ## Disturbances
    # directory or geodatabase
    NFDB_workspace = r"{}\01_spatial\03_disturbances\01_historic\01_fire\shapefiles".format(external_data)
    # filter to get all layers within the directory/geodatabase, following glob syntax
    NFDB_filter = "NFDB*.shp"
    # the field from which the year can be extracted
    NFDB_year_field = "YEAR_"
    NBAC_workspace = r"{}\01_spatial\03_disturbances\01_historic\01_fire\shapefiles".format(external_data)
    NBAC_filter = "NBAC*.shp"
    NBAC_year_field = "EDATE"
    harvest_workspace = r"{}\01_spatial\03_disturbances\01_historic\02_harvest".format(external_data)
    harvest_filter = "BC_cutblocks90_15.shp"
    harvest_year_field = "HARV_YR"
    MPB_workspace = r"{}\01_spatial\03_disturbances\01_historic\03_insect".format(external_data)
    MPB_filter = "mpb*.shp"

    projScenBase_workspace = r"{}\01_spatial\03_disturbances\02_future\projDist_BASE".format(external_data)
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

    # directory path to the spatial reference directory containing the TSA and PSPU boundaries
    spatial_reference = r"{}\01_spatial\01_spatial_reference".format(external_data)
    # file name or filter to find the TSA boundaries in the spatial reference directory
    spatial_boundaries_tsa = "TSA_boundaries_2016.shp"
    # file name or filter to find the PSPU boundaries in the spatial reference directory
    spatial_boundaries_pspu = "PSPUS_2016.shp"
    # filter used to get the desired study area from the TSA boundaries.
    # change only the associated values for "field" and "code"
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
    NAmat_path = r"{}\01_spatial\04_environment\NAmerica_MAT_1971_2000.tif".format(external_data)

    ## Rollback Output
    # rolled back inventory output directory
    inventory_raster_out = r"{}\01a_pretiled_layers\02_inventory".format(working_directory)
    # rollback disturbances output file
    rollback_dist_out = r"{}\01a_pretiled_layers\03_disturbances\03_rollback\rollbackDist.shp".format(working_directory)
    # future disturbances input directory for woodstock
    future_dist_input_dir = r'{}\01a_pretiled_layers\03_disturbances\02_future\inputs'.format(working_directory)

    reprojected_redirection = ('01_spatial', '03_spatial_reprojected')
    clipped_redirection = (r'00_external_data\01_spatial', r'TSA_{}\01a_pretiled_layers'.format(TSA))

    ### Initialize Spatial Inputs
    inventory = preprocess_tools.inputs.Inventory(workspace=inventory_workspace, filter=inventory_layer,
        year=inventory_year, classifiers_attr=inventory_classifier_attr, field_names=inventory_field_names)
    historicFire1 = preprocess_tools.inputs.HistoricDisturbance(NFDB_workspace, NFDB_filter, NFDB_year_field)
    historicFire2 = preprocess_tools.inputs.HistoricDisturbance(NBAC_workspace, NBAC_filter, NBAC_year_field)
    historicHarvest = preprocess_tools.inputs.HistoricDisturbance(harvest_workspace, harvest_filter, harvest_year_field)
    historicMPB = preprocess_tools.inputs.HistoricDisturbance(MPB_workspace, MPB_filter, None)
    projectedDistBase = preprocess_tools.inputs.ProjectedDisturbance(projScenBase_workspace, projScenBase_filter, "Base", projScenBase_lookuptable)
    spatialBoundaries = preprocess_tools.inputs.SpatialBoundaries(spatial_reference, spatial_boundaries_tsa, spatial_boundaries_pspu,
        "shp", study_area_filter, spatial_boundaries_attr)
    NAmat = preprocess_tools.inputs.NAmericaMAT(os.path.dirname(NAmat_path), os.path.basename(NAmat_path))
    rollbackDisturbances = preprocess_tools.inputs.RollbackDisturbances(rollback_dist_out)

    external_spatial_data = [historicFire1, historicFire2, historicHarvest, historicMPB, projectedDistBase, NAmat, spatialBoundaries]
    # Warning: All spatial inputs that are not in WGS 1984 coordinate system need
    # to be reprojected
    reproject = [
        # historicFire1, historicFire2, historicHarvest, historicMPB, projectedDistBase, NAmat, spatialBoundaries
    ]
    clip = [historicFire1, historicFire2, historicHarvest, historicMPB]
    copy = [sp for sp in external_spatial_data if sp not in clip]

    TSA_filter = '"{}" = {}'.format(study_area_filter["field"], study_area_filter["code"])

    inventory.clipCutPolys(inventory.getWorkspace(), spatialBoundaries.getPathTSA(), TSA_filter,
        r'{}\01a_pretiled_layers\00_Workspace.gdb'.format(working_directory), name='tsa{}'.format(TSA))

    for spatial_input in reproject:
        spatial_input.reproject(spatial_input.getWorkspace().replace(reprojected_redirection[0], reprojected_redirection[1]))
    for spatial_input in clip:
        spatial_input.clip(spatial_input.getWorkspace(), spatialBoundaries.getPathTSA(), TSA_filter,
            spatial_input.getWorkspace().replace(clipped_redirection[0], clipped_redirection[1]))
    for spatial_input in copy:
        spatial_input.copy(spatial_input.getWorkspace().replace(clipped_redirection[0], clipped_redirection[1]))


    ### Aspatial Inputs

    # Different scenarios to be ran by the tiler (before Disturbance Matrix distinctions)
    tiler_scenarios = ['Base']
    # GCBM scenarios (after Disturbance Matrix distinctions) with the associated tiler scenario as the key
    GCBM_scenarios = {'Base':'Base'}

    ## Recliner2GCBM
    recliner2gcbm_config_dir = r"{}\02a_recliner2GCBM_input".format(working_directory)
    recliner2gcbm_output_path = r"{}\02b_recliner2GCBM_output\GCBMinput.db".format(working_directory)

    # directory where the tiler will output to
    tiler_output_dir = r"{}\01b_tiled_layers".format(working_directory)

    ## Yield table
    # path to yield table in external data
    original_yieldTable_path = r"{}\02_aspatial\02_yield_table\yield.csv".format(external_data)
    # path to the yield table (recommended to be in the recliner2gcbm config directory)
    yieldTable_path = r"{}\yield.csv".format(recliner2gcbm_config_dir)
    # The classifiers as keys and the column as value
    yieldTable_classifier_cols = {"AU":0, "LdSpp":1}
    # True if the first row of the yield table is a header
    yieldTable_header = True
    # year interval between age increments
    yieldTable_interval = 10
    # species column and increment range
    yieldTable_cols = {"SpeciesCol":2,"IncrementRange":[3,38]}

    ## AIDB
    # path to aidb in external data where disturbance matrix is already configured
    # according to scenario definitions
    original_aidb_path = r'{}\02_aspatial\01_AIDB\ArchiveIndex_Beta_Install_BASE.mdb'.format(external_data)
    # path to aidb
    aidb_path = r"{}\02a_recliner2GCBM_input\ArchiveIndex_Beta_Install_BASE.mdb".format(working_directory)

    ## Copy yield table and aidb
    shutil.copyfile(original_yieldTable_path, yieldTable_path)
    shutil.copyfile(original_aidb_path, aidb_path)

    ## GCBM Configuration
    gcbm_configs_dir = r'{}\04_GCBM\00_configs'.format(working_directory)
    gcbm_raw_output_dir = r'{}\04_GCBM\01_run\raw_output'.format(working_directory)
    reporting_indicators = {
        "ProtectedAreas":r"G:\Nick\GCBM\05_Test_Automation\05_working_new\00_external_data\01_spatial\05_reporting_indicators\protectedAreas_moja"
    }
    gcbm_exe = r'm:\spatially_explicit\03_tools\gcbm\moja.cli.exe'


    ### Initialize Aspatial Inputs
    yieldTable = preprocess_tools.inputs.YieldTable(path=yieldTable_path, classifier_cols=yieldTable_classifier_cols,
        header=yieldTable_header, interval=yieldTable_interval, cols=yieldTable_cols)
    AIDB = preprocess_tools.inputs.AIDB(path=aidb_path)
    transitionRules = None
    reportingIndicators = preprocess_tools.inputs.ReportingIndicators(reporting_indicators)

    save_inputs()
