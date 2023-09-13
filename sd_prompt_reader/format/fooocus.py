__author__ = "receyuki"
__filename__ = "fooocus.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json
from xml.dom import minidom

from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class Fooocus(BaseFormat):
    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        self._fc_format()

    def _fc_format(self):
        data_json = self.info
        self._tool = "Fooocus"
        self._positive = data_json.get("prompt")
        self._negative = data_json.get("negative_prompt")
        self._raw = "\n".join([self._positive, self._negative, str(data_json)])
        data_json.pop("prompt")
        data_json.pop("negative_prompt")
        self._setting = remove_quotes(str(data_json)[1:-1])

        self._parameter["model"] = data_json.get("base_model")
        self._parameter["sampler"] = data_json.get("sampler")
        self._parameter["seed"] = data_json.get("seed")
        self._parameter["cfg"] = data_json.get("cfg")
        self._parameter["steps"] = data_json.get("steps")
        self._parameter["size"] = (
            str(data_json.get("width")) + "x" + str(data_json.get("height"))
        )
