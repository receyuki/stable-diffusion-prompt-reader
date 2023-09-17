__author__ = "receyuki"
__filename__ = "a1111.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import re

from ..format.base_format import BaseFormat
from ..utility import add_quotes


class A1111(BaseFormat):
    PROMPT_MAPPING = {
        # "Model": ("sd_model", True),
        # "prompt",
        # "negative_prompt",
        "Seed": ("seed", False),
        "Variation seed strength": ("subseed_strength", False),
        # "seed_resize_from_h",
        # "seed_resize_from_w",
        "Sampler": ("sampler_name", True),
        "Steps": ("steps", False),
        "CFG scale": ("cfg_scale", False),
        # "width",
        # "height",
        "Face restoration": ("restore_faces", False),
    }

    SETTING_KEY = ["Model", "Sampler", "Seed", "CFG scale", "Steps", "Size"]

    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        if not self._raw:
            self._raw = self._info.get("parameters")
        self._sd_format()

    def _sd_format(self):
        if not self._raw:
            self._raw = ""
            return

        steps_index = self._raw.find("\nSteps:")
        # w/ setting
        if steps_index != -1:
            self._positive = self._raw[:steps_index].strip()
            self._setting = self._raw[steps_index:].strip()

        # w/ neg
        if "Negative prompt:" in self._raw:
            prompt_index = self._raw.find("\nNegative prompt:")
            # w/ neg and w/ setting
            if steps_index != -1:
                self._negative = self._raw[
                    prompt_index + len("Negative prompt:") + 1 : steps_index
                ].strip()
            # w/ neg and w/o setting
            else:
                self._negative = self._raw[
                    prompt_index + len("Negative prompt:") + 1 :
                ].strip()
            self._positive = self._raw[:prompt_index].strip()
        # w/o neg and w/o setting
        elif steps_index == -1:
            self._positive = self._raw

        # match parameters like "Steps: x",
        pattern = r"\s*([^:,]+):\s*([^,]+)"
        setting_dict = dict(re.findall(pattern, self._setting))

        [self._width, self._height] = setting_dict.get("Size").split("x")

        for p, s in zip(super().PARAMETER_KEY, A1111.SETTING_KEY):
            self._parameter[p] = setting_dict.get(s)

    def prompt_to_line(self):
        if not self._setting:
            return ""
        single_line_prompt = "--prompt " + add_quotes(self._positive).replace("\n", "")
        if self._negative:
            single_line_prompt += " --negative_prompt " + add_quotes(
                self._negative
            ).replace("\n", "")
        setting = dict(
            filter(
                lambda x: len(x) == 2,
                (param.split(": ") for param in self._setting.split(", ")),
            )
        )
        for key, value in setting.items():
            if key == "Size":
                width, height = value.split("x")
                single_line_prompt += " --width " + width
                single_line_prompt += " --height " + height
            if key == "Seed resize from":
                seed_resize_from_w, seed_resize_from_h = value.split("x")
                single_line_prompt += " --seed_resize_from_w " + seed_resize_from_w
                single_line_prompt += " --seed_resize_from_h " + seed_resize_from_h
            try:
                (tag, is_str) = A1111.PROMPT_MAPPING.get(key)
            except:
                pass
            else:
                if is_str:
                    single_line_prompt += " --" + tag + " " + add_quotes(str(value))
                else:
                    single_line_prompt += " --" + tag + " " + value
        return single_line_prompt
