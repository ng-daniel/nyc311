3/1/26 - testing batch performance

parameters

- start date: 1/1/26
- end date: 2/28/26

### 1K batch size

```
INFO:root:1000 rows (Session: 660000). Latest: 2026-02-26 18:32:26 68137710. Time: 0.58s (Session: 498.68s, Avg: 0.76s)
INFO:root:1000 rows (Session: 661000). Latest: 2026-02-26 20:37:27 68140264. Time: 0.56s (Session: 499.24s, Avg: 0.76s)
INFO:root:1000 rows (Session: 662000). Latest: 2026-02-26 22:41:52 68141500. Time: 0.50s (Session: 499.74s, Avg: 0.75s)
INFO:root:1000 rows (Session: 663000). Latest: 2026-02-27 02:17:05 68145795. Time: 0.49s (Session: 500.23s, Avg: 0.75s)
INFO:root:1000 rows (Session: 664000). Latest: 2026-02-27 07:24:54 68153650. Time: 0.50s (Session: 500.73s, Avg: 0.75s)
INFO:root:1000 rows (Session: 665000). Latest: 2026-02-27 09:02:00 68148629. Time: 0.48s (Session: 501.21s, Avg: 0.75s)
INFO:root:1000 rows (Session: 666000). Latest: 2026-02-27 10:29:28 68155739. Time: 0.44s (Session: 501.66s, Avg: 0.75s)
INFO:root:1000 rows (Session: 667000). Latest: 2026-02-27 12:12:20 68155107. Time: 0.45s (Session: 502.11s, Avg: 0.75s)
INFO:root:1000 rows (Session: 668000). Latest: 2026-02-27 13:44:51 68154208. Time: 0.74s (Session: 502.85s, Avg: 0.75s)
INFO:root:1000 rows (Session: 669000). Latest: 2026-02-27 15:15:05 68151969. Time: 0.79s (Session: 503.64s, Avg: 0.75s)
Traceback (most recent call last):
  File "C:\Users\ng17d\Desktop\Notebooks\nyc311\ingestion\ingestion.py", line 414, in <module>
    ingestion.run_ingest_pipeline(start_date=start_date)
  File "C:\Users\ng17d\Desktop\Notebooks\nyc311\ingestion\ingestion.py", line 340, in run_ingest_pipeline
    data = self.extract_batch(self.batch_size, last_created_date=last_date, last_unique_key=last_key)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\ng17d\Desktop\Notebooks\nyc311\ingestion\ingestion.py", line 164, in extract_batch
    response.raise_for_status()
  File "C:\Users\ng17d\Desktop\Notebooks\nyc311\.venv\Lib\site-packages\requests\models.py", line 1026, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 500 Server Error: Server Error for url: https://data.cityofnewyork.us/resource/erm2-nwe9.json?%24order=created_date+ASC%2C+unique_key+ASC&%24select=%2A&%24where=created_date+%3E+%272026-02-27T15%3A15%3A05.000%27&%24limit=999
```

literally encountered a serverside error before it could finish... nothing wrong with the URL, pasted it into browser and it worked

### 10K batch size

last 10 rows

```
INFO:root:10000 rows (Session: 590000). Latest: 2026-02-22 00:44:48 68066878. Time: 5.57s (Session: 248.78s, Avg: 4.22s)
INFO:root:10000 rows (Session: 600000). Latest: 2026-02-23 08:07:18 68080455. Time: 4.89s (Session: 253.67s, Avg: 4.23s)
INFO:root:10000 rows (Session: 610000). Latest: 2026-02-23 19:27:06 68082304. Time: 5.28s (Session: 258.95s, Avg: 4.25s)
INFO:root:10000 rows (Session: 620000). Latest: 2026-02-24 09:16:36 68116259. Time: 4.81s (Session: 263.76s, Avg: 4.25s)
INFO:root:10000 rows (Session: 630000). Latest: 2026-02-24 16:20:26 68111708. Time: 6.04s (Session: 269.80s, Avg: 4.28s)
INFO:root:10000 rows (Session: 640000). Latest: 2026-02-25 09:23:11 68128509. Time: 5.15s (Session: 274.95s, Avg: 4.30s)
INFO:root:10000 rows (Session: 650000). Latest: 2026-02-25 23:03:16 68125906. Time: 5.18s (Session: 280.13s, Avg: 4.31s)
INFO:root:10000 rows (Session: 660000). Latest: 2026-02-26 18:32:26 68137710. Time: 4.90s (Session: 285.04s, Avg: 4.32s)
INFO:root:10000 rows (Session: 670000). Latest: 2026-02-27 16:45:15 68155291. Time: 3.16s (Session: 288.20s, Avg: 4.30s)
INFO:root:3960 rows (Session: 673960). Latest: 2026-02-28 03:04:45 68152447. Time: 1.10s (Session: 289.29s, Avg: 4.25s)
INFO:root:No more rows to ingest.
```

### 100K batch size

small enough number of batches that I can just post the whole thing

```
INFO:root:Starting ingestion at provided start_date: 2026-01-01 00:00:00.
INFO:root:100000 rows (Session: 100000). Latest: 2026-01-11 11:11:00 67459402. Time: 44.18s (Session: 44.18s, Avg: 44.18s)
INFO:root:100000 rows (Session: 200000). Latest: 2026-01-21 12:32:22 67564207. Time: 42.72s (Session: 86.91s, Avg: 43.45s)
INFO:root:100000 rows (Session: 300000). Latest: 2026-01-28 17:02:44 67656343. Time: 46.14s (Session: 133.05s, Avg: 44.35s)
INFO:root:100000 rows (Session: 400000). Latest: 2026-02-04 17:57:23 67855944. Time: 50.66s (Session: 183.71s, Avg: 45.93s)
INFO:root:100000 rows (Session: 500000). Latest: 2026-02-12 20:36:28 67973013. Time: 38.89s (Session: 222.60s, Avg: 44.52s)
INFO:root:100000 rows (Session: 600000). Latest: 2026-02-23 08:07:18 68080455. Time: 27.42s (Session: 250.02s, Avg: 41.67s)
INFO:root:73960 rows (Session: 673960). Latest: 2026-02-28 03:04:45 68152447. Time: 14.94s (Session: 264.96s, Avg: 37.85s)
INFO:root:No more rows to ingest.
```

## conclusions

seems like 100K is a good place to be, since improvements are much less noticable from 10K to 100K compared with 1K to 10K.

might need to rebenckmark on more data to compare 100K with higher batch sizes depending on how much data I want in this dashboard
