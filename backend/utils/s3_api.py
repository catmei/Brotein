import boto3
from botocore.exceptions import NoCredentialsError
import os
import io
from dotenv import load_dotenv


load_dotenv()
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("AWS_S3_BUCKET")


def upload_file_to_s3(file_name, file_data, bucket=BUCKET_NAME):
    # Convert bytes data to a BytesIO object for S3 upload
    file_data_io = io.BytesIO(file_data)

    # Upload the file to S3
    s3_client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

    try:
        s3_client.upload_fileobj(file_data_io, bucket, file_name)
        print(f"File uploaded successfully to {bucket}/{file_name}")
        return f"https://{bucket}.s3.amazonaws.com/{file_name}"
    except NoCredentialsError:
        print("Credentials not available")
        raise Exception
