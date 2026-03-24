# 📊 Streamlit Setup Guide: Visual Governance Dashboard

Follow these steps to run your Visual Governance Dashboard locally as a student-friendly alternative to QuickSight.

## Prerequisites
- **Python 3.8+** installed.
- **AWS CLI** configured with credentials that have Athena and S3 permissions.
- **Athena Database**: Ensure you have run the DDL in `infrastructure/athena_queries.sql`.

## Step 1: Install Dependencies
Open your terminal in the project root and run:
```bash
pip install streamlit pandas boto3 plotly
```

## Step 2: Configure AWS Permissions
Ensure your IAM user/role has:
1. `athena:StartQueryExecution`
2. `athena:GetQueryResults`
3. `athena:GetQueryExecution`
4. `s3:GetBucketLocation`
5. `s3:GetObject` (on the Analytics bucket)
6. `s3:PutObject` (on your Athena query output bucket)

## Step 3: Run the Dashboard
Navigate to the project root and execute:
```bash
streamlit run src/dashboard/app.py
```

## Step 4: Using the Dashboard
1. **Mock Data Mode**: If you haven't set up AWS yet, leave the "Query Output Bucket" empty to see how the dashboard looks with generated data.
2. **Live Data Mode**: 
   - Enter your **Athena Database** name (default: `visual_governance_db`).
   - Enter an **S3 Path** for Athena to store temporary query results (e.g., `s3://your-bucket-name/athena-results/`).
   - Use the **Date Filters** in the sidebar to narrow down insights.
   - Click **Refresh Data** to pull latest results from S3.

## Why Streamlit?
- **Zero Cost**: Running locally is free. Free hosting is available via Streamlit Cloud.
- **Python-Native**: No need to learn complex BI tools; just use the Python skills you already have.
- **Highly Customizable**: Easily add new charts or filters using Plotly and Pandas.
