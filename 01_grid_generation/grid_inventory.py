import logging
import inspect
import multiprocessing
from functools import partial

import pgdata


def parallel_tiled(db_url, sql, block, n_subs=2):
    """
    Create a connection and execute query for specified block.
    n_subs is the number of places in the sql query that should be
    substituted by the block id
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

    def __init__(
        self,
        inventory,
        resolution,
        output_dbf_dir,
        sql_path,
        ProgressPrinter,
        area_majority_rule=True,
    ):
        logging.info("Initializing class {}".format(self.__class__.__name__))
        self.ProgressPrinter = ProgressPrinter
        self.inventory = inventory
        self.resolution = resolution
        self.output_dbf_dir = output_dbf_dir
        self.area_majority_rule = area_majority_rule
        self.inventory_layer = r"preprocessing.inventory"
        self.grid = "preprocessing.grid"
        self.blocks = "preprocessing.blocks"
        self.gridded_inventory_lut = "preprocessing.inventory_grid_xref"
        # make sure the fishnet function exists
        self.db = pgdata.connect(sql_path=sql_path)
        self.db.execute(self.db.queries['ST_Fishnet'])
        self.n_processes = multiprocessing.cpu_count() - 1

    def create_blocks(self):
        """Create .1 deg blocks
        """
        db = self.db
        db[self.blocks].drop()
        db.execute(db.queries['create_blocks'])

    def create_grid(self):
        """
        Create empty grid table, then insert cells by looping through blocks
        (creating a very large grid in one step with ST_Fishnet is not supported)
        """
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
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
        blocks = [b for b in self.db['preprocessing.blocks'].distinct('block_id')]
        # run the query in several threads
        func = partial(parallel_tiled, self.db.url, sql, n_subs=2)
        pool = multiprocessing.Pool(self.n_processes)
        pool.map(func, blocks)
        pool.close()
        pool.join()
        pp.finish()

    def grid_inventory(self):
        """
        Create inventoyr_grid_xref table, populate by overlay grid with inventory,
        block by block
        """
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        self.db['preprocessing.inventory_grid_xref'].drop()
        self.db.execute(
            """
            CREATE TABLE preprocessing.inventory_grid_xref
             (grid_id integer,
              objectid integer)"""
        )
        sql = self.db.queries['load_inventory_grid_xref']
        blocks = [b for b in self.db['preprocessing.blocks'].distinct('block_id')]
        # run the query in several threads
        func = partial(parallel_tiled, self.db.url, sql, n_subs=1)
        pool = multiprocessing.Pool(self.n_processes)
        pool.map(func, blocks)
        pool.close()
        pool.join()
        pp.finish()
