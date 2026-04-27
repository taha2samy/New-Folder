#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE DATABASE patient_db;
	CREATE DATABASE clinical_db;
	CREATE DATABASE pharmacy_db;
	CREATE DATABASE aggregator_db;
	CREATE DATABASE laboratory_db;
	CREATE DATABASE keycloak_db;
	CREATE DATABASE billing_db;
	CREATE DATABASE master_data_db;
EOSQL