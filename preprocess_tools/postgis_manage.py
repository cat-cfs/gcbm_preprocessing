import logging, os, json, inspect, psycopg2, uuid
from contextlib import contextmanager

def get_connection_variables(var_path):
    with open(var_path) as json_data:
        return json.load(json_data)

def save_connection_variables(var_path, **values):
    with open(var_path, 'w') as outfile:
        json.dump(values, outfile, indent=4)

def load_environment_variables(connectionVariables):
    '''
    Set postgres connection environment variables
    '''
    logging.info("Set postgres connection environment variables")
    os.environ["PGHOST"] = str(connectionVariables["PGHOST"])
    os.environ["PGPORT"] = str(connectionVariables["PGPORT"])
    os.environ["PGDATABASE"] = str(connectionVariables["PGDATABASE"])
    os.environ["PGUSER"] = str(connectionVariables["PGUSER"])
    os.environ["PGPASSWORD"] = str(connectionVariables["PGPASSWORD"])
    os.environ["DATABASE_URL"] = r"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}" \
        .format(PGHOST = os.environ["PGHOST"],
                PGPORT = os.environ["PGPORT"],
                PGDATABASE = os.environ["PGDATABASE"],
                PGUSER = os.environ["PGUSER"],
                PGPASSWORD = os.environ["PGPASSWORD"])

def url_string(**kwargs):
    return r"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}" \
            .format(PGHOST = kwargs["PGHOST"],
                    PGPORT = kwargs["PGPORT"],
                    PGDATABASE = kwargs["PGDATABASE"],
                    PGUSER = kwargs["PGUSER"],
                    PGPASSWORD = kwargs["PGPASSWORD"])

def get_url(**kwargs):
    config = load_connection_variables()
    config.update(kwargs)
    return url_string(**kwargs)

@contextmanager
def connect(**kwargs):
    yield psycopg2.connect(
        dbname = kwargs["PGDATABASE"],
        user = kwargs["PGUSER"],
        password = kwargs["PGPASSWORD"],
        host = kwargs["PGHOST"],
        port = kwargs["PGPORT"])

@contextmanager
def cursor(**kwargs):
    with connect(**kwargs) as connection:
        yield connection.cursor()

def create_postgis_extension(var_path):
    with cursor(get_connection_variables(var_path)) as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")

def drop_preprocessing_schema(var_path):
    with cursor(get_connection_variables(var_path)) as cur:
        cur.execute("DROP SCHEMA IF EXISTS preprocessing CASCADE")

def create_preprocessing_schema(var_path):
    with cursor(get_connection_variables(var_path)) as cur:
        cur.execute("CREATE SCHEMA preprocessing")

def generate_unique_db_name():
    return "gcbm_preprocessing_{}".format(
        uuid.uuid4().bytes
            .encode('base64') # shorten up the uuid
            .rstrip('=\n') # trim off the end bytes
            .replace('/','_') # postgres allows _ but not / in identifiers
            .replace('+','$')) # postgres allows $ but not + in identifiers

def create_database(var_path, dbname):
    with cursor(**get_connection_variables(var_path)) as cur:
        cur.execute("""
            CREATE DATABASE %(dbname)s
            WITH 
            OWNER = postgres
            ENCODING = 'UTF8'
            LC_COLLATE = 'English_Canada.1252'
            LC_CTYPE = 'English_Canada.1252'
            TABLESPACE = pg_default
            CONNECTION LIMIT = -1;
            """, {"dbname": dbname})


