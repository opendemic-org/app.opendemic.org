import re
import uuid

uuid4_regex = re.compile(
	pattern="[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
	flags=re.I
)


def verify_uuid_regex(s: str) -> bool:
	r = re.compile(pattern=uuid4_regex)
	try:
		response = bool(r.fullmatch(s))
	except TypeError:
		response = False
	return response


def gen_uuid() -> str:
	return str(uuid.uuid4())
