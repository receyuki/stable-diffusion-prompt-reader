__author__ = "receyuki"
__filename__ = "invokeai.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json
import re

from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class InvokeAI(BaseFormat):
    SETTING_KEY_INVOKEAI_METADATA = [
        "",
        ("scheduler", "refiner_scheduler"),
        "seed",
        ("cfg_scale", "refiner_cfg_scale"),
        ("steps", "refiner_steps"),
        "",
    ]
    SETTING_KEY_METADATA = [
        "model_weights",
        "sampler",
        "seed",
        "cfg_scale",
        "steps",
        "",
    ]
    SETTING_KEY_DREAM = ["", "A", "S", "C", "s", ""]
    DREAM_MAPPING = {
        "Steps": "s",
        "Seed": "S",
        "Size": "",
        "CFG scale": "C",
        "Sampler": "A",
    }

    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        if "invokeai_metadata" in self._info:
            self._invoke_invoke_metadata()
        elif "sd-metadata" in self._info:
            self._invoke_metadata()
        elif "Dream" in self._info:
            self._invoke_dream()

    def _invoke_invoke_metadata(self):
        data_json = json.loads(self._info.get("invokeai_metadata"))
        self._positive = data_json.pop("positive_prompt").strip()
        self._negative = data_json.pop("negative_prompt").strip()
        self._raw = "\n".join([self._positive, self._negative, str(data_json)])
        self._setting = remove_quotes(str(data_json)).strip("{ }")
        self._width = str(data_json.get("width"))
        self._height = str(data_json.get("height"))

        has_refiner = True if data_json.get("refiner_model") else False

        for p, s in zip(super().PARAMETER_KEY, InvokeAI.SETTING_KEY_INVOKEAI_METADATA):
            match p:
                case "model":
                    self._parameter[p] = remove_quotes(
                        str(
                            (
                                data_json.get("model").get("model_name"),
                                data_json.get("refiner_model").get("model_name"),
                            )
                        )
                        if has_refiner
                        else str(data_json.get("model").get("model_name"))
                    )
                case "seed":
                    self._parameter["seed"] = str(data_json.get("seed"))
                case "size":
                    self._parameter["size"] = (
                        str(data_json.get("width")) + "x" + str(data_json.get("height"))
                    )
                case _:
                    self._parameter[p] = remove_quotes(
                        str((data_json.get(s[0]), data_json.get(s[1])))
                        if has_refiner
                        else str(data_json.get(s[0]))
                    )

    def _invoke_metadata(self):
        data_json = json.loads(self._info.get("sd-metadata"))
        image = data_json.pop("image")
        prompt = (
            image.get("prompt")[0].get("prompt")
            if isinstance(image.get("prompt"), list)
            else image.get("prompt")
        )

        self._positive, self._negative = self.split_prompt(prompt)

        raw_list = [
            item
            for item in [
                self._positive,
                self._negative,
                self._info.get("Dream"),
                self._info.get("sd-metadata"),
            ]
            if item != ""
        ]

        self._raw = "\n".join(raw_list).strip()

        image.pop("prompt")
        self._setting = remove_quotes(
            ", ".join([str(data_json).strip("{ }"), str(image).strip("{ }")])
        )

        self._width = str(image.get("width"))
        self._height = str(image.get("height"))

        for p, s in zip(super().PARAMETER_KEY, InvokeAI.SETTING_KEY_METADATA):
            match p:
                case "model":
                    self._parameter["model"] = data_json.get(s)
                case "size":
                    self._parameter["size"] = (
                        str(image.get("width")) + "x" + str(image.get("height"))
                    )
                case _:
                    self._parameter[p] = str(image.get(s))

    def _invoke_dream(self):
        data = self._info.get("Dream")

        # match parameters like '"Prompt"Setting'
        pattern = r'"(.*?)"\s*(.*?)$'
        prompt, setting = re.search(pattern, data).groups()
        self._positive, self._negative = self.split_prompt(prompt.strip('" '))

        self._raw = "\n".join([self._positive, self.negative, self._info.get("Dream")])

        # match parameters like "-s 30"
        pattern = r"-(\w+)\s+([\w.-]+)"
        setting_dict = dict(re.findall(pattern, setting))
        setting_list = []
        for key, value in InvokeAI.DREAM_MAPPING.items():
            if key == "Size":
                setting_list.append(
                    key + ": " + setting_dict.get("W") + "x" + setting_dict.get("H")
                )
            else:
                setting_list.append(key + ": " + setting_dict.get(value))
        self._setting = ", ".join(setting_list)

        self._width = str(setting_dict.get("W"))
        self._height = str(setting_dict.get("H"))

        for p, s in zip(super().PARAMETER_KEY, InvokeAI.SETTING_KEY_DREAM):
            match p:
                case "model":
                    self._parameter["model"] = ""
                case "size":
                    self._parameter["size"] = (
                        str(setting_dict.get("W")) + "x" + str(setting_dict.get("H"))
                    )
                case _:
                    self._parameter[p] = setting_dict.get(s)

    @staticmethod
    def split_prompt(prompt: str):
        # match parameters like "Positive[Negative]"
        pattern = r"^(.*?)\[(.*?)\]$"
        match = re.match(pattern, prompt)

        if match:
            positive, negative = match.groups()
            positive = positive.strip()
            negative = negative.strip()
        else:
            positive = prompt.strip()
            negative = ""
        return positive, negative
