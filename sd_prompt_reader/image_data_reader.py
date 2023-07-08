# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'image_data_reader.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

import json
from xml.dom import minidom
from pathlib import PureWindowsPath, PurePosixPath

import piexif
import piexif.helper
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from sd_prompt_reader.constants import PARAMETER_PLACEHOLDER

# comfyui node types
KSAMPLER_TYPES = ["KSampler", "KSamplerAdvanced"]
VAE_ENCODE_TYPE = ["VAEEncode", "VAEEncodeForInpaint"]
CHECKPOINT_LOADER_TYPE = ["CheckpointLoader", "CheckpointLoaderSimple", "unCLIPCheckpointLoader"]
EASYDIFFUSION_MAPPING_A = {
    "prompt": "Prompt",
    "negative_prompt": "Negative Prompt",
    "seed": "Seed",
    "use_stable_diffusion_model": "Stable Diffusion model",
    "clip_skip": "Clip Skip",
    "use_vae_model": "VAE model",
    "sampler_name": "Sampler",
    "width": "Width",
    "height": "Height",
    "num_inference_steps": "Steps",
    "guidance_scale": "Guidance Scale",
}

EASYDIFFUSION_MAPPING_B = {
    "prompt": "prompt",
    "negative_prompt": "negative_prompt",
    "seed": "seed",
    "use_stable_diffusion_model": "use_stable_diffusion_model",
    "clip_skip": "clip_skip",
    "use_vae_model": "use_vae_model",
    "sampler_name": "sampler_name",
    "width": "width",
    "height": "height",
    "num_inference_steps": "num_inference_steps",
    "guidance_scale": "guidance_scale",
}

PROMPT_MAPPING = {
    # "Model":                    ("sd_model",            True),
    # "prompt",
    # "negative_prompt",
    "Seed":                     ("seed",                False),
    "Variation seed strength":  ("subseed_strength",    False),
    # "seed_resize_from_h",
    # "seed_resize_from_w",
    "Sampler":                  ("sampler_name",        True),
    "Steps":                    ("steps",               False),
    "CFG scale":                ("cfg_scale",           False),
    # "width",
    # "height",
    "Face restoration":         ("restore_faces",       False),
}


