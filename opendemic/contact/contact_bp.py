from config.config import CONFIG, ENV, Environments
from flask import Blueprint, Response, render_template, abort, request
from enum import Enum
import boto3
from botocore.exceptions import ClientError

blueprint = Blueprint('contact', __name__)

ADMIN_EMAIL = 'teamopendemic@gmail.com'
RECIPIENT_EMAIL = 'dhachuel@hsph.harvard.edu'


class ContactFormFields(Enum):
	NAME = 'name'
	EMAIL = 'email'
	MESSAGE = 'message'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_


@blueprint.route('/contact', methods=['POST'])
def contact():
	# get payload
	name = request.form.get(ContactFormFields.NAME.value)
	email = request.form.get(ContactFormFields.EMAIL.value)
	message = request.form.get(ContactFormFields.MESSAGE.value)

	print("""
		name: {}
		email: {}
		message: {}
	""".format(name, email, message))

	SENDER = ADMIN_EMAIL
	RECIPIENT = RECIPIENT_EMAIL
	AWS_REGION = "us-east-1"
	SUBJECT = "Message from{}<{}>".format(" " + name + " ", email)
	BODY_TEXT = message
	CHARSET = "UTF-8"

	# Create a new SES resource and specify a region.
	session = boto3.session.Session()
	# client = session.client(
	# 	service_name='ses',
	# 	region_name=AWS_REGION
	# )
	client = boto3.client('ses', region_name=AWS_REGION)

	# Try to send the email.
	try:
		# Provide the contents of the email.
		response = client.send_email(
			Destination={
				'ToAddresses': [
					RECIPIENT,
				],
			},
			Message={
				'Body': {
					'Text': {
						'Charset': CHARSET,
						'Data': BODY_TEXT,
					},
				},
				'Subject': {
					'Charset': CHARSET,
					'Data': SUBJECT,
				},
			},
			Source=SENDER
		)
	# Display an error if something goes wrong.
	except ClientError as e:
		print(e.response['Error']['Message'])
	else:
		print("Email sent! Message ID:"),
		print(response['MessageId'])

	return "Success!", 200