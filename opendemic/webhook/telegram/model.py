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