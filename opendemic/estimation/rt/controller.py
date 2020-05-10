from config.config import CONFIG, logger
from flask import Blueprint, Response, request
from opendemic.human.location.util import Coordinate
import json
import datetime
from opendemic.estimation.rt.types import RtModelResourceFields
from opendemic.estimation.rt.model import coord_to_fips, fetch_usa_rt_estimate, RtEstimate

blueprint = Blueprint('rt', __name__)


def validate_rt_model_url_params(params: dict) -> list:
	validation_error_response = []
	for param_name in params:
		if params[param_name] is None:
			validation_error_response.append({
				"error": "attribute `{}` not found".format(param_name)
			})

		if param_name == RtModelResourceFields.LATITUDE.value:
			lat_val, lat_error = Coordinate.validate_latitude(lat=params[param_name])
			if not lat_val:
				validation_error_response.append({
					"error": str(lat_error)
				})

		if param_name == RtModelResourceFields.LONGITUDE.value:
			lng_val, lng_error = Coordinate.validate_longitude(lng=params[param_name])
			if not lng_val:
				validation_error_response.append({
					"error": str(lng_error)
				})

		return validation_error_response


@blueprint.route('/rt', methods=['GET'])
def rt():
	params = {
		RtModelResourceFields.LATITUDE.value: request.args.get(RtModelResourceFields.LATITUDE.value),
		RtModelResourceFields.LONGITUDE.value: request.args.get(RtModelResourceFields.LONGITUDE.value)
	}

	validation_error_response = validate_rt_model_url_params(params=params)
	if len(validation_error_response) > 0:
		response = Response(
			response=json.dumps(validation_error_response),
			status=403,
			mimetype='application/json'
		)
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

	fips, county, state, country = coord_to_fips(
		lat=params[RtModelResourceFields.LATITUDE.value],
		lng=params[RtModelResourceFields.LONGITUDE.value]
	)

	rt_estimate: RtEstimate = fetch_usa_rt_estimate(fips=fips)

	def date_serializer(d):
		if isinstance(d, datetime.date):
			return "{}-{}-{}".format(d.year, d.month, d.day)

	response = Response(
		response=json.dumps({
			"request": {
				"lat": params[RtModelResourceFields.LATITUDE.value],
				"lng": params[RtModelResourceFields.LONGITUDE.value]
			},
			"response": {
				"fips": fips,
				"county": county,
				"state": state,
				"country": country,
				"date": rt_estimate.date,
				"rt_estimate": rt_estimate.rt_estimate,
				"rt_low": rt_estimate.rt_low,
				"rt_high": rt_estimate.rt_high
			}
		}, default=date_serializer),
		status=200,
		mimetype='application/json'
	)
	response.headers.add('Access-Control-Allow-Origin', '*')
	return response
