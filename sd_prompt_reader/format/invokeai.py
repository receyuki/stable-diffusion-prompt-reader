__author__ = "receyuki"
__filename__ = "invokeai.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json

from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class InvokeAI(BaseFormat):
    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        if "sd-metadata" in self._info:
            self._invoke_metadata()
        elif "Dream" in self._info:
            self._invoke_dream()

    def _invoke_metadata(self):
        metadata = json.loads(self._info.get("sd-metadata"))
        image = metadata.get("image")
        prompt = (
            image.get("prompt")[0].get("prompt")
            if isinstance(image.get("prompt"), list)
            else image.get("prompt")
        )
        prompt_index = [prompt.rfind("["), prompt.rfind("]")]

        # w/ neg
        if -1 not in prompt_index:
            self._positive = prompt[: prompt_index[0]]
            self._negative = prompt[prompt_index[0] + 1 : prompt_index[1]]
        # w/o neg
        else:
            self._positive = prompt

        self._raw += self._positive
        self._raw += "\n" + self.negative
        self._raw += (
            "\n" + self._info.get("Dream") + "\n" + self._info.get("sd-metadata")
        )
        self._setting = (
            f"Steps: {image.get('steps')}"
            f", Sampler: {image.get('sampler')}"
            f", CFG scale: {image.get('cfg_scale')}"
            f", Seed: {image.get('seed')}"
            f", Size: {image.get('width')}x{image.get('height')}"
            f", Model hash: {metadata.get('model_hash')}"
            f", Model: {metadata.get('model_weights')}"
            f", Threshold: {image.get('threshold')}"
            f", Perlin: {image.get('perlin')}"
            f", Hires fix: {image.get('hires_fix')}"
            f", Seamless: {image.get('seamless')}"
            f", Type: {image.get('type')}"
            f", Postprocessing: {remove_quotes(image.get('postprocessing'))}"
            f", Variations: {image.get('variations')}"
        )

        self._parameter["model"] = metadata.get("model_weights")
        self._parameter["sampler"] = image.get("sampler")
        self._parameter["seed"] = image.get("seed")
        self._parameter["cfg"] = image.get("cfg_scale")
        self._parameter["steps"] = image.get("steps")
        self._parameter["size"] = (
            str(image.get("width")) + "x" + str(image.get("height"))
        )

    def _invoke_dream(self):
        dream = self._info.get("Dream")
        prompt_index = dream.rfind('"')
        neg_index = [dream.rfind("["), dream.rfind("]")]

        # w/ neg
        if -1 not in neg_index:
            self._positive = dream[1 : neg_index[0]]
            self._negative = dream[neg_index[0] + 1 : neg_index[1]]
        # w/o neg
        else:
            self._positive = dream[1:prompt_index]

        self._raw += self._positive
        self._raw += "\n" + self.negative
        self._raw += "\n" + self._info.get("Dream")

        setting_index = [
            dream.rfind("-s"),
            dream.rfind("-S"),
            dream.rfind("-W"),
            dream.rfind("-H"),
            dream.rfind("-C"),
            dream.rfind("-A"),
        ]
        self._setting = (
            f"Steps: {dream[setting_index[0] + 3:setting_index[1] - 1]}"
            f", Sampler: {dream[setting_index[5] + 3:].split()[0]}"
            f", CFG scale: {dream[setting_index[4] + 3:setting_index[5] - 1]}"
            f", Seed: {dream[setting_index[1] + 3:setting_index[2] - 1]}"
            f", Size: {dream[setting_index[2] + 3:setting_index[3] - 1]}"
            f"x{dream[setting_index[3] + 3:setting_index[4] - 1]}"
        )

        self._parameter["sampler"] = dream[setting_index[5] + 3 :].split()[0]
        self._parameter["seed"] = dream[setting_index[1] + 3 : setting_index[2] - 1]
        self._parameter["cfg"] = dream[setting_index[4] + 3 : setting_index[5] - 1]
        self._parameter["steps"] = dream[setting_index[0] + 3 : setting_index[1] - 1]
        self._parameter["size"] = (
            str(dream[setting_index[2] + 3 : setting_index[3] - 1])
            + "x"
            + str(dream[setting_index[3] + 3 : setting_index[4] - 1])
        )
