# Amazon QuickSight Dashboard Setup

This document outlines the steps required to configure the Amazon QuickSight dashboard for the Automated Visual Governance & Analytics Dashboard.

## Prerequisites
1. Ensure the Lambda function (`vision_agent.py`) has processed some images, so data exists in your `analytics-results-bucket`.
2. Run the DDL statements from `athena_queries.sql` in **Amazon Athena** to create the `visual_governance_db` and the external tables (`moderation_results`, `label_results`).
3. Have an active Amazon QuickSight Enterprise Edition account.

## Step 1: Connect QuickSight to Athena
1. Go to the AWS Management Console and open **QuickSight**.
2. From the navigation pane, click on **Datasets**.
3. Choose **New Dataset** -> **Athena**.
4. Name the data source `VisualGovernanceSource` and click **Create data source**.
5. Select the database `visual_governance_db`.
6. For the tables, select `moderation_results`. Click **Edit/Preview Data**.
7. In the top toolbar, you can use **Custom SQL** or add the predefined queries from `athena_queries.sql` as Custom SQL queries to build pre-calculated datasets.
8. Save & Publish the Dataset. Repeat the process to create another QuickSight dataset for the `label_results` table.

## Step 2: Build the Required Visuals

Create a **New Analysis** in QuickSight and add the datasets you created. Implement the following visuals:

### 1. Flagged vs Safe Images (Pie Chart)
* **Dataset**: `moderation_results` (or Custom SQL Query A)
* **Visual Type**: Pie Chart
* **Group/Color**: `image_status`
* **Value**: Count of `total_images`
* *Purpose*: Shows the percentage of unsafe vs safe images processed by the system.

### 2. Top Unsafe Categories (Bar Chart)
* **Dataset**: `moderation_results`
* **Visual Type**: Vertical Bar Chart
* **X-Axis**: `label_name`
* **Value**: Count of `image_name`
* **Filter**: Set `label_name` does NOT equal `SAFE`.
* *Purpose*: Shows the most frequent violation category (e.g., Violence, Explicit Nudity).

### 3. Upload Trends Over Time (Line Chart)
* **Dataset**: `label_results`
* **Visual Type**: Line Chart
* **X-Axis**: `timestamp` (Aggregated by Day)
* **Value**: Count distinct of `image_name`
* *Purpose*: Shows trends of system usage over time.

### 4. Average Confidence Score Distribution (Histogram)
* **Dataset**: `moderation_results` / `label_results` combined
* **Visual Type**: Histogram or KPI
* **Value**: `confidence_score` (Average)
* *Purpose*: Shows the average confidence level for detected moderation and object labels.

## Step 3: Publish the Dashboard
1. Arrange the widgets onto a clean, presentation-ready layout.
2. Click **Share** -> **Publish Dashboard**.
3. Name it "Automated Visual Governance & Analytics Dashboard".
4. Share the dashboard with the relevant stakeholders or embed it into a portal.
