from config.config import CONFIG, ENV, Environments
from config.types import TelegramBotCommand
import time
import os
import random
import datetime
from flask import (
	Blueprint, request, abort, url_for
)
from opendemic.channels.telegram import get_telegram_bot_instance, \
    make_reply_keyboard_markup, TelegramCommand, \
    get_webhook_update, get_telegram_menu
from helpers.url import url_add_params, compose_client_url
from opendemic.fulfillment.command import process_telegram_command
from opendemic.database.sql_db import RDBManager
import datetime
from helpers.formatting import mysql_db_format_value
from config.config import CONFIG, ENV, Environments, LOCAL
from config.types import TelegramBotCommand, Symptoms
import os
from opendemic.channels.telegram import get_telegram_bot_instance
from opendemic.channels.telegram import make_reply_keyboard_markup
from opendemic.models.human import Human

blueprint = Blueprint('telegram_webhook', __name__)


def log_action(
	human_id: str,
	from_human: bool,
	action_type: str,
	telegram_human_id: int = None,
	action_value: str = None,
	local_timestamp: datetime.datetime = None,
	message_id: int = None,
	elapsed_seconds: int = None,
	tag: str = None
):
	# init db connection
	rdb = RDBManager()
	if ENV == Environments.DEVELOPMENT.value:
		print("ACTION VALUE : {}".format(action_value))
	try:
		# run query
		if human_id is not None:
			_, row_count = rdb.execute(
				sql_query="""
						INSERT IGNORE
						INTO `log` (
							`human_id`, `from`, `to`, `action_type`, `action_value`, 
							`created`, `message_id`, `telegram_human_id`)
						VALUES ({}, {}, {}, {}, {}, UTC_TIMESTAMP(), {}, {})
						""".format(
					mysql_db_format_value(value=human_id),
					mysql_db_format_value(value="human" if from_human else "bot"),
					mysql_db_format_value(value="bot" if from_human else "human"),
					mysql_db_format_value(value=action_type),
					mysql_db_format_value(value=action_value),
					mysql_db_format_value(value=message_id),
					mysql_db_format_value(value=telegram_human_id)
				)
			)
	except Exception as e:
		if ENV == Environments.DEVELOPMENT.value:
			print(e)


def log_sent_message(payload: dict, human_id: str = None, tag: str = None):
	# parse payload components
	content_type = 'unknown'
	message_id = None
	telegram_human_id = None
	telegram_message_timestamp = datetime.datetime.now()
	message_text = None
	try:
		content_type = payload.content_type
	except AttributeError as e:
		pass
	try:
		message_id = int(payload.message_id)
	except AttributeError as e:
		pass
	try:
		telegram_human_id = int(payload.chat.id)
	except AttributeError as e:
		pass
	try:
		telegram_message_timestamp = datetime.datetime.fromtimestamp(payload.date)
	except AttributeError as e:
		pass
	try:
		message_text = payload.text
	except AttributeError as e:
		pass

	# log message
	log_action(
		human_id=human_id,
		telegram_human_id=telegram_human_id,
		from_human=False,
		action_type="SENT_CONTENT["+content_type+"]",
		action_value=message_text,
		local_timestamp=telegram_message_timestamp,
		message_id=message_id,
		tag=tag
	)

	return message_id


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


