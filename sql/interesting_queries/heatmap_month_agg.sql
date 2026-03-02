SELECT d.year, d.month, m.latitude_rounded, m.longitude_rounded, SUM(m.complaint_count) AS total_complaints, AVG(m.avg_resolution_hours) 
FROM marts.fct_311_geo_heatmap m 
INNER JOIN marts.dim_date d 
    ON m.created_date = d.date_day 
GROUP BY d.year, d.month, m.latitude_rounded, m.longitude_rounded 
ORDER BY d.month 
LIMIT 100;