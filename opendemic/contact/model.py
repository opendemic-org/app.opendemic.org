from enum import Enum


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
