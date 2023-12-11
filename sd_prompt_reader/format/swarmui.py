__author__ = "receyuki"
__filename__ = "swarmui.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json

from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class SwarmUI(BaseFormat):
    SETTING_KEY = ["model", "", "seed", "cfgscale", "steps", ""]

    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        if not self._info:
            self._info = json.loads(self._raw)
        self._ss_format()

    def _ss_format(self):
        data_json = self._info.get("sui_image_params")
        self._positive = data_json.get("prompt").strip()
        self._negative = data_json.get("negativeprompt").strip()
        self._raw = "\n".join([self._positive, self._negative, str(data_json)]).strip()
        data_json.pop("prompt")
        data_json.pop("negativeprompt")
        self._setting = remove_quotes(str(data_json).strip("{ }"))
        self._width = str(data_json.get("width"))
        self._height = str(data_json.get("height"))

        for p, s in zip(super().PARAMETER_KEY, SwarmUI.SETTING_KEY):
            match p:
                case "sampler":
                    comfyuisampler = data_json.get("comfyuisampler")
                    autowebuisampler = data_json.get("autowebuisampler")
                    self._parameter["sampler"] = str(
                        remove_quotes((comfyuisampler, autowebuisampler))
                        if comfyuisampler and autowebuisampler
                        else comfyuisampler or autowebuisampler
                    )
                case "size":
                    self._parameter["size"] = (
                        str(data_json.get("width")) + "x" + str(data_json.get("height"))
                    )
                case _:
                    self._parameter[p] = str(data_json.get(s))
