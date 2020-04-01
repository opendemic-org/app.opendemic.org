from config.config import CONFIG, ENV, Environments
from flask import Blueprint, Response, render_template, abort, request
from opendemic.controllers.human import Human, get_all_risky_humans, get_confirmed_cases_geojson
import json
from enum import Enum

blueprint = Blueprint('symptom', __name__)


class SymptomResourceFields(Enum):
	FINGERPRINT = 'fingerprint'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_


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
