import simplejson as json
import gdal
import os
import io
import codecs
from functools import partial
from gcbm_aws import util

import multiprocess
import dill

from gdalconst import *
from multiprocessing import Pool
from gcbm_aws.mojadata.config import *


class Tiler2D(object):

    def __init__(self, bounding_box, tile_extent=1.0, block_extent=0.1,
                 use_bounding_box_resolution=False):
        self._bounding_box = bounding_box
        self._tile_extent = tile_extent
        self._block_extent = block_extent
        self._use_bounding_box_resolution = use_bounding_box_resolution

    def tile(self, layers):
        Pool(PROCESS_POOL_SIZE).map(_tile_layer, [[
            self._bounding_box,
            layer,
            {
                "tile_extent": self._tile_extent,
                "block_extent": self._block_extent,
                "use_bbox_res": self._use_bounding_box_resolution
            }] for layer in layers])

def _tile_layer(args):
    bbox, layer, config = args
    print "Processing layer: {}".format(layer.name)
    if layer.is_empty():
        print "  Layer is empty - skipping."
        return

    layer = bbox.normalize(
        layer,
        config["block_extent"],
        bbox.pixel_size if config["use_bbox_res"] else None)

    raster_name, _ = os.path.splitext(os.path.basename(layer.path))
    output_folder = os.path.join(os.path.dirname(layer.path), raster_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    metadata_path = os.path.join(output_folder, "{}.json".format(raster_name))
    _write_metadata(layer, config, metadata_path)

    ds = gdal.Open(layer.path, GA_ReadOnly)
    for tile in layer.tiles(config["tile_extent"], config["block_extent"]):
        print "  Processing tile: {}".format(tile.name)
        band = ds.GetRasterBand(1)
        out_path = os.path.join(
            output_folder,
            "{}_{}.blk".format(raster_name, tile.name))

        with open(out_path, "wb") as blocked_file:
            for block in tile.blocks:
                data = band.ReadAsArray(block.x_offset, block.y_offset,
                                        block.x_size, block.y_size)
                b = str(bytearray(data))
                blocked_file.write(b)

def _write_metadata(layer, config, path):
    metadata = {
        "layer_type"  : "GridLayer",
        "layer_data"  : layer.data_type,
        "nodata"      : layer.nodata_value,
        "tileLatSize" : config["tile_extent"],
        "tileLonSize" : config["tile_extent"],
        "blockLatSize": config["block_extent"],
        "blockLonSize": config["block_extent"],
        "cellLatSize" : layer.pixel_size,
        "cellLonSize" : layer.pixel_size
    }

    if layer.attribute_table:
        attributes = {}
        for pixel_value, attr_values in layer.attribute_table.iteritems():
            if len(attr_values) == 1:
                attributes[pixel_value] = attr_values[0]
            else:
                attributes[pixel_value] = dict(zip(layer.attributes, attr_values))

        metadata["attributes"] = attributes
        
    with io.open(path, "w", encoding="utf8") as out_file:
        out_file.write(json.dumps(metadata, out_file, indent=4, ensure_ascii=False))
