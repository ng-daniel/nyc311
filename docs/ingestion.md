# Ingestion Layer

```
+---ingestion
|       ingestion.py
```

currently just a single python script, might refactor things and modularize
some stuff if I plan on adding additional data sources

running python ingestion/ingestion.py should do the trick

pulls from the nyc open data 311 2020-present API, starts at whatever start
date is specified in the script (leaving it empty makes it start at the oldest date)

## Features

- Pulls the data, normalizes it to expected columns, and drops it into a raw SQL table

- Requests data in fixed-size batches, makes two requests per batch to optimize the socrata QL performance

- Handles query timeouts, implements exponential backoff retry logic

- Enforces idempotency through duplicate unique key checking via temp tables

- Maintains a metadata table to keep track of the most recent pulled data for efficient incremental updates
