from config.config import CONFIG, logger
import boto3
from botocore.exceptions import ClientError


def send_email(
	sender: str,
	recipient: str,
	subject: str,
	body_text: str
) -> bool:
	charset = "UTF-8"
	client = boto3.client('ses', region_name=CONFIG.get('aws-region'))
	try:
		response = client.send_email(
			Destination={
				'ToAddresses': [
					recipient
				],
			},
			Message={
				'Body': {
					'Text': {
						'Charset': charset,
						'Data': body_text
					},
				},
				'Subject': {
					'Charset': charset,
					'Data': subject
				},
			},
			Source=sender
		)
	except ClientError as e:
		logger.error(e.response['Error']['Message'])
		return False
	else:
		logger.debug("Email sent! Message ID : {}".format(response['MessageId']))
		return True
