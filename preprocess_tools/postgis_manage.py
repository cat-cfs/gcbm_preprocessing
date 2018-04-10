import logging, subprocess, os, json, inspect

def get_connection_variables_path():
    return os.path.join(
        os.path.dirname(inspect.stack()[0][1]),
       "postgis_connnection_variables.json")

def get_connection_variables():
    with open(get_connection_variables_path()) as json_data:
        return json.load(json_data)

def execute(command):
    try:
        logging.info("issuing command: {0}".format(command))
        cmnd_output = subprocess.check_output(command, 
                                                stderr=subprocess.STDOUT,
                                                shell=False, 
                                                universal_newlines=True);
        logging.info("command executed successfully")
    except subprocess.CalledProcessError as cp_ex:
        logging.exception("error occurred running command")
        logging.error(cp_ex.output)
        raise cp_ex
    except Exception as ex:
        logging.exception("error occurred running command")
        raise ex

def save_connection_variables(PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD):
    with open(get_connection_variables_path(), 'w') as outfile:
        values = {
            "PGHOST": PGHOST,
            "PGPORT": PGPORT,
            "PGDATABASE": PGDATABASE,
            "PGUSER": PGUSER,
            "PGPASSWORD": PGPASSWORD
        }
        json.dump(values, outfile, indent=4)

def load_connection_variables():
        '''
        Set postgres connection environment variables
        '''
        logging.info("Set postgres connection variables")
        connectionVariables = get_connection_variables()
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

def create_postgis_extension():
    command = ["psql",
               "-c",
               "CREATE EXTENSION IF NOT EXISTS postgis"]
    execute(command)

def drop_preprocessing_schema():
    command = ["psql",
               "-c",
               "DROP SCHEMA IF EXISTS preprocessing CASCADE"]
    execute(command)

def create_preprocessing_schema():
    command = ["psql",
               "-c",
               "CREATE SCHEMA preprocessing"]
    execute(command)


