from config.config import CONFIG, logger
from flask import Blueprint, render_template, abort, request
from opendemic.human.model import Human
from opendemic.map.model import get_risky_humans_geojson

blueprint = Blueprint('maps', __name__)


@blueprint.route('/map/<string:human_id>', methods=['GET'])
def local_map(human_id):
	try:
		human = Human(human_id=human_id)
	except Exception as e:
		logger.error(e)
		abort(403)

	# get most recent coordinates
	most_recent_location = human.get_most_recent_location()
	if most_recent_location is None:
		return "Nothing to show. Share your location first.", 200
	else:
		lat, lng = most_recent_location

	self_lat_lng = [lng, lat]
	self_geojson_feature = {
		'type': "Point",
		'coordinates': self_lat_lng
	}

	risky_humans_geojson = get_risky_humans_geojson(lat=lat, lng=lng)

	return render_template(
		'map.html',
		self_geojson_feature=self_geojson_feature,
		self_lat_lng=self_lat_lng,
		risky_humans_geojson=risky_humans_geojson,
		km_radius=int(CONFIG.get('km_radius')),
		include_legend=True,
		zoom_level=9
	)


@blueprint.route('/global/<string:token>', methods=['GET'])
def global_map(token):
	if token != CONFIG.get('global-map-token'):
		abort(403)

	data = dict()
	data['lat'] = request.args.get('lat')
	data['lng'] = request.args.get('lng')

	if data['lat'] is not None and data['lng'] is not None:
		self_lat_lng = [data['lng'], data['lat']]
	else:
		self_lat_lng = [-73.966912, 40.715857]

	risky_humans_geojson = get_risky_humans_geojson(lat=data['lat'], lng=data['lng'])

	return render_template(
		'map.html',
		self_geojson_feature=None,
		self_lat_lng=self_lat_lng,
		risky_humans_geojson=risky_humans_geojson,
		km_radius=0,
		include_legend=True,
		zoom_level=1
	)
