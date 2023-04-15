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
            # a1111 png format
            if "parameters" in self._info and f.format == "PNG":
                self._sd_png()
            # a1111 jpeg and webp format
            elif "exif" in self._info and (f.format == "JPEG" or f.format == "WEBP"):
                self._sd_jpg()
            # novelai format
            elif self._info.get("Software") == "NovelAI" and f.format == "PNG":
                self._nai_png()
            # comfyui format
            elif self._info.get("prompt") and f.format == "PNG":
                self._comfy_png()

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
        self._raw += "\n" + comment
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

    def _comfy_png(self):
        prompt = self._info.get("prompt") or {}
        workflow = self._info.get("workflow") or {}
        prompt_json = json.loads(prompt)
        self._raw += str(prompt)

        if workflow:
            self._raw += "\n" + workflow
        # for value in prompt_json.values():
        #     if value.get("class_type") in sampler_type and value.get("inputs").get("model"):
        #         ksampler = value

        # ksampler = next(filter(lambda value: value.get("class_type") in sampler_type, prompt_json.values()), None)
        # multi chain
        end_nodes = list(filter(lambda item: item[-1].get("class_type") == "SaveImage", prompt_json.items()))
        chains = []
        # print(end_nodes)

        for end_node in end_nodes:
            chain = {}
            chain = self._comfy_traverse(prompt_json, str(end_node[0]))
            print(chain)
            chains.append(chain)

        # print(prompt)

    def _comfy_traverse(self, prompt, end_node):
        SAMPLES_SKIP_TYPES = ["VAEDecode", "LatentUpscale"]
        KSAMPLER_TYPES = ["KSampler", "KSamplerAdvanced"]
        chain = {}
        if prompt[end_node]["class_type"] == "SaveImage":
            print(end_node)
            chain.update(self._comfy_traverse(prompt, prompt[end_node]["inputs"]["images"][0]))
        elif prompt[end_node]["class_type"] in KSAMPLER_TYPES:
            print(end_node)
            chain = prompt[end_node]["inputs"]
            branch1 = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["model"][0]) or {}
            branch2 = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["latent_image"][0]) or {}
            chain.update(max([branch1, branch2], key=len))
        elif prompt[end_node]["class_type"] == "LoraLoader":
            print(end_node)
            chain = prompt[end_node]["inputs"]
            chain.update(self._comfy_traverse(prompt, prompt[end_node]["inputs"]["model"][0]))
        elif prompt[end_node]["class_type"] == "CheckpointLoaderSimple":
            print(end_node)
            return prompt[end_node]["inputs"]
        elif prompt[end_node]["class_type"] == "EmptyLatentImage":
            print(end_node)
            return
        elif prompt[end_node]["class_type"] == "VAEEncode":
            print(end_node)
            chain.update(self._comfy_traverse(prompt, prompt[end_node]["inputs"]["pixels"][0]))
        elif prompt[end_node]["class_type"] == "ImageScale":
            print(end_node)
            chain = prompt[end_node]["inputs"]
            chain.update(self._comfy_traverse(prompt, prompt[end_node]["inputs"]["image"][0]))
        elif prompt[end_node]["class_type"] == "ImageUpscaleWithModel":
            print(end_node)
            chain = prompt[end_node]["inputs"]
            chain.update(self._comfy_traverse(prompt, prompt[end_node]["inputs"]["image"][0]))
        elif prompt[end_node]["class_type"] in SAMPLES_SKIP_TYPES:
            print(end_node)
            chain.update(self._comfy_traverse(prompt, prompt[end_node]["inputs"]["samples"][0]))

        print(chain)
        return chain
    #add latent image

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
