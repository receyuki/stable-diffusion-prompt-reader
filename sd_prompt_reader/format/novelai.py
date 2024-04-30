__author__ = "receyuki"
__filename__ = "novelai.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json
import gzip

from ..format.base_format import BaseFormat
from ..utility import remove_quotes


class NovelAI(BaseFormat):
    SETTING_KEY_LEGACY = [
        "",
        "sampler",
        "seed",
        "scale",
        "steps",
        "",
    ]

    SETTING_KEY_STEALTH = ["Source", "sampler", "seed", "scale", "steps", ""]

    class LSBExtractor:
        def __init__(self, img):
            self.data = list(img.getdata())
            self.width, self.height = img.size
            self.data = [
                self.data[i * self.width : (i + 1) * self.width]
                for i in range(self.height)
            ]
            self.dim = 4
            self.bits = 0
            self.byte = 0
            self.row = 0
            self.col = 0

        def _extract_next_bit(self):
            if self.row < self.height and self.col < self.width:
                bit = self.data[self.row][self.col][self.dim - 1] & 1
                self.bits += 1
                self.byte <<= 1
                self.byte |= bit
                self.row += 1
                if self.row == self.height:
                    self.row = 0
                    self.col += 1

        def get_one_byte(self):
            while self.bits < 8:
                self._extract_next_bit()
            byte = bytearray([self.byte])
            self.bits = 0
            self.byte = 0
            return byte

        def get_next_n_bytes(self, n):
            bytes_list = bytearray()
            for _ in range(n):
                byte = self.get_one_byte()
                if not byte:
                    break
                bytes_list.extend(byte)
            return bytes_list

        def read_32bit_integer(self):
            bytes_list = self.get_next_n_bytes(4)
            if len(bytes_list) == 4:
                integer_value = int.from_bytes(bytes_list, byteorder="big")
                return integer_value
            else:
                return None

    def __init__(
        self,
        info: dict = None,
        raw: str = "",
        extractor: LSBExtractor = None,
        width: int = 0,
        height: int = 0,
    ):
        super().__init__(info, raw, width, height)
        self._extractor = extractor

    def _process(self):
        if self._info:
            self._nai_legacy()
        elif self._extractor:
            self._nai_stealth()

    def _nai_legacy(self):
        self._positive = self._info.get("Description").strip()
        self._raw += self._positive
        data = self._info.get("Comment") or {}
        data_json = json.loads(data)
        self._negative = data_json.get("uc").strip()
        self._raw += "\n".join([self._positive, self.negative, str(data_json)]).strip()

        data_json.pop("uc")
        self._setting = remove_quotes(str(data_json)).strip("{ }")

        for p, s in zip(super().PARAMETER_KEY, NovelAI.SETTING_KEY_LEGACY):
            match p:
                case "model":
                    self._parameter["model"] = ""
                case "size":
                    self._parameter["size"] = str(self._width) + "x" + str(self._height)
                case _:
                    self._parameter[p] = str(data_json.get(s))

    def _nai_stealth(self):
        read_len = self._extractor.read_32bit_integer() // 8
        json_data = self._extractor.get_next_n_bytes(read_len)
        json_data = json.loads(gzip.decompress(json_data).decode("utf-8"))
        self._raw = str(json_data)
        if "Comment" in json_data:
            json_data = json_data | json.loads(json_data["Comment"])
            json_data.pop("Comment")
            self._positive = json_data.get("prompt").strip()
            json_data.pop("prompt")
            self._negative = json_data.get("uc").strip()
            json_data.pop("uc")
        else:
            self._positive = json_data.get("Description").strip()
        json_data.pop("Description")
        self._setting = remove_quotes(str(json_data)).strip("{ }")
        for p, s in zip(super().PARAMETER_KEY, NovelAI.SETTING_KEY_STEALTH):
            match p:
                case "size":
                    self._parameter["size"] = (
                        str(json_data.get("width")) + "x" + str(json_data.get("height"))
                    )
                case _:
                    self._parameter[p] = str(json_data.get(s))
