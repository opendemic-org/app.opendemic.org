from urllib.parse import urlparse, urlencode
import copy
import os


def url_add_params(url, params):
	new_url = copy.deepcopy(url)
	new_url += ('&' if urlparse(url).query else '?') + urlencode(params)
	return new_url


def compose_client_url(base_url: str, route: str, human_id: str, auth_token: str):
	return os.path.join(base_url, human_id, auth_token, route)
