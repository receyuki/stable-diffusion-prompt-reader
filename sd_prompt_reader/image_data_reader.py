# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'image_data_reader.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

import json
import traceback

import piexif
from PIL import Image
from piexif import helper


class ImageDataReader():
    def __init__(self, file):
        self.file = file

    @staticmethod
    def read_info_from_image(self, image):
        items = image.info or {}

        geninfo = items.pop('parameters', None)

        if "exif" in items:
            exif = piexif.load(items["exif"])
            exif_comment = (exif or {}).get("Exif", {}).get(piexif.ExifIFD.UserComment, b'')
            try:
                exif_comment = piexif.helper.UserComment.load(exif_comment)
            except ValueError:
                exif_comment = exif_comment.decode('utf8', errors="ignore")

            if exif_comment:
                items['exif comment'] = exif_comment
                geninfo = exif_comment

            for field in ['jfif', 'jfif_version', 'jfif_unit', 'jfif_density', 'dpi', 'exif',
                          'loop', 'background', 'timestamp', 'duration']:
                items.pop(field, None)

            if items.get("Software", None) == "NovelAI":
                try:
                    json_info = json.loads(items["Comment"])
                    sampler = sd_samplers.samplers_map.get(json_info["sampler"], "Euler a")

                    geninfo = f"""{items["Description"]}
        Negative prompt: {json_info["uc"]}
        Steps: {json_info["steps"]}, Sampler: {sampler}, CFG scale: {json_info["scale"]}, Seed: {json_info["seed"]}, Size: {image.width}x{image.height}, Clip skip: 2, ENSD: 31337"""
                except Exception:
                    print("Error parsing NovelAI image generation parameters:", file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)

        return geninfo, items

    def image_data(file):
        try:
            image = Image.open(file)
            image.info
            textinfo, _ = read_info_from_image(image)
            return textinfo, None
        except Exception:
            pass

        # try:
        #     text = data.decode('utf8')
        #     assert len(text) < 10000
        #     return text, None
        #
        # except Exception:
        #     pass

        return '', None

    @staticmethod
    def read_info(file):
        with Image.open(file) as image:
            items = image.info or {}
            # geninfo = items.pop('parameters', None)
            print(items.pop('parameters'))
            print(items.pop('exif'))

            print("parammeters" in items)
            print("exif" in items)

