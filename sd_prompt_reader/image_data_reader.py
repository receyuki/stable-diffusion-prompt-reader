# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'image_data_reader.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

import json
import piexif
import piexif.helper
from PIL import Image


class ImageDataReader:
    def __init__(self, file):
        self._height = None
        self._width = None
        self._info = {}
        self._positive = ""
        self._negative = ""
        self._setting = ""
        self._raw = ""
        self.read_data(file)

    def _sd_format(self):
        if self._raw and "Negative prompt:" in self._raw and "\nSteps:" in self._raw:
            prompt_index = [self._raw.index("\nNegative prompt:"),
                            self._raw.index("\nSteps:")]
            self._positive = self._raw[:prompt_index[0]]
            self._negative = self._raw[prompt_index[0] + 1 + len("Negative prompt: "):prompt_index[1]]
            self._setting = self._raw[prompt_index[1] + 1:]
        else:
            self._raw = ""

    def read_data(self, file):
        with Image.open(file) as f:
            self._width = f.width
            self._height = f.height
            self._info = f.info
            if "parameters" in self._info and f.format == "PNG":
                self._sd_png()
            elif "exif" in self._info and (f.format == "JPEG" or f.format == "WEBP"):
                self._sd_jpg()
            elif self._info.get("Software") == "NovelAI" and f.format == "PNG":
                self._nai_png()

    def _sd_png(self):
        self._raw = self._info.get("parameters")
        self._sd_format()

    def _sd_jpg(self):
        exif = piexif.load(self._info.get("exif")) or {}
        try:
            self._raw = piexif.helper.UserComment.load(exif.get("Exif").get(piexif.ExifIFD.UserComment))
        except Exception:
            pass
        else:
            self._sd_format()

    def _nai_png(self):
        self._positive = self._info.get("Description")
        self._raw += self._positive
        comment = self._info.get("Comment") or {}
        comment_json = json.loads(comment)
        self._raw += "\n"+comment
        self._negative = comment_json.get("uc")
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

    @property
    def positive(self):
        return self._positive

    @property
    def negative(self):
        return self._negative

    @property
    def setting(self):
        return self._setting

    @property
    def raw(self):
        return self._raw
