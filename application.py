from opendemic import create_app
from flask import url_for
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://bb302e59e8e142cc95476900c24156fd@o376793.ingest.sentry.io/5197984",
    integrations=[FlaskIntegration()]
)
application = create_app()

if __name__ == "__main__":
	application.run()
	# application.run(use_reloader=False)
