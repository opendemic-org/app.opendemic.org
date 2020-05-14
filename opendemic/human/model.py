"""
import os
os.environ['FLASK_ENV'] = 'production'
os.environ['LOCAL'] = '0'
"""
from config.config import CONFIG, logger
from helpers.id import verify_uuid_regex
from opendemic.database import RDBManager
from opendemic.webhook.telegram.util import get_telegram_bot_instance, make_reply_keyboard_markup
from opendemic.map.model import CoordinateType
from opendemic.human.symptom.types import Symptoms
from helpers.formatting import mysql_db_format_value
from typing import Tuple
from enum import Enum
import uuid


class HumanProperties(Enum):
	ID = 'id'
	HUMAN_ID = 'human_id'
	TELEGRAM_HUMAN_ID = 'telegram_human_id'
	UNSUBSCRIBED = 'unsubscribed'
	FINGERPRINT = 'fingerprint'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_


class Human(object):
	_human_id = None
	_fingerprint_ = None
	_telegram_human_id = None

	def __init__(self, human_id: str):
		human_exists, human_data = verify_human_exists(human_id=human_id)
		assert human_exists

		self._human_id = human_data[HumanProperties.ID.value]
		self._fingerprint_ = human_data[HumanProperties.FINGERPRINT.value]
		try:
			self._telegram_human_id = int(human_data[HumanProperties.TELEGRAM_HUMAN_ID.value])
		except TypeError as e:
			self._telegram_human_id = None

	@property
	def id(self) -> str:
		return self._human_id

	def get_fingerprint(self) -> str:
		return self._fingerprint_

	@property
	def telegram_human_id(self) -> int:
		return self._telegram_human_id

	@property
	def unsubscribed(self) -> bool:
		unsub_status = False
		try:
			unsub_status = bool(self.get_human_attribute(attribute_name=HumanProperties.UNSUBSCRIBED.value))
		except Exception as e:
			logger.error(e)
		return unsub_status

	def unsubscribe(self) -> bool:
		rdb = RDBManager()
		err = None
		try:
			_, err = rdb.execute(
				sql_query="""
					UPDATE `humans`
					SET
						`unsubscribed` = 1
					WHERE
						`id` = {}
						""".format(
					mysql_db_format_value(value=self.id)
				)
			)
		except Exception as e:
			logger.error(e)

		return err is None

	def get_human_attribute(self, attribute_name: str) -> str:
		rdb = RDBManager(True)
		try:
			human_id_search_results, err = rdb.execute(
				sql_query="""
					SELECT *
					FROM `humans`
					WHERE `id` = '{}'
				""".format(self._human_id)
			)
		except Exception as e:
			logger.error(e)

		if len(human_id_search_results) == 1:
			if attribute_name in human_id_search_results[0]:
				return human_id_search_results[0][attribute_name]
		return None

	def log_symptom(self, symptom_name: str) -> bool:
		if not Symptoms.has_value(symptom_name):
			return False

		rdb = RDBManager()
		try:
			_, err = rdb.execute(
				sql_query="""
							INSERT IGNORE 
							INTO `symptoms`(`human_id`, `created`, `modified`, `symptom`, `value`)
							VALUES ({}, UTC_TIMESTAMP(), UTC_TIMESTAMP(), {}, 1.0)
						""".format(
					mysql_db_format_value(value=self.id),
					mysql_db_format_value(value=symptom_name)
				)
			)
		except Exception as e:
			logger.error(e)
			return False
		return err is None

	def get_most_recent_location(self) -> (float, float):
		rdb = RDBManager(True)
		err = None
		try:
			most_recent_location, err = rdb.execute(
				sql_query="""
					SELECT 
						`latitude` AS `{}`, 
						`longitude` AS `{}`
					FROM `geolocations`
					WHERE 
						`human_id` = {}
						AND
						`latitude` IS NOT NULL
						AND
						`longitude` IS NOT NULL
					ORDER BY `created` DESC
					LIMIT 1
				""".format(
					CoordinateType.LATITUDE.value,
					CoordinateType.LONGITUDE.value,
					mysql_db_format_value(value=self.id)
				)
			)
		except Exception as e:
			logger.error(e)

		if len(most_recent_location) == 1:
			return float(most_recent_location[0][CoordinateType.LATITUDE.value]), \
				   float(most_recent_location[0][CoordinateType.LONGITUDE.value])
		else:
			return None, None

	def send_proximity_alert(self, lat: float, lng: float) -> bool:
		if self.telegram_human_id is None:
			return False

		alert_message = get_proximity_alert(lat=lat, lng=lng)

		bot = get_telegram_bot_instance()
		try:
			bot.send_message(
				chat_id=self.telegram_human_id,
				text=alert_message,
				parse_mode='markdown',
				reply_markup=make_reply_keyboard_markup(markup_map=[
					{'text': "🌍 See Map", 'url': CONFIG.get('client-url')},
				])
			)
		except Exception as e:
			logger.error(e)
			self.unsubscribe()
			return False
		else:
			return True

	def log_location(self, latitude: float, longitude: float, send_alert: bool = True) -> bool:
		if not isinstance(latitude, float) or not isinstance(longitude, float):
			return False

		rdb = RDBManager()
		err = None
		try:
			_, err = rdb.execute(
				sql_query="""
					INSERT IGNORE 
					INTO `geolocations`(
						`human_id`, `created`, `modified`, `latitude`, `longitude`, `latitude_noise`, `longitude_noise`
					)
					VALUES ({}, UTC_TIMESTAMP(), UTC_TIMESTAMP(), {}, {}, ROUND(gauss(0,0.001), 10), ROUND(gauss(0,0.001), 10))
				""".format(
					mysql_db_format_value(value=self.id),
					mysql_db_format_value(value=round(latitude, 10)),
					mysql_db_format_value(value=round(longitude, 10))
				)
			)
		except Exception as e:
			logger.error(e)

		if send_alert:
			self.send_proximity_alert(lat=latitude, lng=longitude)

		self.update_tz(lat=latitude, lng=longitude)

		return err is None

	def update_tz(self, lat: float, lng: float) -> bool:
		rdb = RDBManager()
		err = None
		try:
			_, err = rdb.execute(
				sql_query="""
					UPDATE `humans`
					SET
						`current_tz` = (
							SELECT `timezone_name`
							FROM `timezones`
							WHERE mbrcontains(area, point({}, {})) 
							LIMIT 1
						)
					WHERE
						`id` = {}
						""".format(
					mysql_db_format_value(value=lng),
					mysql_db_format_value(value=lat),
					mysql_db_format_value(value=self.id)
				)
			)
		except Exception as e:
			logger.error(e)

		return err is None


