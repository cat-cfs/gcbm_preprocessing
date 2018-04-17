-- tl;dr assigning disturbances to a grid cell is quick and dirty

-- Whichever individual record has the maximum area within the cell gets assigned to
-- that cell. In the event that several small records in the cell with the same
-- disturbance year add up to more area than the max size disturbance, the cell still
-- gets the year value from the max size record. Also, there is no accounting for
-- overlaps - the largest record gets assigned to the cell regardless of what year
-- the disturbance occured. Where areas are equal (common in areas of large
-- disturbances covering an entire cell) the disturbance assigned to the grid cell is
-- random (or perhaps determined by order of insertion when merging disturbances)

-- Note that there is also no minimum size intersection required for a cell to be
-- considered disturbed - with any intersection of a disturbance with a grid cell, the
-- cell is considered disturbed

-- It is possible to aggregate the disturbances by year and assign the year with
-- the maximum area to the cell (and also get a preferred year value when areas for
-- different years are equal) but I'm not sure if this output is what is required
-- in subsequent steps, we may need to tie back to the individual disturbance_id

-- However - when we later intersect inventory with disturbances, we throw out disturbed
-- cells if the inventory age is > disturbance data (eg, if inventory says cell is 80 but
-- disturbance says there was a fire 5 years ago, the cell is not considered disturbed).
-- This corrects for the methods noted above.

-- Note also that we are assigning disturbances to the *inventory* grid - if a
-- disturbance occurs outside of a cell that is non-inventory, it is not retained

INSERT INTO preprocessing.disturbances_grid_xref (grid_id, disturbance_id)

WITH intersections AS
(SELECT
  g.grid_id,
  g.geom as geom_f,
  d.disturbance_id,
  d.geom as geom_d
FROM preprocessing.grid g
INNER JOIN preprocessing.disturbances d
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
  ST_Area(ST_Safe_Intersection(i.geom_f, i.geom_d)) as area
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
