REM -----------------------------------
REM Set postgres connection variables
REM -----------------------------------
SET PGHOST=localhost
SET PGPORT=5432
SET PGDATABASE=BC_GCBM_runs
SET PGUSER=postgres
SET PGPASSWORD=postgres
SET DATABASE_URL=postgresql://%PGUSER%:%PGPASSWORD%@%PGHOST%:%PGPORT%/%PGDATABASE%

REM -----------------------------------
REM Install PostGIS on the database
REM -----------------------------------
psql -c "CREATE EXTENSION IF NOT EXISTS postgis"

REM -----------------------------------
REM Create the preprocessing schema
REM (Note that we drop it first, use this with caution!)
REM -----------------------------------
psql -c "DROP SCHEMA IF EXISTS preprocessing CASCADE"
psql -c "CREATE SCHEMA preprocessing"

REM -----------------------------------
REM Add lostgis functions to database (installing the lostgis extension
REM via https://github.com/pgxn tool does not work on Windows)
REM -----------------------------------
git clone https://github.com/gojuno/lostgis.git
psql -f lostgis\functions\ST_Safe_Difference.sql
psql -f lostgis\functions\ST_Safe_Intersection.sql
psql -f lostgis\functions\ST_Safe_Repair.sql

