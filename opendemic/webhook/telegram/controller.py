import time
import os
import random
from config.config import CONFIG, ENV, Environments, LOCAL, logger
from config.types import TelegramBotCommand, Symptoms
from telebot.types import Update
from flask import Blueprint, request, abort
import datetime
from opendemic.webhook.log.model import log_action, log_sent_message
from opendemic.human.human import Human
from opendemic.webhook.telegram.api_helpers import get_telegram_menu, get_telegram_bot_instance, \
    get_webhook_update, make_reply_keyboard_markup
from opendemic.webhook.telegram.model import TelegramCommand

blueprint = Blueprint('telegram_webhook', __name__)


@blueprint.route('/telegram/<string:token>', methods=['POST'])
def telegram(token):
    # authenticate webhook
    if token != CONFIG.get('webhook_token'):
        abort(404)

    # fetch and validate request content type
    if request.headers.get('content-type') == 'application/json':
        return process_telegram_update(update=get_webhook_update(request=request))
    else:
        abort(403)


def fulfill_log_symptom(human: Human, symptom_name: str) -> bool:
    bot = get_telegram_bot_instance()

    try:
        human.log_symptom(symptom_name=symptom_name)

        log_sent_message(bot.send_message(
            chat_id=human.telegram_human_id,
            text="Noted!"
        ), human_id=human.id)
    except Exception as e:
        logger.error(e)
        return False
    return True


def fulfill_my_map_request(human: Human) -> bool:
    bot = get_telegram_bot_instance()
    try:
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
        logger.error(e)
        return False
    return True


def fulfill_help_request(human: Human) -> bool:
    bot = get_telegram_bot_instance()
    try:
        log_sent_message(bot.send_message(
            chat_id=human.telegram_human_id,
            text="Click here to talk to us: @OpendemicTeam"
        ), human_id=human.id)
    except Exception as e:
        logger.error(e)
        return False
    return True


def fulfill_start_telegram_command(human: Human) -> bool:
    bot = get_telegram_bot_instance()
    try:
        log_sent_message(bot.send_message(
            chat_id=human.telegram_human_id,
            text="Welcome back!",
            reply_markup=get_telegram_menu()
        ), human_id=human.id)
    except Exception as e:
        logger.error(e)
        return False
    return True


def fulfill_report_telegram_command(human: Human) -> bool:
    bot = get_telegram_bot_instance()
    try:
        log_sent_message(bot.send_message(
            chat_id=human.telegram_human_id,
            text="See options below 👇",
            reply_markup=get_telegram_menu()
        ), human_id=human.id)
    except Exception as e:
        logger.error(e)
        return False
    return True


def fulfill_invalid_telegram_command(human: Human) -> bool:
    bot = get_telegram_bot_instance()
    try:
        log_sent_message(bot.send_message(
            chat_id=human.telegram_human_id,
            text="Oops... This command is not valid. Type `/` to see valid commands.",
            reply_markup=get_telegram_menu()
        ), human_id=human.id)
    except Exception as e:
        logger.error(e)
        return False
    return True


def fulfill_intent(intent: str, human_id: str) -> bool:
    if human_id is None:
        return False
    human = Human(human_id=human_id)

    if "Report fever" in intent:
        return fulfill_log_symptom(human=human, symptom_name=Symptoms.FEVER.value)
    elif "Report cough" in intent:
        return fulfill_log_symptom(human=human, symptom_name=Symptoms.COUGH.value)
    elif "Report shortness of breath" in intent:
        return fulfill_log_symptom(human=human, symptom_name=Symptoms.SHORTNESS_OF_BREATH.value)
    elif "My Map" in intent:
        return fulfill_my_map_request(human=human)
    elif "Help" in intent:
        return fulfill_help_request(human=human)

    return True


def fulfill_telegram_command(telegram_command: TelegramCommand, human_id: str):
    if not isinstance(telegram_command, TelegramCommand):
        logger.error(
            TypeError("Expected `telegram_command` to be of type TelegramCommand. Got {}".format(
                type(telegram_command)
            ))
        )

    if human_id is None:
        return False
    human = Human(human_id=human_id)

    if not TelegramBotCommand.has_value(telegram_command.command):
        return fulfill_invalid_telegram_command(human=human)
    elif telegram_command.command == TelegramBotCommand.START.value:
        return fulfill_start_telegram_command(human=human)
    elif telegram_command.command == TelegramBotCommand.HELP.value:
        return fulfill_help_request(human=human)
    elif telegram_command.command == TelegramBotCommand.REPORT.value:
        return fulfill_report_telegram_command(human=human)
    elif telegram_command.command == TelegramBotCommand.MY_MAP.value:
        return fulfill_my_map_request(human=human)

    return True


def process_telegram_update(update: Update):
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

    logger.debug("[TELEGRAM WEBHOOK REQUEST] human : {}".format(telegram_human_id))
    logger.debug("[TELEGRAM WEBHOOK REQUEST] timestamp : {}".format(telegram_message_timestamp))
    logger.debug("[TELEGRAM WEBHOOK REQUEST] message : {}".format(telegram_message_id))

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
        fulfill_intent(
            intent=callback_data,
            human_id=human_id
        )

    elif is_message:

        # case text
        if message_content_type == 'text':

            # case command
            if message_is_command:

                # process command
                fulfill_telegram_command(
                    telegram_command=telegram_command,
                    human_id=human_id
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
                    valid_intent = fulfill_intent(
                        intent=message_text,
                        human_id=human_id
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

