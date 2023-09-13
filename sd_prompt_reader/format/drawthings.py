__author__ = "receyuki"
__filename__ = "drawthings.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json
from xml.dom import minidom

from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class DrawThings(BaseFormat):
    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        self._dt_format()

    def _dt_format(self):
        data_json = self.info
        self._tool = "Draw Things"
        self._positive = data_json.get("c")
        self._negative = data_json.get("uc")
        self._raw = "\n".join([self._positive, self._negative, str(data_json)])
        data_json.pop("c")
        data_json.pop("uc")
        self._setting = remove_quotes(str(data_json)[1:-1])

        self._parameter["model"] = data_json.get("model")
        self._parameter["sampler"] = data_json.get("sampler")
        self._parameter["seed"] = data_json.get("seed")
        self._parameter["cfg"] = data_json.get("scale")
        self._parameter["steps"] = data_json.get("steps")
        self._parameter["size"] = data_json.get("size")
