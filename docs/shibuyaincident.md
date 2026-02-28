2/27/2026 - the horrors oh god

hey i spend like 4 hours trying to debug something in ingestion I thought was a bug

basically the created_date and closed_date columns were showing the same value for many rows
although they shouldn't be, as it doesn't make sense for a ticket to open and close instantly
so frequently

so much suffering unnecessary suffering

but some might say it was not too bad because we got some very good information from it

# department of buildings incident, 2025-10-31

turns out the same value thing is not a bug (appears in the source). all the records that show this
trait so far have been from DOB, department of buildings:

nyc311_analytics=# SELECT c.unique_key, c.closed_date, c.created_date, c.agency FROM raw.nyc_311_complaints c OR
DER BY c.created_date DESC LIMIT 50;

| unique_key | closed_date         | created_date        | agency |
| ---------- | ------------------- | ------------------- | ------ |
| 42306178   | 2025-10-31 20:44:36 | 2025-10-31 20:44:36 | DOB    |
| 42318606   | 2025-10-31 20:09:23 | 2025-10-31 20:09:23 | DOB    |
| 42306361   | 2025-10-31 20:08:50 | 2025-10-31 20:08:50 | DOB    |
| 42379581   | 2025-10-31 20:06:18 | 2025-10-31 20:06:18 | DOB    |
| 42330767   | 2025-10-31 20:05:39 | 2025-10-31 20:05:39 | DOB    |
| 42368197   | 2025-10-31 20:05:11 | 2025-10-31 20:05:11 | DOB    |
| 42330768   | 2025-10-31 20:04:36 | 2025-10-31 20:04:36 | DOB    |
| 42306283   | 2025-10-31 20:03:22 | 2025-10-31 20:03:22 | DOB    |
| 42379589   | 2025-10-31 19:57:33 | 2025-10-31 19:57:33 | DOB    |
| 42343504   | 2025-10-31 19:56:44 | 2025-10-31 19:56:44 | DOB    |
| 42367401   | 2025-10-31 19:52:59 | 2025-10-31 19:52:59 | DOB    |
| 42380209   | 2025-10-31 19:39:12 | 2025-10-31 19:39:12 | DOB    |
| 42331442   | 2025-10-31 19:38:57 | 2025-10-31 19:38:57 | DOB    |
| 42355204   | 2025-10-31 19:38:15 | 2025-10-31 19:38:15 | DOB    |
| 42355740   | 2025-10-31 19:32:48 | 2025-10-31 19:32:48 | DOB    |
| 42368219   | 2025-10-31 19:29:59 | 2025-10-31 19:29:59 | DOB    |
| 42330833   | 2025-10-31 19:21:49 | 2025-10-31 19:21:49 | DOB    |
| 42343352   | 2025-10-31 19:17:18 | 2025-10-31 19:17:18 | DOB    |
| 42306145   | 2025-10-31 19:17:15 | 2025-10-31 19:17:15 | DOB    |

so it's probably some automated 311 ticket BS and not a bug. at least now we know they exist and can be flagged as such when we find other rows with the same create/closed times

# these unique keys SUCK

apparently they're not entirely in order. basically, don't batch ingestion by unique key, as the created_date values would be all out of wack
not gonna post an example for this because im tired but I can assure you it is 100% true.
I'll need to refactor batching to go by date ranges, which is probably more flexible long term anyways

# your loading strategy maybe isn't the best?

idk, check it out https://www.reddit.com/r/dataengineering/comments/11kdvkr/insert_data_into_db_best_practice/

# TLDR

im tired, gonna get a mickydees ice cream now bye

didn't even get to test my dbt models
