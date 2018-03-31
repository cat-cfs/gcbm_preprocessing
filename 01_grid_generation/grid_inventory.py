
import logging
import inspect
import multiprocessing
from functools import partial

import pgdata

from preprocess_tools.licensemanager import *


class GridInventory(object):
    def __init__(self, inventory, resolution, output_dbf_dir, sql_path, ProgressPrinter,  area_majority_rule=True):
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

    def parallel_tiled(self, sql, block, n_subs=2):
        """
        Create a connection and execute query for specified block
        n_subs is the number of places in the sql query that should be
        substituted by the block name
        """
        # create a new connection
        db_url = self.db.url
        db = pgdata.connect(db_url, multiprocessing=True)
        # As we are explicitly splitting up our job we don't want the database to try
        # and manage parallel execution of these queries within these connections.
        # Turn off this connection's parallel execution for pg version >= 10:
        version_string = db.query('SELECT version()').fetchone()[0]
        major_version_number = int(version_string.split(' ')[1].split('.')[0])
        if major_version_number >= 10:
            db.execute("SET max_parallel_workers_per_gather = 0")
        db.execute(sql, (block) * n_subs)

    def create_blocks(self):
        """Create .1deg blocks to iterate over
        """
        db = self.db
        db[self.blocks].drop()
        db.execute(db.queries['create_blocks'])

    def create_grid(self):
        """
        Create grid table, then insert cells by looping through blocks
        (creating a very large grid with ST_Fishnet will throw errors)
        """
        pp = self.ProgressPrinter.newProcess(inspect.stack()[0][3], 1, 1).start()
        self.db['preprocessing.grid'].drop()
        self.db.execute("""
            CREATE TABLE preprocessing.grid
             (grid_id SERIAL PRIMARY KEY,
              block_id integer,
              shape_area_ha float,
              geom geometry)""")
        # load query that does the work
        sql = self.db.queries['create_block_grid']

        #for block in self.db['preprocessing.blocks']:
        #    self.db.execute(sql, (block['block_id'], block['block_id']))
        blocks = [6, 7]
        for block in blocks:
            self.db.execute(sql, (block, block))
        #blocks = [b for b in self.db['preprocessing.blocks'].distinct('block_id')]
        # run the query in several processes
        #func = partial(self.parallel_tiled, self.db.url, sql, n_subs=2)
        #pool = multiprocessing.Pool(self.n_processes)
        #pool.map(func, blocks)
        #pool.close()
        #pool.join()

        pp.finish()
