import json
import time
from io import BytesIO

import boto3
from botocore.exceptions import ClientError

from app import config

last_key = "last"


def get_s3():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_KEY,
        aws_secret_access_key=config.AWS_SECRET_KEY,
    )
    return s3


def generate_io(data: str):
    bytesIO = BytesIO()
    bytesIO.write(data.encode("utf-8"))
    bytesIO.seek(0)
    return bytesIO


def put(data: str):
    s3 = get_s3()
    f: BytesIO = generate_io(data)
    try:
        s3.copy_object(
            Bucket=config.BUCKET,
            CopySource=f"{config.BUCKET}/{last_key}",
            Key=f"{int(time.time())}",
        )
        s3.delete_object(Bucket=config.BUCKET, Key=last_key)
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchKey":
            raise e

    s3.upload_fileobj(f, config.BUCKET, last_key)
    f.close()


def get_latest():
    s3 = get_s3()
    try:
        data = s3.get_object(Bucket=config.BUCKET, Key=last_key)
        contents = data["Body"].read()
        return json.loads(contents.decode("utf-8"))
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchKey":
            raise e
    return ""
