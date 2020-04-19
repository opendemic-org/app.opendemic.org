class Coordinate(object):
	_lat = None
	_lng = None

	def __init__(self, lat: float, lng: float) -> (bool, Exception):
		if not isinstance(lat, float):
			try:
				lat = float(lat)
			except Exception as a:
				raise TypeError('Expected `lat` to be float or float-able. Received `{}`'.format(type(lat)))
		if lat < -90 or lat > 90:
			raise ValueError('Expected `lat` to be between -90 and 90. Got {}'.format(lat))

		if not isinstance(lng, float):
			try:
				lng = float(lng)
			except Exception as a:
				raise TypeError('Expected `lng` to be float or float-able. Received `{}`'.format(type(lng)))
		if lng < -180 or lng > 180:
			raise ValueError('Expected `lng` to be between -90 and 90. Got {}'.format(lng))

		self._lat = lat
		self._lng = lng

	@staticmethod
	def validate_latitude(lat: float):
		if not isinstance(lat, float):
			try:
				lat = float(lat)
			except Exception as a:
				return False, TypeError('Expected `lat` to be float or float-able. Received `{}`'.format(type(lat)))
		if lat < -90 or lat > 90:
			return False, ValueError('Expected `lat` to be between -90 and 90. Got {}'.format(lat))

		return True, None

	@staticmethod
	def validate_longitude(lng: float):
		if not isinstance(lng, float):
			try:
				lng = float(lng)
			except Exception as a:
				return False, TypeError('Expected `lng` to be float or float-able. Received `{}`'.format(type(lng)))
		if lng < -180 or lng > 180:
			return False, ValueError('Expected `lng` to be between -90 and 90. Got {}'.format(lng))

		return True, None



