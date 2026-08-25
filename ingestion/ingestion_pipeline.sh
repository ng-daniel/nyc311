#!/bin/bash
# run from whatever the project root is

# data API to raw data postgres
source .venv/bin/activate
python ingestion/ingestion.py

if [ $? -ne 0 ]; then
    echo "Ingestion failed"
    deactivate
    exit 1
fi

deactivate

# raw postgres to dbt transformation + validation
docker compose run --rm dbt deps
if [ $? -ne 0 ]; then
    echo "DBT deps failed"
    exit 1
fi

docker compose run --rm dbt build
if [ $? -ne 0 ]; then
    echo "DBT build failed"
    exit 1
fi

docker compose run --rm dbt test
if [ $? -ne 0 ]; then
    echo "DBT test failed"
    exit 1
fi

echo "Ingestion and DBT pipeline completed successfully"
exit 0