from config.config import logger
from flask import Blueprint, Response, request
from opendemic.human.model import create_human, get_human_from_fingerprint
import json
from opendemic.human.location.util import Coordinate
from opendemic.human.symptom.types import Symptoms
from enum import Enum

blueprint = Blueprint('symptom', __name__)


class SymptomResourceFields(Enum):
	FINGERPRINT = 'fingerprint'
	SYMPTOMS = 'symptoms'
	SYMPTOMS_FEVER = 'fever'
	SYMPTOMS_COUGH = 'cough'
	SYMPTOMS_ANOSMIA = 'anosmia'
	SYMPTOMS_DIARRHEA = 'diarrhea'
	SYMPTOMS_ABDOMINAL_PAIN = 'abPain'
	SYMPTOMS_FATIGUE = 'fatigue'
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
	SymptomResourceFields.SYMPTOMS_ANOSMIA.value: Symptoms.ANOSMIA.value,
	SymptomResourceFields.SYMPTOMS_DIARRHEA.value: Symptoms.DIARRHEA.value,
	SymptomResourceFields.SYMPTOMS_ABDOMINAL_PAIN.value: Symptoms.ABDOMINAL_PAIN.value,
	SymptomResourceFields.SYMPTOMS_FATIGUE.value: Symptoms.FATIGUE.value,
	SymptomResourceFields.SYMPTOMS_CONFIRMED_COVID.value: Symptoms.CONFIRMED_COVID19.value
}


@blueprint.route('/symptom', methods=['POST'])
def symptom():
	if request.method == 'POST':
		payload = json.loads(request.data)

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

		human = get_human_from_fingerprint(fingerprint=fingerprint)
		if human is None:
			human = create_human(fingerprint=fingerprint)

		if SymptomResourceFields.LOCATION.value in payload:
			if SymptomResourceFields.LOCATION_LAT.value in payload[SymptomResourceFields.LOCATION.value] and \
					SymptomResourceFields.LOCATION_LNG.value in payload[SymptomResourceFields.LOCATION.value]:
				lat = payload[SymptomResourceFields.LOCATION.value][SymptomResourceFields.LOCATION_LAT.value]
				lng = payload[SymptomResourceFields.LOCATION.value][SymptomResourceFields.LOCATION_LNG.value]
				lat_val, lat_error = Coordinate.validate_latitude(lat=lat)
				lng_val, lng_error = Coordinate.validate_longitude(lng=lng)

				if lat_val and lng_val:
					try:
						lat = float(lat)
						lng = float(lng)
					except ValueError as val_err:
						logger.error(val_err)
					except TypeError as type_err:
						logger.error(type_err)
					else:
						logger.debug("logging location at {}, {}".format(lat, lng))
						human.log_location(latitude=lat, longitude=lng, send_alert=False)
				else:
					logger.error(lat_val)
					logger.error(lng_val)

		if SymptomResourceFields.SYMPTOMS.value in payload:
			symptoms = payload[SymptomResourceFields.SYMPTOMS.value]
			for symptom_key in symptoms:
				if symptoms[symptom_key] == 1 and symptom_key in SYMPTOMS_MAP:
					logged_symptom_success = human.log_symptom(symptom_name=SYMPTOMS_MAP[symptom_key])
					if logged_symptom_success:
						logger.debug("logged symptom {}".format(SYMPTOMS_MAP[symptom_key]))
					else:
						logger.error(Exception("could not log symptom : {}".format(SYMPTOMS_MAP[symptom_key])))

		response = Response(
			response=json.dumps({
				"status": "OK"
			}),
			status=200,
			mimetype='application/json'
		)
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response
