__author__ = "receyuki"
__filename__ = "comfyui.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json

from sd_prompt_reader.format.base_format import BaseFormat
from sd_prompt_reader.utility import remove_quotes, merge_dict

# comfyui node types
KSAMPLER_TYPES = ["KSampler", "KSamplerAdvanced"]
VAE_ENCODE_TYPE = ["VAEEncode", "VAEEncodeForInpaint"]
CHECKPOINT_LOADER_TYPE = [
    "CheckpointLoader",
    "CheckpointLoaderSimple",
    "unCLIPCheckpointLoader",
    "Checkpoint Loader (Simple)",
]
CLIP_TEXT_ENCODE_TYPE = [
    "CLIPTextEncode",
    "CLIPTextEncodeSDXL",
    "CLIPTextEncodeSDXLRefiner",
]
SAVE_IMAGE_TYPE = ["SaveImage", "Image Save"]


class ComfyUI(BaseFormat):
    def __init__(
        self, info: dict = None, raw: str = "", width: int = None, height: int = None
    ):
        super().__init__(info, raw, width, height)
        self._comfy_png()

    def _comfy_png(self):
        prompt = self._info.get("prompt") or {}
        workflow = self._info.get("workflow") or {}
        prompt_json = json.loads(prompt)

        # find end node of each flow
        end_nodes = list(
            filter(
                lambda item: item[-1].get("class_type")
                in ["SaveImage"] + KSAMPLER_TYPES,
                prompt_json.items(),
            )
        )
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

        if not self._is_sdxl:
            self._raw += self._positive
            self._raw += "\n" + self._negative or ""
        else:
            self._raw += self._positive_sdxl.get("Clip G") or ""
            self._raw += "\n" + (self._positive_sdxl.get("Clip L") or "")
            self._raw += "\n" + (self._positive_sdxl.get("Refiner") or "")
            self._raw += "\n" + (self._negative_sdxl.get("Clip G") or "")
            self._raw += "\n" + (self._negative_sdxl.get("Clip L") or "")
            self._raw += "\n" + (self._negative_sdxl.get("Refiner") or "")
        self._raw += "\n" + str(prompt)
        if workflow:
            self._raw += "\n" + str(workflow)

        seed = str(
            longest_flow.get("seed")
            if longest_flow.get("seed")
            else longest_flow.get("noise_seed")
        )

        self._setting = (
            f"Steps: {longest_flow.get('steps')}"
            f", Sampler: {remove_quotes(longest_flow.get('sampler_name'))}"
            f", CFG scale: {longest_flow.get('cfg')}"
            f", Seed: {seed}"
            f", Size: {self._width}x{self._height}"
            f", Model: {remove_quotes(longest_flow.get('ckpt_name'))}"
            f", Scheduler: {remove_quotes(longest_flow.get('scheduler'))}"
        )
        if "denoise" in longest_flow:
            self._setting += f", Denoise: {longest_flow.get('denoise')}"
        if "upscale_method" in longest_flow:
            self._setting += (
                f", Upscale method: {remove_quotes(longest_flow.get('upscale_method'))}"
            )
        if "upscaler" in longest_flow:
            self._setting += (
                f", Upscale model: {remove_quotes(longest_flow.get('upscaler'))}"
            )

        self._parameter["model"] = str(remove_quotes(longest_flow.get("ckpt_name")))
        self._parameter["sampler"] = str(
            remove_quotes(longest_flow.get("sampler_name"))
        )
        self._parameter["seed"] = seed
        self._parameter["cfg"] = str(longest_flow.get("cfg"))
        self._parameter["steps"] = str(longest_flow.get("steps"))
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
            case node_type if node_type in SAVE_IMAGE_TYPE:
                try:
                    last_flow, last_node = self._comfy_traverse(
                        prompt, inputs["images"][0]
                    )
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI SaveImage error")
            case node_type if node_type in KSAMPLER_TYPES:
                try:
                    flow = inputs
                    last_flow1, last_node1 = self._comfy_traverse(
                        prompt, inputs["model"][0]
                    )
                    last_flow2, last_node2 = self._comfy_traverse(
                        prompt, inputs["latent_image"][0]
                    )
                    positive = self._comfy_traverse(prompt, inputs["positive"][0])
                    if isinstance(positive, str):
                        self._positive = positive
                    elif isinstance(positive, dict):
                        self._positive_sdxl.update(positive)
                    negative = self._comfy_traverse(prompt, inputs["negative"][0])
                    if isinstance(negative, str):
                        self._negative = negative
                    elif isinstance(negative, dict):
                        self._negative_sdxl.update(negative)
                    seed = None
                    # handle "CR Seed"
                    if inputs.get("seed") and isinstance(inputs.get("seed"), list):
                        seed = {"seed": self._comfy_traverse(prompt, inputs["seed"][0])}
                    elif inputs.get("noise_seed") and isinstance(
                        inputs.get("noise_seed"), list
                    ):
                        seed = {
                            "noise_seed": self._comfy_traverse(
                                prompt, inputs["noise_seed"][0]
                            )
                        }
                    if seed:
                        flow.update(seed)
                    flow = merge_dict(flow, last_flow1)
                    flow = merge_dict(flow, last_flow2)
                    node += last_node1 + last_node2
                except:
                    print("comfyUI KSampler error")
            case node_type if node_type in CLIP_TEXT_ENCODE_TYPE:
                try:
                    match node_type:
                        case "CLIPTextEncode":
                            return inputs.get("text")
                        case "CLIPTextEncodeSDXL":
                            # SDXLPromptStyler
                            self._is_sdxl = True
                            if isinstance(inputs["text_g"], list):
                                text_g = int(inputs["text_g"][0])
                                text_l = int(inputs["text_l"][0])
                                prompt_styler_g = self._comfy_traverse(
                                    prompt, str(text_g)
                                )
                                prompt_styler_l = self._comfy_traverse(
                                    prompt, str(text_l)
                                )
                                self._positive_sdxl["Clip G"] = prompt_styler_g[0]
                                self._positive_sdxl["Clip L"] = prompt_styler_l[0]
                                self._negative_sdxl["Clip G"] = prompt_styler_g[1]
                                self._negative_sdxl["Clip L"] = prompt_styler_l[1]
                                return
                            elif isinstance(inputs["text_g"], str):
                                return {
                                    "Clip G": inputs.get("text_g"),
                                    "Clip L": inputs.get("text_l"),
                                }
                        case "CLIPTextEncodeSDXLRefiner":
                            self._is_sdxl = True
                            if isinstance(inputs["text"], list):
                                # SDXLPromptStyler
                                text = int(inputs["text"][0])
                                prompt_styler = self._comfy_traverse(prompt, str(text))
                                self._positive_sdxl["Refiner"] = prompt_styler[0]
                                self._negative_sdxl["Refiner"] = prompt_styler[1]
                                return
                            elif isinstance(inputs["text"], str):
                                return {"Refiner": inputs.get("text")}
                except:
                    print("comfyUI CLIPText error")
            case "LoraLoader":
                try:
                    flow = inputs
                    last_flow, last_node = self._comfy_traverse(
                        prompt, inputs["model"][0]
                    )
                    flow = merge_dict(flow, last_flow)
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
                    last_flow, last_node = self._comfy_traverse(
                        prompt, inputs["pixels"][0]
                    )
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI VAE error")
            case "ImageScale":
                try:
                    flow = inputs
                    last_flow, last_node = self._comfy_traverse(
                        prompt, inputs["image"][0]
                    )
                    flow = merge_dict(flow, last_flow)
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
                    last_flow, last_node = self._comfy_traverse(
                        prompt, inputs["image"][0]
                    )
                    model = self._comfy_traverse(prompt, inputs["upscale_model"][0])
                    flow = merge_dict(flow, last_flow)
                    flow = merge_dict(flow, model)
                    node += last_node
                except:
                    print("comfyUI UpscaleModel error")
            case "ConditioningCombine":
                try:
                    last_flow1, last_node1 = self._comfy_traverse(
                        prompt, inputs["conditioning_1"][0]
                    )
                    last_flow2, last_node2 = self._comfy_traverse(
                        prompt, inputs["conditioning_2"][0]
                    )
                    flow = merge_dict(flow, last_flow1)
                    flow = merge_dict(flow, last_flow2)
                    node += last_node1 + last_node2
                except:
                    print("comfyUI ConditioningCombine error")
            # custom nodes
            case "SDXLPromptStyler":
                try:
                    return inputs.get("text_positive"), inputs.get("text_negative")
                except:
                    print("comfyUI SDXLPromptStyler error")
            case "CR Seed":
                try:
                    return inputs.get("seed")
                except:
                    print("comfyUI CR Seed error")
            case _:
                try:
                    last_flow = {}
                    last_node = []
                    if inputs.get("samples"):
                        last_flow, last_node = self._comfy_traverse(
                            prompt, inputs["samples"][0]
                        )
                    elif inputs.get("image"):
                        last_flow, last_node = self._comfy_traverse(
                            prompt, inputs["image"][0]
                        )
                    elif inputs.get("model"):
                        last_flow, last_node = self._comfy_traverse(
                            prompt, inputs["model"][0]
                        )
                    elif inputs.get("clip"):
                        last_flow, last_node = self._comfy_traverse(
                            prompt, inputs["clip"][0]
                        )
                    elif inputs.get("samples_from"):
                        last_flow, last_node = self._comfy_traverse(
                            prompt, inputs["samples_from"][0]
                        )
                    elif inputs.get("conditioning"):
                        result = self._comfy_traverse(prompt, inputs["conditioning"][0])
                        if isinstance(result, str):
                            return result
                        elif isinstance(result, list):
                            last_flow, last_node = result
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI bridging node error")
        return flow, node
