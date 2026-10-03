-- SQL Queries used to produce reports/facts.json
-- Generated on: 2026-10-03T21:14:58.154864+00:00

-- [sample_count]
SELECT COUNT(*) FROM water_samples;

-- [reading_count]
SELECT COUNT(*) FROM readings;

-- [historical_event_count]
SELECT COUNT(*) FROM historical_contamination;

-- [historical_distinct_villages]
SELECT COUNT(DISTINCT village_id) FROM historical_contamination;

-- [band_counts]
SELECT band, COUNT(*) 
        FROM risk_scores 
        GROUP BY band 
        ORDER BY CASE band 
            WHEN 'Critical' THEN 1 
            WHEN 'High' THEN 2 
            WHEN 'Medium' THEN 3 
            WHEN 'Low' THEN 4 
            ELSE 5 END;

-- [state_metrics]
SELECT s.name AS state, COUNT(rs.id) AS samples, ROUND(AVG(rs.score)::numeric, 2) AS mean_crs
        FROM risk_scores rs
        JOIN water_samples ws ON rs.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        GROUP BY s.name
        ORDER BY s.name;

-- [top_districts_by_mean_crs]
SELECT d.name AS district, s.name AS state, COUNT(rs.id) AS samples, ROUND(AVG(rs.score)::numeric, 2) AS mean_crs
        FROM risk_scores rs
        JOIN water_samples ws ON rs.sample_id = ws.id
        JOIN villages v ON ws.village_id = v.id
        JOIN districts d ON v.district_id = d.id
        JOIN states s ON d.state_id = s.id
        GROUP BY d.name, s.name
        ORDER BY mean_crs DESC
        LIMIT 10;

-- [top_parameters_by_exceedance]
SELECT r.parameter_key, COUNT(*) AS exceedances
        FROM readings r
        JOIN bis_parameters bp ON r.parameter_key = bp.key
        WHERE (bp.strategy != 'range' AND r.value > bp.acceptable_limit)
           OR (bp.strategy = 'range' AND (r.value < bp.acceptable_limit OR r.value > bp.permissible_limit))
        GROUP BY r.parameter_key
        ORDER BY exceedances DESC;

