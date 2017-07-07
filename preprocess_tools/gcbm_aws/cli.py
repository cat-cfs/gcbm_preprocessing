import os
import csv
from math import ceil
from urlparse import urlparse
import multiprocessing

from shapely.geometry import box, mapping
import fiona
from fiona.crs import from_epsg
import click
import pgdb

import util


CONFIG = {
    "source_path": "inputs",
    "datalist": r"/Volumes/Data/Projects/cat/aws_processing/gcbm_aws/config/bc/nass.csv",
    "db_url": "postgresql://postgres:postgres@localhost:5432/nass",
    "n_processes": multiprocessing.cpu_count() - 1
    }


HELP = {
  "source_path": 'Path to folder holding input data',
  "datalist": 'Path to csv that lists all input data sources',
  "name": "The 'name' key identifing the source of interest, from source csv"}


@click.group()
def cli():
    pass


@cli.command()
@click.argument('datalist', type=click.Path(exists=True), required=True)
@click.option(
    '--like', type=click.Path(exists=True),
    help='Vector dataset to use as a template for bbox and output crs')
@click.option(
    '--bbox', default=None, metavar="w,s,e,n",
    help="Filter for features intersecting a bounding box")
@click.option(
    '--dst-crs', '--dst_crs', help="Destination CRS as 'EPSG:1234' string")
@click.option(
    '--out_path', '-o',
    default=os.getcwd(), help="Path to create output files")
def extract(datalist, like, bbox, dst_crs, out_path):
    """Extract/reproject data within lat/lon bbox
    """
    # check that enough options are provided
    if not like and not bbox:
        util.error("Provide bounds as either a 'like' dataset or a bbox")
    # read input csv listing layers
    layers = [s for s in csv.DictReader(open(datalist, 'rb'))]
    # parse bbox
    if bbox:
        bbox = tuple(map(float, bbox.split(',')))
    # derive bbox/crs from aoi/like layer (ignoring any provided bbox)
    if like:
        bbox = util.get_bbox(like)
        dst_crs = util.get_crs(like)
    # parse provided epsg code
    elif dst_crs:
        dst_crs = from_epsg(dst_crs.split(':')[1])
    # name is derived from config file name
    if not out_path:
        b = os.path.basename(datalist)
        out_path = os.path.join(os.getcwd(), os.path.splitext(b)[0])
    util.make_sure_path_exists(out_path)
    # process each layer
    for layer in layers:
        click.echo('Extracting %s' % layer['name'])
        if util.describe(layer['path'])['type'] == 'VECTOR':
            util.bbox_copy(layer['path'], os.path.join(out_path,
                                                       layer['name']+".shp"),
                           bbox, in_layer=layer['layer'], dst_crs=dst_crs)
        elif util.describe(layer['path'])['type'] == 'RASTER':
            util.bbox_copyraster(layer['path'],
                                 os.path.join(out_path,
                                              layer['name']+'.tif'),
                                 bbox, dst_crs=dst_crs)


@cli.command()
@click.argument('in_file', type=click.Path(exists=True))
@click.argument('out_file')
@click.argument('cell_size', type=int, default=100)
@click.option('--layer', '-l', help='Input layer')
@click.option('--tile_area', '-t', type=int, default='100000',
              help='Max area covered per tile_id (ha)')
def create_grid(in_file, out_file, cell_size, layer, tile_area):
    '''Create regular polygon grid shapefile
    '''
    if not layer:
        layer = 0
    # read CRS and bounds from source
    with fiona.open(in_file, 'r', layer=layer) as src:
        crs = src.crs
        xmin, ymin, xmax, ymax = src.bounds

    if crs['units'] != 'm':
        raise RuntimeError('Input layer crs must have unit metres (m)')

    # n rows, n columns
    rows = int(ceil((ymax-ymin)/cell_size))
    cols = int(ceil((xmax-xmin)/cell_size))

    # convert tile area to m2
    tile_area = tile_area * 10000

    # write grid to .shp
    schema = {'geometry': 'Polygon', 'properties': {'cell_id': 'str',
                                                    'tile_id': 'int'}}
    with fiona.open(out_file, 'w', 'ESRI Shapefile', schema, crs=crs) as sink:
        with click.progressbar(range(rows)) as bar:
            area = 0
            for row_id in bar:
                for col_id in range(cols):
                    x = xmin + (col_id * cell_size)
                    y = ymin + (row_id * cell_size)
                    tile_id = int(ceil(area / tile_area)) + 1
                    f = {}
                    f['geometry'] = mapping(box(x, y,
                                                x + cell_size, y + cell_size))
                    f['properties'] = {"cell_id":
                                       str(col_id + 1)+','+str(row_id + 1),
                                       "tile_id": tile_id}
                    sink.write(f)
                    area = area + (cell_size * cell_size)


# load source data to postgres
# (would be useful for processing rollback on AWS)
@cli.command()
@click.option('--datalist', '-dl', default=CONFIG["datalist"],
              type=click.Path(exists=True), help=HELP['datalist'])
@click.option('--source_path', default=CONFIG["source_path"],
              type=click.Path(exists=True), help=HELP['source_path'])
@click.option('--name', '-n', help=HELP['name'])
def load(source_csv, source_path, name):
    '''Load a spatial data table/layer to postgres
    '''
    db = pgdb.connect(CONFIG["db_url"])
    sources = [s for s in csv.DictReader(open(source_csv, 'rb'))]
    # filter sources based on optional provided name
    if name:
        sources = [s for s in sources if s['name'] == name]
    # load to postgres
    for source in sources:
        pgdb.ogr2pg(db, os.path.join(source_path, source['name']))


@cli.command()
@click.argument('in_file', type=click.Path(exists=True))
@click.option('--layer', '-l', help='Input layer', default=0)
def get_bbox(in_file, layer):
    click.echo(util.get_bbox(in_file, layer))
