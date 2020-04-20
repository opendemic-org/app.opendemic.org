from config.config import CONFIG
from opendemic.human.model import Human
from enum import Enum


class CoordinateType(Enum):
	LATITUDE = 'lat'
	LONGITUDE = 'lng'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_


def get_risky_humans_geojson(
	lat: float,
	lng: float,
	days_window: int = int(CONFIG.get('days_window')),
	km_radius: int = int(CONFIG.get('km_radius'))
) -> dict:
	# get risky humans
	risky_humans = Human.get_risky_humans(
		lat=lat,
		lng=lng,
		days_window=days_window,
		km_radius=km_radius
	)

	risky_humans_geojson = {
		"type": "FeatureCollection",
		"src": "https://raw.githubusercontent.com/beoutbreakprepared/nCoV2019/master/latest_data/latestdata.csv",
		"features": []
	}

	for risky_human in risky_humans:
		risky_humans_geojson["features"].append({
			'type': 'Feature',
			"properties": {
				"mag": risky_human['mag']
			},
			'geometry': {
				'type': 'Point',
				'coordinates': [
					float(risky_human[CoordinateType.LONGITUDE.value]),
					float(risky_human[CoordinateType.LATITUDE.value])
				]
			}
		})

	return risky_humans
