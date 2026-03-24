# Automated Visual Governance & Analytics Dashboard

## Project Setup

This project deploys an automated image moderation pipeline using **AWS Lambda**, **Amazon S3**, **Amazon Rekognition**, and **Amazon QuickSight**.

### Architecture
1. **Raw S3 Bucket**: Images are uploaded here.
2. **Vision Agent (Lambda)**: Triggered by S3. Calls Amazon Rekognition for moderation/label detection.
3. **Analytics S3 Bucket**: The parsed moderation data is saved here as CSV representations, acting as our Data Lake.
4. **Amazon Athena & QuickSight**: Used to query and visualize the moderation results.

### Deployment Details

We provide infrastructure code (`infrastructure/cdk_app.py`). You can deploy this using AWS CDK:

```bash
# Initialize CDK project
npx aws-cdk init app --language python

# Install dependencies
pip install aws-cdk-lib constructs boto3

# Replace the generated app code with our `infrastructure/cdk_app.py`
# synth and deploy
npx aws-cdk synth
npx aws-cdk deploy
```

If you prefer deploying via the AWS Management Console:
1. Create two S3 Buckets (`raw-images-xyz` and `analytics-data-xyz`).
2. Create an IAM Role using `infrastructure/lambda_policy.json`.
3. Create a Python 3.9 Lambda Function with the code in `src/lambda/vision_agent.py`. Set the `ANALYTICS_BUCKET` environment variable.
4. Add an S3 event trigger on your `raw-images-xyz` bucket pointing to your Lambda.

### QuickSight and Athena Integration

After deployment and uploading some test images:
1. Go to AWS Glue and create a Crawler over your Analytics S3 bucket to catalog the CSV data.
2. Go to **Amazon QuickSight**. Create a new Dataset using **Amazon Athena**.
3. Select the Glue database/table created by the crawler. 
4. Build Dashboards mapping the `TopCategory` and `IsFlagged` distributions using Pie Charts, and `Timestamp` trends with Line Graphs.
