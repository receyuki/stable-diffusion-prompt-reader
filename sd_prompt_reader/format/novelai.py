__author__ = "receyuki"
__filename__ = "novelai.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json

from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class NovelAI(BaseFormat):
    SETTING_KEY = [
        "",
        "sampler",
        "seed",
        "scale",
        "steps",
        "",
    ]

    def __init__(
        self, info: dict = None, raw: str = "", width: int = 0, height: int = 0
    ):
        super().__init__(info, raw, width, height)
        self._nai_png()

    def _nai_png(self):
        self._positive = self._info.get("Description").strip()
        self._raw += self._positive
        data = self._info.get("Comment") or {}
        data_json = json.loads(data)
        self._negative = data_json.get("uc").strip()
        self._raw += "\n".join([self._positive, self.negative, str(data_json)]).strip()

        data_json.pop("uc")
        self._setting = remove_quotes(str(data_json)).strip("{ }")

        for p, s in zip(super().PARAMETER_KEY, NovelAI.SETTING_KEY):
            match p:
                case "model":
                    self._parameter["model"] = ""
                case "size":
                    self._parameter["size"] = str(self._width) + "x" + str(self._height)
                case _:
                    self._parameter[p] = str(data_json.get(s))
