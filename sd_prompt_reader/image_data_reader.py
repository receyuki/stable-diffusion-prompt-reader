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
        self._tool = ""
        self.read_data(file)

    def _sd_format(self):
        if self._raw and "\nSteps:" in self._raw:
            if "Negative prompt:" in self._raw:
                prompt_index = [self._raw.index("\nNegative prompt:"),
                                self._raw.index("\nSteps:")]
            else:
                prompt_index = [self._raw.index("\nSteps:"),
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
                self._tool = "A1111 webUI"
                self._sd_png()
            # a1111 jpeg and webp format
            elif "exif" in self._info and (f.format == "JPEG" or f.format == "WEBP"):
                self._tool = "A1111 webUI"
                self._sd_jpg()
            # novelai format
            elif self._info.get("Software") == "NovelAI" and f.format == "PNG":
                self._tool = "NovelAI"
                self._nai_png()
            # comfyui format
            elif self._info.get("prompt") and f.format == "PNG":
                self._tool = "ComfyUI"
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
        self._negative = comment_json.get("uc")
        self._raw += "\n" + self.negative
        self._raw += "\n" + comment
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

        # for value in prompt_json.values():
        #     if value.get("class_type") in sampler_type and value.get("inputs").get("model"):
        #         ksampler = value

        # ksampler = next(filter(lambda value: value.get("class_type") in sampler_type, prompt_json.values()), None)
        # multi chain
        end_nodes = list(filter(lambda item: item[-1].get("class_type") == "SaveImage", prompt_json.items()))
        # flows = []
        # node_flows = []
        # print(end_nodes)
        longest_flow = {}
        longest_nodes = []
        longest_flow_len = 0
        for end_node in end_nodes:
            chain = {}
            flow, nodes = self._comfy_traverse(prompt_json, str(end_node[0]))
            # flows.append(chain)
            # node_flows.append(nodes)
            if len(nodes) > longest_flow_len:
                longest_flow = flow
                longest_nodes = nodes
                longest_flow_len = len(nodes)

        self._raw += self._positive
        self._raw += "\n" + self._negative
        self._raw += "\n" + str(prompt)
        if workflow:
            self._raw += "\n" + str(workflow)
        self._setting = (
            f"Seed: {longest_flow.get('seed')}"
            f", Steps: {longest_flow.get('steps')}"
            f", CFG scale: {longest_flow.get('cfg')}"
            f", Sampler: {self.remove_quotes(longest_flow.get('sampler_name'))}"
            f", Scheduler: {self.remove_quotes(longest_flow.get('scheduler'))}"
            f", Size: {self._width}x{self._height}"
            f", Model: {self.remove_quotes(longest_flow.get('ckpt_name'))}"
        )
        if "denoise" in longest_flow:
            self._setting += f", Denoise: {longest_flow.get('denoise')}"
        if "upscale_method" in longest_flow:
            self._setting += f", Upscale method: {self.remove_quotes(longest_flow.get('upscale_method'))}"
        if "upscaler" in longest_flow:
            self._setting += f", Upscale model: {self.remove_quotes(longest_flow.get('upscaler'))}"

    def _comfy_traverse(self, prompt, end_node):
        ksampler_types = ["KSampler", "KSamplerAdvanced"]
        vae_encode_type = ["VAEEncode", "VAEEncodeForInpaint"]
        checkpoint_loader_type = ["CheckpointLoader", "CheckpointLoaderSimple"]
        flow = {}
        node = [end_node]
        match prompt[end_node]["class_type"]:
            case "SaveImage":
                try:
                    last_flow, last_node = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["images"][0])
                    flow = self.merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI SaveImage error")
            case node_type if node_type in ksampler_types:
                try:
                    flow = prompt[end_node]["inputs"]
                    last_flow1, last_node1 = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["model"][0])
                    last_flow2, last_node2 = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["latent_image"][0])
                    self._positive = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["positive"][0])
                    self._negative = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["negative"][0])
                    flow = self.merge_dict(flow, last_flow1)
                    flow = self.merge_dict(flow, last_flow2)
                    node += last_node1 + last_node2
                except:
                    print("comfyUI KSampler error")
            case "CLIPTextEncode":
                try:
                    return prompt[end_node]["inputs"]["text"]
                except:
                    print("comfyUI CLIPText error")
            case "LoraLoader":
                try:
                    flow = prompt[end_node]["inputs"]
                    last_flow, last_node = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["model"][0])
                    flow = self.merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI LoraLoader error")
            case node_type if node_type in checkpoint_loader_type:
                try:
                    return prompt[end_node]["inputs"], node
                except:
                    print("comfyUI CheckpointLoader error")
            case node_type if node_type in vae_encode_type:
                try:
                    last_flow, last_node = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["pixels"][0])
                    flow = self.merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI VAE error")
            case "ImageScale":
                try:
                    flow = prompt[end_node]["inputs"]
                    last_flow, last_node = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["image"][0])
                    flow = self.merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI ImageScale error")
            case "UpscaleModelLoader":
                try:
                    return {"upscaler": prompt[end_node]["inputs"]["model_name"]}
                except:
                    print("comfyUI UpscaleLoader error")
            case "ImageUpscaleWithModel":
                try:
                    flow = prompt[end_node]["inputs"]
                    last_flow, last_node = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["image"][0])
                    model = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["upscale_model"][0])
                    flow = self.merge_dict(flow, last_flow)
                    flow = self.merge_dict(flow, model)
                    node += last_node
                except:
                    print("comfyUI UpscaleModel error")
            case "ConditioningCombine":
                try:
                    last_flow1, last_node1 = self._comfy_traverse(prompt,
                                                                  prompt[end_node]["inputs"]["conditioning_1"][0])
                    last_flow2, last_node2 = self._comfy_traverse(prompt,
                                                                  prompt[end_node]["inputs"]["conditioning_2"][0])
                    flow = self.merge_dict(flow, last_flow1)
                    flow = self.merge_dict(flow, last_flow2)
                    node += last_node1 + last_node2
                except:
                    print("comfyUI ConditioningCombine error")
            case _:
                try:
                    last_flow = {}
                    last_node = []
                    if prompt[end_node]["inputs"].get("samples"):
                        last_flow, last_node = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["samples"][0])
                    elif prompt[end_node]["inputs"].get("image"):
                        last_flow, last_node = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["image"][0])
                    elif prompt[end_node]["inputs"].get("model"):
                        last_flow, last_node = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["model"][0])
                    elif prompt[end_node]["inputs"].get("clip"):
                        last_flow, last_node = self._comfy_traverse(prompt, prompt[end_node]["inputs"]["clip"][0])
                    elif prompt[end_node]["inputs"].get("samples_from"):
                        last_flow, last_node = self._comfy_traverse(prompt,
                                                                    prompt[end_node]["inputs"]["samples_from"][0])
                    elif prompt[end_node]["inputs"].get("conditioning"):
                        last_flow, last_node = self._comfy_traverse(prompt,
                                                                    prompt[end_node]["inputs"]["conditioning"][0])
                    flow = self.merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI bridging node error")
        return flow, node

    @staticmethod
    def remove_data(image_file):
        with Image.open(image_file) as f:
            image_data = list(f.getdata())
            image_without_exif = Image.new(f.mode, f.size)
            image_without_exif.putdata(image_data)
            return image_without_exif

    @staticmethod
    def merge_str_to_tuple(item1, item2):
        if not isinstance(item1, tuple):
            item1 = (item1,)
        if not isinstance(item2, tuple):
            item2 = (item2,)
        return item1 + item2

    def merge_dict(self, dict1, dict2):
        dict3 = dict1.copy()
        for k, v in dict2.items():
            dict3[k] = self.merge_str_to_tuple(v, dict3[k]) if k in dict3 else v
        return dict3

    @staticmethod
    def remove_quotes(string):
        return str(string).replace('"', '').replace("'", "")

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

    @property
    def tool(self):
        return self._tool
