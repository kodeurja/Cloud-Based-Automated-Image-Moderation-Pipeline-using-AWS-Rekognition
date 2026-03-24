import urllib.parse
import boto3
import json
import csv
import os
from io import StringIO
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')

# Environment variable for the destination bucket
DESTINATION_BUCKET = os.environ.get('ANALYTICS_BUCKET')

def lambda_handler(event, context):
    try:
        # Get the bucket and object key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        
        print(f"Processing image: {key} from bucket: {bucket}")
        
        # 1. Call Amazon Rekognition to detect moderation labels
        moderation_response = rekognition_client.detect_moderation_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MinConfidence=50 # Configure minimum confidence threshold as needed
        )
        
        # 2. Call Amazon Rekognition to detect general labels (objects, scenes)
        labels_response = rekognition_client.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=15,
            MinConfidence=70
        )
        
        # Extract data
        moderation_labels = moderation_response.get('ModerationLabels', [])
        general_labels = labels_response.get('Labels', [])
        
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Prepare CSV records
        # Schema: Image Name, Label Type, Label Name, Confidence Score, Timestamp
        
        moderation_records = []
        if not moderation_labels:
             # Explicitly add a SAFE record if no moderation labels exist 
             moderation_records.append([key, 'Moderation', 'SAFE', '100.0', timestamp])
        else:
            for label in moderation_labels:
                moderation_records.append([
                    key, 
                    'Moderation', 
                    label['Name'], 
                    str(round(label['Confidence'], 2)), 
                    timestamp
                ])
                
        general_records = []
        for label in general_labels:
            general_records.append([
                key, 
                'Object', 
                label['Name'], 
                str(round(label['Confidence'], 2)), 
                timestamp
            ])
        
        # Helper function to create CSV string
        def create_csv_string(records):
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            # Write Header
            writer.writerow(['Image Name', 'Label Type', 'Label Name', 'Confidence Score', 'Timestamp'])
            for record in records:
                writer.writerow(record)
            return csv_buffer.getvalue()

        moderation_csv = create_csv_string(moderation_records)
        general_csv = create_csv_string(general_records)

        # 4. Save to Analytics S3 Bucket (if configured)
        if DESTINATION_BUCKET:
            dt_now = datetime.utcnow()
            date_prefix = f"year={dt_now.year}/month={dt_now.month:02}/day={dt_now.day:02}"
            base_filename = key.split('.')[0]
            
            # Save Moderation results
            mod_output_key = f"moderation-results/{date_prefix}/{base_filename}_moderation.csv"
            s3_client.put_object(
                Bucket=DESTINATION_BUCKET,
                Key=mod_output_key,
                Body=moderation_csv
            )
            print(f"Successfully saved moderation results to s3://{DESTINATION_BUCKET}/{mod_output_key}")
            
            # Save General Label results
            label_output_key = f"label-results/{date_prefix}/{base_filename}_labels.csv"
            s3_client.put_object(
                Bucket=DESTINATION_BUCKET,
                Key=label_output_key,
                Body=general_csv
            )
            print(f"Successfully saved label results to s3://{DESTINATION_BUCKET}/{label_output_key}")
            
        else:
            print("Warning: ANALYTICS_BUCKET environment variable not set. Results not saved to S3.")

        return {
            'statusCode': 200,
            'body': json.dumps('Image analysis complete.')
        }

    except Exception as e:
        print(f"Error processing image: {e}")
        raise e
