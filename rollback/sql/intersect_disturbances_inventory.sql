-- Create a date lookup so we only pass the inv_year and rollback_start values to the
-- query once
WITH
dates AS
(
  SELECT
  %s AS inv_year,
  %s AS rollback_start
),

-- Select only inventory cells where age is less than the rollback period
-- (inventory age - minus year of rollback start)
rollback_inventory AS
(
  SELECT g.grid_id, i.age, g.geom
  FROM preprocessing.grid g
  INNER JOIN preprocessing.inventory_grid_xref x
  ON g.grid_id = x.grid_id
  INNER JOIN preprocessing.inventory i
  ON x.inventory_id = i.inventory_id
  CROSS JOIN dates dt
  WHERE i.age < (dt.inv_year - dt.rollback_start)
),

-- Select only disturbances that occur before the inventory vintage
-- (disturbance year < inventory vintage)
gridded_disturbances AS
(
  SELECT g.grid_id, d.year as dist_year, d.dist_type, g.geom
  FROM preprocessing.grid g
  INNER JOIN preprocessing.disturbances_grid_xref x
  ON g.grid_id = x.grid_id
  INNER JOIN preprocessing.disturbances d
  ON x.disturbance_id = d.disturbance_id
  CROSS JOIN dates dt
  WHERE d.year < dt.inv_year
)

-- For all inventory to be rolled back, calculate output inventory columns that do not
-- depend on random assignment of pre_dist_age
SELECT
  i.grid_id,
  i.age,
  d.dist_year,
  -- stand establishment date: simply inventory date minus age
  dt.inv_year - i.age AS establishment_date,
  CASE
    WHEN d.dist_year IS NOT NULL THEN (dt.inv_year - i.age) - d.dist_year
    ELSE 0
  END AS dist_date_diff,
  -- disturbance type : taken directly from the input disturbances
  CASE
    WHEN d.dist_type = 'Wild Fires' THEN 1
    WHEN d.dist_type = 'Clearcut harvesting with salvage' THEN 2
  END as dist_type,
  -- regen delay :
  -- if there is a disturbance, and establishment date minus disturbance year is > 0,
  -- regen delay is establisment date minus disturbance year
  CASE
    WHEN d.dist_year IS NOT NULL AND (dt.inv_year - i.age) - d.dist_year > 0
      THEN (dt.inv_year - i.age) - d.dist_year
    ELSE 0
  END AS regen_delay,
  -- disturbance date :
  -- if there is a disturbance, and establishment date minus disturbance year is > 0,
  -- set the new disturbance year to the year of the disturbance
  -- Otherwise, disturbance date is the same as establishment date
  CASE
    WHEN d.dist_year IS NOT NULL AND (dt.inv_year - i.age) - d.dist_year > 0
      THEN d.dist_year
    ELSE dt.inv_year - i.age
  END AS new_disturbance_yr,
  0 AS pre_dist_age, -- populate this in separate script
  0 AS rollback_age  -- populate this in separate script
FROM rollback_inventory i
LEFT OUTER JOIN gridded_disturbances d
ON i.grid_id = d.grid_id
CROSS JOIN dates as dt
