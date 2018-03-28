CREATE TABLE gridded_inventory_lut AS

WITH intersections AS
(SELECT
  f.cell_id,
  f.geom as geom_f,
  i.objectid,
  i.geom as geom_i
FROM fishnet f
INNER JOIN inventory i
ON ST_Intersects(f.geom, i.geom)
WHERE age2015 > 0
ORDER BY cell_id),

count_intersections AS
(SELECT
  cell_id,
  count(*) as n_intersections
FROM intersections
GROUP BY cell_id
ORDER BY cell_id),

largest_overlap AS
(SELECT DISTINCT ON (cell_id)
  i.cell_id,
  i.objectid,
  ST_Area(ST_Intersection(i.geom_f, i.geom_i)) as area
  --ST_Area(ST_Transform(ST_Intersection(i.geom_f, i.geom_i), 3005)) as area
FROM intersections i
INNER JOIN count_intersections c ON i.cell_id = c.cell_id
WHERE c.n_intersections > 1
ORDER BY cell_id asc, area desc)

SELECT cell_id, objectid from largest_overlap
UNION ALL
SELECT i.cell_id, i.objectid
FROM intersections i
INNER JOIN count_intersections c ON i.cell_id = c.cell_id
WHERE c.n_intersections = 1
