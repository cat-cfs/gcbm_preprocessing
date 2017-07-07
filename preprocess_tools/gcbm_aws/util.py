# a great deal of code modified and copied from:
# https://github.com/OpenBounds/Processing

import sys
import os
import logging
import subprocess
import tempfile
import glob

import click

from pyproj import Proj, transform
import fiona
from fiona.crs import from_epsg, to_string
from fiona.transform import transform_geom
import rasterio

import boto3


def info(*strings):
    if sys.stdout.isatty():
        click.echo(' '.join(strings))
    else:
        logging.info(' '.join(strings))


def error(*strings):
    if sys.stdout.isatty():
        click.secho(' '.join(strings), fg='red')
    else:
        logging.error(' '.join(strings))


def success(*strings):
    if sys.stdout.isatty():
        click.secho(' '.join(strings), fg='green')
    else:
        logging.info(' '.join(strings))


def sizeof_fmt(num):
    """Human readable file size.
    Modified from http://stackoverflow.com/a/1094933/1377021
    :param num: float
    :returns: string
    """
    for unit in ['', 'k', 'm', 'g', 't', 'p', 'e', 'z']:
        if abs(num) < 1024.0:
            return "%.0f%s%s" % (num, unit, 'b')
        num /= 1024.0

    return "%.f%s%s" % (num, 'y', 'b')


def make_sure_path_exists(path):
    """
    Make directories in path if they do not exist.
    Modified from http://stackoverflow.com/a/5032238/1377021
    """
    try:
        os.makedirs(path)
    except:
        pass


def scan_for_layers(path, filters):
    # https://stackoverflow.com/questions/4568580/python-glob-multiple-filetypes
    if type(filters) == str:
        filters = [filters]
    if type(filters) in [list, tuple]:
        files = []
        for f in filters:
            files.extend(glob.glob(os.path.join(path, f)))
        return sorted(files,
                      key=os.path.basename)
    else:
        error('scan_for_layers requires a glob string or a list/tuple of strings')


def transform_bbox(bbox, in_crs='EPSG:4326', out_crs='EPSG:3005'):
    """Transform bbox coordinates
    """
    in_proj = Proj(in_crs)
    out_proj = Proj(out_crs)
    a = transform(in_proj, out_proj, bbox[0], bbox[1])
    b = transform(in_proj, out_proj, bbox[2], bbox[3])
    return (a+b)


def describe(in_file, layer=0):
    """Basically fio and rio info
    https://github.com/Toblerity/Fiona/blob/master/fiona/fio/info.py
    https://github.com/mapbox/rasterio/blob/master/rasterio/rio/info.py
    """
    # try vector first
    try:
        with fiona.drivers():
            with fiona.open(in_file, layer=layer) as src:
                inf = src.meta
                inf.update(bounds=src.bounds, name=src.name)
                try:
                    inf.update(count=len(src))
                except TypeError:
                    inf.update(count=None)
                    info("Setting 'count' to None/null - layer does "
                         "not support counting")
                proj4 = fiona.crs.to_string(src.crs)
                if proj4.startswith('+init=epsg'):
                    proj4 = proj4.split('=')[1].upper()
                inf['crs'] = proj4
                inf['type'] = 'VECTOR'
    # if fiona fails, try rasterio
    except:
        with rasterio.open(in_file) as src:
            inf = dict(src.profile)
            inf['shape'] = (inf['height'], inf['width'])
            inf['bounds'] = src.bounds
            proj4 = src.crs.to_string()
            if proj4.startswith('+init=epsg'):
                proj4 = proj4.split('=')[1].upper()
            inf['crs'] = proj4
            inf['type'] = 'RASTER'
    return inf


def get_bbox(in_file, layer=0):
    """ Get wgs84 bbox of in_file
    """
    meta = describe(in_file, layer)
    bbox = meta['bounds']
    if meta['crs'] != from_epsg(4326):
        bbox = transform_bbox(bbox, meta['crs'], from_epsg(4236))
    return bbox


def get_crs(in_file, layer=0):
    """Return CRS of intput as a Proj.4 mapping
    """
    return describe(in_file, layer)['crs']


def bbox_copy(in_file, out_file, bbox, in_layer=0, out_layer=None, dst_crs=None):
    """Dump all features within the provided WGS84 bbox to a new file
    """
    with fiona.drivers():
        with fiona.open(in_file, layer=in_layer) as source:
            output_schema = source.schema.copy()
            # transform the provided bbox to the crs of source data
            bbox_proj = transform_bbox(bbox, from_epsg(4326),
                                       out_crs=source.meta['crs'])
            # use source crs if no reprojection specified
            if dst_crs:
                out_crs = dst_crs
            else:
                out_crs = source.crs
            with fiona.open(out_file, 'w',
                            crs=out_crs, driver="ESRI Shapefile",
                            schema=output_schema) as sink:
                for f in source.filter(bbox=bbox_proj):
                    # transform only if dst_crs specified
                    if dst_crs:
                        g = transform_geom(
                                    source.crs, dst_crs, f['geometry'],
                                    antimeridian_cutting=True)
                        f['geometry'] = g
                    sink.write(f)


def bbox_copyraster(in_file, out_file, bbox, dst_crs=None):
    """Rather than re-invent rio clip, rio warp just call them directly
    """
    with rasterio.open(in_file) as source:
        bbox = transform_bbox(bbox, from_epsg(4326), out_crs=source.meta['crs'])
    bbox = [str(b) for b in bbox]
    if not dst_crs:
        clip_file = out_file
    else:
        clip_file = os.path.join(tempfile.gettempdir(), "rio_temp.tif")
    command = ['rio', 'clip', in_file, clip_file,
               '--bounds', '"'+" ".join(bbox)+'"']
    subprocess.call(" ".join(command), shell=True)
    if dst_crs:
        # convert crs to string and wrap in quotes
        if type(dst_crs) == dict:
            dst_crs = to_string(dst_crs)
        dst_crs = '"'+dst_crs+'"'
        command = ['rio', 'warp', clip_file, out_file,
                   '--dst-crs', dst_crs,
                   '--force-overwrite']
        subprocess.call(" ".join(command), shell=True)
        os.unlink(clip_file)


def upload_s3(bucket_name, path):
    """Upload a file to S3
    deprecated - use awscli
    """
    s3 = boto3.resource('s3')
    buckets = [b.name for b in s3.buckets.all()]
    if bucket_name not in buckets:
        s3.create_bucket(Bucket=bucket_name)
    info('Uploading', path)
    filesize = os.path.getsize(path)
    key = os.path.split(path)[1]
    s3.Object(bucket_name, key).put(Body=open(path, 'rb'))
    success('Done. Uploaded', sizeof_fmt(filesize))


def download_s3(bucket_name, key, out_path=None):
    """Download a file from S3
    deprecated - use awscli
    """
    if not out_path:
        out_path = os.getcwd()
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    info('Downloading', key)
    bucket.download_file(key, os.path.join(out_path, key))
    success('Done. Downloaded %s' % key)
