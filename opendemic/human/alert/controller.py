from flask import Blueprint, Response, request
from opendemic.human.model import get_proximity_alert
from opendemic.human.location.util import Coordinate
import json
from opendemic.map.model import CoordinateType

blueprint = Blueprint('alert', __name__)


def validate_alert_url_params(params: dict) -> list:
	validation_errors = []
	for param_name in params:
		if params[param_name] is None:
			validation_errors.append({
				"error": "attribute `{}` not found".format(param_name)
			})

		if param_name == CoordinateType.LATITUDE.value:
			lat_val, lat_error = Coordinate.validate_latitude(lat=params[param_name])
			if not lat_val:
				validation_errors.append({
					"error": str(lat_error)
				})

		if param_name == CoordinateType.LONGITUDE.value:
			lng_val, lng_error = Coordinate.validate_longitude(lng=params[param_name])
			if not lng_val:
				validation_errors.append({
					"error": str(lng_error)
				})

		return validation_errors


@blueprint.route('/alert', methods=['GET'])
def alert():
	params = dict()
	params[CoordinateType.LATITUDE.value] = request.args.get(CoordinateType.LATITUDE.value)
	params[CoordinateType.LONGITUDE.value] = request.args.get(CoordinateType.LONGITUDE.value)

	validation_errors = validate_alert_url_params(params=params)

	if len(validation_errors) > 0:
		response = Response(
			response=json.dumps(validation_errors),
			status=403,
			mimetype='application/json'
		)
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

	alert_message = get_proximity_alert(
		lat=params[CoordinateType.LATITUDE.value],
		lng=params[CoordinateType.LONGITUDE.value]
	)

	response = Response(
		response=json.dumps({"alert_message": alert_message}),
		status=200,
		mimetype='application/json'
	)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
