from config.config import CONFIG, ENV, Environments, LOCAL
import os
from config.types import TelegramBotCommand
from opendemic.channels.telegram import TelegramCommand, get_telegram_bot_instance, \
	make_reply_keyboard_markup, get_telegram_menu
from telebot import types
from opendemic.models.human import Human
from helpers.url import url_add_params, compose_client_url
import random


def process_telegram_command(
		telegram_command: TelegramCommand,
		human_id: str,
		telegram_human_id: int
):
	# validate type
	if not isinstance(telegram_command, TelegramCommand):
		raise TypeError("Expected `telegram_command` to be of type TelegramCommand. Got {}".format(
			type(telegram_command)
		))

	# initialize bot
	bot = get_telegram_bot_instance()

	# is valid command
	if not TelegramBotCommand.has_value(telegram_command.command):
		# invalid command
		log_sent_message(bot.send_message(
			chat_id=telegram_human_id,
			text="Oops... This command is not valid. Type `/` to see valid commands.",
			reply_markup=get_telegram_menu()
		), human_id=human_id)

	# ------------------------------------------------------------------------------------------------------------------
	# start command
	# ------------------------------------------------------------------------------------------------------------------
	elif telegram_command.command == TelegramBotCommand.START.value:
		log_sent_message(bot.send_message(
			chat_id=telegram_human_id,
			text="Welcome back!",
			reply_markup=get_telegram_menu()
		), human_id=human_id)

	# ------------------------------------------------------------------------------------------------------------------
	# help command
	# ------------------------------------------------------------------------------------------------------------------
	elif telegram_command.command == TelegramBotCommand.HELP.value:
		log_sent_message(bot.send_message(
			chat_id=telegram_human_id,
			text="Click here to talk to us: @OpendemicTeam",
			reply_markup=get_telegram_menu()
		), human_id=human_id)

	# ------------------------------------------------------------------------------------------------------------------
	# report command
	# ------------------------------------------------------------------------------------------------------------------
	elif telegram_command.command == TelegramBotCommand.REPORT.value:
		# case existing user
		if human_id is not None:
			# get human
			human = Human(human_id=human_id)

			# send message
			log_sent_message(bot.send_message(
				chat_id=telegram_human_id,
				text="See options below 👇",
				reply_markup=get_telegram_menu()
			), human_id=human_id)

	# ------------------------------------------------------------------------------------------------------------------
	# my map command
	# ------------------------------------------------------------------------------------------------------------------
	elif telegram_command.command == TelegramBotCommand.MY_MAP.value:
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

