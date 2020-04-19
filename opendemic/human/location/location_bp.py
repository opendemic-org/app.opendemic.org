from config.config import CONFIG, ENV, Environments
from flask import Blueprint, Response, render_template, request
from opendemic.human.model import Human
from opendemic.human.location.geo import Coordinate
import json
from enum import Enum

blueprint = Blueprint('location', __name__)


class LocationResourceFields(Enum):
	FINGERPRINT = 'fingerprint'
	LATITUDE = 'lat'
	LONGITUDE = 'lng'
	INCLUDE_LEGEND = 'include_legend'

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
		params[LocationResourceFields.INCLUDE_LEGEND.value] = request.args.get(LocationResourceFields.INCLUDE_LEGEND.value)
		if params[LocationResourceFields.INCLUDE_LEGEND.value] is None:
			params[LocationResourceFields.INCLUDE_LEGEND.value] = True
		else:
			try:
				include_legend = bool(eval(str(params[LocationResourceFields.INCLUDE_LEGEND.value]).capitalize()))
			except NameError as e:
				if ENV == Environments.DEVELOPMENT.value:
					print(e)
				include_legend = True
			params[LocationResourceFields.INCLUDE_LEGEND.value] = include_legend

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
				longitude=float(params[LocationResourceFields.LONGITUDE.value]),
				send_alert=False
			)
		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)

		# get risky humans
		risky_humans = Human.get_risky_humans(
			lat=params[LocationResourceFields.LATITUDE.value],
			lng=params[LocationResourceFields.LONGITUDE.value],
			days_window=int(CONFIG.get('days_window')),
			km_radius=int(CONFIG.get('km_radius'))
		)
		risky_humans_geojson = {
			"type": "FeatureCollection",
			"src": "https://raw.githubusercontent.com/beoutbreakprepared/nCoV2019/master/latest_data/latestdata.csv",
			"features": []
		}
		if risky_humans is not None:
			for risky_human in risky_humans:
				risky_humans_geojson["features"].append({
					'type': 'Feature',
					"properties": {
						"mag": risky_human['mag']
					},
					'geometry': {
						'type': 'Point',
						'coordinates': [float(risky_human['longitude']), float(risky_human['latitude'])]
					}
				})

		# prepare map response
		self_lat_lng = [params[LocationResourceFields.LONGITUDE.value], params[LocationResourceFields.LATITUDE.value]]
		self_geojson_feature = {
			'type': "Point",
			'coordinates': self_lat_lng
		}

		return render_template('map.html',
							   self_geojson_feature=self_geojson_feature,
							   self_lat_lng=self_lat_lng,
							   risky_humans_geojson=risky_humans_geojson,
							   km_radius=int(CONFIG.get('km_radius')),
							   include_legend=params[LocationResourceFields.INCLUDE_LEGEND.value],
							   zoom_level=9
							   )
