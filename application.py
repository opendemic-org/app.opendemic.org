from opendemic import create_app
from flask import url_for

application = create_app()

if __name__ == "__main__":
	application.run()
	# application.run(use_reloader=False)
