from config.config import logger
from opendemic.database import RDBManager
import datetime
from helpers.formatting import mysql_db_format_value
import re


class TelegramCommand(object):
    _data = None
    _command = None
    _payload = None
    _bot = None
    _telegram_command_data_regex = "^(/){1}[a-zA-Z0-9_]+$|^(/){1}[a-zA-Z0-9_]+\s{1}[a-zA-Z0-9_]{1}[a-zA-Z0-9_\-\s]*$"
    _telegram_command_regex = "^(/){1}[a-zA-Z0-9_]+"
    _telegram_command_payload_regex = "^(/){1}[a-zA-Z0-9_]+"

    def __init__(self, data):
        if not self.is_telegram_command(data=data):
            raise ValueError("Wrong data format for command")

        self._data = data
        self._command = re.search(self._telegram_command_regex, data).group(0).replace("/", "")
        self._payload = " ".join(data.split(" ")[1:]) if len(data.split(" ")) >= 2 else None

    @classmethod
    def is_telegram_command(cls, data):
        return bool(re.fullmatch(pattern=cls._telegram_command_data_regex, string=data))

    @property
    def data(self):
        return self._data

    @property
    def command(self):
        return self._command

    @property
    def payload(self):
        return self._payload


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
    rdb = RDBManager()
    logger.debug("[TELEGRAM LOG] {} : {}".format(action_type, action_value))
    try:
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
        logger.error(e)


def log_sent_message(payload: dict, human_id: str = None, tag: str = None):
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
