import simplejson as json
import gdal
import os
import io
import codecs
import zipfile
from zipfile import ZipFile
from gdalconst import *

class CompressingTiler2D(object):

    def __init__(self, bounding_box, tile_extent=1.0, block_extent=0.1,
                 use_bounding_box_resolution=False):
        self._bounding_box = bounding_box
        self._tile_extent = tile_extent
        self._block_extent = block_extent
        self._use_bounding_box_resolution = use_bounding_box_resolution

    def tile(self, layers):
        for layer in layers:
            print "Processing layer: {}".format(layer.name)
            layer = self._bounding_box.normalize(
                layer,
                self._block_extent,
                self._bounding_box.pixel_size if self._use_bounding_box_resolution
                                              else None)

            output_folder = os.path.dirname(layer.path)
            if output_folder and not os.path.exists(output_folder):
                os.makedirs(output_folder)

            raster_name, _ = os.path.splitext(os.path.basename(layer.path))
            output_filename = os.path.join(output_folder, "{}.zip".format(raster_name))
            with ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as output_container:
                metadata_path = os.path.join("{}.json".format(raster_name))
                self._write_metadata(layer, metadata_path, output_container)

                ds = gdal.Open(layer.path, GA_ReadOnly)
                for tile in layer.tiles(self._tile_extent, self._block_extent):
                    print "  Processing tile: {}".format(tile.name)
                    band = ds.GetRasterBand(1)
                    tile_out_path = os.path.join(
                        output_folder,
                        "{}_{}".format(raster_name, tile.name))

                    for i, block in enumerate(tile.blocks):
                        block_out_path = os.path.join(tile_out_path, "{}.blk".format(i))
                        data = band.ReadAsArray(block.x_offset, block.y_offset,
                                                block.x_size, block.y_size)
                        b = str(bytearray(data))
                        output_container.writestr(block_out_path, b)

    def _write_metadata(self, layer, metadata_path, output_container):
        metadata = {
            "layer_type"  : "GridLayer",
            "layer_data"  : layer.data_type,
            "nodata"      : layer.nodata_value,
            "tileLatSize" : self._tile_extent,
            "tileLonSize" : self._tile_extent,
            "blockLatSize": self._block_extent,
            "blockLonSize": self._block_extent,
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
        
        output_container.writestr(
            metadata_path,
            json.dumps(metadata, indent=4, ensure_ascii=False).encode("utf8"))
