# 🚀 Deployment Guide: Automated Visual Governance

This guide provides a detailed, step-by-step walkthrough to deploy your "Visual Governance" system from scratch to AWS.

## 📋 Prerequisites
Before you start, make sure you have these installed on your computer:
1. **Node.js**: [Download here](https://nodejs.org/) (Required for AWS CDK).
2. **Python 3.9+**: [Download here](https://www.python.org/).
3. **AWS CLI**: [Download here](https://aws.amazon.com/cli/).

---

## 🛠️ Step 1: AWS Account Setup
You need to tell your computer who you are in AWS.

1. Open your Command Prompt (CMD) or PowerShell.
2. Type: `aws configure`
3. Enter your:
   - **AWS Access Key ID**
   - **AWS Secret Access Key**
   - **Default region name**: `us-east-1`
   - **Default output format**: `json`

---

## 🏗️ Step 2: Deploy Cloud Infrastructure (CDK)
This step creates your S3 Buckets, the Lambda Robot, and the AI permissions.

1. Open a terminal in the project folder.
2. Install the AWS CDK tool:
   ```bash
   npm install -g aws-cdk
   ```
3. Prepare your AWS account for CDK (only do this once):
   ```bash
   cdk bootstrap
   ```
4. Deploy everything:
   ```bash
   cd infrastructure
   ```
   *Wait for it to finish. It will give you the names of your new S3 buckets!*

---

## 📚 Step 3: Setup the Librarian (Athena)
Now we must tell Athena how to read the AI's notes in S3.

1. Go to the [AWS Athena Console](https://console.aws.amazon.com/athena/).
2. Click on **Query Editor**.
3. Open the file `infrastructure/athena_queries.sql` in your project.
4. **Run the queries in order**:
   - **Query 1**: Creates the `visual_governance_db`.
   - **Query 2**: Creates the `moderation_results` table.
   - **Query 3**: Creates the `label_results` table.
   - **Query 4**: Runs `MSCK REPAIR TABLE` to find your data.

---

## 🖥️ Step 4: Launch the Dashboard (Streamlit)
Finally, start your visual interface.

1. Open a terminal in the project root folder.
2. Install the Python requirements:
   ```bash
   pip install streamlit pandas boto3 plotly
   ```
3. Run the dashboard:
   ```bash
   streamlit run src/dashboard/app.py
   ```
4. **Configuration in Sidebar**:
   - Enter your **Athena Database** name.
   - Enter your **S3 Output Path** (e.g., `s3://your-analytics-bucket/athena-results/`).
   - Click **Refresh Data**!

---

## ✅ Step 5: Final Test
1. Go to the **Real-time Analysis** tab in your dashboard.
2. Upload a test image.
3. Click **Start Deep Analysis**.
4. Check if the **Global Analytics** tab updates with your new data! 🛡️📊
