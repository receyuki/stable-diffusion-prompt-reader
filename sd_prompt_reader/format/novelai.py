__author__ = "receyuki"
__filename__ = "novelai.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json

from ..format.base_format import BaseFormat


class NovelAI(BaseFormat):
    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        self._nai_png()

    def _nai_png(self):
        self._positive = self._info.get("Description")
        self._raw += self._positive
        comment = self._info.get("Comment") or {}
        comment_json = json.loads(comment)
        self._negative = comment_json.get("uc")
        self._raw += "\n" + self.negative
        self._raw += "\n" + comment
        self._setting = (
            f"Steps: {comment_json.get('steps')}"
            f", Sampler: {comment_json.get('sampler')}"
            f", CFG scale: {comment_json.get('scale')}"
            f", Seed: {comment_json.get('seed')}"
            f", Size: {self._width}x{self._height}"
        )
        if "strength" in comment_json:
            self._setting += f", Strength: {comment_json.get('strength')}"
        if "noise" in comment_json:
            self._setting += f", Noise: {comment_json.get('noise')}"
        if "scale" in comment_json:
            self._setting += f", Scale: {comment_json.get('scale')}"
        if self._setting:
            self._setting += ", Clip skip: 2, ENSD: 31337"

        self._parameter["sampler"] = comment_json.get("sampler")
        self._parameter["seed"] = comment_json.get("seed")
        self._parameter["cfg"] = comment_json.get("scale")
        self._parameter["steps"] = comment_json.get("steps")
        self._parameter["size"] = str(self._width) + "x" + str(self._height)
