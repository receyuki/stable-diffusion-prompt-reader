__author__ = "receyuki"
__filename__ = "drawthings.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"


from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class DrawThings(BaseFormat):
    SETTING_KEY = ["model", "sampler", "seed", "scale", "steps", "size"]

    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        self._dt_format()

    def _dt_format(self):
        data_json = self.info
        self._tool = "Draw Things"
        self._positive = data_json.get("c").strip()
        self._negative = data_json.get("uc").strip()
        self._raw = "\n".join([self._positive, self._negative, str(data_json)])
        data_json.pop("c")
        data_json.pop("uc")
        self._setting = remove_quotes(str(data_json)[1:-1]).strip()
        [self._width, self._height] = data_json.get("size").split("x")

        for p, s in zip(super().PARAMETER_KEY, DrawThings.SETTING_KEY):
            self._parameter[p] = str(data_json.get(s))
