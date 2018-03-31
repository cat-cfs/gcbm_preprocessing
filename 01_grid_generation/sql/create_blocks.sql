--- Create .1 degree block cells covering inventory

CREATE TABLE preprocessing.blocks
(block_id SERIAL PRIMARY KEY,
 geom geometry (POLYGON, 4326));


INSERT INTO preprocessing.blocks (geom)

WITH blocks AS
(SELECT
   ST_Fishnet(ST_Envelope(ST_Collect(geom)), .1, .1) AS geom
 FROM preprocessing.inventory)

SELECT DISTINCT
   b.geom
FROM blocks b
INNER JOIN preprocessing.inventory i
ON ST_Intersects(b.geom, i.geom);