WITH gridded_inventory AS
(SELECT g.grid_id, i.age2015, g.geom
FROM preprocessing.grid g
INNER JOIN preprocessing.inventory_grid_xref x
ON g.grid_id = x.grid_id
INNER JOIN preprocessing.inventory i
ON x.objectid = i.objectid
WHERE i.age2015 < (2015 - 1990))

disturbances AS
(SELECT *
 FROM preprocessing.disturbances
 WHERE year < 2015)