@blueprint.route('/telegram/<string:token>', methods=['POST'])
def telegram(token):

    # authenticate webhook
    if token != CONFIG.get('webhook_token'):
        abort(404)

    # fetch and validate request content type
    if request.headers.get('content-type') == 'application/json':
        update = get_webhook_update(request=request)
        bot = get_telegram_bot_instance()

        # get payload attributes
        if update.callback_query is not None:
            telegram_human_id = int(update.callback_query.from_user.id)
            telegram_message_timestamp = datetime.datetime.fromtimestamp(update.callback_query.message.date)
            telegram_message_id = int(update.callback_query.message.message_id)
            try:
                bot.delete_message(chat_id=telegram_human_id, message_id=telegram_message_id)
            except Exception as e:
                pass
        elif update.message is not None:
            telegram_human_id = int(update.message.from_user.id)
            telegram_message_timestamp = datetime.datetime.fromtimestamp(update.message.date)
            telegram_message_id = int(update.message.message_id)
        else:
            return '', 204

        # authenticate human
        human_exists, human_id = Human.validate_telegram_human_id(telegram_human_id=telegram_human_id)

        # debug prints
        if ENV == Environments.DEVELOPMENT.name:
            print(update)
            print("** [POST] human : {} **".format(telegram_human_id))
            print("** [POST] timestamp : {} **".format(telegram_message_timestamp))
            print("** [POST] message : {} **".format(telegram_message_id))

        # typing animation
        try:
            bot.send_chat_action(
                chat_id=telegram_human_id,
                action='typing'
            )
        except Exception as e:
            return '', 204
        else:
            time.sleep(0.1)

        # detect action type
        is_message = False
        is_callback = False
        callback_data = None
        message_content_type = None
        message_is_command = False
        message_text = None
        telegram_command = None
        is_reply = False
        reply_to_message_id = None
        if update.callback_query is not None:
            # fetch callback data
            callback_data = update.callback_query.data
            is_callback = True
        if update.message is not None:
            # set flag
            is_message = True
            is_reply = update.message.reply_to_message is not None
            if is_reply:
                reply_to_message_id = update.message.reply_to_message.message_id

            # fetch message content type
            message_content_type = update.message.content_type

            # case message is text
            if message_content_type == 'text':
                message_text = update.message.text

                # case message is Telegram command
                if TelegramCommand.is_telegram_command(data=message_text):
                    telegram_command = TelegramCommand(data=message_text)
                    message_is_command = True

        # log message
        if is_callback:
            action_type = CONFIG.get('INTENT-ACTION')
            action_value = callback_data
        elif is_message:
            if message_is_command:
                action_type = CONFIG.get('TELEGRAM-COMMAND')
                action_value = telegram_command.command
            else:
                action_type = message_content_type
                action_value = message_text
        log_action(
            human_id=human_id,
            telegram_human_id=telegram_human_id,
            from_human=True,
            action_type=action_type,
            action_value=action_value,
            local_timestamp=telegram_message_timestamp,
            message_id=telegram_message_id
        )

        # redirect to landing unless
        if human_exists:
            # fetch human
            human = Human(human_id=human_id)
        else:
            try:
                log_sent_message(bot.send_message(
                    chat_id=telegram_human_id,
                    text="Welcome to Opendemic!",
                    reply_markup=get_telegram_menu()
                ), human_id=human_id)
            except Exception as e:
                return '', 204
            else:
                human = Human.new(
                    telegram_human_id=telegram_human_id
                )

                log_sent_message(bot.send_message(
                    chat_id=telegram_human_id,
                    text="""
                        *Opendemic* is an non-profit anonymous COVID-19 proximity alert system.
                        
    Here is how it works ⬇️:
    
    1. Anonymously share your location and symptoms as much as you can (we'll send you reminders to prompt you)
    2. You'll get an alert if you've been in close proximity to a potential COVID-19 case
    3. *Opendemic* will only share anonymous data with public health authorities 
                    """,
                    parse_mode='markdown',
                    reply_markup=get_telegram_menu()
                ), human_id=human_id)

                return '', 204

        # case callback
        if is_callback:
            # process callback
            process_intent(
                intent=callback_data,
                human_id=human_id,
                telegram_human_id=telegram_human_id
            )

        elif is_message:

            # case text
            if message_content_type == 'text':

                # case command
                if message_is_command:

                    # process command
                    process_telegram_command(
                        telegram_command=telegram_command,
                        human_id=human_id,
                        telegram_human_id=telegram_human_id
                    )

                # case free-form message
                else:
                    if is_reply:
                        log_action(
                            human_id=human_id,
                            telegram_human_id=telegram_human_id,
                            from_human=True,
                            action_type="REPLY_TO[{}]".format(reply_to_message_id),
                            action_value=message_text,
                            local_timestamp=telegram_message_timestamp,
                            message_id=telegram_message_id,
                            tag=CONFIG.get('REFER-REPLY-ACTION')
                        )
                    else:
                        valid_intent = process_intent(
                            intent=message_text,
                            human_id=human_id,
                            telegram_human_id=telegram_human_id
                        )
                        if not valid_intent:
                            # log_sent_message(bot.reply_to(
                            #     message=update.message,
                            #     text=random.choice([
                            #         "Sorry, we are still training Opendemic... ",
                            #         "Apologies, we are still training Opendemic to learn natural language...",
                            #         "Woops, Opendemic hasn't been trained to understand that just yet."
                            #     ])
                            # ), human_id=human_id)
                            try:
                                log_sent_message(bot.send_message(
                                    chat_id=telegram_human_id,
                                    text="Please use '/' commands to communicate with *Opendemic*.",
                                    parse_mode="Markdown"
                                ), human_id=human_id)
                            except Exception as e:
                                return '', 204

            # case location
            elif message_content_type == 'location':
                try:
                    log_sent_message(bot.reply_to(
                        message=update.message,
                        text=random.choice([
                            "Thanks for sharing your location 🙏",
                            "Great, got it!",
                            "Thanks! We'll keep that secure."
                        ])
                    ), human_id=human_id)
                except Exception as e:
                    return '', 204
                else:
                    human.log_location(
                        latitude=update.message.location.latitude,
                        longitude=update.message.location.longitude
                    )

            # case photo
            elif message_content_type == 'photo':
                try:
                    log_sent_message(bot.reply_to(
                        message=update.message,
                        text=random.choice([
                            "Thanks for the pic! But we can't process it just yet.",
                            "Cannot process photos just yet, though we are sure that's a great pic!"
                        ])
                    ), human_id=human_id)
                    log_sent_message(bot.send_message(
                        chat_id=telegram_human_id,
                        text="Please use '/' commands to communicate with *Opendemic*.",
                        parse_mode="Markdown"
                    ), human_id=human_id)
                except Exception:
                    return '', 204

            # case documents
            elif message_content_type == 'document':
                try:
                    log_sent_message(bot.reply_to(
                        message=update.message,
                        text=random.choice([
                            "Thanks for the document! But we can't process it just yet.",
                            "Cannot process photos just yet, though we are sure that's a great document!"
                        ])
                    ), human_id=human_id)
                    log_sent_message(bot.send_message(
                        chat_id=telegram_human_id,
                        text="Please use '/' commands to communicate with *Opendemic*.",
                        parse_mode="Markdown"
                    ), human_id=human_id)
                except Exception as e:
                    return '', 204

            # case sticker
            elif message_content_type == 'sticker':
                try:
                    log_sent_message(bot.reply_to(
                        message=update.message,
                        text=random.choice([
                            "Thanks for the sticker! But we can't process it just yet.",
                            "Cannot process stickers just yet, though that looks like a great sticker!"
                        ])
                    ), human_id=human_id)
                    log_sent_message(bot.send_message(
                        chat_id=telegram_human_id,
                        text="Please use '/' commands to communicate with *Opendemic*.",
                        parse_mode="Markdown"
                    ), human_id=human_id)
                except Exception:
                    return '', 204

        return '', 204
    else:
        abort(403)
