__author__ = "receyuki"
__filename__ = "fooocus.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"


from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class Fooocus(BaseFormat):
    SETTING_KEY = [
        "base_model",
        "sampler",
        "seed",
        "cfg",
        "steps",
        "",
    ]

    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        self._fc_format()

    def _fc_format(self):
        data_json = self.info
        self._tool = "Fooocus"
        self._positive = data_json.get("prompt").strip()
        self._negative = data_json.get("negative_prompt").strip()
        self._raw = "\n".join([self._positive, self._negative, str(data_json)])
        data_json.pop("prompt")
        data_json.pop("negative_prompt")
        self._setting = remove_quotes(str(data_json)[1:-1]).strip()
        self._width = str(data_json.get("width"))
        self._height = str(data_json.get("height"))

        for p, s in zip(super().PARAMETER_KEY, Fooocus.SETTING_KEY):
            match p:
                case "size":
                    self._parameter["size"] = (
                        str(data_json.get("width")) + "x" + str(data_json.get("height"))
                    )
                case _:
                    self._parameter[p] = str(data_json.get(s))
