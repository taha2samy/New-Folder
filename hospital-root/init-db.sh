#!/bin/bash
set -e

function create_database() {
	local database=$1
	local exists=$(psql -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$database'")
	if [ "$exists" != "1" ]; then
		psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
			CREATE DATABASE $database;
EOSQL
	fi
}

databases=(
	"patient_db"
	"clinical_db"
	"pharmacy_db"
	"aggregator_db"
	"laboratory_db"
	"reference_db"
	"keycloak_db"
	"billing_db"
)

for db in "${databases[@]}"; do
	create_database $db
done