def get_human_from_fingerprint(fingerprint: str) -> Human:
	rdb = RDBManager(True)
	err = None
	try:
		records, err = rdb.execute(
			sql_query="""
						SELECT `{}`
						FROM `humans`
						WHERE `{}` = {}
					""".format(
				HumanProperties.ID.value,
				HumanProperties.FINGERPRINT.value,
				mysql_db_format_value(fingerprint)
			)
		)
	except Exception as e:
		logger.error(e)

	return Human(human_id=records[0][HumanProperties.ID.value]) if len(records) == 1 else None


def get_all_humans_for_telegram_notifications(hours_of_day: list) -> list:
	if not isinstance(hours_of_day, list) or len(hours_of_day) == 0:
		return []

	for hour_of_day in hours_of_day:
		if not isinstance(hour_of_day, int) or (hour_of_day < 0 or hour_of_day > 23):
			return []

	hours_of_day = list(set(hours_of_day))

	rdb = RDBManager(True)
	audience = []
	try:
		audience, err = rdb.execute(
			sql_query="""
				SELECT 
					`id`, 
					`telegram_human_id`
				FROM `humans`
				WHERE
					HOUR(CONVERT_TZ(UTC_TIMESTAMP(),'UTC',`current_tz`)) IN ({})
					AND 
					`telegram_human_id` is not null
					AND 
					`unsubscribed` = 0
			""".format(
				", ".join([str(hour_of_day) for hour_of_day in hours_of_day])
			)
		)
	except Exception as e:
		logger.error(e)
	return audience


