from config.config import CONFIG, ENV, Environments
from flask import Blueprint, Response, render_template, abort, request
from enum import Enum
from opendemic.database import RDBManager
from helpers.formatting import mysql_db_format_value, quote_wrap
import uuid

blueprint = Blueprint('subscribe', __name__)


class SubscribeFormFields(Enum):
	PHONE = 'subscribe-phone'
	EMAIL = 'subscribe-email'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_


@blueprint.route('/subscribe', methods=['POST'])
def subscribe():
	# get payload
	phone = request.form.get(SubscribeFormFields.PHONE.value)
	email = request.form.get(SubscribeFormFields.EMAIL.value)
	if phone is None or len(phone) == 0:
		phone = None
	if email is None or len(email) == 0:
		email = None

	if ENV == Environments.DEVELOPMENT.value:
		print("""
			phone: {}
			email: {}
		""".format(phone, email))

	if phone is not None or email is not None:
		# create DB connection
		rdb = RDBManager()

		# check if contact exists
		try:
			existing_contact, _ = rdb.execute(
				sql_query="""
					SELECT `id`
					FROM `contact`
					WHERE
						`phone_number` = {}
						OR
						`email` = {}
					LIMIT 1
				""".format(
					mysql_db_format_value(value=phone),
					mysql_db_format_value(value=email)
				)
			)
		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)
			return "An error occurred while processing your registration. Please try again.", 200
		else:
			if len(existing_contact) == 1 and 'id' in existing_contact[0]:
				contact_id = existing_contact[0]['id']

				# update existing contact
				try:
					_, updated_records = rdb.execute(
						sql_query="""
							UPDATE `contact`
							SET
								`phone_number` = IF({} is not null, {}, `phone_number`),
								`email` = IF({} is not null, {}, `email`)
							WHERE
								`id` = {}
								""".format(
							mysql_db_format_value(value=phone),
							quote_wrap(phone),
							mysql_db_format_value(value=email),
							mysql_db_format_value(value=email),
							mysql_db_format_value(value=contact_id)
						)
					)
				except Exception as e:
					if ENV == Environments.DEVELOPMENT.value:
						print(e)
			else:
				# create contact_id
				contact_id = str(uuid.uuid4())

				# register contact information
				_, records_affected = rdb.execute(
					sql_query="""
						INSERT IGNORE INTO `contact` (`id`, `phone_number`, `email`)
						VALUES
							({}, {}, {})
							""".format(
						mysql_db_format_value(value=contact_id),
						quote_wrap(phone),
						mysql_db_format_value(value=email)
					)
				)
			return "Subscribed!", 200
	else:
		return "Seems like you didn't provide any contact information. Please try again.", 200