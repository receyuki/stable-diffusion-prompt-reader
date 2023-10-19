__author__ = "receyuki"
__filename__ = "comfyui.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json

from ..format.base_format import BaseFormat
from ..utility import remove_quotes, merge_dict


class ComfyUI(BaseFormat):
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
    SAVE_IMAGE_TYPE = ["SaveImage", "Image Save", "SDPromptSaver"]

    SETTING_KEY = [
        "ckpt_name",
        "sampler_name",
        "",
        "cfg",
        "steps",
        "",
    ]

    def __init__(
        self, info: dict = None, raw: str = "", width: int = None, height: int = None
    ):
        super().__init__(info, raw, width, height)
        self._comfy_png()

    def _comfy_png(self):
        prompt = self._info.get("prompt", {})
        workflow = self._info.get("workflow", {})
        prompt_json = json.loads(prompt)

        # find end node of each flow
        end_nodes = list(
            filter(
                lambda item: item[-1].get("class_type")
                in ["SaveImage"] + ComfyUI.KSAMPLER_TYPES,
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
            self._raw = "\n".join(
                [
                    self._positive.strip(),
                    self._negative.strip(),
                ]
            ).strip()
        else:
            sdxl_keys = ["Clip G", "Clip L", "Refiner"]
            self._raw = "\n".join(
                [
                    self._positive_sdxl.get(key).strip()
                    for key in sdxl_keys
                    if self._positive_sdxl.get(key)
                ]
                + [
                    self._negative_sdxl.get(key).strip()
                    for key in sdxl_keys
                    if self._negative_sdxl.get(key)
                ]
            )
        self._raw += "\n" + str(prompt)
        if workflow:
            self._raw += "\n" + str(workflow)

        add_noise = (
            f"Add noise: {remove_quotes(longest_flow.get('add_noise'))}"
            if longest_flow.get("add_noise")
            else ""
        )

        seed = (
            f"Seed: {longest_flow.get('seed')}"
            if longest_flow.get("seed")
            else f"Noise seed: {longest_flow.get('noise_seed')}"
        )

        start_at_step = (
            f"Start at step: {longest_flow.get('start_at_step')}"
            if longest_flow.get("start_at_step")
            else ""
        )

        end_at_step = (
            f"End at step: {longest_flow.get('end_at_step')}"
            if longest_flow.get("end_at_step")
            else ""
        )

        return_with_left_over_noise = (
            f"Return with left over noise: {longest_flow.get('return_with_left_over_noise')}"
            if longest_flow.get("return_with_left_over_noise")
            else ""
        )

        denoise = (
            f"Denoise: {longest_flow.get('denoise')}"
            if longest_flow.get("denoise")
            else ""
        )

        upscale_method = (
            f"Upscale method: {remove_quotes(longest_flow.get('upscale_method'))}"
            if longest_flow.get("upscale_method")
            else ""
        )

        upscaler = (
            f"Upscaler: {remove_quotes(longest_flow.get('upscaler'))}"
            if longest_flow.get("upscaler")
            else ""
        )

        self._setting = ", ".join(
            list(
                filter(
                    lambda item: item != "",
                    [
                        f"Steps: {longest_flow.get('steps')}",
                        f"Sampler: {remove_quotes(longest_flow.get('sampler_name'))}",
                        f"CFG scale: {longest_flow.get('cfg')}",
                        add_noise,
                        seed,
                        f"Size: {self._width}x{self._height}",
                        f"Model: {remove_quotes(longest_flow.get('ckpt_name'))}",
                        f"Scheduler: {remove_quotes(longest_flow.get('scheduler'))}",
                        start_at_step,
                        end_at_step,
                        return_with_left_over_noise,
                        denoise,
                        upscale_method,
                        upscaler,
                    ],
                )
            )
        )

        for p, s in zip(super().PARAMETER_KEY, ComfyUI.SETTING_KEY):
            match p:
                case k if k in ("model", "sampler"):
                    self._parameter[p] = str(remove_quotes(longest_flow.get(s)))
                case "seed":
                    self._parameter[p] = (
                        str(longest_flow.get("seed"))
                        if longest_flow.get("seed")
                        else str(longest_flow.get("noise_seed"))
                    )
                case "size":
                    self._parameter["size"] = str(self._width) + "x" + str(self._height)
                case _:
                    self._parameter[p] = str(longest_flow.get(s))

        if self._is_sdxl:
            if not self._positive and self.positive_sdxl:
                self._positive = self.merge_clip(self.positive_sdxl)
            if not self._negative and self.negative_sdxl:
                self._negative = self.merge_clip(self.negative_sdxl)

    @staticmethod
    def merge_clip(data: dict):
        clip_g = data.get("Clip G").strip(" ,")
        clip_l = data.get("Clip L").strip(" ,")

        if clip_g == clip_l:
            return clip_g
        else:
            return ",\n".join([clip_g, clip_l])

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
            case node_type if node_type in ComfyUI.SAVE_IMAGE_TYPE:
                try:
                    last_flow, last_node = self._comfy_traverse(
                        prompt, inputs["images"][0]
                    )
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI SaveImage error")
            case node_type if node_type in ComfyUI.KSAMPLER_TYPES:
                try:
                    seed = None
                    flow = inputs
                    last_flow1, last_node1, last_flow2, last_node2 = {}, [], {}, []
                    for key, value in inputs.items():
                        match key:
                            case "model":
                                traverse_result = self._comfy_traverse(prompt, value[0])
                                if isinstance(traverse_result, tuple):
                                    last_flow1, last_node1 = traverse_result
                                elif isinstance(traverse_result, dict):
                                    flow.update({key: traverse_result.get("ckpt_name")})
                            case "latent_image":
                                last_flow2, last_node2 = self._comfy_traverse(
                                    prompt, value[0]
                                )
                            case "positive":
                                positive = self._comfy_traverse(prompt, value[0])
                                if isinstance(positive, str):
                                    self._positive = positive
                                elif isinstance(positive, dict):
                                    if positive_prompt := positive.get("positive"):
                                        self._positive = positive_prompt
                                    else:
                                        self._positive_sdxl.update(positive)
                            case "negative":
                                negative = self._comfy_traverse(prompt, value[0])
                                if isinstance(negative, str):
                                    self._negative = negative
                                elif isinstance(negative, dict):
                                    if negative_prompt := negative.get("negative"):
                                        self._negative = negative_prompt
                                    else:
                                        self._negative_sdxl.update(negative)
                            case key_name if key_name in ("seed", "noise_seed"):
                                # handle "CR Seed"
                                if isinstance(value, list):
                                    traverse_result = self._comfy_traverse(
                                        prompt, value[0]
                                    )
                                    if isinstance(traverse_result, dict):
                                        seed = {key_name: traverse_result.get("seed")}
                                    else:
                                        seed = {key_name: traverse_result}
                                if seed:
                                    flow.update(seed)
                            case _ as key_name:
                                if isinstance(value, list):
                                    traverse_result = self._comfy_traverse(
                                        prompt, value[0]
                                    )
                                    if isinstance(traverse_result, dict):
                                        flow.update(
                                            {key_name: traverse_result.get(key_name)}
                                        )

                    flow = merge_dict(flow, last_flow1)
                    flow = merge_dict(flow, last_flow2)
                    node += last_node1 + last_node2
                except:
                    print("comfyUI KSampler error")
            case node_type if node_type in ComfyUI.CLIP_TEXT_ENCODE_TYPE:
                try:
                    match node_type:
                        case "CLIPTextEncode":
                            # SDXLPromptStyler & SDPromptReader
                            if isinstance(inputs["text"], list):
                                text = int(inputs["text"][0])
                                traverse_result = self._comfy_traverse(
                                    prompt, str(text)
                                )
                                if isinstance(traverse_result, tuple):
                                    self._positive = traverse_result[0]
                                    self._negative = traverse_result[1]
                                elif isinstance(traverse_result, dict):
                                    return traverse_result
                                return
                            elif isinstance(inputs["text"], str):
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
            case node_type if node_type in ComfyUI.CHECKPOINT_LOADER_TYPE:
                try:
                    return inputs, node
                except:
                    print("comfyUI CheckpointLoader error")
            case node_type if node_type in ComfyUI.VAE_ENCODE_TYPE:
                try:
                    last_flow, last_node = self._comfy_traverse(
                        prompt, inputs["pixels"][0]
                    )
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI VAE error")
            case "ControlNetApplyAdvanced":
                try:
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

                    last_flow, last_node = self._comfy_traverse(
                        prompt, inputs["image"][0]
                    )
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    print("comfyUI ControlNetApply error")
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
            # SD Prompt Reader Node
            case "SDPromptReader":
                try:
                    return json.loads(prompt[end_node]["is_changed"][0])
                except:
                    print("comfyUI SDPromptReader error")
            case "SDParameterGenerator":
                try:
                    return inputs
                except:
                    print("comfyUI SDParameterGenerator error")
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
                    elif inputs.get("image") and isinstance(inputs.get("image"), list):
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
