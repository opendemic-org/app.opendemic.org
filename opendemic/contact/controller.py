from config.config import logger
from flask import Blueprint, request
from helpers.aws_ses import send_email
from opendemic.contact.model import ContactFormFields

blueprint = Blueprint('contact', __name__)

ADMIN_EMAIL = 'teamopendemic@gmail.com'
RECIPIENT_EMAIL = 'dhachuel@hsph.harvard.edu'


@blueprint.route('/contact', methods=['POST'])
def contact():
	# get payload
	name = request.form.get(ContactFormFields.NAME.value)
	email = request.form.get(ContactFormFields.EMAIL.value)
	message = request.form.get(ContactFormFields.MESSAGE.value)

	email_sent = send_email(
		sender=ADMIN_EMAIL,
		recipient=RECIPIENT_EMAIL,
		subject="Message from{}<{}>".format(" " + name + " ", email),
		body_text=message
	)
	if not email_sent:
		logger.error("Error in sending SES email from {} to {} with values: {} - {} - {}".format(
			ADMIN_EMAIL,
			RECIPIENT_EMAIL,
			name,
			email,
			message
		))

	return "Success!", 200
