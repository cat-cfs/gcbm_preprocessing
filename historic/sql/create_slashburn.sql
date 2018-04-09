INSERT INTO preprocessing.temp_slashburn (grid_id, dist_type, year)

-- Select the year so that we can take receive year argument just once and
-- use it several times
WITH year AS
(
  SELECT %s as year
),

-- select all potential harvest records for given year, in random order,
-- then give each result a row number so that we can select just the number needed
shuffled AS
(
  SELECT
    row_number() over() AS n,
    grid_id
  FROM
    ( SELECT grid_id
      FROM preprocessing.inventory_rollback,
      year y
      WHERE dist_type = 2 AND new_disturbance_yr = y.year
      ORDER BY random()
    ) AS harv
),

-- How many cells to extract from total shuffled is determined by the
-- slashburn percentage
sample_size AS
(
  SELECT
    round((count(*) * %s) / 100) AS n
  FROM shuffled
)

-- select grid cells with row number less than or equal to the sample size
-- and provide a disturbance type (always 13 for slashburn)
SELECT
  grid_id, 13, year.year
FROM shuffled, sample_size, year
WHERE shuffled.n <= sample_size.n

