from flask import Blueprint, Response, request
from opendemic.human.model import Human
from opendemic.human.location.geo import Coordinate
import json
from enum import Enum

blueprint = Blueprint('alert', __name__)


class AlertResourceFields(Enum):
	LATITUDE = 'lat'
	LONGITUDE = 'lng'

	@classmethod
	def value_to_member_name(cls, value):
		if cls.has_value(value):
			return cls._value2member_map_[value].name

	@classmethod
	def has_value(cls, value):
		return value in cls._value2member_map_


@blueprint.route('/alert', methods=['GET'])
def alert():
	# get URL parameters
	params = dict()
	params[AlertResourceFields.LATITUDE.value] = request.args.get(AlertResourceFields.LATITUDE.value)
	params[AlertResourceFields.LONGITUDE.value] = request.args.get(AlertResourceFields.LONGITUDE.value)

	# validate URL parameters
	validation_error_response = []
	for param_name in params:
		# validate existence
		if params[param_name] is None:
			validation_error_response.append({
				"error": "attribute `{}` not found".format(param_name)
			})

		# validate LATITUDE
		if param_name == AlertResourceFields.LATITUDE.value:
			lat_val, lat_error = Coordinate.validate_latitude(lat=params[param_name])
			if not lat_val:
				validation_error_response.append({
					"error": str(lat_error)
				})

		# validate LONGITUDE
		if param_name == AlertResourceFields.LONGITUDE.value:
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

	# get alert message
	alert_message = Human.get_proximity_alert(
		lat=params[AlertResourceFields.LATITUDE.value],
		lng=params[AlertResourceFields.LONGITUDE.value]
	)

	response = Response(
		response=json.dumps({"alert_message": alert_message}),
		status=200,
		mimetype='application/json'
	)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
