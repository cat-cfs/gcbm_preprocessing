import os
import logging
import inspect

import pgdata


def intersect_disturbances_inventory(
        inventory_workspace,
        inventory_year,
        inventory_field_names,
        rollback_start
):
    logging.info("Intersecting rollback disturbances and inventory")
    # point to the sql folder within rollback module and run the query
    sql_path = os.path.join(os.path.dirname(inspect.stack()[0][1]), 'sql')
    db = pgdata.connect(sql_path=sql_path)
    db['preprocessing.inventory_disturbed'].drop()
    db.execute(db.queries['intersect_disturbances_inventory'],
               (inventory_year, rollback_start))
