import re
import random
import pymysql
import unicodedata
from datetime import date, datetime, time
from unidecode import unidecode


def date_to_human_date(dt):
	if isinstance(dt, date):
		return dt.strftime("%A, %B %d")
	return dt


def datetime_to_human_datetime(dt):
	if isinstance(dt, datetime):
		return dt.strftime("%A, %B %d at %I:%M%p")
	return dt


def time_to_human_time(dt):
	if isinstance(dt, date):
		return dt.strftime("%I:%M%p")
	return dt

def de_emojify(s):
	return_string = ""
	for character in s:
		try:
			character.encode("ascii")
			return_string += character
		except UnicodeEncodeError:
			replaced = unidecode(str(character))
			if replaced != '':
				return_string += replaced
			else:
				try:
					return_string += "[" + unicodedata.name(character) + "]"
				except ValueError:
					return_string += "[x]"
	return return_string


def url2base_url(s):
	return s.split("://")[0]+"://"+s.split("://")[1].split("/")[0]


def getWords(text):
	return re.compile('\w+').findall(text)


def chooseRandomString(strings: list):
	return random.choice(strings)


def quote_wrap(s: str):
	return "'"+str(s)+"'"


def mysql_db_format_value(value):
	if value is None or value == "":
		return 'NULL'

	new_value = value
	if isinstance(value, str):
		if value.isnumeric():
			new_value = int(value)
		else:
			try:
				new_value = float(value)
			except ValueError:
				pass
	if isinstance(new_value, (float, int)):
		return new_value
	else:
		try:
			return quote_wrap(s=pymysql.escape_string(de_emojify(new_value)))
		except Exception:
			return quote_wrap(s=pymysql.escape_string(new_value))
