from application import Application
pathData = {
    "Working_Dir": ["F:/","GCBM","17_BC_ON_1ha","05_working_BC"],
    "External_Spatial_Dir": ["${Working_Dir}","00_external_data","01_spatial"],
    "Spatial_Boundaries": ["${External_Spatial_Dir}", "01_spatial_reference"],
    "Inventory_Workspace": ["${External_Spatial_Dir}", "02_inventory"],
    "External_Historic_Dist": ["${External_Spatial_Dir}", "03_disturbances", "01_historic"],
    "Historic_Fire_Dir": ["${External_Historic_Dist}", "01_fire", "shapefiles"],
    "Historic_Harvest_Dir": ["${External_Historic_Dist}", "02_harvest"],
    "Historic_Insect_Dir": ["${External_Historic_Dist}", "03_insect_filtered"],
    "Environment_Dir": ["${External_Spatial_Dir}","04_environment"],
    "SubRegionDir": ["${Working_Dir}", "${Region_Name}"],
    "Pretiled_Layers": ["${SubRegionDir}", "01a_pretiled_layers"],
    "Clipped_Inventory_Path": ["${Pretiled_Layers}","00_Workspace.gdb"],
    "Clipped_Historic_Disturbance_Path": ["${Pretiled_Layers}", "03_disturbances", "01_historic"],
    "Clipped_Historic_Fire_Path": ["${Clipped_Historic_Disturbance_Path}", "01_fire", "shapefiles"],
    "Clipped_Historic_Harvest_Path": ["${Clipped_Historic_Disturbance_Path}", "02_harvest"],
    "Clipped_Historic_Insect_Path": ["${Clipped_Historic_Disturbance_Path}", "03_insect_filtered"],
    "Copied_Environment_Dir": ["${Pretiled_Layers}", "04_environment"]
}

clip = {
"ClipCutPolysTasks":[
    {
        "workspace": "Inventory_Workspace",
        "workspace_filter": "Processed.gdb",
        "new_workspace": "Clipped_Inventory_Path",
        "name": "Non"
    }
],
"ClipTasks": [
    {
        "workspace": "Historic_Fire_Dir",
        "workspace_filter": "NFDB*.shp",
        "output_path": "Clipped_Historic_Disturbance_Path"
    },
    {
        "workspace": "Historic_Fire_Dir",
        "workspace_filter": "NBAC*.shp",
        "output_path": "Clipped_Historic_Disturbance_Path"
    },
    {
        "workspace": "Historic_Harvest_Dir",
        "workspace_filter": "BC_cutblocks90_15.shp",
        "output_path": "Clipped_Historic_Harvest_Path"
    },
    {
        "workspace": "Historic_Insect_Dir",
        "workspace_filter": "mpb*.shp",
        "output_path": "Clipped_Historic_Insect_Path"
    }
],
"CopyTasks": [
    {
        "workspace": "Environment_Dir",
        "workspace_filter": "NAmerica_MAT_1971_2000.tif",
        "new_workspace_path": "Copied_Environment_Dir"
    },
    {
        "workspace": "Environment_Dir",
        "workspace_filter": "NAmerica_MAT_1971_2000.tif",
        "new_workspace_path": "Copied_Environment_Dir"
    }
],
"SubRegions": [
    {
    "Name": "Boundary",
    "Region_Number": 2,
    "clip_feature": "inventory",
    "clip_feature_filter": "\"TSA_NUMBER\" = 'Boundary TSA'",
    "Spatial_Boundaries_Filter": "\"TSA_NUMBER\" = 'Boundary TSA'",
    }]
}


app = Application("TSA_2_Boundary", pathData)