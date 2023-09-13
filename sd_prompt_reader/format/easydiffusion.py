__author__ = "receyuki"
__filename__ = "easydiffusion.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import json
from pathlib import PureWindowsPath, PurePosixPath

from ..format.base_format import BaseFormat
from ..utility import remove_quotes

# easy diffusion mapping table
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


class EasyDiffusion(BaseFormat):
    def __init__(self, info: dict = None, raw: str = ""):
        super().__init__(info, raw)
        if not self._raw:
            self._raw = str(self._info).replace("'", '"')
        self._ed_format()

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
        if PureWindowsPath(data.get(ed["use_stable_diffusion_model"])).drive:
            file = PureWindowsPath(data.get(ed["use_stable_diffusion_model"])).name
        else:
            file = PurePosixPath(data.get(ed["use_stable_diffusion_model"])).name

        self._setting = remove_quotes(data).replace("{", "").replace("}", "")
        self._parameter["model"] = file
        self._parameter["sampler"] = data.get(ed["sampler_name"])
        self._parameter["seed"] = data.get(ed["seed"])
        self._parameter["cfg"] = data.get(ed["guidance_scale"])
        self._parameter["steps"] = data.get(ed["num_inference_steps"])
        self._parameter["size"] = (
            str(data.get(ed["width"])) + "x" + str(data.get(ed["height"]))
        )
