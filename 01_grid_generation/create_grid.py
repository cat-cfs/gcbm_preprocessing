import logging


def fishnet(db, in_table, out_table, resolution=0.001):
    """Create a fishnet of square tiles at given resoulution covering extent of in_layer
    """
    logging.info(
        "Creating fishnet covering {lyr} at resolution {res}".format(
            lyr=in_table, res=resolution
        )
    )

    # make sure output tables do not already exist
    db['public.grid_prelim'].drop()
    db['public.'+out_table].drop()

    # create the fishnet for the entire extent
    db.execute(
        """
        CREATE TABLE public.grid_prelim (
          grid_id SERIAL PRIMARY KEY,
          geom geometry)
        """
    )
    db['public.grid_prelim'].create_index_geom()
    db.execute(
        """
        INSERT INTO public.grid_prelim (geom)
        SELECT ST_Fishnet(ST_Envelope(ST_Collect(geom)), %s, %s) AS geom
        FROM public.{in_table}
        """.format(in_table=in_table),
        (resolution, resolution)
    )
    # retain just the grid cells that actually intersect the input layer
    # ** NOTE **
    # We are using BC Albers projection to calc the area, this should be changed to a
    # Canada wide equal area projection
    db.execute(
        """
        CREATE TABLE public.{out_table} (
          cell_id SERIAL PRIMARY KEY,
          shape_area_ha float,
          geom geometry)
        """.format(out_table=out_table)
    )
    db['public.'+out_table].create_index_geom()
    db.execute(
        """
        INSERT INTO public.{out_table} (shape_area_ha, geom)
        SELECT
          (ST_Area(
            ST_Transform(grid.geom, 3005))
             ) / 10000 AS shape_area_ha,
          grid.geom
        FROM public.grid_prelim grid
        INNER JOIN public.{in_table} aoi
        ON ST_Intersects(grid.geom, aoi.geom)
        """.format(out_table=out_table,
                   in_table=in_table)
    )
    return out_table


def subdivide(db, in_table, out_table):
    # Just in case the source data has very large polygons, subdivide for quick overlays
    # Retain all source columns without listing them by using this terrible hack
    # http://www.postgresonline.com/journal/archives/41-How-to-SELECT-ALL-EXCEPT-some-columns-in-a-table.html
    db['public.aoi_subdivided'].drop()
    sql = """SELECT 'SELECT ' || array_to_string(ARRAY(SELECT 'o' || '.' || c.column_name
              FROM information_schema.columns As c
              WHERE table_name = '{in_table}'
              AND  c.column_name NOT IN('geom')
              ), ',') || ', ST_Subdivide(geom) as geom FROM {in_table} As o' As sqlstmt
           """.format(in_table=in_table)
    sql = db.query(sql).fetchone()[0]
    db.execute("CREATE TABLE public.{out_table} AS "+sql)

    # index the geometry
    db['public.'+out_table].create_index_geom()
