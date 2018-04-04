import os
import glob
import logging

from osgeo import gdal
import pgdata


def scan_for_layers(path, filter):
    return sorted(glob.glob(os.path.join(path, filter)), key=os.path.basename)


def merge_disturbances(disturbances):
    logging.info("Merging disturbances")
    pg = ("PG:host='{h}' port='{p}' dbname='{db}' "
          "user='{usr}' password='{pwd}'").format(
        h=os.environ['PGHOST'],
        p=os.environ['PGPORT'],
        db=os.environ['PGDATABASE'],
        usr=os.environ['PGUSER'],
        pwd=os.environ['PGPASSWORD']
    )
    db = pgdata.connect()
    gdal.SetConfigOption('PG_USE_COPY', 'YES')
    db['preprocessing.rollback_disturbances'].drop()
    for i, dist in enumerate(disturbances):
        for j, filename in enumerate(scan_for_layers(dist["Workspace"], dist["WorkspaceFilter"])):
            # The first input source defines the table creation, requiring
            # - layer creation options provided, including schema name - schema
            #   is not included in the new layer name
            # - access mode is null
            layer = os.path.splitext(os.path.basename(filename))[0]
            if i + j == 0:
                table_name = 'rollback_disturbances'
                access_mode = None
                layer_creation_options = ['SCHEMA=preprocessing',
                                          'GEOMETRY_NAME=geom']
            else:
                table_name = 'preprocessing.rollback_disturbances'
                access_mode = 'append'
                layer_creation_options = None
            gdal.VectorTranslate(
                pg,
                os.path.join(dist["WorkspaceFilter"], filename),
                format='PostgreSQL',
                layerName=table_name,
                accessMode=access_mode,
                # Note that GEOMETRY column is not required if using OGRSQL dialect.
                # The SQLITE dialect provides more options for manipulating the data
                SQLStatement=dist["YearSQL"] + ", '" + layer + "' as source, GEOMETRY FROM {lyr}".format(
                    lyr=layer),
                SQLDialect='SQLITE',
                dim='2',
                geometryType='PROMOTE_TO_MULTI',
                layerCreationOptions=layer_creation_options
            )
