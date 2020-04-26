from enum import Enum


class Symptoms(Enum):
	FEVER = 'fever'
	SHORTNESS_OF_BREATH = 'shortness_of_breath'
	COUGH = 'cough'
	ANOSMIA = 'anosmia'
	DIARRHEA = 'diarrhea'
	ABDOMINAL_PAIN = 'abdominal_pain'
	FATIGUE = 'fatigue'
	CONFIRMED_COVID19 = 'confirmed_covid19'  # self-reported
	VERIFIED_COVID19 = 'verified_covid19'  # official

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_
