#author: Max Fellows

#edits by Scott Morken in March 2018

import os
import simplejson as json
import argparse
import logging
import sys
from future.utils import viewitems
from argparse import ArgumentParser
from glob import glob

def scan_for_layers(layer_root):
    provider_layers = []
    layers = glob(os.path.join(layer_root, "*_moja"))
    for layer in layers:
        logging.debug("Found layer: {}".format(layer))
        layer_prefix, _ = os.path.splitext(os.path.basename(layer))
        layer_path = os.path.join(layer_root, layer_prefix)
        layer_name, _ = layer_prefix.split("_moja")
        provider_layers.append({
            "name"  : layer_name,
            "type"  : None,
            "path"  : layer_path,
            "prefix": layer_prefix
        })
        
    return provider_layers

def update_provider_config(provider_config_path, study_area, layer_root,
                          dbpath, use_relpaths=True):
    logging.info("Updating {} with layers in {}".format(provider_config_path, layer_root))

    with open(provider_config_path, "r") as provider_config_file:
        provider_config = json.load(provider_config_file)
    
    provider_section = provider_config["Providers"]
    layer_config = None
    for provider, config in viewitems(provider_section):
        if "layers" in config:
            spatial_provider_config = config
            break

    spatial_provider_config["tileLatSize"]  = study_area["tile_size"]
    spatial_provider_config["tileLonSize"]  = study_area["tile_size"]
    spatial_provider_config["blockLatSize"] = study_area["block_size"]
    spatial_provider_config["blockLonSize"] = study_area["block_size"]
    spatial_provider_config["cellLatSize"]  = study_area["pixel_size"]
    spatial_provider_config["cellLonSize"]  = study_area["pixel_size"]
            
    provider_layers = []
    relative_layer_root = os.path.relpath(layer_root, os.path.dirname(provider_config_path)) \
        if use_relpaths else layer_root
    for layer in study_area["layers"]:
        logging.debug("Added {} to provider configuration".format(layer))
  
        provider_layers.append({
            "name"        : layer["name"],
            "layer_path"  : os.path.join(relative_layer_root, os.path.basename(layer["path"])),
            "layer_prefix": layer["prefix"]
        })
        
    layer_config = spatial_provider_config["layers"] = provider_layers
    if use_relpaths:
        relative_db_path = os.path.relpath(os.path.dirname(dbpath), os.path.dirname(provider_config_path))
        provider_section["SQLite"]["path"] = os.path.join(relative_db_path, os.path.basename(dbpath))
    else:
        provider_section["SQLite"]["path"] = dbpath
    
    with open(provider_config_path, "w") as provider_config_file:
        provider_config_file.write(json.dumps(provider_config, indent=4, ensure_ascii=False))
        
    logging.info("Provider configuration updated")

def update_gcbm_config(gcbm_config_path, study_area,
                       start_year, end_year, classifiers,
                       reporting_classifiers, output_db_path,
                       variable_grid_output_dir, output_relpaths=True):
    logging.info("Updating {}".format(gcbm_config_path))
    
    with open(gcbm_config_path, "r") as gcbm_config_file:
        gcbm_config = json.load(gcbm_config_file)
    
    tile_size    = study_area["tile_size"]
    pixel_size   = study_area["pixel_size"]
    tile_size_px = int(tile_size / pixel_size)
    
    localdomain_config = gcbm_config["LocalDomain"]
    localdomain_config["start_date"] = "{}/01/01".format(start_year)
    localdomain_config["end_date"] = "{}/01/01".format(end_year)


    landscape_config = gcbm_config["LocalDomain"]["landscape"]
    landscape_config["tile_size_x"] = tile_size
    landscape_config["tile_size_y"] = tile_size
    landscape_config["x_pixels"]    = tile_size_px
    landscape_config["y_pixels"]    = tile_size_px
    landscape_config["tiles"]       = study_area["tiles"]
    
    disturbance_listener_config = gcbm_config["Modules"]["CBMDisturbanceListener"]
    if not "settings" in disturbance_listener_config:
        disturbance_listener_config["settings"] = {}

    disturbance_listener_config["settings"]["vars"] = []
    disturbance_layers = disturbance_listener_config["settings"]["vars"]

    output_db_path = os.path.relpath(output_db_path, os.path.dirname(gcbm_config_path)) \
        if output_relpaths else output_db_path
    CBMAggregatorSQLiteWriter_config = gcbm_config["Modules"]["CBMAggregatorSQLiteWriter"]
    CBMAggregatorSQLiteWriter_config["settings"]["databasename"] = output_db_path

    variable_grid_output_dir = os.path.relpath(variable_grid_output_dir, os.path.dirname(gcbm_config_path)) \
        if output_relpaths else variable_grid_output_dir

    WriteVariableGrid_config = gcbm_config["Modules"]["WriteVariableGrid"]
    WriteVariableGrid_config["settings"]["output_path"] = variable_grid_output_dir

    variable_config = gcbm_config["Variables"]
    variable_names = [var_name.lower() for var_name in variable_config]
    for layer in study_area["layers"]:
        layer_name = layer["name"]
        if layer.get("type") == "DisturbanceLayer":
            disturbance_layers.append(layer_name)
            
        if layer_name.lower() in variable_names:
            logging.debug("Variable {} already present in config - skipping update".format(layer_name))
            continue
        
        variable_config[layer_name] = {
            "transform": {
                "library" : "internal.flint",
                "type"    : "LocationIdxFromFlintDataTransform",
                "provider": "RasterTiled",
                "data_id" : layer_name
            }
        }

    variable_config["initial_classifier_set"]["transform"]["vars"] = classifiers
    variable_config["reporting_classifiers"]["transform"]["vars"].extend(reporting_classifiers)

    with open(gcbm_config_path, "w") as gcbm_config_file:
        gcbm_config_file.write(json.dumps(gcbm_config, indent=4, ensure_ascii=False))
    
    logging.info("GCBM configuration updated")
    
def get_study_area(layer_root):
    study_area = {
        "tile_size" : 1.0,
        "block_size": 0.1,
        "pixel_size": 0.00025,
        "tiles"     : [],
        "layers"    : []
    }
    
    study_area_path = os.path.join(layer_root, "study_area.json")
    if os.path.exists(study_area_path):
        with open(study_area_path, "r") as study_area_file:
            study_area.update(json.load(study_area_file))

    # Find all of the layers for the simulation physically present on disk, then
    # add any extra metadata available from the tiler's study area output.
    layers = scan_for_layers(layer_root)
    study_area_layers = study_area.get("layers")
    if study_area_layers:
        for layer in layers:
            for layer_metadata \
            in filter(lambda l: l.get("name") == layer.get("name"), study_area_layers):
                layer.update(layer_metadata)
    
    study_area["layers"] = layers
   
    return study_area

