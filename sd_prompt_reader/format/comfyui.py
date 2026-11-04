__author__ = "receyuki"
__filename__ = "comfyui.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json

from ..format.base_format import BaseFormat
from ..utility import remove_quotes, merge_dict


class ComfyUI(BaseFormat):
    # comfyui node types
    KSAMPLER_TYPES = ["KSampler", "KSamplerAdvanced", "KSampler (Efficient)"]
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
        self._prompt = ""
        self._workflow = ""
        self._active_nodes = set()
        self._traversal_count = 0

    def parse(self):
        try:
            self._process()
        except Exception:
            self._warn("Malformed or unsupported ComfyUI metadata.")
            self._status = self.Status.COMFYUI_ERROR
            return self._status
        else:
            self._status = (
                self.Status.COMFYUI_ERROR
                if self._parse_warnings
                else self.Status.READ_SUCCESS
            )
            return self._status

    def _warn(self, reason):
        if reason not in self._parse_warnings:
            self._parse_warnings += (reason,)

    def _process(self):
        self._comfy_png()

    def _comfy_png(self):
        self._prompt = self._info.get("prompt", "")
        self._workflow = self._info.get("workflow", "")
        self._raw = "\n".join(
            value
            for value in (self._prompt, self._workflow)
            if isinstance(value, str) and value
        )
        if not self._prompt:
            self._warn(
                "API prompt metadata is missing; workflow is available only as raw data."
            )
            return
        prompt_json = json.loads(self._prompt)

        # find end node of each flow
        end_nodes = list(
            filter(
                lambda item: isinstance(item[-1], dict)
                and item[-1].get("class_type")
                in ["SaveImage"] + ComfyUI.KSAMPLER_TYPES,
                prompt_json.items(),
            )
        )
        longest_flow = {}
        longest_flow_len = 0
        selected = None

        # traverse each flow from the end
        for end_node in end_nodes:
            self._positive = self._negative = ""
            self._positive_sdxl, self._negative_sdxl = {}, {}
            self._is_sdxl = False
            self._parse_warnings = ()
            self._traversal_count = 0
            self._seen_sampler = False
            flow, nodes = self._comfy_traverse(prompt_json, str(end_node[0]))
            if len(nodes) > longest_flow_len:
                longest_flow = flow
                longest_flow_len = len(nodes)
                selected = (
                    self._positive,
                    self._negative,
                    self._positive_sdxl,
                    self._negative_sdxl,
                    self._is_sdxl,
                    self._parse_warnings,
                    self._seen_sampler,
                )
        if selected is not None:
            (
                self._positive,
                self._negative,
                self._positive_sdxl,
                self._negative_sdxl,
                self._is_sdxl,
                self._parse_warnings,
                self._seen_sampler,
            ) = selected
        if selected is None or not self._seen_sampler:
            self._warn("No supported sampler found in the selected flow.")
            return

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
        self._raw += "\n" + str(self._prompt)
        if self._workflow:
            self._raw += "\n" + str(self._workflow)

        for key in ("ckpt_name", "sampler_name", "seed", "noise_seed", "cfg", "steps"):
            if key in longest_flow:
                value = longest_flow[key]
                values = value if isinstance(value, tuple) else (value,)
                if not values or not all(
                    type(item) in (str, int, float) for item in values
                ):
                    longest_flow[key] = None
                    self._warn("Malformed or unresolved supported parameter.")

        add_noise = (
            f"Add noise: {remove_quotes(longest_flow.get('add_noise'))}"
            if longest_flow.get("add_noise")
            else ""
        )

        seed = (
            f"Seed: {longest_flow.get('seed')}"
            if "seed" in longest_flow
            else f"Noise seed: {longest_flow.get('noise_seed')}"
        )

        start_at_step = (
            f"Start at step: {longest_flow.get('start_at_step')}"
            if "start_at_step" in longest_flow
            else ""
        )

        end_at_step = (
            f"End at step: {longest_flow.get('end_at_step')}"
            if "end_at_step" in longest_flow
            else ""
        )

        return_with_left_over_noise = (
            f"Return with left over noise: {longest_flow.get('return_with_left_over_noise')}"
            if longest_flow.get("return_with_left_over_noise")
            else ""
        )

        denoise = (
            f"Denoise: {longest_flow.get('denoise')}"
            if "denoise" in longest_flow
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
                        if "seed" in longest_flow
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
        if "Clip G" not in data and "Clip L" not in data:
            return data.get("Refiner", "").strip(" ,")
        clip_g = data.get("Clip G", "").strip(" ,")
        clip_l = data.get("Clip L", "").strip(" ,")
        if "Clip G" not in data:
            return clip_l
        if "Clip L" not in data:
            return clip_g

        if clip_g == clip_l:
            return clip_g
        else:
            return ",\n".join([clip_g, clip_l])

    def _text(self, prompt, value):
        if isinstance(value, str):
            return value
        source = self._reference(prompt, value)
        if source is None:
            return
        node = prompt[source]
        kind, slot = node.get("class_type"), value[1]
        text = None
        if kind == "SDXLPromptStyler":
            text = node["inputs"].get("text_positive" if slot == 0 else "text_negative")
        elif kind == "SDPromptReader" and slot in (2, 3):
            try:
                props = json.loads(node["is_changed"][0])
                text = props.get("positive" if slot == 2 else "negative")
            except (KeyError, IndexError, TypeError, ValueError):
                pass
        if isinstance(text, str):
            return text
        self._warn("Unsupported or malformed required text source.")

    def _reference(self, prompt, reference):
        if (
            not isinstance(reference, list)
            or len(reference) != 2
            or type(reference[0]) not in (str, int)
            or type(reference[1]) is not int
            or reference[1] < 0
        ):
            self._warn("Invalid required node reference.")
            return None
        node_id, slot = str(reference[0]), reference[1]
        source = prompt.get(node_id)
        if not isinstance(source, dict) or not isinstance(source.get("inputs"), dict):
            self._warn("Missing or malformed required node.")
            return None
        kind = source.get("class_type")
        if not isinstance(kind, str):
            self._warn("Missing or malformed required node.")
            return None
        output_counts = {
            "CheckpointLoader": 3,
            "CheckpointLoaderSimple": 3,
            **dict.fromkeys(["KSampler", "KSamplerAdvanced"] + self.VAE_ENCODE_TYPE, 1),
            "VAEDecode": 1,
            "EmptyLatentImage": 1,
            "LoraLoader": 2,
            "LoadImage": 2,
            "ImageScale": 1,
            "ImageUpscaleWithModel": 1,
            "UpscaleModelLoader": 1,
            **dict.fromkeys(self.CLIP_TEXT_ENCODE_TYPE, 1),
            "ConditioningCombine": 1,
            "ConditioningConcat": 1,
            "ControlNetApplyAdvanced": 2,
            "SDXLPromptStyler": 2,
            "SDPromptReader": 12,
            "SDParameterGenerator": 17,
            "CR Seed": 1,
        }
        if slot >= output_counts.get(kind, slot + 1):
            self._warn("Invalid required node output slot.")
            return None
        return node_id

    def _comfy_link(self, prompt, reference, model=False):
        source = self._reference(prompt, reference)
        if source is None:
            return {}, []
        kind = prompt[source].get("class_type")
        if model and (
            (kind in self.CHECKPOINT_LOADER_TYPE + ["LoraLoader"] and reference[1] != 0)
            or kind
            in (
                self.CLIP_TEXT_ENCODE_TYPE
                + self.VAE_ENCODE_TYPE
                + [
                    "KSampler",
                    "KSamplerAdvanced",
                    "VAEDecode",
                    "EmptyLatentImage",
                    "LoadImage",
                    "ImageScale",
                    "ImageUpscaleWithModel",
                    "UpscaleModelLoader",
                    "LatentUpscale",
                    "LatentUpscaleBy",
                    "ConditioningCombine",
                    "ConditioningConcat",
                    "ControlNetApplyAdvanced",
                ]
            )
        ):
            self._warn("Invalid required model source or output slot.")
            return {}, []
        return self._comfy_traverse(prompt, source, reference[1])

    def _comfy_traverse(self, prompt, end_node, output_slot=0):
        end_node = str(end_node)
        if end_node in self._active_nodes:
            self._warn("Cycle detected in required node path.")
            return {}, []
        if len(self._active_nodes) >= 64 or self._traversal_count >= 2048:
            self._warn("Required node traversal limit reached.")
            return {}, []
        self._traversal_count += 1
        self._active_nodes.add(end_node)
        try:
            return self._comfy_node(prompt, end_node, output_slot)
        finally:
            self._active_nodes.remove(end_node)

    def _comfy_node(self, prompt, end_node, output_slot=0):
        flow = {}
        node = [end_node]
        inputs = {}
        try:
            inputs = prompt[end_node]["inputs"]
        except:
            self._warn("Malformed or unsupported required node.")
            return flow, node
        match prompt[end_node]["class_type"]:
            case node_type if node_type in ComfyUI.SAVE_IMAGE_TYPE:
                try:
                    last_flow, last_node = self._comfy_link(prompt, inputs["images"])
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    self._warn("Malformed or unsupported required node.")
            case node_type if node_type in ComfyUI.KSAMPLER_TYPES:
                self._seen_sampler = True
                required = {
                    "positive",
                    "negative",
                    "model",
                    "latent_image",
                    "steps",
                    "cfg",
                    "sampler_name",
                }
                if not required.issubset(inputs) or not (
                    {"seed", "noise_seed"} & inputs.keys()
                ):
                    self._warn("Missing required sampler input.")
                try:
                    seed = None
                    flow = inputs.copy()
                    last_flow1, last_node1, last_flow2, last_node2 = {}, [], {}, []
                    for key, value in inputs.items():
                        match key:
                            case "model":
                                traverse_result = self._comfy_link(
                                    prompt, value, model=True
                                )
                                if isinstance(traverse_result, tuple):
                                    last_flow1, last_node1 = traverse_result
                                elif isinstance(traverse_result, dict):
                                    flow.update({key: traverse_result.get("ckpt_name")})
                            case "latent_image":
                                last_flow2, last_node2 = self._comfy_link(prompt, value)
                            case "positive":
                                source = self._reference(prompt, value)
                                if source is None:
                                    continue
                                positive = self._comfy_link(prompt, value)
                                if isinstance(positive, str):
                                    self._positive = positive
                                elif isinstance(positive, dict):
                                    if positive_prompt := positive.get("positive"):
                                        self._positive = positive_prompt
                                    else:
                                        self._positive_sdxl.update(positive)
                                elif prompt.get(str(value[0]), {}).get(
                                    "class_type"
                                ) not in (
                                    self.CLIP_TEXT_ENCODE_TYPE
                                    + ["ControlNetApplyAdvanced"]
                                ):
                                    self._warn(
                                        "Unsupported required conditioning source."
                                    )
                            case "negative":
                                source = self._reference(prompt, value)
                                if source is None:
                                    continue
                                negative = self._comfy_link(prompt, value)
                                if isinstance(negative, str):
                                    self._negative = negative
                                elif isinstance(negative, dict):
                                    if negative_prompt := negative.get("negative"):
                                        self._negative = negative_prompt
                                    else:
                                        self._negative_sdxl.update(negative)
                                elif prompt.get(str(value[0]), {}).get(
                                    "class_type"
                                ) not in (
                                    self.CLIP_TEXT_ENCODE_TYPE
                                    + ["ControlNetApplyAdvanced"]
                                ):
                                    self._warn(
                                        "Unsupported required conditioning source."
                                    )
                            case key_name if key_name in ("seed", "noise_seed"):
                                # handle "CR Seed"
                                if isinstance(value, list):
                                    traverse_result = self._comfy_link(prompt, value)
                                    if isinstance(traverse_result, dict):
                                        seed = {key_name: traverse_result.get("seed")}
                                    else:
                                        seed = {key_name: traverse_result}
                                if seed:
                                    flow.update(seed)
                            case _ as key_name:
                                if isinstance(value, list):
                                    traverse_result = self._comfy_link(prompt, value)
                                    if isinstance(traverse_result, dict):
                                        flow.update(
                                            {key_name: traverse_result.get(key_name)}
                                        )

                    flow = merge_dict(flow, last_flow1)
                    flow = merge_dict(flow, last_flow2)
                    node += last_node1 + last_node2
                except:
                    self._warn("Malformed or unsupported required node.")
            case node_type if node_type in ComfyUI.CLIP_TEXT_ENCODE_TYPE:
                if node_type == "CLIPTextEncode":
                    return self._text(prompt, inputs.get("text"))
                self._is_sdxl = True
                channels = (
                    {"Clip G": "text_g", "Clip L": "text_l"}
                    if node_type == "CLIPTextEncodeSDXL"
                    else {"Refiner": "text"}
                )
                result = {
                    key: self._text(prompt, inputs.get(value))
                    for key, value in channels.items()
                }
                return {
                    key: value
                    for key, value in result.items()
                    if isinstance(value, str)
                }
            case "LoraLoader":
                try:
                    flow = inputs.copy()
                    last_flow, last_node = self._comfy_link(
                        prompt, inputs["model"], model=True
                    )
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    self._warn("Malformed or unsupported required node.")
            case node_type if node_type in ComfyUI.CHECKPOINT_LOADER_TYPE:
                try:
                    return inputs, node
                except:
                    self._warn("Malformed or unsupported required node.")
            case node_type if node_type in ComfyUI.VAE_ENCODE_TYPE:
                try:
                    last_flow, last_node = self._comfy_link(prompt, inputs["pixels"])
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    self._warn("Malformed or unsupported required node.")
            case "ControlNetApplyAdvanced":
                try:
                    self._comfy_link(prompt, inputs["image"])
                    conditioning = self._comfy_link(
                        prompt, inputs["positive" if output_slot == 0 else "negative"]
                    )
                    if isinstance(conditioning, (str, dict)):
                        return conditioning
                    self._warn("Unsupported required conditioning source.")
                except:
                    self._warn("Malformed or unsupported required node.")
            case "ImageScale":
                try:
                    flow = inputs.copy()
                    last_flow, last_node = self._comfy_link(prompt, inputs["image"])
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    self._warn("Malformed or unsupported required node.")
            case "UpscaleModelLoader":
                try:
                    return {"upscaler": inputs["model_name"]}
                except:
                    self._warn("Malformed or unsupported required node.")
            case "ImageUpscaleWithModel":
                try:
                    flow = inputs.copy()
                    last_flow, last_node = self._comfy_link(prompt, inputs["image"])
                    model = self._comfy_link(prompt, inputs["upscale_model"])
                    flow = merge_dict(flow, last_flow)
                    flow = merge_dict(flow, model)
                    node += last_node
                except:
                    self._warn("Malformed or unsupported required node.")
            case "ConditioningCombine" | "ConditioningConcat":
                keys = (
                    ("conditioning_1", "conditioning_2")
                    if prompt[end_node]["class_type"] == "ConditioningCombine"
                    else ("conditioning_to", "conditioning_from")
                )
                sources = [self._reference(prompt, inputs.get(key)) for key in keys]
                if any(
                    source is None
                    or prompt[source].get("class_type")
                    not in self.CLIP_TEXT_ENCODE_TYPE
                    for source in sources
                ):
                    self._warn("Nested or unsupported conditioning operation.")
                    return
                first = self._comfy_traverse(prompt, sources[0])
                second = self._comfy_traverse(prompt, sources[1])
                if isinstance(first, str) and isinstance(second, str):
                    return "\n".join([first, second])
                if isinstance(first, dict) and isinstance(second, dict):
                    if first.keys() != second.keys():
                        self._warn("Unsupported or unresolved conditioning channels.")
                    return {
                        key: "\n".join([first[key], second[key]])
                        for key in first
                        if key in second
                    }
                self._warn("Unsupported or unresolved conditioning channels.")
                return
            # SD Prompt Reader Node
            case "SDPromptReader":
                try:
                    return json.loads(prompt[end_node]["is_changed"][0])
                except:
                    self._warn("Malformed or unsupported required node.")
            case "SDParameterGenerator":
                try:
                    return inputs
                except:
                    self._warn("Malformed or unsupported required node.")
            # custom nodes
            case "SDXLPromptStyler":
                try:
                    return inputs.get("text_positive"), inputs.get("text_negative")
                except:
                    self._warn("Malformed or unsupported required node.")
            case "CR Seed":
                try:
                    return inputs.get("seed")
                except:
                    self._warn("Malformed or unsupported required node.")
            case _:
                if prompt[end_node]["class_type"] not in (
                    "EmptyLatentImage",
                    "LoadImage",
                    "VAEDecode",
                    "LatentUpscaleBy",
                    "LatentUpscale",
                    "FaceDetailer",
                    "UltimateSDUpscale",
                    "CR Apply LoRA Stack",
                    "MiDaS-DepthMapPreprocessor",
                ):
                    self._warn("Unsupported required node source.")
                try:
                    last_flow = {}
                    last_node = []
                    if inputs.get("samples"):
                        last_flow, last_node = self._comfy_link(
                            prompt, inputs["samples"]
                        )
                    elif inputs.get("image") and isinstance(inputs.get("image"), list):
                        last_flow, last_node = self._comfy_link(prompt, inputs["image"])
                    elif inputs.get("model"):
                        last_flow, last_node = self._comfy_link(prompt, inputs["model"])
                    elif inputs.get("clip"):
                        last_flow, last_node = self._comfy_link(prompt, inputs["clip"])
                    elif inputs.get("samples_from"):
                        last_flow, last_node = self._comfy_link(
                            prompt, inputs["samples_from"]
                        )
                    elif inputs.get("conditioning"):
                        result = self._comfy_link(prompt, inputs["conditioning"])
                        if isinstance(result, str):
                            return result
                        elif isinstance(result, list):
                            last_flow, last_node = result
                    flow = merge_dict(flow, last_flow)
                    node += last_node
                except:
                    self._warn("Malformed or unsupported required node.")
        return flow, node
