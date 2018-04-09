import inspect
import logging
import os
import tempfile
from xml.sax.saxutils import escape


from osgeo import gdal
import pgdata


def generate_slashburn(
    inventory_workspace,
    inventory_disturbance_year_fieldname,
    harvest_shp,
    harvest_shp_year_field,
    year_range,
    sb_percent
):
    """
    Generate annual slashburn disturbances for the rollback period.

    Note:
    slashburn disturbances are written as grid cells to preprocessing.temp_slashburn
    (this lets us use the same query to generate slashburn for rollback and historic)
    """
    logging.info("Generating slashburn")
    logging.info('Making slashburn for the range {}-{}'.format(
        year_range[0], year_range[-1]))

    sql_path = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'sql')
    db = pgdata.connect(sql_path=sql_path)
    db['preprocessing.temp_slashburn'].drop()
    db.execute("""
        CREATE TABLE preprocessing.temp_slashburn
        (slashburn_id serial primary key,
         grid_id integer,
         dist_type integer,
         year integer)
    """)
    for year in year_range:
        db.execute(db.queries['create_slashburn'], (year, sb_percent))

    sb_shp = os.path.join(os.path.dirname(harvest_shp), "slashburn.shp")
    logging.info('Saving slashburn to {}'.format(sb_shp))
    sql = """
        SELECT
          i.grid_id AS cell_id,
          i.dist_type,
          i.year,
          ST_Union(g.geom) as geom
        FROM preprocessing.temp_slashburn i
        INNER JOIN preprocessing.inventory_grid_xref x
        ON i.grid_id = x.grid_id
        INNER JOIN preprocessing.grid g
        ON x.grid_id = g.grid_id
        WHERE i.year IS NOT NULL
        GROUP BY
          i.grid_id,
          i.dist_type,
          i.year
    """
    # gdal.VectorTranslate option SQLStatement doesn't seem to pick up that we want to
    # use the PG driver's sql - it seems to be using OGRSQL so it throws errors when
    # trying to use ST_Union and similar
    # Lets just create a VRT as as work-around
    out_layer = os.path.splitext(os.path.basename(sb_shp))[0]
    vrtpath = _create_pg_vrt(sql, out_layer)
    gdal.VectorTranslate(
        sb_shp,
        vrtpath,
        accessMode='overwrite')
    return sb_shp


def _create_pg_vrt(sql, out_layer):
    """ Create a quick temp vrt file pointing to layer name, pg connection and query
    """
    pgcred = 'host={h} user={u} dbname={db} password={p}'.format(
        h=os.environ['PGHOST'],
        u=os.environ['PGUSER'],
        db=os.environ['PGDATABASE'],
        p=os.environ['PGPASSWORD'])
    vrt = """<OGRVRTDataSource>
               <OGRVRTLayer name="{layer}">
                 <SrcDataSource>PG:{pgcred}</SrcDataSource>
                 <SrcSQL>{sql}</SrcSQL>
               </OGRVRTLayer>
             </OGRVRTDataSource>
          """.format(layer=out_layer,
                     sql=escape(sql.replace("\n", " ")),
                     pgcred=pgcred)
    vrtpath = os.path.join(tempfile.gettempdir(), "pg_dump.vrt")
    if os.path.exists(vrtpath):
        os.remove(vrtpath)
    with open(vrtpath, "w") as vrtfile:
        vrtfile.write(vrt)
    return vrtpath
