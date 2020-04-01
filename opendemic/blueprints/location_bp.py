from config.config import CONFIG, ENV, Environments
from flask import Blueprint, Response, render_template, abort, request
from opendemic.controllers.human import Human, get_all_risky_humans, get_confirmed_cases_geojson
from opendemic.controllers.geo import Coordinate
import json
from enum import Enum
import math

blueprint = Blueprint('location', __name__)


class LocationResourceFields(Enum):
	FINGERPRINT = 'fingerprint'
	LATITUDE = 'lat'
	LONGITUDE = 'lng'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_


@blueprint.route('/location', methods=['GET'])
def location():
	if request.method == 'GET':
		# get URL parameters
		params = dict()
		params[LocationResourceFields.FINGERPRINT.value] = request.args.get(LocationResourceFields.FINGERPRINT.value)
		params[LocationResourceFields.LATITUDE.value] = request.args.get(LocationResourceFields.LATITUDE.value)
		params[LocationResourceFields.LONGITUDE.value] = request.args.get(LocationResourceFields.LONGITUDE.value)

		# validate URL parameters
		validation_error_response = []
		for param_name in params:
			# validate existence
			if params[param_name] is None:
				validation_error_response.append({
					"error": "attribute `{}` not found".format(param_name)
				})

			# validate FINGERPRINT
			if param_name == LocationResourceFields.FINGERPRINT.value:
				fingerprint_val, fingerprint_error = Human.validate_fingerprint(
					fingerprint=params[LocationResourceFields.FINGERPRINT.value]
				)
				if not fingerprint_val:
					validation_error_response.append({
						"error": str(fingerprint_error)
					})


			# validate LATITUDE
			if param_name == LocationResourceFields.LATITUDE.value:
				lat_val, lat_error = Coordinate.validate_latitude(lat=params[param_name])
				if not lat_val:
					validation_error_response.append({
						"error": str(lat_error)
					})

			# validate LONGITUDE
			if param_name == LocationResourceFields.LONGITUDE.value:
				lng_val, lng_error = Coordinate.validate_longitude(lng=params[param_name])
				if not lng_val:
					validation_error_response.append({
						"error": str(lng_error)
					})

		if len(validation_error_response) > 0:
			response = Response(
				response=json.dumps(validation_error_response),
				status=403,
				mimetype='application/json'
			)
			response.headers.add('Access-Control-Allow-Origin', '*')
			return response

		# authenticate
		human = Human.get_human_from_fingerprint(fingerprint=params[LocationResourceFields.FINGERPRINT.value])
		if human is None:
			human = Human.new(fingerprint=params[LocationResourceFields.FINGERPRINT.value])

		# log human location
		try:
			human.log_location(
				latitude=float(params[LocationResourceFields.LATITUDE.value]),
				longitude=float(params[LocationResourceFields.LONGITUDE.value])
			)
		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)

		# return risky humans
		risky_humans = get_all_risky_humans(days_window=int(CONFIG.get('days_window')))
		risky_humans_geojson = get_confirmed_cases_geojson()
		for risky_human in risky_humans:
			risky_humans_geojson["features"].append({
				'type': 'Feature',
				"properties": {
					"mag": risky_human['risk_level']
				},
				'geometry': {
					'type': 'Point',
					'coordinates': [float(risky_human['longitude']), float(risky_human['latitude'])]
				}
			})
		response = Response(
			response=json.dumps(risky_humans_geojson),
			status=200,
			mimetype='application/json'
		)
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response