def verify_telegram_id_exists(telegram_human_id: int) -> (bool, str):
	if not isinstance(telegram_human_id, int):
		return TypeError('`telegram_human_id` of type {}. Expected [int]'.format(type(telegram_human_id)))

	rdb = RDBManager(True)
	err = None
	try:
		telegram_human_id_search_results, err = rdb.execute(
			sql_query="""
						SELECT `{}`
						FROM `humans`
						WHERE `{}` = {}
					""".format(
				HumanProperties.ID.value,
				HumanProperties.TELEGRAM_HUMAN_ID.value,
				telegram_human_id
			)
		)
	except Exception as e:
		logger.error(e)

	if len(telegram_human_id_search_results) == 1:
		return True, telegram_human_id_search_results[0][HumanProperties.ID.value]
	else:
		return False, None


def get_proximity_alert(lat: float, lng: float) -> str:
	km_radius = int(CONFIG.get('km_radius'))
	days_window = int(CONFIG.get('days_window'))
	risky_humans = get_risky_humans(lat=lat, lng=lng, days_window=days_window, km_radius=km_radius)

	if len(risky_humans) == 0:
		alert_emoji = '🔔'
		alert_info = "*0 individuals* who self-reported symptoms (fever, cough, shortness of breath) were found"
	else:
		alert_emoji = '❗'
		alert_info = "*{} individual(s)* who self-reported symptoms (fever, cough, shortness of breath) were found. ".format(
			len(risky_humans)
		)
		alert_info += "\n\nSee specific locations on the map below ⬇️ and *please exercise additional caution* ⚠️."

	alert_message = """
	{} During the last {} days and within a {} km ({} miles) radius from your current location, {}

	DISCLAIMER: This only represents the data *Opendemic* users have shared and might not be complete. Always be cautious and follow your local public health authority's guidelines.
			""".format(
		alert_emoji,
		days_window,
		km_radius,
		round(km_radius / 1.609, 1),
		alert_info
	)

	return alert_message


def create_human(telegram_human_id: int = None, fingerprint: str = None) -> Tuple[Human, str]:
	if telegram_human_id is None and fingerprint is None:
		return None

	human_id: str = str(uuid.uuid4())
	rdb: RDBManager = RDBManager(reader=False)
	try:
		_, db_err = rdb.execute(
			sql_query="""
				INSERT IGNORE INTO `humans`(
					`{}`, `{}`, `{}`, `created`, `modified`
				)
				VALUES (
					{}, {}, {}, UTC_TIMESTAMP(), UTC_TIMESTAMP()
				)
			""".format(
				HumanProperties.ID.value,
				HumanProperties.TELEGRAM_HUMAN_ID.value,
				HumanProperties.FINGERPRINT.value,
				mysql_db_format_value(value=human_id),
				mysql_db_format_value(value=telegram_human_id),
				mysql_db_format_value(value=fingerprint)
			)
		)
	except Exception as query_creation_err:
		logger.error(query_creation_err)
		return None, query_creation_err
	if db_err is not None:
		return None, db_err
	try:
		new_human: Human = Human(human_id=human_id)
	except AssertionError as assert_err:
		logger.error(assert_err)
		return None, assert_err
	return new_human, None


def validate_fingerprint(fingerprint: str) -> (bool, Exception):
	if not isinstance(fingerprint, str):
		return False, TypeError("attribute `fingerprint` is not of type `str`")
	if len(fingerprint) != 64:
		return False, ValueError("attribute `fingerprint` is not of length 64")

	return True, None


