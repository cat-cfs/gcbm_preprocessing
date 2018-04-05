INSERT INTO preprocessing.disturbances_grid_xref (grid_id, disturbance_id)

WITH intersections AS
(SELECT
  g.grid_id,
  g.geom as geom_f,
  d.disturbance_id,
  d.geom as geom_d
FROM preprocessing.grid g
INNER JOIN preprocessing.rollback_disturbances d
ON ST_Intersects(g.geom, d.geom)
WHERE g.block_id = %s
ORDER BY grid_id),

count_intersections AS
(SELECT
  grid_id,
  count(*) as n_intersections
FROM intersections
GROUP BY grid_id
ORDER BY grid_id),

largest_overlap AS
(SELECT DISTINCT ON (grid_id)
  i.grid_id,
  i.disturbance_id,
  ST_Area(ST_Intersection(i.geom_f, i.geom_d)) as area
  --ST_Area(ST_Transform(ST_Intersection(i.geom_f, i.geom_i), 3005)) as area
FROM intersections i
INNER JOIN count_intersections c ON i.grid_id = c.grid_id
WHERE c.n_intersections > 1
ORDER BY grid_id asc, area desc)

SELECT grid_id, disturbance_id
FROM largest_overlap
UNION ALL
SELECT i.grid_id, i.disturbance_id
FROM intersections i
INNER JOIN count_intersections c ON i.grid_id = c.grid_id
WHERE c.n_intersections = 1
