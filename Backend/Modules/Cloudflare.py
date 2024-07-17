import os
import boto3

from botocore.config import Config

def SET_R2_Client():
	return  boto3.client(
		service_name = 's3',
		endpoint_url = f"https://{os.getenv('R2_BUCKET_URL')}.r2.cloudflarestorage.com",
		aws_access_key_id = os.getenv('R2_ACCESS_KEY_ID'),
		aws_secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY'),
		config = Config(signature_version = 'v4')
	)