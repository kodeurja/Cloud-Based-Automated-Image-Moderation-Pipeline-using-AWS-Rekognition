# aws-cdk-lib>=2.0.0
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3_notifications as s3_notifications,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

class VisualGovernanceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create S3 Bucket for Raw Imagery (Uploads)
        raw_image_bucket = s3.Bucket(
            self, "RawImageBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            # Block public access as these could be unsafe images
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # 2. Create S3 Bucket for Analytics Data (CSV files / The Data Lake)
        analytics_bucket = s3.Bucket(
            self, "AnalyticsBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        # 3. Create the Vision Agent Lambda Function
        vision_agent_lambda = _lambda.Function(
            self, "VisionAgentLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="vision_agent.lambda_handler",
            code=_lambda.Code.from_asset("src/lambda"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "ANALYTICS_BUCKET": analytics_bucket.bucket_name
            }
        )

        # 4. Grant Permissions to the Lambda Function
        
        # S3 Permissions
        raw_image_bucket.grant_read(vision_agent_lambda)
        analytics_bucket.grant_write(vision_agent_lambda)
        
        # Amazon Rekognition Permissions
        vision_agent_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "rekognition:DetectModerationLabels",
                    "rekognition:DetectLabels"
                ],
                resources=["*"] # Rekognition operations don't target specific ARNs usually
            )
        )
        
        # 5. Add S3 Event Trigger to the Lambda Function
        # Trigger lambda whenever a new object is created in the raw image bucket
        raw_image_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(vision_agent_lambda)
        )
