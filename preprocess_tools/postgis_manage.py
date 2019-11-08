import logging, os, json, inspect, psycopg2, uuid
from psycopg2.extensions import AsIs
from contextlib import contextmanager

def get_connection_variables(var_path):
    with open(var_path) as json_data:
        return json.load(json_data)

def save_connection_variables(var_path, **values):
    with open(var_path, 'w') as outfile:
        json.dump(values, outfile, indent=4)

def get_gdal_conn_string(var_path):
    vars = get_connection_variables(var_path)
    return "PG:host='{h}' port='{p}' dbname='{db}' user='{usr}' password='{pwd}'".format(
            h=vars['PGHOST'],
            p=vars['PGPORT'],
            db=vars['PGDATABASE'],
            usr=vars['PGUSER'],
            pwd=vars['PGPASSWORD'])

def url_string(**kwargs):
    return r"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}" \
            .format(PGHOST = kwargs["PGHOST"],
                    PGPORT = kwargs["PGPORT"],
                    PGDATABASE = kwargs["PGDATABASE"],
                    PGUSER = kwargs["PGUSER"],
                    PGPASSWORD = kwargs["PGPASSWORD"])

def get_url(var_path):
    return url_string(**get_connection_variables(var_path))

@contextmanager
def connect(**kwargs):
    conn = psycopg2.connect(
        dbname = kwargs["PGDATABASE"],
        user = kwargs["PGUSER"],
        password = kwargs["PGPASSWORD"],
        host = kwargs["PGHOST"],
        port = kwargs["PGPORT"])
    yield conn

@contextmanager
def cursor(**kwargs):
    with connect(**kwargs) as connection:
        yield connection.cursor()
        connection.commit()

def create_postgis_extension(var_path):
    logging.info("enable postgis")
    with cursor(**get_connection_variables(var_path)) as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")

def drop_preprocessing_schema(var_path):
    with cursor(**get_connection_variables(var_path)) as cur:
        cur.execute("DROP SCHEMA IF EXISTS preprocessing CASCADE")

def create_preprocessing_schema(var_path):
    logging.info("creating preprocessing schema")
    with cursor(**get_connection_variables(var_path)) as cur:
        cur.execute("CREATE SCHEMA preprocessing")

def get_db_name_prefix():
    return "gcbm_preprocessing"

def generate_unique_db_name():
    return "{prefix}_{uuid}".format(
        prefix = get_db_name_prefix(),
        uuid = uuid.uuid4().bytes
            .encode('base64') # shorten up the uuid
            .rstrip('=\n') # trim off the end bytes
            .replace('/','_') # postgres allows _ but not / in identifiers
            .replace('+','$')) # postgres allows $ but not + in identifiers

def create_database(var_path, dbname):

    with connect(**get_connection_variables(var_path)) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("""
                CREATE DATABASE "%s"
                WITH 
                OWNER = postgres
                ENCODING = 'UTF8'
                TABLESPACE = pg_default
                CONNECTION LIMIT = -1;
                """, (AsIs(dbname),))

def drop_database(var_path, dbname):
    vars = get_connection_variables(var_path)
    if dbname.lower().strip() == "postgres":
        raise ValueError("cannot delete database 'postgres'")
    if not dbname.lower().startswith(get_db_name_prefix().lower()):
        raise ValueError("cannot delete database '{}'".format(vars["PGDATABASE"]))
    with connect(**vars) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("""UPDATE pg_database SET datallowconn = 'false' WHERE datname = '%s' """, (AsIs(dbname),))
            cur.execute("""SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '%s' """, (AsIs(dbname),))
            cur.execute("""DROP DATABASE IF EXISTS "%s" """, (AsIs(dbname),))

def drop_working_db(root_postgis_var_path, region_postgis_var_path):
    if os.path.exists(region_postgis_var_path):
        drop_db_name = get_connection_variables(region_postgis_var_path)["PGDATABASE"]
        logging.info("dropping working db '{}'".format(drop_db_name))
        drop_database(root_postgis_var_path, drop_db_name)

def set_up_working_db(root_postgis_var_path, region_postgis_var_path, sql_files):

    drop_working_db(root_postgis_var_path, region_postgis_var_path)

    root_postgis_vars = get_connection_variables(
        root_postgis_var_path)

    region_postgis_vars = root_postgis_vars.copy()

    region_postgis_vars["PGDATABASE"] = generate_unique_db_name()
    save_connection_variables(
        region_postgis_var_path,
        **region_postgis_vars)
    logging.info("creating working db '{}'".format(region_postgis_vars["PGDATABASE"]))
    create_database(root_postgis_var_path, region_postgis_vars["PGDATABASE"])
    
    create_preprocessing_schema(region_postgis_var_path)
    create_postgis_extension(region_postgis_var_path)

    if sql_files:
        with cursor(**region_postgis_vars) as cur:
            for f in sql_files:
                with open(f, 'r') as sqlFile:
                    fileQuery = sqlFile.read()
                    logging.info("running query {} on working db".format(f))
                    cur.execute(fileQuery)

    return url_string(**region_postgis_vars)


