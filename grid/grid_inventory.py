import os
import inspect
import multiprocessing
from functools import partial
import logging

from osgeo import gdal
import pgdata


def parallel_tiled(db_url, sql, block, n_subs=2):
    """
    Create a connection and execute query for specified block.
    n_subs is the number of places in the sql query that should be
    substituted by the block id

    this should live in pgdata
    """
    # create a new connection
    db = pgdata.connect(db_url, multiprocessing=True)
    # As we are explicitly splitting up our job we don't want the database to try
    # and manage parallel execution of these queries within these connections.
    # Turn off this connection's parallel execution for pg version >= 10:
    version_string = db.query('SELECT version()').fetchone()[0]
    major_version_number = int(version_string.split(' ')[1].split('.')[0])
    if major_version_number >= 10:
        db.execute("SET max_parallel_workers_per_gather = 0")
    db.execute(sql, (block,) * n_subs)


class GridInventory(object):

    def __init__(self, config):
        self.config = config
        self.n_processes = config.GetNProcesses()
        self.area_majority_rule = config.GetAreaMajorityRule()
        self.resolution = config.GetResolution()

        # point to the sql folder within grid module
        sql_path = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'sql')
        self.db = pgdata.connect(sql_path=sql_path)
        self.db.execute(self.db.queries['ST_Fishnet'])
        self.inventory = 'preprocessing.inventory'
        self.gridded_inventory_lut = "preprocessing.inventory_grid_xref"

    def load_to_postgres(self, in_workspace, in_layer):
        """ Load inventory to db
        """

        # find inventory columns to retain
        reporting_classifiers = self.config.GetReportingClassifiers()
        inventory_classifiers = self.config.GetInventoryClassifiers()
        inventory_fields = reporting_classifiers.copy()
        inventory_fields.update(inventory_classifiers)
        inventory_fields["species"] = self.config.GetInventoryFieldNames()["species"]
        inventory_fields["age"] = self.config.GetInventoryFieldNames()["age"]

        # build a SQL string that remaps the columns as specified in config
        remap_string = ", ".join(
            [c_in+' AS '+c_out.lower() for c_out, c_in in inventory_fields.iteritems()])

        # build age > 0 filter
        filter_string = "{a} > 0".format(a=inventory_fields["age"])
        logging.info("Loading inventory to postgres for gridding")

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
                layerName=self.inventory,
                accessMode='overwrite',
                dim='2',
                SQLStatement="""
                    SELECT {remap}
                    FROM {lyr}
                    WHERE {filter}""".format(
                    remap=remap_string,
                    lyr=in_layer,
                    filter=filter_string),
                SQLDialect='OGRSQL',
                geometryType='PROMOTE_TO_MULTI',
                layerCreationOptions=['OVERWRITE=YES',
                                      'SCHEMA=preprocessing',
                                      'GEOMETRY_NAME=geom']
        )
        db = pgdata.connect()
        db.execute("""
            ALTER TABLE preprocessing.inventory
            RENAME COLUMN ogc_fid TO inventory_id""")

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
        # load Canada Albers projection
        self.db.execute(self.db.queries['load_canada_albers'])
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
        sql = self.db.queries['load_grid']
        # add resolution to query
        lookup = {'x_res': str(self.resolution), 'y_res': str(self.resolution)}
        sql = self.db.build_query(sql, lookup)
        blocks = [b for b in self.db['preprocessing.blocks'].distinct('block_id')]
        func = partial(parallel_tiled, self.db.url, sql, n_subs=2)
        pool = multiprocessing.Pool(self.n_processes)
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
              inventory_id integer)"""
        )
        if self.area_majority_rule:
            query = 'load_inventory_grid_xref_areamajority'
        else:
            query = 'load_inventory_grid_xref_centroid'
            return ValueError('Centroid inventory gridding is not currently supported')
        sql = self.db.queries[query]
        blocks = [b for b in self.db['preprocessing.blocks'].distinct('block_id')]
        func = partial(parallel_tiled, self.db.url, sql, n_subs=1)
        pool = multiprocessing.Pool(self.n_processes)
        pool.map(func, blocks)
        pool.close()
        pool.join()

        # create indexes
        self.db['preprocessing.inventory_grid_xref'].create_index(['grid_id'])
        self.db['preprocessing.inventory_grid_xref'].create_index(['inventory_id'])
