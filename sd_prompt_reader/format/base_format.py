__author__ = "receyuki"
__filename__ = "base_format.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"


class BaseFormat:
    def __init__(
        self, info: dict = None, raw: str = "", width: int = None, height: int = None
    ):
        self._height = height
        self._width = width
        self._info = info
        self._positive = ""
        self._negative = ""
        self._positive_sdxl = {}
        self._negative_sdxl = {}
        self._setting = ""
        self._raw = raw
        self._parameter_key = ["model", "sampler", "seed", "cfg", "steps", "size"]
        self._parameter = dict.fromkeys(self._parameter_key, "")
        self._is_sdxl = False

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    @property
    def info(self):
        return self._info

    @property
    def positive(self):
        return self._positive

    @property
    def negative(self):
        return self._negative

    @property
    def positive_sdxl(self):
        return self._positive_sdxl

    @property
    def negative_sdxl(self):
        return self._negative_sdxl

    @property
    def setting(self):
        return self._setting

    @property
    def raw(self):
        return self._raw

    @property
    def parameter(self):
        return self._parameter

    @property
    def is_sdxl(self):
        return self._is_sdxl
