#!/bin/bash

# Load environment variables
source .env

echo "Creating table in PostgreSQL master..."
PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -p $PG_WRITE_PORT -U $PG_USER -d $PG_DATABASE -f Discord_Bot/create_table.sql

echo "Table creation complete!"
