from config.config import CONFIG, ENV, Environments
from config.types import Symptoms
from flask import Blueprint, Response, render_template, abort, request
from opendemic.controllers.human import Human, get_all_risky_humans, get_confirmed_cases_geojson
import json
from opendemic.controllers.geo import Coordinate
from enum import Enum

blueprint = Blueprint('symptom', __name__)


class SymptomResourceFields(Enum):
	FINGERPRINT = 'fingerprint'
	SYMPTOMS = 'symptoms'
	SYMPTOMS_FEVER = 'fever'
	SYMPTOMS_COUGH = 'cough'
	SYMPTOMS_SHORTNESS_OF_BREATH = 'shortBreath'
	SYMPTOMS_CONFIRMED_COVID = 'confirmedCovid'
	LOCATION = 'location'
	LOCATION_LAT = 'lat'
	LOCATION_LNG = 'lng'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_

SYMPTOMS_MAP = {
	SymptomResourceFields.SYMPTOMS_FEVER.value: Symptoms.FEVER.value,
	SymptomResourceFields.SYMPTOMS_COUGH.value: Symptoms.COUGH.value,
	SymptomResourceFields.SYMPTOMS_SHORTNESS_OF_BREATH.value: Symptoms.SHORTNESS_OF_BREATH.value,
	SymptomResourceFields.SYMPTOMS_CONFIRMED_COVID.value: Symptoms.CONFIRMED_COVID19.value
}

@blueprint.route('/symptom', methods=['POST'])
def symptom():
	if request.method == 'POST':
		# get payload
		payload = json.loads(request.data)

		# fetch fingerprint
		if SymptomResourceFields.FINGERPRINT.value not in payload:
			response = Response(
				response=json.dumps({
					"error": "attribute `{}` not found".format(SymptomResourceFields.FINGERPRINT.value)
				}),
				status=403,
				mimetype='application/json'
			)
			response.headers.add('Access-Control-Allow-Origin', '*')
			return response

		fingerprint = payload[SymptomResourceFields.FINGERPRINT.value]

		# get human
		try:
			human = Human.get_human_from_fingerprint(fingerprint=fingerprint)
			if human is None:
				human = Human.new(fingerprint=fingerprint)
		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)
			abort(403)

		# process location
		if SymptomResourceFields.LOCATION.value in payload:
			# case coordinate values present
			if SymptomResourceFields.LOCATION_LAT.value in payload[SymptomResourceFields.LOCATION.value] and \
					SymptomResourceFields.LOCATION_LNG.value in payload[SymptomResourceFields.LOCATION.value]:
				# validate lat and lng
				lat = payload[SymptomResourceFields.LOCATION.value][SymptomResourceFields.LOCATION_LAT.value]
				lng = payload[SymptomResourceFields.LOCATION.value][SymptomResourceFields.LOCATION_LNG.value]
				lat_val, lat_error = Coordinate.validate_latitude(lat=lat)
				lng_val, lng_error = Coordinate.validate_longitude(lng=lng)

				# case lat and lng are valid
				if lat_val and lng_val:
					try:
						lat = float(lat)
						lng = float(lng)
					except ValueError:
						if ENV == Environments.DEVELOPMENT.value:
							print("coordinates value error")
					except TypeError:
						if ENV == Environments.DEVELOPMENT.value:
							print("coordinates type error")
					else:
						if ENV == Environments.DEVELOPMENT.value:
							print("logging location at {}, {}".format(lat, lng))
						human.log_location(latitude=lat, longitude=lng, send_alert=False)
				else:
					if ENV == Environments.DEVELOPMENT.value:
						print("invalid coordinates")

		# process symptoms
		if SymptomResourceFields.SYMPTOMS.value in payload:
			symptoms = payload[SymptomResourceFields.SYMPTOMS.value]
			for symptom_key in symptoms:
				if ENV == Environments.DEVELOPMENT.value:
					print('valid symptom : {}'.format(Symptoms.has_value(SYMPTOMS_MAP[symptom_key])))
				# case symptom is present
				if symptoms[symptom_key] == 1 and symptom_key in SYMPTOMS_MAP:
					resp = human.log_symptom(symptom_name=SYMPTOMS_MAP[symptom_key])
					if ENV == Environments.DEVELOPMENT.value:
						print("logged symptom {}".format(SYMPTOMS_MAP[symptom_key]))

		# create response
		response = Response(
			response=json.dumps({
				"status": "OK"
			}),
			status=200,
			mimetype='application/json'
		)
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response
