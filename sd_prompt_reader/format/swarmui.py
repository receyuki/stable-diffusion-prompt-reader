__author__ = "receyuki"
__filename__ = "swarmui.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

from sd_prompt_reader.format.base_format import BaseFormat
from sd_prompt_reader.utility import remove_quotes


class SwarmUI(BaseFormat):
    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        self._ss_format()

    def _ss_format(self):
        data_json = self._info.get("sui_image_params")
        self._positive = data_json.get("prompt")
        self._negative = data_json.get("negativeprompt")
        self._raw = "\n".join([self._positive, self._negative, str(data_json)])
        data_json.pop("prompt")
        data_json.pop("negativeprompt")
        self._setting = remove_quotes(str(data_json)[1:-1])

        self._parameter["model"] = data_json.get("model")
        comfyuisampler = data_json.get("comfyuisampler")
        autowebuisampler = data_json.get("autowebuisampler")
        if comfyuisampler and autowebuisampler:
            self._parameter["sampler"] = str(
                remove_quotes((comfyuisampler, autowebuisampler))
            )
        else:
            self._parameter["sampler"] = str(comfyuisampler or autowebuisampler)
        self._parameter["seed"] = data_json.get("seed")
        self._parameter["cfg"] = data_json.get("cfgscale")
        self._parameter["steps"] = data_json.get("steps")
        self._parameter["size"] = (
            str(data_json.get("width")) + "x" + str(data_json.get("height"))
        )
