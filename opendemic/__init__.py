import json
from config.config import CONFIG
from flask import Flask, Response, render_template, abort
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from opendemic.channels.telegram import register_webhook_url, get_telegram_menu, get_telegram_bot_instance
from opendemic.database.sql_db import RDBManager
from opendemic.controllers.human import Human, get_all_risky_humans, get_confirmed_cases_geojson, \
    get_all_humans_for_notifications


def send_reminders():
    audience = get_all_humans_for_notifications()

    # create bot
    bot = get_telegram_bot_instance()


    # send to audience
    notify_admin = True
    count = 0
    for member in audience:
        try:
            bot.send_message(
                chat_id=member['telegram_human_id'],
                text="👇 Remember to report your location (always) and symptoms (if any) 👇",
                reply_markup=get_telegram_menu()
            )

        except Exception as e:
            if notify_admin:
                bot.send_message(
                    chat_id=int(CONFIG.get('telegram-credentials-telegram-admin-id')),
                    text="[ADMIN] `send_reminders` exception : {}".format(e)
                )
                notify_admin = False
        else:
            count += 1

    # alert admin
    bot.send_message(
        chat_id=int(CONFIG.get('telegram-credentials-telegram-admin-id')),
        text="[ADMIN] Sent reminder to {}/{} humans.".format(count, len(audience))
    )


def send_daily_report():
    audience = get_all_humans_for_notifications()

    # create bot
    bot = get_telegram_bot_instance()

    # send to audience
    notify_admin = True
    count = 0
    for member in audience:
        try:
            human = Human(human_id=member['id'])

            # get most recent coordinates
            most_recent_location = human.get_most_recent_location()
            if most_recent_location is None:
                return "NOTHING TO SHOW. SHARE YOUR LOCATION FIRST."
            lat, lng = most_recent_location
            human.send_proximity_alert(lat=lat, lng=lng)
            count += 1

        except Exception as e:
            if notify_admin:
                bot.send_message(
                    chat_id=int(CONFIG.get('telegram-credentials-telegram-admin-id')),
                    text="[ADMIN] `send_daily_report` exception : {}".format(e)
                )
                notify_admin = False

    # alert admin
    bot.send_message(
        chat_id=int(CONFIG.get('telegram-credentials-telegram-admin-id')),
        text="[ADMIN] Sent proximity report to {}/{} humans.".format(count, len(audience))
    )


def send_feedback_request():
    audience = get_all_humans_for_notifications()

    # create bot
    bot = get_telegram_bot_instance()

    # send to audience
    notify_admin = True
    count = 0
    for member in audience:
        try:
            bot.send_message(
                chat_id=member['telegram_human_id'],
                text="*[🤙 Feedback Request]* Please share your feedback on the product by clicking here: @OpendemicTeam",
                parse_mode='markdown',
                reply_markup=get_telegram_menu()
            )
        except Exception as e:
            if notify_admin:
                bot.send_message(
                    chat_id=int(CONFIG.get('telegram-credentials-telegram-admin-id')),
                    text="[ADMIN] `send_feedback_request` exception : {}".format(e)
                )
                notify_admin = False
        else:
            count += 1

    # alert admin
    bot.send_message(
        chat_id=int(CONFIG.get('telegram-credentials-telegram-admin-id')),
        text="[ADMIN] Sent feedback request to {}/{} humans.".format(count, len(audience))
    )


def create_worker():
    # create and configure the app
    worker = Flask(__name__, instance_relative_config=True)

    # declare scheduler
    scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})

    # add jobs
    scheduler.add_job(send_reminders, 'cron', args=[], day='*', hour='0, 6, 12, 18', minute='0')
    scheduler.add_job(send_daily_report, 'cron', args=[], day='*', hour='6, 18', minute='0')
    scheduler.add_job(send_feedback_request, 'cron', args=[], day='*/2', hour='8', minute='0')

    # start scheduler
    scheduler.start()

    # index endpoint
    @worker.route('/')
    def index():
        response = Response(
            response=json.dumps({
                "success": True
            }),
            status=200,
            mimetype='application/json'
        )
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    return worker


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=CONFIG.get("app-secret-key-value")
    )
    # add CORS
    cors = CORS(app)

    # register blueprints
    from .blueprints import telegram_bp, maps_bp, location_bp, symptom_bp
    app.register_blueprint(blueprint=telegram_bp.blueprint, url_prefix='/webhook')
    app.register_blueprint(blueprint=location_bp.blueprint, url_prefix='/human')
    app.register_blueprint(blueprint=symptom_bp.blueprint, url_prefix='/human')
    app.register_blueprint(blueprint=maps_bp.blueprint)

    # register Telegram bot
    try:
        register_webhook_url()
    except Exception as exception:
        print("An exception occurred while registering the telegram webhook: ", exception)

    # index endpoint
    @app.route('/')
    def index():
        response = Response(
            response=json.dumps({
                "success": True
            }),
            status=200,
            mimetype='application/json'
        )
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @app.route('/debug-sentry')
    def trigger_error():
        division_by_zero = 1 / 0

    @app.route('/privacy')
    def privacy():
        return render_template(
            template_name_or_list="privacy.html"
        )

    return app




def generate_db_uri():
    return 'mysql://' + CONFIG.get('rds-aurora-mysql-opendemic-username') + ':' + \
                        CONFIG.get('rds-aurora-mysql-opendemic-password') + '@' + \
                        CONFIG.get('rds-aurora-mysql-opendemic-host') + ':' + \
                        CONFIG.get('rds-aurora-mysql-opendemic-port') + '/' +\
                        CONFIG.get('rds-aurora-mysql-opendemic-database')