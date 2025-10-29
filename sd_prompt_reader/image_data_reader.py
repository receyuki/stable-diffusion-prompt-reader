# HYPOTHETICAL MODIFIED version of 
# receyuki/stable-diffusion-prompt-reader/sd_prompt_reader/image_data_reader.py
# showing integration of a new CivitaiComfyUIFormat parser.
# ALL original methods and properties are included in this version.

__author__ = "receyuki"
__filename__ = "image_data_reader.py" # (Hypothetically Modified)
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
    # --- HYPOTHETICAL ADDITION: Import your new parser ---
    CivitaiComfyUIFormat, # Assuming this would be added to format/__init__.py and assuming it's a class i can import?)
    # --- For direct import if not in __init__.py during development:
    # from .format.civitai import CivitaiComfyUIFormat 
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
            if self._parser: self._tool = getattr(self._parser, 'tool', "A1111 webUI (txt)")
            # According to their original code, this path returns early.
            return 

        with Image.open(file) as f:
            self._width = f.width
            self._height = f.height
            self._info = f.info 
            self._format = f.format 
            self._parser = None 

            # --- SwarmUI Legacy EXIF (ModelID 0x0110) ---
            try:
                exif_model_json_str = f.getexif().get(0x0110)
                if exif_model_json_str:
                    exif_data = json.loads(exif_model_json_str)
                    if "sui_image_params" in exif_data:
                        self._tool = "StableSwarmUI"
                        self._parser = SwarmUI(info=exif_data)
            except (TypeError, AttributeError, json.JSONDecodeError, ValueError):
                pass

            # --- PNG Processing ---
            if not self._parser and f.format == "PNG":
                if "parameters" in self._info:
                    parameters_str = self._info.get("parameters", "")
                    if "sui_image_params" in parameters_str:
                        self._tool = "StableSwarmUI"; self._parser = SwarmUI(raw=parameters_str)
                    else:
                        self._tool = "A1111 webUI" if "prompt" not in self._info else "ComfyUI\n(A1111 compatible)"
                        self._parser = A1111(info=self._info) 
                elif "postprocessing" in self._info:
                    self._tool = "A1111 webUI\n(Postprocessing)"; self._parser = A1111(info=self._info)
                elif ("negative_prompt" in self._info or "Negative Prompt" in self._info):
                    self._tool = "Easy Diffusion"; self._parser = EasyDiffusion(info=self._info)
                elif "invokeai_metadata" in self._info:
                    self._tool = "InvokeAI"; self._parser = InvokeAI(info=self._info)
                elif "sd-metadata" in self._info:
                    self._tool = "InvokeAI"; self._parser = InvokeAI(info=self._info)
                elif "Dream" in self._info: # invokeai legacy dream format
                    self._tool = "InvokeAI"; self._parser = InvokeAI(info=self._info)
                elif self._info.get("Software") == "NovelAI":
                    self._tool = "NovelAI"; self._parser = NovelAI(info=self._info, width=self._width, height=self._height)
                elif "prompt" in self._info: # Standard ComfyUI PNG (workflow in 'prompt' key)
                    self._tool = "ComfyUI"; self._parser = ComfyUI(info=self._info, width=self._width, height=self._height)
                elif "Comment" in self._info: # Fooocus PNG
                    try:
                        self._tool = "Fooocus"; self._parser = Fooocus(info=json.loads(self._info.get("Comment")))
                    except Exception: self._logger.warn("Fooocus PNG format error")
                elif "XML:com.adobe.xmp" in self._info: # DrawThings
                    try:
                        data = minidom.parseString(self._info.get("XML:com.adobe.xmp"))
                        data_json = json.loads(data.getElementsByTagName("exif:UserComment")[0].childNodes[1].childNodes[1].childNodes[0].data)
                        self._tool = "Draw Things"; self._parser = DrawThings(info=data_json)
                    except Exception: self._logger.warn("Draw things format error"); self._status = BaseFormat.Status.FORMAT_ERROR
                elif f.mode == "RGBA": # NovelAI Stealth PNG
                    try:
                        reader = NovelAI.LSBExtractor(f)
                        read_magic = reader.get_next_n_bytes(len(self.NOVELAI_MAGIC)).decode("utf-8")
                        assert self.NOVELAI_MAGIC == read_magic, "NovelAI stealth png info magic number error"
                        self._tool = "NovelAI"; self._parser = NovelAI(extractor=reader)
                    except Exception as e: self._logger.warn(e); self._status = BaseFormat.Status.FORMAT_ERROR


            # --- JPEG/WEBP Processing ---
            elif not self._parser and f.format in ["JPEG", "WEBP"]:
                raw_user_comment_from_piexif = None
                exif_dict_piexif = {} 
                software_tag_str = ""

                exif_bytes = self._info.get("exif")
                if exif_bytes:
                    try:
                        exif_dict_piexif = piexif.load(exif_bytes)
                        user_comment_bytes = exif_dict_piexif.get("Exif", {}).get(piexif.ExifIFD.UserComment)
                        if user_comment_bytes:
                            raw_user_comment_from_piexif = piexif.helper.UserComment.load(user_comment_bytes)
                            self._logger.info(f"piexif decoded UserComment (first 100): {raw_user_comment_from_piexif[:100] if raw_user_comment_from_piexif else 'None'}")
                        software_tag_bytes = exif_dict_piexif.get("0th", {}).get(piexif.ImageIFD.Software)
                        if software_tag_bytes:
                            software_tag_str = software_tag_bytes.decode('ascii', 'ignore').strip()
                            self._logger.info(f"Software Tag: {software_tag_str}")
                    except Exception as e_piexif:
                        self._logger.warn(f"piexif error processing EXIF: {e_piexif}")
                
                # --- START OF HYPOTHETICAL CIVITAI COMFYUI PARSER INTEGRATION ---
                if raw_user_comment_from_piexif and not self._parser:
                    is_potential_civitai = False
                    # Heuristic 1: Check Civitai's known Software tag value
                    if software_tag_str == "4c6047c3-8b1c-4058-8888-fd48353bf47d": 
                        is_potential_civitai = True
                        self._logger.info("Civitai software tag detected.")
                    # Heuristic 2: Content of UserComment if software tag is not definitive
                    elif "charset=Unicode" in raw_user_comment_from_piexif:
                        temp_data_after_prefix = raw_user_comment_from_piexif.split("charset=Unicode", 1)[-1].strip()
                        if (temp_data_after_prefix.startswith('笀∀爀攀猀漀甀爀挀攀') or \
                            temp_data_after_prefix.startswith('{"resource-stack":')) and \
                           '"extraMetadata":' in temp_data_after_prefix:
                            is_potential_civitai = True
                            self._logger.info("Civitai UserComment content pattern detected (mojibake or clean JSON).")
                    elif raw_user_comment_from_piexif.startswith('{"resource-stack":') and \
                         '"extraMetadata":' in raw_user_comment_from_piexif:
                         is_potential_civitai = True # piexif might fully clean it
                         self._logger.info("Civitai UserComment clean JSON content pattern detected.")

                    if is_potential_civitai:
                        self._logger.info("Attempting CivitaiComfyUIFormat parser.")
                        from .format import CivitaiComfyUIFormat # Ensure this import works in their structure
                        
                        temp_civitai_parser = CivitaiComfyUIFormat(raw=raw_user_comment_from_piexif)
                        temp_status = temp_civitai_parser.parse() 
                        if temp_status == BaseFormat.Status.READ_SUCCESS:
                            self._tool = getattr(temp_civitai_parser, 'tool_name', "Civitai ComfyUI") # Parser should define its tool name
                            self._parser = temp_civitai_parser
                            self._logger.info(f"Successfully parsed as {self._tool}.")
                        else:
                            self._logger.warn(f"CivitaiComfyUIFormat parsing failed. Error: {getattr(temp_civitai_parser, '_error', 'N/A')}. Falling back.")
                # --- END OF HYPOTHETICAL CIVITAI COMFYUI PARSER INTEGRATION ---

                if not self._parser: # If Civitai parser didn't claim it or failed
                    # Fooocus (checks self._info.get("comment") - different from UserComment)
                    if "comment" in self._info and not self._parser:
                        try:
                            fooocus_comment_data = json.loads(self._info.get("comment"))
                            self._tool = "Fooocus"
                            self._parser = Fooocus(info=fooocus_comment_data)
                        except: self._logger.warn("Fooocus (JPEG/comment) format error")
                    
                    # Standard UserComment fallbacks if still no parser and we have a UserComment
                    if not self._parser and raw_user_comment_from_piexif:
                        self._raw = raw_user_comment_from_piexif 
                        if "sui_image_params" in raw_user_comment_from_piexif: # SwarmUI in UserComment
                             self._tool = "StableSwarmUI"
                             self._parser = SwarmUI(raw=raw_user_comment_from_piexif)
                        elif raw_user_comment_from_piexif.strip().startswith("{"): # Easy Diffusion JSON
                            self._tool = "Easy Diffusion"
                            self._parser = EasyDiffusion(raw=raw_user_comment_from_piexif)
                        else: # A1111 text block
                            self._tool = "A1111 webUI"
                            self._parser = A1111(raw=raw_user_comment_from_piexif)
                
                # NovelAI LSB in RGBA JPEGs/WebPs
                if not self._parser and f.mode == "RGBA":
                    try:
                        reader = NovelAI.LSBExtractor(f)
                        read_magic = reader.get_next_n_bytes(len(self.NOVELAI_MAGIC)).decode("utf-8")
                        assert self.NOVELAI_MAGIC == read_magic, "NovelAI stealth LSB magic error"
                        self._tool = "NovelAI"; self._parser = NovelAI(extractor=reader)
                    except Exception as e_lsb: self._logger.warn(f"NovelAI LSB error: {e_lsb}")

            # --- FINAL PARSE CALL ---
            if self._parser and self._status == BaseFormat.Status.UNREAD:
                self._logger.info(f"Format determined: {self._tool if self._tool else 'Unknown'}. Parsing...")
                self._status = self._parser.parse()
            elif not self._parser and not self._is_txt and self._status == BaseFormat.Status.UNREAD:
                 self._logger.warn("Could not determine image format or no parser assigned for image file.")
                 self._status = BaseFormat.Status.FORMAT_ERROR
            
            self._logger.info(f"Reading Status: {self._status.name if hasattr(self._status, 'name') else self._status}")

    # --- Original staticmethods and properties ---
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
                                        data, encoding="unicode" # piexif "unicode" means UTF-16LE + prefix
                                    )
                                )
                            },
                        }
                    )
        with Image.open(image_path) as f:
            try:
                match image_format.upper():
                    case "PNG":
                        if data: f.save(new_path, pnginfo=metadata)
                        else: f.save(new_path)
                    case "JPEG" | "JPG":
                        f.save(new_path, quality="keep") # Preserves original quality
                        if data: piexif.insert(metadata, str(new_path))
                    case "WEBP":
                        f.save(new_path, quality=100, lossless=True)
                        if data: piexif.insert(metadata, str(new_path))
            except Exception as e_save:
                # Using f-string for better error message
                Logger("SD_Prompt_Reader.ImageDataReader").error(f"Save error: {e_save}")


    @staticmethod
    def construct_data(positive, negative, setting):
        return "\n".join(filter(None, [
            f"{positive}" if positive else "",
            f"Negative prompt: {negative}" if negative else "",
            f"{setting}" if setting else "",
        ]))

    def prompt_to_line(self):
        return self._parser.prompt_to_line() if self._parser else ""

    # Properties (added hasattr for safety, good practice)
    @property
    def height(self): return self._parser.height if self._parser and hasattr(self._parser, 'height') else self._height
    @property
    def width(self): return self._parser.width if self._parser and hasattr(self._parser, 'width') else self._width
    @property
    def info(self): return self._info
    @property
    def positive(self): return self._parser.positive if self._parser and hasattr(self._parser, 'positive') else self._positive
    @property
    def negative(self): return self._parser.negative if self._parser and hasattr(self._parser, 'negative') else self._negative
    @property
    def positive_sdxl(self): return self._parser.positive_sdxl if self._parser and hasattr(self._parser, 'positive_sdxl') else self._positive_sdxl
    @property
    def negative_sdxl(self): return self._parser.negative_sdxl if self._parser and hasattr(self._parser, 'negative_sdxl') else self._negative_sdxl
    @property
    def setting(self): return self._parser.setting if self._parser and hasattr(self._parser, 'setting') else self._setting
    @property
    def raw(self): return self._parser.raw if self._parser and hasattr(self._parser, 'raw') else self._raw
    @property
    def tool(self): return self._parser.tool if self._parser and hasattr(self._parser, 'tool') else self._tool # Let parser define tool name
    @property
    def parameter(self): return self._parser.parameter if self._parser and hasattr(self._parser, 'parameter') else self._parameter
    @property
    def format(self): return self._format
    @property
    def is_sdxl(self): return self._parser.is_sdxl if self._parser and hasattr(self._parser, 'is_sdxl') else self._is_sdxl
    @property
    def props(self): return self._parser.props if self._parser and hasattr(self._parser, 'props') else self._props
    @property
    def status(self): return self._status
