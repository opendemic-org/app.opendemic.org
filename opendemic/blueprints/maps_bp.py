from config.config import CONFIG, ENV, Environments
from flask import Blueprint, Response, render_template, abort, request
from opendemic.controllers.human import Human, get_all_risky_humans, get_confirmed_cases_geojson


blueprint = Blueprint('maps', __name__)


@blueprint.route('/map/<string:human_id>', methods=['GET'])
def local_map(human_id):
	# get human
	try:
		human = Human(human_id=human_id)
	except Exception as e:
		if ENV == Environments.DEVELOPMENT.value:
			print(e)
		abort(403)

	# get most recent coordinates
	most_recent_location = human.get_most_recent_location()
	if most_recent_location is None:
		return "NOTHING TO SHOW. SHARE YOUR LOCATION FIRST."
	else:
		lat, lng = most_recent_location

	self_lat_lng = [lng, lat]
	self_geojson_feature = {
		'type': "Point",
		'coordinates': self_lat_lng
	}

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

	return render_template('map.html',
		self_geojson_feature=self_geojson_feature,
		self_lat_lng=self_lat_lng,
		risky_humans_geojson=risky_humans_geojson,
		km_radius=int(CONFIG.get('km_radius')),
		include_legend=True,
		zoom_level=9
	)


@blueprint.route('/global_map', methods=['GET'])
def global_map():
	data = {}
	data['lat'] = request.args.get('lat')
	data['lng'] = request.args.get('lng')

	# get most recent coordinates
	if data['lat'] is not None and data['lng'] is not None:
		self_lat_lng = [data['lng'], data['lat']]
	else:
		self_lat_lng = [-73.966912, 40.715857]

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

	return render_template(
		'map.html',
		self_geojson_feature=None,
		self_lat_lng=self_lat_lng,
		risky_humans_geojson=risky_humans_geojson,
		km_radius=0,
		include_legend=True,
		zoom_level=1
	)