class ImageDataReader:
    def __init__(self, file, is_txt: bool = False):
        self._height = None
        self._width = None
        self._info = {}
        self._positive = ""
        self._negative = ""
        self._setting = ""
        self._raw = ""
        self._tool = ""
        self.parameter_key = ["model", "sampler", "seed", "cfg", "steps", "size"]
        self._parameter = dict.fromkeys(self.parameter_key, PARAMETER_PLACEHOLDER)
        self._is_txt = is_txt
        self._format = ""
        self.read_data(file)

    def read_data(self, file):
        if self._is_txt:
            self._raw = file.read()
            self._sd_format()
            return
        with Image.open(file) as f:
            self._width = f.width
            self._height = f.height
            self._info = f.info
            self._format = f.format
            if f.format == "PNG":
                # a1111 png format
                if "parameters" in self._info:
                    self._tool = "A1111 webUI"
                    self._raw = self._info.get("parameters")
                    self._sd_format()
                # easydiff png format
                if "negative_prompt" in self._info or "Negative Prompt" in self._info:
                    self._tool = "Easy Diffusion"
                    self._raw = str(self._info).replace("'", '"')
                    self._ed_format()
                # invokeai metadata format
                elif "sd-metadata" in self._info:
                    self._tool = "InvokeAI"
                    self._invoke_metadata()
                # invokeai legacy dream format
                elif "Dream" in self._info:
                    self._tool = "InvokeAI"
                    self._invoke_dream()
                # novelai format
                elif self._info.get("Software") == "NovelAI":
                    self._tool = "NovelAI"
                    self._nai_png()
                # comfyui format
                elif "prompt" in self._info:
                    self._tool = "ComfyUI"
                    self._comfy_png()
                # drawthings format
                elif "XML:com.adobe.xmp" in self._info:
                    self._tool = "Draw Things"
                    self._dt_format()
            elif f.format == "JPEG" or f.format == "WEBP":
                try:
                    exif = piexif.load(self._info.get("exif")) or {}
                    self._raw = piexif.helper.UserComment.load(exif.get("Exif").get(piexif.ExifIFD.UserComment))
                except TypeError:
                    print("empty jpeg")
                except Exception:
                    pass
                else:
                    # easydiff jpeg and webp format
                    if self._raw[0] == "{":
                        self._tool = "Easy Diffusion"
                        self._ed_format()
                    # a1111 jpeg and webp format
                    else:
                        self._tool = "A1111 webUI"
                        self._sd_format()

    def _sd_format(self):
        if self._raw and "\nSteps:" in self._raw:
            # w/ neg
            if "Negative prompt:" in self._raw:
                prompt_index = [self._raw.index("\nNegative prompt:"),
                                self._raw.index("\nSteps:")]
            # w/o neg
            else:
                prompt_index = [self._raw.index("\nSteps:")]
            self._positive = self._raw[:prompt_index[0]]
            self._negative = self._raw[prompt_index[0] + 1 + len("Negative prompt: "):prompt_index[-1]]
            self._setting = self._raw[prompt_index[-1] + 1:]

            parameter_index = [
                self._setting.find("Model: ") + len("Model: "),
                self._setting.find("Sampler: ") + len("Sampler: "),
                self._setting.find("Seed: ") + len("Seed: "),
                self._setting.find("CFG scale: ") + len("CFG scale: "),
                self._setting.find("Steps: ") + len("Steps: "),
                self._setting.find("Size: ") + len("Size: "),
            ]
            if self._setting.find("Model: ") != -1:
                self._parameter["model"] = self._setting[parameter_index[0]:self._setting.find(",", parameter_index[0])]
            self._parameter["sampler"] = self._setting[parameter_index[1]:self._setting.find(",", parameter_index[1])]
            self._parameter["seed"] = self._setting[parameter_index[2]:self._setting.find(",", parameter_index[2])]
            self._parameter["cfg"] = self._setting[parameter_index[3]:self._setting.find(",", parameter_index[3])]
            self._parameter["steps"] = self._setting[parameter_index[4]:self._setting.find(",", parameter_index[4])]
            self._parameter["size"] = self._setting[parameter_index[5]:self._setting.find(",", parameter_index[5])]
        elif self._raw:
            # w/ neg
            if "Negative prompt:" in self._raw:
                prompt_index = [self._raw.index("\nNegative prompt:")]
                self._negative = self._raw[prompt_index[0] + 1 + len("Negative prompt: "):]
            # w/o neg
            else:
                prompt_index = [len(self._raw)]
            self._positive = self._raw[:prompt_index[0]]
        else:
            self._raw = ""

    def _ed_format(self):
        data = json.loads(self._raw)
        if data.get("prompt"):
            ed = EASYDIFFUSION_MAPPING_B
        else:
            ed = EASYDIFFUSION_MAPPING_A
        self._positive = data.get(ed["prompt"])
        data.pop(ed["prompt"])
        self._negative = data.get(ed["negative_prompt"])
        data.pop(ed["negative_prompt"])
        if PureWindowsPath(data.get(ed['use_stable_diffusion_model'])).drive:
            file = PureWindowsPath(data.get(ed['use_stable_diffusion_model'])).name
        else:
            file = PurePosixPath(data.get(ed['use_stable_diffusion_model'])).name

        self._setting = self.remove_quotes(data).replace("{", "").replace("}", "")
        self._parameter["model"] = file
        self._parameter["sampler"] = data.get(ed['sampler_name'])
        self._parameter["seed"] = data.get(ed['seed'])
        self._parameter["cfg"] = data.get(ed['guidance_scale'])
        self._parameter["steps"] = data.get(ed['num_inference_steps'])
        self._parameter["size"] = str(data.get(ed['width'])) + "x" + str(data.get(ed['height']))

    def _invoke_metadata(self):
        metadata = json.loads(self._info.get("sd-metadata"))
        image = metadata.get("image")
        prompt = image.get("prompt")
        prompt_index = [prompt.rfind("["), prompt.rfind("]")]

        # w/ neg
        if -1 not in prompt_index:
            self._positive = prompt[:prompt_index[0]]
            self._negative = prompt[prompt_index[0] + 1:prompt_index[1]]
        # w/o neg
        else:
            self._positive = prompt

        self._raw += self._positive
        self._raw += "\n" + self.negative
        self._raw += "\n" + self._info.get("Dream") + "\n" + self._info.get("sd-metadata")
        self._setting = (
            f"Steps: {image.get('steps')}"
            f", Sampler: {image.get('sampler')}"
            f", CFG scale: {image.get('cfg_scale')}"
            f", Seed: {image.get('seed')}"
            f", Size: {image.get('width')}x{image.get('height')}"
            f", Model hash: {metadata.get('model_hash')}"
            f", Model: {metadata.get('model_weights')}"
            f", Threshold: {image.get('threshold')}"
            f", Perlin: {image.get('perlin')}"
            f", Hires fix: {image.get('hires_fix')}"
            f", Seamless: {image.get('seamless')}"
            f", Type: {image.get('type')}"
            f", Postprocessing: {self.remove_quotes(image.get('postprocessing'))}"
            f", Variations: {image.get('variations')}"
        )

        self._parameter["model"] = metadata.get('model_weights')
        self._parameter["sampler"] = image.get('sampler')
        self._parameter["seed"] = image.get('seed')
        self._parameter["cfg"] = image.get('cfg_scale')
        self._parameter["steps"] = image.get('steps')
        self._parameter["size"] = str(image.get('width')) + "x" + str(image.get('height'))

    def _invoke_dream(self):
        dream = self._info.get("Dream")
        prompt_index = dream.rfind('"')
        neg_index = [dream.rfind("["), dream.rfind("]")]

        # w/ neg
        if -1 not in neg_index:
            self._positive = dream[1:neg_index[0]]
            self._negative = dream[neg_index[0] + 1:neg_index[1]]
        # w/o neg
        else:
            self._positive = dream[1:prompt_index]

        self._raw += self._positive
        self._raw += "\n" + self.negative
        self._raw += "\n" + self._info.get("Dream")

        setting_index = [dream.rfind("-s"),
                         dream.rfind("-S"),
                         dream.rfind("-W"),
                         dream.rfind("-H"),
                         dream.rfind("-C"),
                         dream.rfind("-A")]
        self._setting = (
            f"Steps: {dream[setting_index[0] + 3:setting_index[1] - 1]}"
            f", Sampler: {dream[setting_index[5] + 3:].split()[0]}"
            f", CFG scale: {dream[setting_index[4] + 3:setting_index[5] - 1]}"
            f", Seed: {dream[setting_index[1] + 3:setting_index[2] - 1]}"
            f", Size: {dream[setting_index[2] + 3:setting_index[3] - 1]}"
            f"x{dream[setting_index[3] + 3:setting_index[4] - 1]}"
        )

        self._parameter["sampler"] = dream[setting_index[5] + 3:].split()[0]
        self._parameter["seed"] = dream[setting_index[1] + 3:setting_index[2] - 1]
        self._parameter["cfg"] = dream[setting_index[4] + 3:setting_index[5] - 1]
        self._parameter["steps"] = dream[setting_index[0] + 3:setting_index[1] - 1]
        self._parameter["size"] = str(dream[setting_index[2] + 3:setting_index[3] - 1]) + "x" \
                                  + str(dream[setting_index[3] + 3:setting_index[4] - 1])

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

        self._parameter["sampler"] = comment_json.get('sampler')
        self._parameter["seed"] = comment_json.get('seed')
        self._parameter["cfg"] = comment_json.get('scale')
        self._parameter["steps"] = comment_json.get('steps')
        self._parameter["size"] = str(self._width) + "x" + str(self._height)

    def _dt_format(self):
        try:
            data = minidom.parseString(self._info.get("XML:com.adobe.xmp"))
            data_json = json.loads(data.getElementsByTagName("exif:UserComment")[0]
                                   .childNodes[1].childNodes[1].childNodes[0].data)
        except:
            print("Draw things format error")
        else:
            self._positive = data_json.get("c")
            self._negative = data_json.get("uc")
            self._raw = "\n".join([self._positive, self._negative, str(data_json)])
            data_json.pop("c")
            data_json.pop("uc")
            self._setting = self.remove_quotes(str(data_json)[1:-1])

            self._parameter["model"] = data_json.get('model')
            self._parameter["sampler"] = data_json.get('sampler')
            self._parameter["seed"] = data_json.get('seed')
            self._parameter["cfg"] = data_json.get('scale')
            self._parameter["steps"] = data_json.get('steps')
            self._parameter["size"] = data_json.get('size')

    def _comfy_png(self):
        prompt = self._info.get("prompt") or {}
        workflow = self._info.get("workflow") or {}
        prompt_json = json.loads(prompt)

        # find end node of each flow
        end_nodes = list(filter(lambda item: item[-1].get("class_type") == "SaveImage", prompt_json.items()))
        longest_flow = {}
        longest_nodes = []
        longest_flow_len = 0

        # traverse each flow from the end
        for end_node in end_nodes:
            flow, nodes = self._comfy_traverse(prompt_json, str(end_node[0]))
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
            f"Steps: {longest_flow.get('steps')}"
            f", Sampler: {self.remove_quotes(longest_flow.get('sampler_name'))}"
            f", CFG scale: {longest_flow.get('cfg')}"
            f", Seed: {longest_flow.get('seed')}"
            f", Size: {self._width}x{self._height}"
            f", Model: {self.remove_quotes(longest_flow.get('ckpt_name'))}"
            f", Scheduler: {self.remove_quotes(longest_flow.get('scheduler'))}"
        )
        if "denoise" in longest_flow:
            self._setting += f", Denoise: {longest_flow.get('denoise')}"
        if "upscale_method" in longest_flow:
            self._setting += f", Upscale method: {self.remove_quotes(longest_flow.get('upscale_method'))}"
        if "upscaler" in longest_flow:
            self._setting += f", Upscale model: {self.remove_quotes(longest_flow.get('upscaler'))}"

        self._parameter["model"] = str(self.remove_quotes(longest_flow.get('ckpt_name')))
        self._parameter["sampler"] = str(self.remove_quotes(longest_flow.get('sampler_name')))
        self._parameter["seed"] = str(longest_flow.get('seed'))
        self._parameter["cfg"] = str(longest_flow.get('cfg'))
        self._parameter["steps"] = str(longest_flow.get('steps'))
        self._parameter["size"] = str(self._width) + "x" + str(self._height)

    def _comfy_traverse(self, prompt, end_node):
        flow = {}
        node = [end_node]
        inputs = {}
        try:
            inputs = prompt[end_node]["inputs"]
        except:
            print("node error")
            return flow, node
        match prompt[end_node]["class_type"]:
            case "SaveImage":
                try:
                    last_flow, last_node = self._comfy_traverse(prompt, inputs["images"][0])
                    flow = self.merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI SaveImage error")
            case node_type if node_type in KSAMPLER_TYPES:
                try:
                    flow = inputs
                    last_flow1, last_node1 = self._comfy_traverse(prompt, inputs["model"][0])
                    last_flow2, last_node2 = self._comfy_traverse(prompt, inputs["latent_image"][0])
                    self._positive = self._comfy_traverse(prompt, inputs["positive"][0])
                    self._negative = self._comfy_traverse(prompt, inputs["negative"][0])
                    flow = self.merge_dict(flow, last_flow1)
                    flow = self.merge_dict(flow, last_flow2)
                    node += last_node1 + last_node2
                except:
                    print("comfyUI KSampler error")
            case "CLIPTextEncode":
                try:
                    return inputs.get("text")
                except:
                    print("comfyUI CLIPText error")
            case "LoraLoader":
                try:
                    flow = inputs
                    last_flow, last_node = self._comfy_traverse(prompt, inputs["model"][0])
                    flow = self.merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI LoraLoader error")
            case node_type if node_type in CHECKPOINT_LOADER_TYPE:
                try:
                    return inputs, node
                except:
                    print("comfyUI CheckpointLoader error")
            case node_type if node_type in VAE_ENCODE_TYPE:
                try:
                    last_flow, last_node = self._comfy_traverse(prompt, inputs["pixels"][0])
                    flow = self.merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI VAE error")
            case "ImageScale":
                try:
                    flow = inputs
                    last_flow, last_node = self._comfy_traverse(prompt, inputs["image"][0])
                    flow = self.merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI ImageScale error")
            case "UpscaleModelLoader":
                try:
                    return {"upscaler": inputs["model_name"]}
                except:
                    print("comfyUI UpscaleLoader error")
            case "ImageUpscaleWithModel":
                try:
                    flow = inputs
                    last_flow, last_node = self._comfy_traverse(prompt, inputs["image"][0])
                    model = self._comfy_traverse(prompt, inputs["upscale_model"][0])
                    flow = self.merge_dict(flow, last_flow)
                    flow = self.merge_dict(flow, model)
                    node += last_node
                except:
                    print("comfyUI UpscaleModel error")
            case "ConditioningCombine":
                try:
                    last_flow1, last_node1 = self._comfy_traverse(prompt,
                                                                  inputs["conditioning_1"][0])
                    last_flow2, last_node2 = self._comfy_traverse(prompt,
                                                                  inputs["conditioning_2"][0])
                    flow = self.merge_dict(flow, last_flow1)
                    flow = self.merge_dict(flow, last_flow2)
                    node += last_node1 + last_node2
                except:
                    print("comfyUI ConditioningCombine error")
            case _:
                try:
                    last_flow = {}
                    last_node = []
                    if inputs.get("samples"):
                        last_flow, last_node = self._comfy_traverse(prompt, inputs["samples"][0])
                    elif inputs.get("image"):
                        last_flow, last_node = self._comfy_traverse(prompt, inputs["image"][0])
                    elif inputs.get("model"):
                        last_flow, last_node = self._comfy_traverse(prompt, inputs["model"][0])
                    elif inputs.get("clip"):
                        last_flow, last_node = self._comfy_traverse(prompt, inputs["clip"][0])
                    elif inputs.get("samples_from"):
                        last_flow, last_node = self._comfy_traverse(prompt,
                                                                    inputs["samples_from"][0])
                    elif inputs.get("conditioning"):
                        result = self._comfy_traverse(prompt, inputs["conditioning"][0])
                        if isinstance(result, str):
                            return result
                        elif isinstance(result, list):
                            last_flow, last_node = result
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
    def save_image(image_path, new_path, image_format, data=None):
        metadata = None
        if data:
            match image_format:
                case "PNG":
                    metadata = PngInfo()
                    metadata.add_text("parameters", data)
                case "JPEG" | "WEBP":
                    metadata = piexif.dump({
                        "Exif": {
                            piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(data, encoding="unicode")
                        },
                    })

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

    @staticmethod
    def add_quotes(string):
        return '"'+str(string)+'"'

    def prompt_to_line(self):
        if not self._setting:
            return ""
        single_line_prompt = "--prompt " + self.add_quotes(self._positive).replace("\n", "")
        if self._negative:
            single_line_prompt += " --negative_prompt " + self.add_quotes(self._negative).replace("\n", "")
        setting = dict(filter(lambda x: len(x) == 2, (param.split(": ") for param in self._setting.split(", "))))
        for key, value in setting.items():
            if key == "Size":
                width, height = value.split("x")
                single_line_prompt += " --width " + width
                single_line_prompt += " --height " + height
            if key == "Seed resize from":
                seed_resize_from_w, seed_resize_from_h = value.split("x")
                single_line_prompt += " --seed_resize_from_w " + seed_resize_from_w
                single_line_prompt += " --seed_resize_from_h " + seed_resize_from_h
            try:
                (tag, is_str) = PROMPT_MAPPING.get(key)
            except:
                pass
            else:
                if is_str:
                    single_line_prompt += " --" + tag + " " + self.add_quotes(str(value))
                else:
                    single_line_prompt += " --" + tag + " " + value
        return single_line_prompt

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

    @property
    def parameter(self):
        return self._parameter

    @property
    def format(self):
        return self._format
