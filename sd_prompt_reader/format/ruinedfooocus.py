__author__ = "receyuki"
__filename__ = "ruinedfooocus.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json

from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class RuinedFooocus(BaseFormat):
    SETTING_KEY = ["base_model_name", "sampler_name", "seed", "cfg", "steps", "size"]

    @staticmethod
    def is_format(raw):
        try:
            data = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return False
        return isinstance(data, dict) and data.get("software") == "RuinedFooocus"

    def _process(self):
        self._rf_format()

    def _rf_format(self):
        data_json = json.loads(self._raw)
        if not isinstance(data_json, dict):
            raise ValueError("RuinedFooocus metadata must be an object")
        positive = data_json.get("Prompt")
        negative = data_json.get("Negative")
        if negative is None:
            negative = ""
        if not isinstance(positive, str) or not isinstance(negative, str):
            raise ValueError("RuinedFooocus prompts must be strings")
        self._positive = positive.strip()
        self._negative = negative.strip()
        self._raw = "\n".join([self._positive, self._negative, str(data_json)])
        data_json.pop("Prompt")
        data_json.pop("Negative", None)
        self._setting = remove_quotes(str(data_json)[1:-1]).strip()
        if data_json.get("width") is not None:
            self._width = str(data_json["width"])
        if data_json.get("height") is not None:
            self._height = str(data_json["height"])

        for p, s in zip(super().PARAMETER_KEY, RuinedFooocus.SETTING_KEY):
            match p:
                case "size":
                    self._parameter["size"] = self._width + "x" + self._height
                case _:
                    value = data_json.get(s)
                    self._parameter[p] = "" if value is None else str(value)
