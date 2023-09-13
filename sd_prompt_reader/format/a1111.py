__author__ = "receyuki"
__filename__ = "a1111.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

from ..format.base_format import BaseFormat
from ..utility import add_quotes

PROMPT_MAPPING = {
    # "Model":                    ("sd_model",            True),
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


class A1111(BaseFormat):
    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        if not self._raw:
            self._raw = self._info.get("parameters")
        self._sd_format()

    def _sd_format(self):
        if self._raw and "\nSteps:" in self._raw:
            # w/ neg
            if "Negative prompt:" in self._raw:
                prompt_index = [
                    self._raw.index("\nNegative prompt:"),
                    self._raw.index("\nSteps:"),
                ]
            # w/o neg
            else:
                prompt_index = [self._raw.index("\nSteps:")]
            self._positive = self._raw[: prompt_index[0]]
            self._negative = self._raw[
                prompt_index[0] + 1 + len("Negative prompt: ") : prompt_index[-1]
            ]
            self._setting = self._raw[prompt_index[-1] + 1 :]

            parameter_index = [
                self._setting.find("Model: ") + len("Model: "),
                self._setting.find("Sampler: ") + len("Sampler: "),
                self._setting.find("Seed: ") + len("Seed: "),
                self._setting.find("CFG scale: ") + len("CFG scale: "),
                self._setting.find("Steps: ") + len("Steps: "),
                self._setting.find("Size: ") + len("Size: "),
            ]
            if self._setting.find("Model: ") != -1:
                self._parameter["model"] = self._setting[
                    parameter_index[0] : self._setting.find(",", parameter_index[0])
                ]
            self._parameter["sampler"] = self._setting[
                parameter_index[1] : self._setting.find(",", parameter_index[1])
            ]
            self._parameter["seed"] = self._setting[
                parameter_index[2] : self._setting.find(",", parameter_index[2])
            ]
            self._parameter["cfg"] = self._setting[
                parameter_index[3] : self._setting.find(",", parameter_index[3])
            ]
            self._parameter["steps"] = self._setting[
                parameter_index[4] : self._setting.find(",", parameter_index[4])
            ]
            self._parameter["size"] = self._setting[
                parameter_index[5] : self._setting.find(",", parameter_index[5])
            ]
        elif self._raw:
            # w/ neg
            if "Negative prompt:" in self._raw:
                prompt_index = [self._raw.index("\nNegative prompt:")]
                self._negative = self._raw[
                    prompt_index[0] + 1 + len("Negative prompt: ") :
                ]
            # w/o neg
            else:
                prompt_index = [len(self._raw)]
            self._positive = self._raw[: prompt_index[0]]
        else:
            self._raw = ""

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
                (tag, is_str) = PROMPT_MAPPING.get(key)
            except:
                pass
            else:
                if is_str:
                    single_line_prompt += " --" + tag + " " + add_quotes(str(value))
                else:
                    single_line_prompt += " --" + tag + " " + value
        return single_line_prompt
