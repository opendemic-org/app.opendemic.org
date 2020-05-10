from enum import Enum


class LocationResourceFields(Enum):
    FINGERPRINT = 'fingerprint'
    LATITUDE = 'lat'
    LONGITUDE = 'lng'
    INCLUDE_LEGEND = 'include_legend'

    @classmethod
    def value_to_member_name(cls, value):
        if cls.has_value(value):
            return cls._value2member_map_[value].name

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_
