from config.config import CONFIG, ENV, Environments, LOCAL, logger
from config.types import TelegramBotCommand, Symptoms
import time
import os
import random
from flask import Blueprint, request, abort
from opendemic.database.sql_db import RDBManager
import datetime
from helpers.formatting import mysql_db_format_value
from opendemic.webhook.log.model import log_action, log_sent_message
from opendemic.human.human import Human
import telebot
from telebot import types
import re

blueprint = Blueprint('telegram_webhook', __name__)

telegram_command_data_regex = "^(/){1}[a-zA-Z0-9_]+$|^(/){1}[a-zA-Z0-9_]+\s{1}[a-zA-Z0-9_]{1}[a-zA-Z0-9_\-\s]*$"
telegram_command_regex = "^(/){1}[a-zA-Z0-9_]+"
telegram_command_payload_regex = "^(/){1}[a-zA-Z0-9_]+"


class TelegramCommand(object):
    _data = None
    _command = None
    _payload = None
    _bot = None

    def __init__(self, data):
        if not self.is_telegram_command(data=data):
            raise ValueError("Wrong data format for command")

        self._bot = get_telegram_bot_instance()
        self._data = data
        self._command = re.search(telegram_command_regex, data).group(0).replace("/", "")
        self._payload = " ".join(data.split(" ")[1:]) if len(data.split(" ")) >= 2 else None

    @staticmethod
    def is_telegram_command(data):
        return bool(re.fullmatch(pattern=telegram_command_data_regex, string=data))

    @property
    def data(self):
        return self._data

    @property
    def command(self):
        return self._command

    @property
    def payload(self):
        return self._payload


def get_telegram_bot_instance():
    bot = telebot.TeleBot(CONFIG.get('telegram-credentials-telegram-token'))
    return bot


def make_reply_keyboard_markup(markup_map: list, column_stacked: bool = True) -> types.InlineKeyboardMarkup:
    # validate input
    if not isinstance(markup_map, list):
        return None
    if len(markup_map) == 0:
        return None

    # build keyboard
    keyboard_markup = types.InlineKeyboardMarkup()
    if column_stacked:
        for item in markup_map:
            keyboard_markup.add(
                types.InlineKeyboardButton(
                    text=item['text'] if 'text' in item else None,
                    url=item['url'] if 'url' in item else None,
                    callback_data=item['callback_data'] if 'callback_data' in item else None
                )
            )
    else:
        button_list = []
        for item in markup_map:
            button_list.append(
                types.InlineKeyboardButton(
                    text=item['text'] if 'text' in item else None,
                    url=item['url'] if 'url' in item else None,
                    callback_data=item['callback_data'] if 'callback_data' in item else None
                )
            )
        keyboard_markup.row(*button_list)

    return keyboard_markup


def register_webhook_url():
    bot = get_telegram_bot_instance()
    bot.remove_webhook()
    time.sleep(0.1)
    if LOCAL:
        url = os.path.join(CONFIG.get('local-base-url'), "webhook/telegram", CONFIG.get('webhook_token'))
    else:
        url = os.path.join(CONFIG.get('base-url'), "webhook/telegram", CONFIG.get('webhook_token'))
    if ENV == Environments.DEVELOPMENT.value:
        print("Registering Telegram webhook: {}".format(url))
    bot.set_webhook(url=url)


def get_webhook_update(request):
    return types.Update.de_json(request.stream.read().decode("utf-8"))


def get_telegram_menu():
    markup = types.ReplyKeyboardMarkup()
    report_location_btn = types.KeyboardButton('📍 Report Location', request_location=True)
    report_fever_btn = types.KeyboardButton('🤒 Report fever')
    report_cough_btn = types.KeyboardButton('😷 Report cough')
    report_shortness_of_breath_btn = types.KeyboardButton('😤 Report shortness of breath')
    my_map_btn = types.KeyboardButton('🌍 My Map')
    help_btn = types.KeyboardButton('👤 Help')
    markup.row(report_location_btn)
    markup.row(report_fever_btn, report_cough_btn)
    markup.row(report_shortness_of_breath_btn)
    markup.row(my_map_btn)
    markup.row(help_btn)
    return markup


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


@blueprint.route('/telegram/<string:token>', methods=['POST'])
def telegram(token):
    # authenticate webhook
    if token != CONFIG.get('webhook_token'):
        abort(404)

    # fetch and validate request content type
    if request.headers.get('content-type') == 'application/json':
        return process_telegram_update(update = get_webhook_update(request=request))
    else:
        abort(403)


def process_telegram_update(update):
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

    logger.debug(update)
    logger.debug("** [POST] human : {} **".format(telegram_human_id))
    logger.debug("** [POST] timestamp : {} **".format(telegram_message_timestamp))
    logger.debug("** [POST] message : {} **".format(telegram_message_id))

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

    # authenticate human
    human_exists, human_id = Human.validate_telegram_human_id(telegram_human_id=telegram_human_id)

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

