import os
import glob
import logging
import inspect
from functools import partial
import multiprocessing

from osgeo import gdal
import pgdata


def _parallel_tiled(db_url, sql, block, n_subs=2):
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


def _scan_for_layers(path, filter):
    return sorted(glob.glob(os.path.join(path, filter)), key=os.path.basename)


def merge_disturbances(db_url, gdal_con, disturbances):
    """ Load all input disturbance data to a single table
    """
    logging.info("Merging disturbances")
    db = pgdata.connect(db_url)
    gdal.SetConfigOption('PG_USE_COPY', 'YES')
    db['preprocessing.disturbances'].drop()
    for i, dist in enumerate(disturbances):
        for j, filename in enumerate(_scan_for_layers(dist["Workspace"], dist["WorkspaceFilter"])):
            # The first input source defines the table creation, requiring
            # - layer creation options provided, including schema name - schema
            #   is not included in the new layer name
            # - access mode is null
            layer = os.path.splitext(os.path.basename(filename))[0]
            if i + j == 0:
                table_name = 'disturbances'
                access_mode = None
                layer_creation_options = ['SCHEMA=preprocessing',
                                          'GEOMETRY_NAME=geom']
            else:
                table_name = 'preprocessing.disturbances'
                access_mode = 'append'
                layer_creation_options = None
            # build sql to translate the data
            column_list = [dist["YearSQL"],
                           str((dist["DisturbanceTypeCode"])) + " AS dist_type",
                           "'" + layer + "' AS source",
                           "GEOMETRY FROM " + layer]
            logging.info(", ".join(column_list))
            gdal.VectorTranslate(
                gdal_con,
                os.path.join(dist["WorkspaceFilter"], filename),
                format='PostgreSQL',
                layerName=table_name,
                accessMode=access_mode,
                # Note that GEOMETRY column is not required if using OGRSQL dialect.
                # The SQLITE dialect provides more options for manipulating the data
                SQLStatement=", ".join(column_list),
                SQLDialect='SQLITE',
                dim='2',
                geometryType='PROMOTE_TO_MULTI',
                layerCreationOptions=layer_creation_options
            )
    # Rename primary key / fid to make queries a bit more readable
    db.execute("""
        ALTER TABLE preprocessing.disturbances
        RENAME COLUMN ogc_fid TO disturbance_id
    """)
    # We *should* easily be able to force the dist_type to integer using CAST in the
    # SQLITE sql expression above, but I'm having difficulty... so just ALTER the table
    # after load is complete
    db.execute("""
        ALTER TABLE preprocessing.disturbances
        ALTER COLUMN dist_type SET DATA TYPE integer
        USING dist_type::integer
    """)


def grid_disturbances(db_url, config):
    """ Create and load disturbances_grid_xref by overlaying disturbances and grid
    """
    # point to the sql folder within grid module
    sql_path = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'sql')
    db = pgdata.connect(db_url, sql_path=sql_path)
    logging.info("Gridding disturbances")
    db['preprocessing.disturbances_grid_xref'].drop()
    db.execute(
        """
        CREATE TABLE preprocessing.disturbances_grid_xref
         (grid_id integer,
          disturbance_id integer)"""
    )
    sql = db.queries['load_disturbances_grid_xref']
    blocks = [b for b in db['preprocessing.blocks'].distinct('block_id')]
    func = partial(_parallel_tiled, db.url, sql, n_subs=1)
    pool = multiprocessing.Pool(config.GetNProcesses())
    pool.map(func, blocks)
    pool.close()
    pool.join()

    db['preprocessing.disturbances_grid_xref'].create_index(['grid_id'])
    db['preprocessing.disturbances_grid_xref'].create_index(['disturbance_id'])


def intersect_disturbances_inventory(db_url, config):
    """
    Create table preprocessing.inventory_disturbed by joining gridded inventory
    to gridded disturbances.
    """
    logging.info("Intersecting rollback disturbances and inventory")
    # point to the sql folder within rollback module and run the query
    sql_path = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'sql')
    db = pgdata.connect(db_url, sql_path=sql_path)
    db['preprocessing.inventory_disturbed'].drop()
    db.execute(
        db.queries['intersect_disturbances_inventory'],
        (config.GetInventoryYear(), config.GetRollbackRange()["StartYear"])
    )
    db['preprocessing.inventory_disturbed'].create_index(['grid_id'])
