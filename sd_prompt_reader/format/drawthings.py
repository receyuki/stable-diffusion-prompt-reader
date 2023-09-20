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
        self._positive = data_json.pop("c").strip()
        self._negative = data_json.pop("uc").strip()
        self._raw = "\n".join([self._positive, self._negative, str(data_json)])
        self._setting = remove_quotes(str(data_json).strip("{ }"))
        [self._width, self._height] = data_json.get("size").split("x")

        for p, s in zip(super().PARAMETER_KEY, DrawThings.SETTING_KEY):
            self._parameter[p] = str(data_json.get(s))
