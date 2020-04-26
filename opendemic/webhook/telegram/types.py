from enum import Enum


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
