import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

# Set default AWS region for test suite to prevent botocore NoRegionError
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Add lambda path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lambda'))

class TestVisionAgent(unittest.TestCase):
    @patch('vision_agent.s3_client')
    @patch('vision_agent.rekognition_client')
    def test_lambda_handler(self, mock_rekognition, mock_s3):
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        import vision_agent
        
        # Setup mock returns
        mock_rekognition.detect_moderation_labels.return_value = {
            'ModerationLabels': [
                {'Name': 'Explicit Nudity', 'Confidence': 99.9},
                {'Name': 'Violence', 'Confidence': 85.5}
            ]
        }
        
        mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Person', 'Confidence': 99.0},
                {'Name': 'Weapon', 'Confidence': 90.0}
            ]
        }
        
        # Set env var
        vision_agent.DESTINATION_BUCKET = 'test-analytics-bucket'
        
        # Create mock event
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {
                            "name": "test-raw-bucket"
                        },
                        "object": {
                            "key": "test_image_123.jpg"
                        }
                    }
                }
            ]
        }
        
        context = {}
        
        # Run the handler
        response = vision_agent.lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        
        # Check that Rekognition was called with correct args
        mock_rekognition.detect_moderation_labels.assert_called_once_with(
            Image={'S3Object': {'Bucket': 'test-raw-bucket', 'Name': 'test_image_123.jpg'}},
            MinConfidence=50
        )
        
        # Check that S3 put_object was called to save CSVs
        self.assertEqual(mock_s3.put_object.call_count, 2)
        
        # Get arguments for both calls
        call_args_1 = mock_s3.put_object.call_args_list[0][1]
        call_args_2 = mock_s3.put_object.call_args_list[1][1]
        
        self.assertEqual(call_args_1['Bucket'], 'test-analytics-bucket')
        self.assertEqual(call_args_2['Bucket'], 'test-analytics-bucket')
        
        # Determine which call is moderation vs labels based on the key
        if 'moderation-results' in call_args_1['Key']:
            mod_args = call_args_1
            label_args = call_args_2
        else:
            mod_args = call_args_2
            label_args = call_args_1
            
        self.assertIn('moderation-results', mod_args['Key'])
        self.assertIn('test_image_123_moderation.csv', mod_args['Key'])
        
        self.assertIn('label-results', label_args['Key'])
        self.assertIn('test_image_123_labels.csv', label_args['Key'])
        
        # Check Moderation CSV contents
        mod_csv_content = mod_args['Body']
        self.assertIn('Image Name,Label Type,Label Name,Confidence Score,Timestamp', mod_csv_content)
        self.assertIn('test_image_123.jpg,Moderation,Explicit Nudity,99.9', mod_csv_content)
        self.assertIn('test_image_123.jpg,Moderation,Violence,85.5', mod_csv_content)
        
        # Check General Labels CSV contents
        label_csv_content = label_args['Body']
        self.assertIn('Image Name,Label Type,Label Name,Confidence Score,Timestamp', label_csv_content)
        self.assertIn('test_image_123.jpg,Object,Person,99.0', label_csv_content)
        self.assertIn('test_image_123.jpg,Object,Weapon,90.0', label_csv_content)
        
        print("All assertions passed successfully!")

if __name__ == '__main__':
    unittest.main()
