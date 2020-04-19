import json
import datetime
import time
from colorama import init
from colorama import Fore
from flask import g, request
from rfc3339 import rfc3339
from config.config import CONFIG, logger
from flask import Flask, Response
from flask_cors import CORS
from opendemic.webhook.telegram.api_helpers import register_webhook_url, get_telegram_menu, get_telegram_bot_instance
from opendemic.database import RDBManager
from opendemic.human.model import Human
from opendemic.scheduler import create_scheduler
import prometheus_client


CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')
REQUEST_COUNT = prometheus_client.Counter(
    'request_count', 'App Request Count', ['app_name', 'method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = prometheus_client.Histogram('request_latency_seconds', 'Request latency', ['app_name', 'endpoint'])


def create_worker():
    worker = Flask(__name__, instance_relative_config=True)

    # start background scheduler
    background_scheduler = create_scheduler()
    background_scheduler.start()

    @worker.route('/')
    def index():
        return "success", 200

    return worker


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=CONFIG.get("app-secret-key-value")
    )

    # add CORS
    cors = CORS(app)
    init(autoreset=True)

    # register routes
    import opendemic.webhook.telegram.controller as telegram_controller
    from opendemic.contact import controller as contact_controller
    from opendemic.map import controller as map_controller

    from opendemic.human.symptom import symptom_bp
    from opendemic.human.subscription import subscribe_bp
    from opendemic.human.location import location_bp
    from opendemic.human.alert import alert_bp
    app.register_blueprint(blueprint=telegram_controller.blueprint, url_prefix='/webhook')
    app.register_blueprint(blueprint=location_bp.blueprint, url_prefix='/human')
    app.register_blueprint(blueprint=symptom_bp.blueprint, url_prefix='/human')
    app.register_blueprint(blueprint=alert_bp.blueprint, url_prefix='/human')
    app.register_blueprint(blueprint=map_controller.blueprint)
    app.register_blueprint(blueprint=contact_controller.blueprint)
    app.register_blueprint(blueprint=subscribe_bp.blueprint)

    # TODO - move Telegram webhook registration to worker
    try:
        register_webhook_url()
    except Exception as exception:
        logger.error("An exception occurred while registering the telegram webhook: ", exception)

    @app.before_request
    def start_timer():
        g.start = time.time()

    @app.after_request
    def log_request(response):

        if request.path == "/metrics/" or request.path == "/metrics":
            return response
        now = time.time()
        duration = round(now - g.start, 2)
        REQUEST_LATENCY.labels('opendemic', request.path).observe(duration)
        dt = datetime.datetime.fromtimestamp(now)
        timestamp = rfc3339(dt, utc=True)
        REQUEST_COUNT.labels('opendemic', request.method, request.path,
                             response.status_code).inc()

        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        host = request.host.split(':', 1)[0]
        args = dict(request.args)

        log_params = [
            ('method', request.method, 'blue'),
            ('path', request.path, 'blue'),
            ('status', response.status_code, 'yellow'),
            ('duration', duration, 'green'),
            ('time', timestamp, 'magenta'),
            ('ip', ip, 'red'),
            ('host', host, 'red'),
            ('params', args, 'blue')
        ]

        request_id = request.headers.get('X-Request-ID')
        if request_id:
            log_params.append(('request_id', request_id, 'yellow'))

        parts = []
        for name, value, color in log_params:
            part = (Fore.BLUE+name+" = "+Fore.GREEN+str(value))
            parts.append(part)
        line = " ".join(parts)

        app.logger.info(line)

        return response

    @app.route('/')
    def index():
        return "success", 200

    @app.route('/debug-sentry')
    def trigger_error():
        division_by_zero = 1 / 0

    @app.route('/metrics/')
    def metrics():
        return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)
    return app

    # TODO move gauss function to migration
    rdb = RDBManager()
    rdb.pre_execute(sql_query="DROP FUNCTION IF EXISTS gauss;")
    rdb.pre_execute(sql_query="""
        CREATE FUNCTION gauss(mean float, stdev float) RETURNS float
        BEGIN
        set @x=rand(), @y=rand();
        set @gaus = ((sqrt(-2*log(@x))*cos(2*pi()*@y))*stdev)+mean;
        return @gaus;
        END;
    """)
    del rdb

    return app
