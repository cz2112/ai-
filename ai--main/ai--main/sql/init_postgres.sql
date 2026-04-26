-- Run with:
--   psql -U postgres -f sql/init_postgres.sql
--
-- This script creates the local PostgreSQL role and database expected by the
-- application defaults. It is intended for psql because it uses \gexec.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'studyapp'
    ) THEN
        CREATE ROLE studyapp LOGIN PASSWORD 'studyapp123';
    END IF;
END
$$;

SELECT 'CREATE DATABASE smart_study OWNER studyapp'
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'smart_study'
)\gexec

GRANT ALL PRIVILEGES ON DATABASE smart_study TO studyapp;

\connect smart_study

ALTER SCHEMA public OWNER TO studyapp;
GRANT ALL ON SCHEMA public TO studyapp;