def verify_human_exists(human_id: str) -> (bool, dict):
	if not verify_uuid_regex(s=human_id):
		return False, None

	rdb = RDBManager(True)
	err = None
	try:
		human_id_search_results, err = rdb.execute(
			sql_query="""
					SELECT *
					FROM `humans`
					WHERE `{}` = '{}'
				""".format(
				HumanProperties.ID.value,
				human_id
			)
		)
	except Exception as e:
		logger.error(e)

	if len(human_id_search_results) == 1:
		return True, human_id_search_results[0]
	else:
		return False, None


def get_risky_humans(lat: float, lng: float, days_window: int, km_radius: int) -> list:
	rdb = RDBManager(True)
	err = None
	try:
		risky_humans, err = rdb.execute(
			sql_query="""						
				SELECT 
					agg.`latitude` AS {},
					agg.`longitude` AS {},
					CASE
						WHEN agg.`risk_level` IN (4,5) THEN agg.`risk_level`
						WHEN COUNT(DISTINCT(agg.`symptom`)) > 3 THEN 3
						ELSE COUNT(DISTINCT(agg.`symptom`))
					END AS 'mag' 
				FROM (
				SELECT
					geo.`human_id`,
					DATE(sym.`created`) AS 'date',
					geo.`latitude` + geo.`latitude_noise` AS 'latitude',
					geo.`longitude` + geo.`longitude_noise` AS 'longitude',
					sym.`symptom`,
					round(( 6373 * acos( least(1.0,  
						cos( radians({}) ) 
						* cos( radians(geo.`latitude`) ) 
						* cos( radians(geo.`longitude`) - radians({}) ) 
						+ sin( radians({}) ) 
						* sin( radians(geo.`latitude`) 
					  ) ) ) 
					), 1) as 'distance',
					CASE 
						WHEN sym.`symptom` = 'verified_covid19' THEN 5
						WHEN sym.`symptom` = 'confirmed_covid19' THEN 4
						ELSE 1
					END AS 'risk_level'
				FROM `geolocations` as geo
				LEFT JOIN `symptoms` as sym
				ON 
					geo.`human_id` = sym.`human_id`
					AND 
					DATE(sym.`created`) = DATE(geo.`created`)
				WHERE 
					sym.`symptom` is not null
					AND
					geo.`latitude` is not null
					AND
					geo.`longitude` is not null
					{}
					AND
					(sym.`value` is not null or sym.`value` > 0)
				{}
				) as agg
				GROUP BY 
					agg.`human_id`,
					agg.`date`,
					agg.`latitude`,
					agg.`longitude`,
					agg.`risk_level`;
										""".format(
				mysql_db_format_value(CoordinateType.LATITUDE.value),
				mysql_db_format_value(CoordinateType.LONGITUDE.value),
				mysql_db_format_value(value=lat),
				mysql_db_format_value(value=lng),
				mysql_db_format_value(value=lat),
				"AND sym.`created` >= DATE(NOW()) - INTERVAL {} DAY".format(days_window) if days_window is not None else "",
				"HAVING distance <= {}".format(km_radius*5) if km_radius is not None else ""
			)
		)
	except Exception as e:
		logger.error(e)

	return risky_humans, err


def get_risky_humans_geojson(lat: float, lng: float, days_window: int, km_radius: int) -> dict:
	risky_humans_geojson = {
		"type": "FeatureCollection",
		"src": "https://raw.githubusercontent.com/beoutbreakprepared/nCoV2019/master/latest_data/latestdata.csv",
		"features": []
	}

	risky_humans, err = get_risky_humans(
		lat=lat,
		lng=lng,
		days_window=days_window,
		km_radius=km_radius
	)

	if err is not None:
		return risky_humans_geojson

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

	logger.debug("returning {} risky humans".format(len(risky_humans)))
	return risky_humans_geojson
