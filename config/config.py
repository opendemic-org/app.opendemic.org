import glob
import os
import copy
from enum import Enum
from helpers.aws_secrets_manager import list_secrets, get_secret
from configparser import ConfigParser, ExtendedInterpolation
import logging.handlers
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration



# create environment Enum class
class Environments(Enum):
	DEFAULT = 'DEFAULT'
	DEVELOPMENT = 'DEVELOPMENT'
	PRODUCTION = 'PRODUCTION'

# mute werkzeug logger
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
# create logger
logger = logging.getLogger("Logger")
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)


logger.debug("RUNNING CONFIG...")

# verify secrets cache
if not os.path.isfile('./config/secrets.ini'):
	logger.debug("COLLECTING SECRETS...")
	secret_names = {i.name:[] for i in list(Environments)}
	for secret_data in list_secrets():
		# determine secret environment
		env = None
		for tag in secret_data['Tags']:
			if tag['Key'] == 'ENV':
				env = tag['Value']
				break
		if env is None:
			raise ValueError("Could NOT find valid `ENV` tag in secret data.")
		if env not in secret_names.keys():
			raise ValueError("Invalid `ENV` parameter value. Expected {}".format(
				secret_names.keys()
			))

		# add secret
		secret_names[env].append(secret_data['Name'])

	# create config parser and populate with values
	secrets_config = ConfigParser()
	for secret_section in secret_names:
		secrets_config[secret_section] = {}
		for secret_name in secret_names[secret_section]:
			# fetch secret value
			secret_value = get_secret(secret_name=secret_name)

			# remove -prod from secret_name
			alt_secret_name = copy.copy(secret_name)
			if len(secret_name) > 5:
				if secret_name[-5:] == "-prod":
					alt_secret_name = secret_name[:-5]

			# store secret
			for index, key in enumerate(secret_value):
				secrets_config[secret_section][alt_secret_name+"-"+key] = str(secret_value[key])

	with open('./config/secrets.ini', 'w') as secrets_config_file:
		secrets_config.write(secrets_config_file)

	del secrets_config

# create parser instance
config_parser = ConfigParser(interpolation=ExtendedInterpolation())

# read .ini files
file_paths = glob.glob('./config/*.ini')
config_parser.read(filenames=file_paths)

# get current environment
try:
	global ENV
	ENV = os.environ['FLASK_ENV'].upper()
	if ENV != "DEVELOPMENT":
		sentry_sdk.init(
			dsn="https://bb302e59e8e142cc95476900c24156fd@o376793.ingest.sentry.io/5197984",
			integrations=[FlaskIntegration()]
		)
	assert ENV in [i.name for i in list(Environments)]
except KeyError as e:
	raise KeyError("Unable to find `FLASK_ENV` environment variable.")

try:
	global LOCAL
	LOCAL = bool(int(os.environ['LOCAL']))
except KeyError as e:
	raise KeyError("Unable to find `LOCAL` environment variable.")

global CONFIG
CONFIG = config_parser[ENV]