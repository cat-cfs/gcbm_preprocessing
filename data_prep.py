### GCBM Preprocessing

## Imports
import archook
archook.get_arcpy()
import arcpy
import os
import preprocess_tools
import cPickle

def save_objects():
    try:
        if not os.path.exists('inputs'):
            os.mkdir('inputs')
        cPickle.dump(inventory, open(r'inputs\inventory.pkl', 'wb'))
        cPickle.dump(historicFire1, open(r'inputs\historicFire1.pkl', 'wb'))
        cPickle.dump(historicFire2, open(r'inputs\historicFire2.pkl', 'wb'))
        cPickle.dump(historicHarvest, open(r'inputs\historicHarvest.pkl', 'wb'))
        cPickle.dump(historicMPB, open(r'inputs\historicMPB.pkl', 'wb'))
        cPickle.dump(projectedDistBase, open(r'inputs\projectedDistBase.pkl', 'wb'))
        cPickle.dump(spatialBoundaries, open(r'inputs\spatialBoundaries.pkl', 'wb'))
        cPickle.dump(NAmat, open(r'inputs\NAmat.pkl', 'wb'))
    except:
        print "Failed to save objects."
        raise

if __name__=="__main__":
    ### Variables
    # directory path to the working directory for relative paths
    working_directory = r'G:\Nick\GCBM\05_Test_Automation\05_working'

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

    ### Initialize inputs
    inventory = preprocess_tools.inputs.Inventory(workspace=inventory_workspace, filter=inventory_layer,
        year=inventory_year, classifiers_attr=inv_classifier_attr)

    historicFire1 = preprocess_tools.inputs.HistoricDisturbance(NFDB_workspace, NFDB_filter, NFDB_year_field)
    historicFire2 = preprocess_tools.inputs.HistoricDisturbance(NBAC_workspace, NBAC_filter, NBAC_year_field)
    historicHarvest = preprocess_tools.inputs.HistoricDisturbance(harvest_workspace, harvest_filter, harvest_year_field)
    historicMPB = preprocess_tools.inputs.HistoricDisturbance(MPB_workspace, MPB_filter, None)

    projectedDistBase = preprocess_tools.inputs.ProjectedDisturbance(projScenBase_workspace, projScenBase_filter, "Base", projScenBase_lookuptable)

    spatialBoundaries = preprocess_tools.inputs.SpatialBoundaries(spatial_reference, spatial_boundaries_tsa, spatial_boundaries_pspu,
        "shp", study_area_filter, spatial_boundaries_attr)

    NAmat = preprocess_tools.inputs.NAmericaMAT(os.path.dirname(NAmat_path), os.path.basename(NAmat_path))

    reproject = [historicFire1, historicFire2, historicHarvest, historicMPB, projectedDistBase, NAmat, spatialBoundaries]
    clip = [historicFire1, historicFire2, historicHarvest, historicMPB, projectedDistBase]

    inventory.reproject(inventory.getWorkspace(), name='inv_reprojected')

    for spatial_input in reproject:
        spatial_input.reproject(spatial_input.getWorkspace().replace('01_external_spatial_data', '01a_reprojected'))
    # for spatial_input in clip:
    #     spatial_input.clip(os.path.join(inventory.getWorkspace(), inventory.getFilter()), os.path.join(spatial_input.getWorkspace(), 'clipped'))

    save_objects()
