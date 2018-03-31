INSERT INTO preprocessing.grid (block_id, shape_area_ha, geom)

WITH cells AS
(SELECT
   ST_Fishnet(ST_Envelope(geom), .001, .001) AS geom
 FROM preprocessing.blocks
 WHERE block_id = %s)

SELECT DISTINCT
   block_id,
   ST_Area(ST_Transform(c.geom, 3005)) / 10000 as area_ha,
   c.geom
FROM cells c
INNER JOIN preprocessing.inventory i
ON ST_Intersects(c.geom, i.geom)
INNER JOIN preprocessing.blocks b
-- small fudge factor for the coveredby
ON ST_CoveredBy(c.geom, ST_Buffer(b.geom, .0002))
WHERE b.block_id = %s