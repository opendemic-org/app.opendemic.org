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
from opendemic.fulfillment.intent import process_intent
from opendemic.logging.action import log_action, log_sent_message
from opendemic.controllers.human import Human, validate_telegram_human_id
from telebot import types

from pymessenger.bot import Bot

ACCESS_TOKEN = 'EAACZCRZAZAmZC0MBANvM9a3Crc7cldOs4nSI0oZAcXZCBwgHRcQnlfbPrfauwZC9nOmOAGNMFTZAaOfqGB6V2mfDiSIpgPvpFRYCZCmflfSUw3ktTcgLZBewivZA5euM5lXibEa4U78RCTCZBZBbFrDDcPPcUBBYi78KZAZCJIynwPc3FFrbS8Nm3VECxzZBsEr2tmDMh5wZD'
VERIFY_TOKEN = '37d961ad-da4f-4921-915e-c84f62ade295'


blueprint = Blueprint('fbmessenger_webhook', __name__)


@blueprint.route('/fbmessenger', methods=['POST', 'GET'])
def fbmessenger():
	bot = Bot(ACCESS_TOKEN)

	if request.method == 'GET':
		"""Before allowing people to message your bot, Facebook has implemented a verify token
		that confirms all requests that your bot receives came from Facebook."""
		token_sent = request.args.get("hub.verify_token")
		return verify_fb_token(token_sent)
	# if the request was not get, it must be POST and we can just proceed with sending a message back to user
	else:
		# get whatever message a user sent the bot
		output = request.get_json()
		print(output)
		for event in output['entry']:
			messaging = event['messaging']
			print("Messaging : {}".format(messaging))
			for message in messaging:
				if message.get('message'):
					# Facebook Messenger ID for user so we know where to send response back to
					recipient_id = message['sender']['id']
					if message['message'].get('text'):
						response_sent_text = get_message()
						send_message(bot, recipient_id, response_sent_text)
					# if user sends us a GIF, photo,video, or any other non-text item
					if message['message'].get('attachments'):
						response_sent_nontext = get_message()
						send_message(bot, recipient_id, response_sent_nontext)
	return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


#chooses a random message to send to the user
def get_message():
    sample_responses = ["You are stunning!", "We're proud of you.", "Keep on being you!", "We're greatful to know you :)"]
    # return selected item to the user
    return random.choice(sample_responses)

#uses PyMessenger to send response to user
def send_message(bot, recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"