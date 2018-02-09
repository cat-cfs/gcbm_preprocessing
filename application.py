from gdb_functions import GDBFunctions

# filter used to get the desired study area from the TSA boundaries.
# change only the associated values for "field" and "code"
study_area_filter = {
    "field": "TSA_NUMBER",
    "code": "'Boundary TSA'"
}
# field names for the Admin and Eco attributes in the spatial_boundaries_ri file
spatial_boundaries_attr = {
    "Admin": "AdminBou_1",
    "Eco": "EcoBound_1"
}

working_directory=""
inventory_workspace_path = r"F:\GCBM\17_BC_ON_1ha\05_working_BC\00_external_data\01_spatial\02_inventory\Processed.gdb"
spatial_boundaries_path = r"F:\GCBM\17_BC_ON_1ha\05_working_BC\00_external_data\01_spatial\01_spatial_reference\PSPUS_2016_FINAL_1_Reprojected.shp"
TSA_filter = "\"TSA_NUMBER\" = 'Boundary TSA'"
new_Workspace = r"F:\GCBM\17_BC_ON_1ha\05_working_BC\TSA_2_Boundary\01a_pretiled_layers\00_Workspace.gdb"
inventoryOutputName = "tsa2"

gdbFunctions = GDBFunctions()

gdbFunctions.clipCutPolys(
    workspace = inventory_workspace_path,
    clip_feature = spatial_boundaries_path,
    clip_feature_filter = TSA_filter,
    new_workspace = new_Workspace,
    name = inventoryOutputName)





