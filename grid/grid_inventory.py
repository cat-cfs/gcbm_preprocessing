import os
import inspect
import multiprocessing
from functools import partial
import logging

from osgeo import gdal
import pgdata

import util


class GridInventory(object):

    def __init__(
        self,
        resolution,
        n_processes,
        area_majority_rule=True,
    ):
        self.resolution = resolution
        self.n_processes = n_processes
        self.area_majority_rule = area_majority_rule
        # point to the sql folder within grid module
        sql_path = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'sql')
        self.db = pgdata.connect(sql_path=sql_path)
        self.db.execute(self.db.queries['ST_Fishnet'])
        self.inventory = 'preprocessing.inventory'
        self.gridded_inventory_lut = "preprocessing.inventory_grid_xref"

    def load_to_postgres(self, in_workspace, in_layer, age_field):
        """ Load inventory to db
        """
        logging.info("Loading inventory to postgres for gridding")
        # don't load inventory where age = 0
        where = age_field + ' > 0'

        # define pg connection string
        pg = "PG:host='{h}' port='{p}' dbname='{db}' user='{usr}' password='{pwd}'".format(
            h=os.environ['PGHOST'],
            p=os.environ['PGPORT'],
            db=os.environ['PGDATABASE'],
            usr=os.environ['PGUSER'],
            pwd=os.environ['PGPASSWORD'])

        gdal.VectorTranslate(
                pg,
                in_workspace,
                format='PostgreSQL',
                layers=[in_layer],
                layerName=self.inventory,
                accessMode='overwrite',
                where=where,
                dim='2',
                geometryType='PROMOTE_TO_MULTI',
                layerCreationOptions=['OVERWRITE=YES',
                                      'SCHEMA=preprocessing',
                                      'GEOMETRY_NAME=geom']
        )

    def create_blocks(self):
        """ Create .1 degree blocks to enable parallelization
        """
        logging.info("Creating .1 degree blocks to split processing")
        db = self.db
        db['preprocessing.blocks'].drop()
        db.execute(db.queries['create_blocks'])

    def create_grid(self):
        """ Create empty grid table, then insert cells by looping through blocks
        """
        logging.info("Creating grid to overlay with inventory")
        self.db['preprocessing.grid'].drop()
        self.db.execute(
            """
            CREATE TABLE preprocessing.grid
             (grid_id SERIAL PRIMARY KEY,
              block_id integer,
              shape_area_ha float,
              geom geometry)"""
        )
        # note that self.resolution is not currently passed to grid creation
        sql = self.db.queries['load_grid']
        blocks = [b for b in self.db['preprocessing.blocks'].distinct('block_id')]
        func = partial(util.parallel_tiled, self.db.url, sql, n_subs=2)
        pool = multiprocessing.Pool(2)
        pool.map(func, blocks)
        pool.close()
        pool.join()

    def grid_inventory(self):
        """ Create and load inventory_grid_xref by overlaying inventory and grid
        """
        logging.info("Overlaying grid with inventory")
        self.db['preprocessing.inventory_grid_xref'].drop()
        self.db.execute(
            """
            CREATE TABLE preprocessing.inventory_grid_xref
             (grid_id integer,
              objectid integer)"""
        )
        if self.area_majority_rule:
            query = 'load_inventory_grid_xref_areamajority'
        else:
            query = 'load_inventory_grid_xref_centroid'
            return ValueError('Centroid inventory gridding is not currently supported')
        sql = self.db.queries[query]
        blocks = [b for b in self.db['preprocessing.blocks'].distinct('block_id')]
        func = partial(util.parallel_tiled, self.db.url, sql, n_subs=1)
        pool = multiprocessing.Pool(self.n_processes)
        pool.map(func, blocks)
        pool.close()
        pool.join()
