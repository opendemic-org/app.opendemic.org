import logging
import boto3
from botocore.exceptions import ClientError
from config.config import CONFIG, ENV, Environments


def get_static_asset(sub_dir: str, path_to_file: str) -> str:
	get_base_url(bucket="auggi-assets", sub_dir=sub_dir)


def create_bucket(bucket_name, region=None):
	"""Create an S3 bucket in a specified region

	If a region is not specified, the bucket is created in the S3 default
	region (us-east-1).

	:param bucket_name: Bucket to create
	:param region: String region to create bucket in, e.g., 'us-west-2'
	:return: True if bucket created, else False
	"""

	# Create bucket
	try:
		if region is None:
			s3_client = boto3.client('s3')
			s3_client.create_bucket(Bucket=bucket_name)
		else:
			s3_client = boto3.client('s3', region_name=region)
			location = {'LocationConstraint': region}
			s3_client.create_bucket(
				Bucket=bucket_name,
				CreateBucketConfiguration=location
			)
	except ClientError as e:
		logging.error(e)
		return False
	return True


def list_existing_buckets(region=None):
	try:
		if region is None:
			s3_client = boto3.client('s3')
		else:
			s3_client = boto3.client('s3', region_name=region)
	except ClientError as e:
		logging.error(e)
		return False

	# Retrieve the list of existing buckets
	response = s3_client.list_buckets()

	# return the bucket names
	return response['Buckets']


def upload_file_object(file_obj, bucket, key, public_read):
	"""Upload a file to an S3 bucket

	:param file_name: File to upload
	:param bucket: Bucket to upload to
	:param object_name: S3 object name. If not specified then file_name is used
	:return: True if file was uploaded, else False
	"""

	# Upload the file
	s3_client = boto3.client('s3')
	try:
		_ = s3_client.upload_fileobj(
			Fileobj=file_obj,
			Bucket=bucket,
			Key=key,
			ExtraArgs={'ACL': 'public-read'} if public_read else None
		)
	except ClientError as e:
		logging.error(e)
		return False
	return True


def get_base_url(bucket, sub_dir=None):
	s3_client = boto3.client('s3')
	bucket_location = s3_client.get_bucket_location(Bucket=bucket)

	try:
		base_url = "https://{}.s3.{}.amazonaws.com/{}".format(
			bucket,
			bucket_location['LocationConstraint'],
			sub_dir+"/" if sub_dir is not None else ""
		)
	except ClientError as e:
		logging.error(e)
		return False
	return base_url


def get_bucket(s3, s3_uri: str):
    """Get the bucket from the resource.
    A thin wrapper, use with caution.

    Example usage:

    >> bucket = get_bucket(get_resource(), s3_uri_prod)"""
    return s3.Bucket(s3_uri)


def isfile_s3(bucket, key: str) -> bool:
    """Returns T/F whether the file exists."""
    objs = list(bucket.objects.filter(Prefix=key))
    return len(objs) == 1 and objs[0].key == key


def isdir_s3(bucket, key: str) -> bool:
    """Returns T/F whether the directory exists."""
    objs = list(bucket.objects.filter(Prefix=key))
    return len(objs) > 1