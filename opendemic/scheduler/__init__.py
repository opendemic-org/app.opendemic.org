from config.config import CONFIG
from apscheduler.schedulers.background import BackgroundScheduler
from opendemic.webhook.telegram.util import get_telegram_menu, get_telegram_bot_instance
from opendemic.human.model import Human, get_all_humans_for_telegram_notifications, HumanProperty


def send_reminders(hours_of_day: list):
	audience = get_all_humans_for_telegram_notifications(hours_of_day=hours_of_day)

	# create bot
	bot = get_telegram_bot_instance()

	# send to audience
	notify_admin = True
	count = 0
	for member in audience:
		try:
			bot.send_message(
				chat_id=member[HumanProperty.TELEGRAM_HUMAN_ID.value],
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
			# try to unsubscribe
			try:
				human = Human(human_id=member[HumanProperty.ID.value])
				human.unsubscribe()
			except Exception as unsb_e:
				pass
		else:
			count += 1

	# alert admin
	bot.send_message(
		chat_id=int(CONFIG.get('telegram-credentials-telegram-admin-id')),
		text="[ADMIN] Sent reminder to {}/{} humans.".format(count, len(audience))
	)


def send_daily_report(hours_of_day: list):
	audience = get_all_humans_for_telegram_notifications(hours_of_day=hours_of_day)

	# create bot
	bot = get_telegram_bot_instance()
	# send to audience
	notify_admin = True
	count = 0
	for member in audience:
		try:
			human = Human(human_id=member[HumanProperty.ID.value])

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


def send_feedback_request(hours_of_day: list):
	audience = get_all_humans_for_telegram_notifications(hours_of_day=hours_of_day)

	# create bot
	bot = get_telegram_bot_instance()

	# send to audience
	notify_admin = True
	count = 0
	for member in audience:
		try:
			bot.send_message(
				chat_id=member[HumanProperty.TELEGRAM_HUMAN_ID.value],
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
			# try to unsubscribe
			try:
				human = Human(human_id=member[HumanProperty.ID.value])
				human.unsubscribe()
			except Exception as unsb_e:
				pass
		else:
			count += 1

	# alert admin
	bot.send_message(
		chat_id=int(CONFIG.get('telegram-credentials-telegram-admin-id')),
		text="[ADMIN] Sent feedback request to {}/{} humans.".format(count, len(audience))
	)


def create_scheduler() -> BackgroundScheduler:
	scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
	scheduler.add_job(send_reminders, 'cron', args=[[8, 20]], day='*', hour='*/2', minute='0')
	scheduler.add_job(send_daily_report, 'cron', args=[[8]], day='*', hour='*/2', minute='0')
	scheduler.add_job(send_feedback_request, 'cron', args=[[10]], day='*/2', hour='*/2', minute='0')
	return scheduler
