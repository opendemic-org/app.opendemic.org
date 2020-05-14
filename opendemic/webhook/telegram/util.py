from config.config import CONFIG, LOCAL, logger
import time
import os
from telebot import types, TeleBot
from werkzeug.local import LocalProxy
import requests


def get_telegram_bot_instance() -> TeleBot:
    return TeleBot(CONFIG.get('telegram-credentials-telegram-token'))


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


def register_webhook_url() -> bool:
    try:
        time.sleep(0.1)
        if LOCAL:
            url = os.path.join(CONFIG.get('local-base-url'), "webhook/telegram", CONFIG.get('webhook_token'))
        else:
            url = os.path.join(CONFIG.get('base-url'), "webhook/telegram", CONFIG.get('webhook_token'))
        logger.info("[TELEGRAM WEBHOOK] registering webhook: {}".format(url))
        payload = {'url': url}
        session = requests.Session()
        response = session.post(
            url='https://api.telegram.org/bot{}/setWebhook'.format(CONFIG.get('telegram-credentials-telegram-token')),
            data=payload
        )
    except Exception as e:
        logger.error(e)
        return False
    if 'result' in response.json():
        return response.json()['result']
    return False


def get_webhook_update(request: LocalProxy) -> types.Update:
    return types.Update.de_json(request.stream.read().decode("utf-8"))


def get_telegram_menu() -> types.ReplyKeyboardMarkup:
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
