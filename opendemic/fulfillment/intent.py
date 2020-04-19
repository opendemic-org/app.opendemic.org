from config.config import CONFIG, ENV, Environments, LOCAL
from config.types import TelegramBotCommand, Symptoms
import os
from opendemic.channels.telegram import get_telegram_bot_instance
from opendemic.channels.telegram import make_reply_keyboard_markup
from opendemic.models.human import Human
from flask import url_for
from helpers.url import url_add_params, compose_client_url


def process_intent(
	intent: str,
	human_id: str,
	telegram_human_id: int
):
	# initialize bot
	bot = get_telegram_bot_instance()

	# ******************************************************************************************************************
	# COMMAND INTENTS
	# ******************************************************************************************************************
	# REPORT COMMAND
	if "Report fever" in intent:
		try:
			# case existing user
			if human_id is not None:
				# get human
				human = Human(human_id=human_id)

				# send message
				log_sent_message(bot.send_message(
					chat_id=telegram_human_id,
					text="Noted!"
				), human_id=human_id)

				# store measurement fever
				human.log_symptom(symptom_name=Symptoms.FEVER.value)


		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)

		return True

	elif "Report cough" in intent:
		try:
			# case existing user
			if human_id is not None:
				# get human
				human = Human(human_id=human_id)

				# send message
				log_sent_message(bot.send_message(
					chat_id=telegram_human_id,
					text="Noted!"
				), human_id=human_id)

				# store measurement cough
				human.log_symptom(symptom_name=Symptoms.COUGH.value)


		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)

		return True

	elif "Report shortness of breath" in intent:
		try:
			# case existing user
			if human_id is not None:
				# get human
				human = Human(human_id=human_id)

				# send message
				log_sent_message(bot.send_message(
					chat_id=telegram_human_id,
					text="Noted!"
				), human_id=human_id)

				# store measurement shortness of breath
				human.log_symptom(symptom_name=Symptoms.SHORTNESS_OF_BREATH.value)


		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)

		return True

	elif "My Map" in intent:
		try:
			# case existing user
			if human_id is not None:
				# get human
				human = Human(human_id=human_id)

				# send message
				if LOCAL:
					map_url = os.path.join(CONFIG.get('local-base-url'), "map", human.id)
				else:
					map_url = os.path.join(CONFIG.get('base-url'), "map", human.id)
				bot.send_message(
					chat_id=human.telegram_human_id,
					text="See who's around you 👇",
					parse_mode='markdown',
					reply_markup=make_reply_keyboard_markup(markup_map=[
						{'text': "🌍 See Map", 'url': map_url},
					])
				)


		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)

		return True

	# HELP COMMAND
	elif "Help" in intent:
		try:
			log_sent_message(bot.send_message(
				chat_id=telegram_human_id,
				text="Click here to talk to us: @OpendemicTeam"
			), human_id=human_id)
		except Exception as e:
			if ENV == Environments.DEVELOPMENT.value:
				print(e)

		return True

	return False