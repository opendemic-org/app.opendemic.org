"""
import os
os.environ['FLASK_ENV'] = 'production'
os.environ['LOCAL'] = '0'
"""
from config.config import CONFIG, ENV, Environments, LOCAL
from config.types import Symptoms
from helpers.id import verify_uuid_regex
from opendemic.database.sql_db import RDBManager
from opendemic.channels.telegram import get_telegram_bot_instance, get_telegram_menu, make_reply_keyboard_markup
from helpers.formatting import quote_wrap, mysql_db_format_value
from helpers.datetime import datetime_to_mysql
from opendemic.logging.action import log_action
import datetime
import json
import uuid
import pandas as pd
import os


class Human(object):
	_human_id = None
	_telegram_human_id = None
	_email = None

	def __init__(self, human_id: str):
		# validate `human_id`
		human_exists, human_data = self.validate_human_id(human_id=human_id)
		assert human_exists

		# populate profile
		self._human_id = human_data['id']
		try:
			self._telegram_human_id = int(human_data['telegram_human_id'])
		except TypeError as e:
			self._telegram_human_id = None

	@property
	def id(self):
		return self._human_id

	@property
	def human_id(self):
		return self._human_id

	@property
	def telegram_human_id(self):
		if self._telegram_human_id is None:
			try:
				self._telegram_human_id = int(self.get_human_attribute(attribute_name='telegram_human_id'))
			except TypeError as e:
				if ENV == Environments.DEVELOPMENT.value:
					print(e)
		return self._telegram_human_id

	@property
	def email(self):
		return self.get_human_attribute(attribute_name='email')

	@property
	def unsubscribed(self):
		return self.get_human_attribute(attribute_name='unsubscribed')

	def unsubscribe(self):
		rdb = RDBManager()
		try:
			_, records_affected = rdb.execute(
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
			if ENV == Environments.DEVELOPMENT.value:
				print(e)

	def get_human_attribute(self, attribute_name: str):
		# validate `human_id` existence
		rdb = RDBManager()
		human_id_search_results, _ = rdb.execute(
			sql_query="""
				SELECT *
				FROM `humans`
				WHERE `id` = '{}'
			""".format(self._human_id)
		)

		# return results
		if len(human_id_search_results) == 1:
			if attribute_name in human_id_search_results[0]:
				return human_id_search_results[0][attribute_name]
			else:
				return None
		else:
			return None

	@staticmethod
	def human_exists(human_id: str) -> bool:
		# validate format
		if not verify_uuid_regex(s=human_id):
			return False

		# validate `human_id` existence
		rdb = RDBManager()
		human_id_search_results, _ = rdb.execute(
			sql_query="""
						SELECT *
						FROM `humans`
						WHERE `id` = '{}'
					""".format(human_id)
		)

		# return results
		return len(human_id_search_results) == 1

	@staticmethod
	def validate_human_id(human_id: str) -> (bool, dict):
		# validate format
		if not verify_uuid_regex(s=human_id):
			return False

		# validate `human_id` existence
		rdb = RDBManager()
		human_id_search_results, _ = rdb.execute(
			sql_query="""
					SELECT *
					FROM `humans`
					WHERE `id` = '{}'
				""".format(human_id)
		)

		# return results
		if len(human_id_search_results) == 1:
			return True, human_id_search_results[0]
		else:
			return False, None

	def log_symptom(self, symptom_name: str):
		# validate inputs
		if not Symptoms.has_value(symptom_name):
			return False

		# log data to db
		rdb = RDBManager()
		_, records_affected = rdb.execute(
			sql_query="""
						INSERT IGNORE 
						INTO `symptoms`(`human_id`, `created`, `modified`, `symptom`, `value`)
						VALUES ({}, UTC_TIMESTAMP(), UTC_TIMESTAMP(), {}, 1.0)
					""".format(
				mysql_db_format_value(value=self.id),
				mysql_db_format_value(value=symptom_name)
			)
		)

		# return results
		return records_affected == 1

	def get_most_recent_location(self):
		# create db instance
		rdb = RDBManager()

		most_recent_location, _ = rdb.execute(
			sql_query="""
				SELECT `latitude`, `longitude`
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
				mysql_db_format_value(value=self.id)
			)
		)

		if len(most_recent_location) == 1:
			return float(most_recent_location[0]['latitude']), float(most_recent_location[0]['longitude'])
		else:
			return None

	@staticmethod
	def get_risky_humans(lat: float, lng: float, days_window: int, km_radius: int = None):
		# get DB
		rdb = RDBManager()

		# fetch cases
		sql_query = """						
				SELECT 
					CASE
						WHEN agg.`risk_level` = 5 THEN round(agg.`latitude` + gauss(0,0.002), 5)
						ELSE round(agg.`latitude` + gauss(0,0.001), 5)
					 END AS 'latitude',
					 CASE
						WHEN agg.`risk_level` = 5 THEN round(agg.`longitude` + gauss(0,0.002), 5)
						ELSE round(agg.`longitude` + gauss(0,0.001), 5)
					 END AS 'longitude',
					CASE
						WHEN agg.`risk_level` > 1 THEN agg.`risk_level`
						ELSE COUNT(DISTINCT(agg.`symptom`))
					END AS 'mag' 
				FROM (
				SELECT
					geo.`human_id`,
					DATE(sym.`created`) AS 'date',
					geo.`latitude`,
					geo.`longitude`,
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
					AND
					sym.`created` >= DATE(NOW()) - INTERVAL {} DAY
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
			mysql_db_format_value(value=lat),
			mysql_db_format_value(value=lng),
			mysql_db_format_value(value=lat),
			days_window,
			"HAVING distance <= {}".format(km_radius*5) if km_radius is not None else ""
		)
		risky_humans, _ = rdb.execute(sql_query=sql_query)
		return risky_humans

	@staticmethod
	def get_proximity_alert(lat: float, lng: float):
		km_radius = int(CONFIG.get('km_radius'))
		days_window = int(CONFIG.get('days_window'))
		risky_humans = Human.get_risky_humans(lat=lat, lng=lng, days_window=days_window, km_radius=km_radius)

		# create alert message
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

	def send_proximity_alert(self, lat: float, lng: float):
		# verify user has telegram id
		if self.telegram_human_id is None:
			return

		# get proximity alert
		alert_message = Human.get_proximity_alert(lat=lat, lng=lng)

		# create bot
		bot = get_telegram_bot_instance()
		if LOCAL:
			map_url = os.path.join(CONFIG.get('local-base-url'), "map", self.id)
		else:
			map_url = os.path.join(CONFIG.get('base-url'), "map", self.id)

		try:
			bot.send_message(
				chat_id=self.telegram_human_id,
				text=alert_message,
				parse_mode='markdown',
				reply_markup=make_reply_keyboard_markup(markup_map=[
					{'text': "🌍 See Map", 'url': map_url},
				])
			)
		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)
			# try to unsubscribe
			try:
				self.unsubscribe()
			except Exception as unsb_e:
				pass

	def log_location(self, latitude: float, longitude: float, send_alert: bool = True) -> (bool, datetime.datetime):
		# validate inputs
		if not isinstance(latitude, float) or not isinstance(longitude, float):
			return False

		# log data to db
		rdb = RDBManager()
		_, records_affected = rdb.execute(
			sql_query="""
				INSERT IGNORE 
				INTO `geolocations`(`human_id`, `created`, `modified`, `latitude`, `longitude`)
				VALUES ({}, UTC_TIMESTAMP(), UTC_TIMESTAMP(), {}, {})
			""".format(
				mysql_db_format_value(value=self.id),
				mysql_db_format_value(value=latitude),
				mysql_db_format_value(value=longitude)
			)
		)

		# send alert
		if send_alert:
			self.send_proximity_alert(lat=latitude, lng=longitude)

		# update TZ
		self.update_tz(lat=latitude, lng=longitude)

		# return results
		return records_affected == 1

	def update_tz(self, lat: float, lng: float):
		# update TZ
		rdb = RDBManager()
		try:
			_, records_affected = rdb.execute(
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
			pass

	@staticmethod
	def validate_fingerprint(fingerprint: str) -> (bool, Exception):
		if not isinstance(fingerprint, str):
			return False, TypeError("attribute `fingerprint` is not of type `str`")
		if len(fingerprint) != 64:
			return False, ValueError("attribute `fingerprint` is not of length 64")

		return True, None

	@staticmethod
	def new(
		telegram_human_id: int = None,
		fingerprint: str = None,
		email: str = None,
		birth_year: int = None,
		biological_sex: str = None,
		tag: str = None,
		utm_source: str = None,
		utm_medium: str = None,
		utm_campaign: str = None,
		utm_term: str = None,
		utm_content: str = None
	) -> bool:
		if telegram_human_id is None and fingerprint is None:
			return None

		# create DB connection
		rdb = RDBManager()

		# create human_id
		human_id = str(uuid.uuid4())

		# send data to db
		_, records_affected = rdb.execute(
			sql_query="""
				INSERT IGNORE INTO `humans`(
					`id`, `telegram_human_id`, `fingerprint`, `created`, `modified`
				)
				VALUES (
					{}, {}, {}, UTC_TIMESTAMP(), UTC_TIMESTAMP()
				)
			""".format(
				mysql_db_format_value(value=human_id),
				mysql_db_format_value(value=telegram_human_id),
				mysql_db_format_value(value=fingerprint)
			)
		)
		if ENV == Environments.DEVELOPMENT.value:
			print("Human.new records_affected : {}".format(records_affected))

		# return results
		if records_affected == 1:
			# get new human
			human = Human(human_id=human_id)
			return human

		return None

	@staticmethod
	def telegram_id_exists(telegram_human_id: int):
		rdb = RDBManager()
		_, records = rdb.execute(
			sql_query="""
					SELECT *
					FROM `humans`
					WHERE `telegram_human_id` = {}
				""".format(
				mysql_db_format_value(telegram_human_id)
			)
		)
		return records == 1

	@staticmethod
	def get_human_from_fingerprint(fingerprint: str):
		rdb = RDBManager()
		records, _ = rdb.execute(
			sql_query="""
						SELECT `id`
						FROM `humans`
						WHERE `fingerprint` = {}
					""".format(
				mysql_db_format_value(fingerprint)
			)
		)

		return Human(human_id=records[0]['id']) if len(records) == 1 else None

	@staticmethod
	def get_all_humans_for_telegram_notifications(hours_of_day: list) -> list:
		# validate `hours_of_day`
		if not isinstance(hours_of_day, list) or len(hours_of_day) == 0:
			return []

		for hour_of_day in hours_of_day:
			if not isinstance(hour_of_day, int) or (hour_of_day < 0 or hour_of_day > 23):
				return []

		# ensure unique values
		hours_of_day = list(set(hours_of_day))

		# generate SQL query
		sql_query = """
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

		# fetch audience from db
		rdb = RDBManager()
		audience = []
		try:
			audience, _ = rdb.execute(sql_query=sql_query)
		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)
		return audience

	@staticmethod
	def validate_telegram_human_id(telegram_human_id: int) -> (bool, str):
		# check `telegram_human_id` type
		if not isinstance(telegram_human_id, int):
			return TypeError('`telegram_human_id` of type {}. Expected [int]'.format(type(telegram_human_id)))

		# init DB connection
		rdb = RDBManager()

		# check if `telegram_id` exists in db
		telegram_human_id_search_results, _ = rdb.execute(
			sql_query="""
				SELECT *
				FROM `humans`
				WHERE `telegram_human_id` = {}
			""".format(telegram_human_id)
		)

		# return results
		if len(telegram_human_id_search_results) == 1:
			return True, telegram_human_id_search_results[0]['id']
		else:
			return False, None


