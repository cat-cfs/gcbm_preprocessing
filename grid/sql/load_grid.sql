INSERT INTO preprocessing.grid (block_id, shape_area_ha, geom)

WITH cells AS
(SELECT
   ST_Fishnet(ST_SetSRID(ST_Extent(geom), 4326), $x_res, $y_res) AS geom
 FROM preprocessing.blocks
 WHERE block_id = %s)

SELECT DISTINCT
   block_id,
   -- Calculate area using Canada Albers
   ST_Area(ST_Transform(c.geom, 102001)) / 10000 as shape_area_ha,
   c.geom
FROM cells c
INNER JOIN preprocessing.inventory i
ON ST_Area(ST_Transform(ST_Intersection(c.geom, i.geom), 102001)) > 100
INNER JOIN preprocessing.blocks b
-- * note *
-- Because ST_Fishnet produces cells outside of the block (along the edges),
-- we only insert grid cells covered by the block. But, to make the coveredby
-- condition work along edges, we apply a small (resolution dependent) fudge
-- factor to ensure all cells are covered by the block. Modify this factor
-- to something under 1/2 of resolution if changing resolution.
ON ST_CoveredBy(c.geom, ST_Buffer(b.geom, .0002))
WHERE b.block_id = %s