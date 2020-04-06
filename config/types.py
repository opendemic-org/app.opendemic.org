from config.config import CONFIG
from enum import Enum


# ----------------------------------------------------------------------------------------------------------------------
# Telegram Bot Commands enums
# ----------------------------------------------------------------------------------------------------------------------
class TelegramBotCommand(Enum):
	START = 'start'
	REPORT = 'report'
	MY_MAP = 'my_map'
	HELP = 'help'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_


# ----------------------------------------------------------------------------------------------------------------------
# Symptoms enums
# ----------------------------------------------------------------------------------------------------------------------
class Symptoms(Enum):
	FEVER = 'fever'
	SHORTNESS_OF_BREATH = 'shortness_of_breath'
	COUGH = 'cough'
	CONFIRMED_COVID19 = 'confirmed_covid19'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_

