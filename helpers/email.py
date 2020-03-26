"""
s = "david-hachuel@gmail. hello@auggi.ai, test@he hello@auggi-health.aosssss helloworld@poopenshafc.co;helloworld@poopenshafc.co ;vs;lhelloworld@poopenshafc.co"

res = email_regex_search(s)
"""
import re
import uuid

email_search_regex = re.compile(
	pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,24}", # max domain extension length is 24 characters
	flags=re.I
)


def email_regex_search(text):
	if not isinstance(text, str):
		return []
	r = re.compile(pattern=email_search_regex)
	try:
		response = r.findall(string=text)
	except Exception as e:
		return []
	else:
		return response

