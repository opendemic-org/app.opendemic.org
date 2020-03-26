import datetime
import pytz
from collections import defaultdict


def get_start_of_day(dt) -> datetime.datetime:
	if isinstance(dt, datetime.datetime):
		return dt.replace(hour=0, minute=0, second=0)
	elif isinstance(dt, datetime.date):
		_dt = datetime.datetime.combine(dt, datetime.datetime.min.time())
		return _dt.replace(hour=0, minute=0, second=0)
	else:
		return None


def get_end_of_day(dt) -> datetime.datetime:
	if isinstance(dt, datetime.datetime):
		return dt.replace(hour=0, minute=0, second=0) + datetime.timedelta(hours=23, minutes=59, seconds=59)
	elif isinstance(dt, datetime.date):
		_dt = datetime.datetime.combine(dt, datetime.datetime.min.time())
		return _dt.replace(hour=0, minute=0, second=0) + datetime.timedelta(hours=23, minutes=59, seconds=59)
	else:
		return None


def datetime_to_mysql(dt):
	if dt is None or not isinstance(dt, (datetime.datetime, datetime.date, datetime.time)):
		return None
	return dt.strftime('%Y-%m-%d %H:%M:%S')


def date_to_mysql(dt):
	if dt is None or not isinstance(dt, (datetime.datetime, datetime.date, datetime.time)):
		return None
	return dt.strftime('%Y-%m-%d')


def time_to_mysql(dt):
	if dt is None or not isinstance(dt, (datetime.datetime, datetime.date, datetime.time)):
		return None
	return dt.strftime('%H:%M:%S')


def get_timezone_from_utc_offset(local_datetime: datetime.datetime):
	# calculate local-utc hour difference
	utc = datetime.datetime.utcnow()
	diff = int((local_datetime-utc).total_seconds()/3600)

	# make list of timezones
	zone_names = defaultdict(list)
	for tz in pytz.common_timezones:
		zone_names[int(utc.astimezone(pytz.timezone(tz)).utcoffset().total_seconds()/3600)].append(tz)

	# return first timezone candidate if exists
	if diff in zone_names.keys():
		return zone_names[diff][0]
	else:
		return None
