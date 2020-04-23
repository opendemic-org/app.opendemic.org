from flask import Blueprint, request
from enum import Enum
from opendemic.human.model import subscribe_to_newsletter

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
	phone = request.form.get(SubscribeFormFields.PHONE.value)
	email = request.form.get(SubscribeFormFields.EMAIL.value)
	if phone is None or len(phone) == 0:
		phone = None
	if email is None or len(email) == 0:
		email = None

	subscribed, msg = subscribe_to_newsletter(phone=phone, email=email)
	return msg, 200
