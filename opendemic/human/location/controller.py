from config.config import CONFIG, logger
from flask import Blueprint, Response, render_template, request
from opendemic.human import model
from opendemic.human.location.util import Coordinate
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
    # Fetch or create human, log its location, and return nearby risky humans
    params = create_parameters()
    validation_error_response = validate_location_url_params(params=params)
    if len(validation_error_response) > 0:
        return_invalid_response(validation_error_response)

    human = model.get_human_from_fingerprint(fingerprint=params[LocationResourceFields.FINGERPRINT.value])
    if human is None:
        human, err = model.create_human(fingerprint=params[LocationResourceFields.FINGERPRINT.value])
        if err is not None:
            logger.error(err)
            response = Response(
                response=json.dumps({
                    "error": "Error creating human with fingerprint {}".format(params[LocationResourceFields.FINGERPRINT.value])
                }),
                status=403,
                mimetype='application/json'
            )
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    human.log_location(
        latitude=float(params[LocationResourceFields.LATITUDE.value]),
        longitude=float(params[LocationResourceFields.LONGITUDE.value]),
        send_alert=False)

    self_lat_lng = [params[LocationResourceFields.LONGITUDE.value], params[LocationResourceFields.LATITUDE.value]]
    self_geojson_feature = {
        'type': "Point",
        'coordinates': self_lat_lng
    }

    risky_humans_geojson = model.get_risky_humans_geojson(
        lat=params[LocationResourceFields.LATITUDE.value],
        lng=params[LocationResourceFields.LONGITUDE.value],
        days_window=int(CONFIG.get('days_window')),
        km_radius=int(CONFIG.get('km_radius'))
    )

    return render_template(
        'map.html',
        self_geojson_feature=self_geojson_feature,
        self_lat_lng=self_lat_lng,
        risky_humans_geojson=risky_humans_geojson,
        km_radius=int(CONFIG.get('km_radius')),
        include_legend=params[LocationResourceFields.INCLUDE_LEGEND.value],
        zoom_level=9
    )


def validate_location_url_params(params: dict) -> list:
    # Sanity check for  location parameters
    validation_error_response = []
    for param_name in params:
        if params[param_name] is None:
            validation_error_response.append({
                "error": "attribute `{}` not found".format(param_name)
            })

        if param_name == LocationResourceFields.FINGERPRINT.value:
            fingerprint_val, fingerprint_error = model.validate_fingerprint(
                fingerprint=params[LocationResourceFields.FINGERPRINT.value]
            )
            if not fingerprint_val:
                validation_error_response.append({
                    "error": str(fingerprint_error)
                })

        if param_name == LocationResourceFields.LATITUDE.value:
            lat_val, lat_error = Coordinate.validate_latitude(lat=params[param_name])
            if not lat_val:
                validation_error_response.append({
                    "error": str(lat_error)
                })

        if param_name == LocationResourceFields.LONGITUDE.value:
            lng_val, lng_error = Coordinate.validate_longitude(lng=params[param_name])
            if not lng_val:
                validation_error_response.append({
                    "error": str(lng_error)
                })

    return validation_error_response


def create_parameters() -> dict:
    # Create parameters from a request
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
            logger.error(e)
            include_legend = True
        params[LocationResourceFields.INCLUDE_LEGEND.value] = include_legend
    return params


def return_invalid_response(message: list) -> Response:
    # Return invalid response
    response = Response(
        response=json.dumps(message),
        status=403,
        mimetype='application/json'
    )
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
