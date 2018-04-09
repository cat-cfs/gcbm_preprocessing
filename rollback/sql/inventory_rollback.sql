CREATE TABLE preprocessing.inventory_rollback AS

-- Select the entire inventory grid, with age
WITH inventory_gridded AS
(SELECT
  g.grid_id,
  i.age
FROM preprocessing.grid g
INNER JOIN preprocessing.inventory_grid_xref x
ON g.grid_id = x.grid_id
INNER JOIN preprocessing.inventory i
ON x.inventory_id = i.inventory_id)

-- Join gridded inventory to disturbed inventory to get disturbed rollback ages.
-- For cells when there is no disturbance, set:
--   rollback age =  age - (vintage - rollback start)
--   regen delay = 0
SELECT
  ig.grid_id,
  ig.age as inv_age,
  d.dist_year,
  d.establishment_date,
  d.dist_date_diff,
  d.dist_type,
  d.new_disturbance_yr,
  d.pre_dist_age,
  CASE
    WHEN d.rollback_age IS NULL THEN ig.age - (%s - %s)
    ELSE d.rollback_age
  END as rollback_age,
  CASE
    WHEN d.regen_delay IS NULL THEN 0
    ELSE d.regen_delay
  END as regen_delay
FROM inventory_gridded ig
LEFT OUTER JOIN preprocessing.inventory_disturbed as d
ON ig.grid_id = d.grid_id
