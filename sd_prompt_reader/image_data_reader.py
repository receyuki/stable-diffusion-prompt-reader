__author__ = "receyuki"
__filename__ = "image_data_reader.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json
from xml.dom import minidom

import piexif
import piexif.helper
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from .logger import Logger
from .constants import PARAMETER_PLACEHOLDER
from .format import (
    BaseFormat,
    A1111,
    EasyDiffusion,
    InvokeAI,
    NovelAI,
    ComfyUI,
    DrawThings,
    SwarmUI,
    Fooocus,
)


class ImageDataReader:
    NOVELAI_MAGIC = "stealth_pngcomp"

    def __init__(self, file, is_txt: bool = False):
        self._height = None
        self._width = None
        self._info = {}
        self._positive = ""
        self._negative = ""
        self._positive_sdxl = {}
        self._negative_sdxl = {}
        self._setting = ""
        self._raw = ""
        self._tool = ""
        self._parameter_key = ["model", "sampler", "seed", "cfg", "steps", "size"]
        self._parameter = dict.fromkeys(self._parameter_key, PARAMETER_PLACEHOLDER)
        self._is_txt = is_txt
        self._is_sdxl = False
        self._format = ""
        self._props = ""
        self._parser = None
        self._status = BaseFormat.Status.UNREAD
        self._logger = Logger("SD_Prompt_Reader.ImageDataReader")
        self.read_data(file)

    def read_data(self, file):
        if self._is_txt:
            self._raw = file.read()
            self._parser = A1111(raw=self._raw)
            return
        with Image.open(file) as f:
            self._width = f.width
            self._height = f.height
            self._info = f.info
            self._format = f.format
            # swarm legacy format
            try:
                exif = json.loads(f.getexif().get(0x0110))
                if "sui_image_params" in exif:
                    self._tool = "StableSwarmUI"
                    self._parser = SwarmUI(info=exif)
            except TypeError:
                if f.format == "PNG":
                    if "parameters" in self._info:
                        # swarm format
                        if "sui_image_params" in self._info.get("parameters"):
                            self._tool = "StableSwarmUI"
                            self._parser = SwarmUI(raw=self._info.get("parameters"))
                        # a1111 png compatible format
                        else:
                            if "prompt" in self._info:
                                self._tool = "ComfyUI\n(A1111 compatible)"
                            else:
                                self._tool = "A1111 webUI"
                            self._parser = A1111(info=self._info)
                    elif "postprocessing" in self._info:
                        self._tool = "A1111 webUI\n(Postprocessing)"
                        self._parser = A1111(info=self._info)
                    # easydiff png format
                    elif (
                        "negative_prompt" in self._info
                        or "Negative Prompt" in self._info
                    ):
                        self._tool = "Easy Diffusion"
                        self._parser = EasyDiffusion(info=self._info)
                    # invokeai3 format
                    elif "invokeai_metadata" in self._info:
                        self._tool = "InvokeAI"
                        self._parser = InvokeAI(info=self._info)
                    # invokeai2 format
                    elif "sd-metadata" in self._info:
                        self._tool = "InvokeAI"
                        self._parser = InvokeAI(info=self._info)
                    # invokeai legacy dream format
                    elif "Dream" in self._info:
                        self._tool = "InvokeAI"
                        self._parser = InvokeAI(info=self._info)
                    # novelai legacy format
                    elif self._info.get("Software") == "NovelAI":
                        self._tool = "NovelAI"
                        self._parser = NovelAI(
                            info=self._info, width=self._width, height=self._height
                        )
                    # comfyui format
                    elif "prompt" in self._info:
                        self._tool = "ComfyUI"
                        self._parser = ComfyUI(
                            info=self._info, width=self._width, height=self._height
                        )
                    # fooocus format
                    elif "Comment" in self._info:
                        try:
                            self._tool = "Fooocus"
                            self._parser = Fooocus(
                                info=json.loads(self._info.get("Comment"))
                            )
                        except Exception:
                            self._logger.warn("Fooocus format error")
                    # drawthings format
                    elif "XML:com.adobe.xmp" in self._info:
                        try:
                            data = minidom.parseString(
                                self._info.get("XML:com.adobe.xmp")
                            )
                            data_json = json.loads(
                                data.getElementsByTagName("exif:UserComment")[0]
                                .childNodes[1]
                                .childNodes[1]
                                .childNodes[0]
                                .data
                            )
                        except Exception:
                            self._logger.warn("Draw things format error")
                            self._status = BaseFormat.Status.FORMAT_ERROR
                        else:
                            self._tool = "Draw Things"
                            self._parser = DrawThings(info=data_json)
                    # novelai stealth pnginfo format
                    elif f.mode == "RGBA":
                        try:
                            reader = NovelAI.LSBExtractor(f)
                            read_magic = reader.get_next_n_bytes(
                                len(self.NOVELAI_MAGIC)
                            ).decode("utf-8")
                            assert (
                                self.NOVELAI_MAGIC == read_magic
                            ), "NovelAI stealth png info magic number error"
                        except Exception as e:
                            self._logger.warn(e)
                            self._status = BaseFormat.Status.FORMAT_ERROR
                        else:
                            self._tool = "NovelAI"
                            self._parser = NovelAI(extractor=reader)
                elif f.format in ["JPEG", "WEBP"]:
                    # fooocus jpeg format
                    if "comment" in self._info:
                        try:
                            self._tool = "Fooocus"
                            self._parser = Fooocus(
                                info=json.loads(self._info.get("comment"))
                            )
                        except Exception:
                            self._logger.warn("Fooocus format error")
                            self._status = BaseFormat.Status.FORMAT_ERROR
                    elif f.mode == "RGBA":
                        try:
                            reader = NovelAI.LSBExtractor(f)
                            read_magic = reader.get_next_n_bytes(
                                len(self.NOVELAI_MAGIC)
                            ).decode("utf-8")
                            assert (
                                self.NOVELAI_MAGIC == read_magic
                            ), "NovelAI stealth png info magic number error"
                        except Exception as e:
                            self._logger.warn(e)
                            self._status = BaseFormat.Status.FORMAT_ERROR
                        else:
                            self._tool = "NovelAI"
                            self._parser = NovelAI(extractor=reader)
                    else:
                        try:
                            exif = piexif.load(self._info.get("exif")) or {}
                            user_comment = exif.get("Exif").get(
                                piexif.ExifIFD.UserComment
                            )
                        except TypeError:
                            self._logger.warn("Empty jpeg")
                            self._status = BaseFormat.Status.FORMAT_ERROR
                        except Exception:
                            pass
                        else:
                            try:
                                # swarm format
                                if "sui_image_params" in user_comment[8:].decode(
                                    "utf-16"
                                ):
                                    self._tool = "StableSwarmUI"
                                    self._parser = SwarmUI(
                                        raw=user_comment[8:].decode("utf-16")
                                    )
                                else:
                                    self._raw = piexif.helper.UserComment.load(
                                        user_comment
                                    )
                                    # easydiff jpeg and webp format
                                    if self._raw[0] == "{":
                                        self._tool = "Easy Diffusion"
                                        self._parser = EasyDiffusion(raw=self._raw)
                                    # a1111 jpeg and webp format
                                    else:
                                        self._tool = "A1111 webUI"
                                        self._parser = A1111(raw=self._raw)
                            except Exception:
                                self._status = BaseFormat.Status.FORMAT_ERROR
            if self._tool and self._status == BaseFormat.Status.UNREAD:
                self._logger.info(f"Format: {self._tool}")
                self._status = self._parser.parse()
            self._logger.info(f"Reading Status: {self._status.name}")

    @staticmethod
    def remove_data(image_file):
        with Image.open(image_file) as f:
            image_data = list(f.getdata())
            image_without_exif = Image.new(f.mode, f.size)
            image_without_exif.putdata(image_data)
            return image_without_exif

    @staticmethod
    def save_image(image_path, new_path, image_format, data=None):
        metadata = None
        if data:
            match image_format.upper():
                case "PNG":
                    metadata = PngInfo()
                    metadata.add_text("parameters", data)
                case "JPEG" | "JPG" | "WEBP":
                    metadata = piexif.dump(
                        {
                            "Exif": {
                                piexif.ExifIFD.UserComment: (
                                    piexif.helper.UserComment.dump(
                                        data, encoding="unicode"
                                    )
                                )
                            },
                        }
                    )

        with Image.open(image_path) as f:
            try:
                match image_format.upper():
                    case "PNG":
                        if data:
                            f.save(new_path, pnginfo=metadata)
                        else:
                            f.save(new_path)
                    case "JPEG" | "JPG":
                        f.save(new_path, quality="keep")
                        if data:
                            piexif.insert(metadata, str(new_path))
                    case "WEBP":
                        f.save(new_path, quality=100, lossless=True)
                        if data:
                            piexif.insert(metadata, str(new_path))
            except Exception:
                print("Save error")

    @staticmethod
    def construct_data(positive, negative, setting):
        return "\n".join(
            filter(
                None,
                [
                    f"{positive}" if positive else "",
                    f"Negative prompt: {negative}" if negative else "",
                    f"{setting}" if setting else "",
                ],
            )
        )

    def prompt_to_line(self):
        return self._parser.prompt_to_line()

    @property
    def height(self):
        return self._parser.height if self._tool else self._height

    @property
    def width(self):
        return self._parser.width if self._tool else self._width

    @property
    def info(self):
        return self._info

    @property
    def positive(self):
        return self._parser.positive if self._tool else self._positive

    @property
    def negative(self):
        return self._parser.negative if self._tool else self._negative

    @property
    def positive_sdxl(self):
        return self._parser.positive_sdxl if self._tool else self._positive_sdxl

    @property
    def negative_sdxl(self):
        return self._parser.negative_sdxl if self._tool else self._negative_sdxl

    @property
    def setting(self):
        return self._parser.setting if self._tool else self._setting

    @property
    def raw(self):
        return self._parser.raw or self._raw

    @property
    def tool(self):
        return self._tool

    @property
    def parameter(self):
        return self._parser.parameter if self._tool else self._parameter

    @property
    def format(self):
        return self._format

    @property
    def is_sdxl(self):
        return self._parser.is_sdxl if self._tool else self._is_sdxl

    @property
    def props(self):
        return self._parser.props if self._tool else self._props

    @property
    def status(self):
        return self._status
