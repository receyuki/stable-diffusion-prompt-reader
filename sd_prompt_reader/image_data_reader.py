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

from .constants import PARAMETER_PLACEHOLDER
from .format import (
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
        self._parser = None
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
                    # novelai format
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
                        except:
                            print("Fooocus format error")
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
                        except:
                            print("Draw things format error")
                        else:
                            self._tool = "Draw Things"
                            self._parser = DrawThings(info=data_json)
                elif f.format in ["JPEG", "WEBP"]:
                    # fooocus jpeg format
                    if "comment" in self._info:
                        try:
                            self._tool = "Fooocus"
                            self._parser = Fooocus(
                                info=json.loads(self._info.get("comment"))
                            )
                        except:
                            print("Fooocus format error")
                    else:
                        try:
                            exif = piexif.load(self._info.get("exif")) or {}
                            user_comment = exif.get("Exif").get(
                                piexif.ExifIFD.UserComment
                            )
                        except TypeError:
                            print("empty jpeg")
                        except Exception:
                            pass
                        else:
                            # swarm format
                            if "sui_image_params" in user_comment[8:].decode("utf-16"):
                                self._tool = "StableSwarmUI"
                                self._parser = SwarmUI(
                                    raw=user_comment[8:].decode("utf-16")
                                )
                            else:
                                self._raw = piexif.helper.UserComment.load(user_comment)
                                # easydiff jpeg and webp format
                                if self._raw[0] == "{":
                                    self._tool = "Easy Diffusion"
                                    self._parser = EasyDiffusion(raw=self._raw)
                                # a1111 jpeg and webp format
                                else:
                                    self._tool = "A1111 webUI"
                                    self._parser = A1111(raw=self._raw)

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
            match image_format:
                case "PNG":
                    metadata = PngInfo()
                    metadata.add_text("parameters", data)
                case "JPEG" | "WEBP":
                    metadata = piexif.dump(
                        {
                            "Exif": {
                                piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(
                                    data, encoding="unicode"
                                )
                            },
                        }
                    )

        with Image.open(image_path) as f:
            try:
                match image_format:
                    case "PNG":
                        if data:
                            f.save(new_path, pnginfo=metadata)
                        else:
                            f.save(new_path)
                    case "JPEG":
                        f.save(new_path, quality="keep")
                        if data:
                            piexif.insert(metadata, str(new_path))
                    case "WEBP":
                        f.save(new_path, quality=100, lossless=True)
                        if data:
                            piexif.insert(metadata, str(new_path))
            except:
                print("Save error")

    def prompt_to_line(self):
        return self._parser.prompt_to_line()

    @property
    def height(self):
        return self._parser.height

    @property
    def width(self):
        return self._parser.width

    @property
    def info(self):
        return self._info

    @property
    def positive(self):
        return self._parser.positive

    @property
    def negative(self):
        return self._parser.negative

    @property
    def positive_sdxl(self):
        return self._parser.positive_sdxl

    @property
    def negative_sdxl(self):
        return self._parser.negative_sdxl

    @property
    def setting(self):
        return self._parser.setting

    @property
    def raw(self):
        return self._parser.raw

    @property
    def tool(self):
        return self._tool

    @property
    def parameter(self):
        return self._parser.parameter

    @property
    def format(self):
        return self._format

    @property
    def is_sdxl(self):
        return self._parser.is_sdxl

    @property
    def props(self):
        return self._parser.props
