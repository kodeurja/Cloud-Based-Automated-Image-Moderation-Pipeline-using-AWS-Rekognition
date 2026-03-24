-- =====================================================================
-- ATHENA DDL EXAMPLES
-- Replace 'your-analytics-bucket-name' with the actual S3 bucket name.
-- =====================================================================

-- 1. Create Database for our visual governance datasets
CREATE DATABASE IF NOT EXISTS visual_governance_db;

-- 2. Create the Moderation Results Table
CREATE EXTERNAL TABLE IF NOT EXISTS visual_governance_db.moderation_results (
    image_name STRING,
    label_type STRING,
    label_name STRING,
    confidence_score DOUBLE,
    `timestamp` TIMESTAMP
)
PARTITIONED BY (year string, month string, day string)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
ESCAPED BY '\\'
LINES TERMINATED BY '\n'
LOCATION 's3://visual-governance-analytics-urja/moderation-results/'
TBLPROPERTIES ('skip.header.line.count'='1');


-- 3. Create the General Label Results Table
CREATE EXTERNAL TABLE IF NOT EXISTS visual_governance_db.label_results (
    image_name STRING,
    label_type STRING,
    label_name STRING,
    confidence_score DOUBLE,
    `timestamp` TIMESTAMP
)
PARTITIONED BY (year string, month string, day string)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
ESCAPED BY '\\'
LINES TERMINATED BY '\n'
LOCATION 's3://visual-governance-analytics-urja/label-results/'
TBLPROPERTIES ('skip.header.line.count'='1');


-- =====================================================================
-- REQUIRED ANALYTICS QUERIES FOR QUICKSIGHT DASHBOARD
-- =====================================================================

-- A) Flagged vs Safe Images (Count of unsafe images vs safe images)
-- This query helps build the 'Flagged vs Safe Images (Pie Chart)'
SELECT 
    CASE WHEN label_name = 'SAFE' THEN 'Safe' ELSE 'Flagged/Unsafe' END AS image_status,
    COUNT(DISTINCT image_name) AS total_images
FROM visual_governance_db.moderation_results
GROUP BY 1;

-- B) Top Regulated/Unsafe Categories (Bar Chart)
-- Shows most frequent violation categories
SELECT 
    label_name AS category,
    COUNT(*) AS flagged_count
FROM visual_governance_db.moderation_results
WHERE label_name != 'SAFE'
GROUP BY label_name
ORDER BY flagged_count DESC;

-- C) General Label Distribution (Bar/Tree Map)
-- Shows what objects/labels are most common
SELECT 
    label_name, 
    COUNT(*) AS label_frequency 
FROM visual_governance_db.label_results 
GROUP BY label_name 
ORDER BY label_frequency DESC 
LIMIT 20;

-- D) Time-based Upload Trends (Line Chart)
-- Shows trends of uploads over time (by date)
SELECT 
    DATE(`timestamp`) AS upload_date,
    COUNT(DISTINCT image_name) AS total_images_uploaded
FROM visual_governance_db.label_results
GROUP BY 1
ORDER BY 1 ASC;

-- E) Average Confidence Score Distribution (Histogram / KPI)
-- Shows average confidence score of both moderation and general labels
SELECT 
    'Moderation' AS detection_type,
    AVG(confidence_score) AS avg_confidence
FROM visual_governance_db.moderation_results
WHERE label_name != 'SAFE'

UNION ALL

SELECT 
    'Object Labels' AS detection_type,
    AVG(confidence_score) AS avg_confidence
FROM visual_governance_db.label_results;
