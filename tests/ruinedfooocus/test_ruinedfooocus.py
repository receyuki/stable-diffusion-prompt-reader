import json
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from sd_prompt_reader.format import BaseFormat, RuinedFooocus
from sd_prompt_reader.image_data_reader import ImageDataReader


SAMPLE = Path(__file__).with_name("issue77.png")


@pytest.fixture
def metadata():
    with Image.open(SAMPLE) as image:
        return json.loads(image.info["parameters"])


def read_parameters(parameters):
    info = PngInfo()
    info.add_text("parameters", parameters)
    stream = BytesIO()
    Image.new("RGB", (32, 24)).save(stream, format="PNG", pnginfo=info)
    stream.seek(0)
    return ImageDataReader(stream)


def test_issue77_original_image(metadata):
    reader = ImageDataReader(SAMPLE)

    assert reader.status == BaseFormat.Status.READ_SUCCESS
    assert reader.tool == "Ruined Fooocus"
    assert reader.format == "PNG"
    assert (reader.width, reader.height) == ("1216", "832")
    assert reader.positive == metadata["Prompt"]
    assert reader.negative == metadata["Negative"]
    assert reader.parameter == {
        "model": "sd_xl\\ultimate42_xl_final_v13.safetensors",
        "sampler": "euler",
        "seed": "2747884721",
        "cfg": "1",
        "steps": "9",
        "size": "1216x832",
    }
    assert reader.info["parameters"] == json.dumps(metadata)
    assert metadata["Prompt"] in reader.raw
    assert metadata["Negative"] in reader.raw
    assert repr(metadata["loras"]) in reader.raw
    assert "scheduler: sgm_uniform" in reader.setting
    assert "base_model_hash: 09920788" in reader.setting
    assert "Prompt:" not in reader.setting
    assert "Negative:" not in reader.setting
    assert json.loads(reader.props)["seed"] == "2747884721"


def test_a1111_prompt_mentioning_ruinedfooocus_is_not_misidentified():
    reader = read_parameters(
        "RuinedFooocus logo\nNegative prompt: blurry\n"
        "Steps: 9, Sampler: Euler, CFG scale: 1, Seed: 0, Size: 32x24"
    )

    assert reader.tool == "A1111 webUI"
    assert reader.status == BaseFormat.Status.READ_SUCCESS
    assert reader.positive == "RuinedFooocus logo"


@pytest.mark.parametrize("negative", [None, ""])
def test_empty_negative_prompt(metadata, negative):
    metadata["Negative"] = negative
    reader = read_parameters(json.dumps(metadata))

    assert reader.status == BaseFormat.Status.READ_SUCCESS
    assert reader.positive == metadata["Prompt"]
    assert reader.negative == ""


def test_missing_optional_fields_and_dimensions(metadata):
    reader = read_parameters(
        json.dumps({"software": "RuinedFooocus", "Prompt": metadata["Prompt"]})
    )

    assert reader.status == BaseFormat.Status.READ_SUCCESS
    assert reader.negative == ""
    assert (reader.width, reader.height) == ("32", "24")
    assert reader.parameter == {
        "model": "",
        "sampler": "",
        "seed": "",
        "cfg": "",
        "steps": "",
        "size": "32x24",
    }


def test_null_optional_fields_and_zero_values(metadata):
    metadata.update(base_model_name=None, width=None, height=None, seed=0, cfg=0)
    reader = read_parameters(json.dumps(metadata))

    assert reader.status == BaseFormat.Status.READ_SUCCESS
    assert reader.parameter["model"] == ""
    assert reader.parameter["seed"] == "0"
    assert reader.parameter["cfg"] == "0"
    assert reader.parameter["size"] == "32x24"


@pytest.mark.parametrize("value", [None, 42, ["prompt"]])
def test_invalid_prompt_returns_format_error(metadata, value):
    metadata["Prompt"] = value
    raw = json.dumps(metadata)
    reader = read_parameters(raw)

    assert reader.status == BaseFormat.Status.FORMAT_ERROR
    assert reader.raw == raw


def test_missing_prompt_returns_format_error(metadata):
    del metadata["Prompt"]
    raw = json.dumps(metadata)
    reader = read_parameters(raw)

    assert reader.status == BaseFormat.Status.FORMAT_ERROR
    assert reader.raw == raw


def test_invalid_negative_prompt_returns_format_error(metadata):
    metadata["Negative"] = ["blurry"]
    raw = json.dumps(metadata)
    reader = read_parameters(raw)

    assert reader.status == BaseFormat.Status.FORMAT_ERROR
    assert reader.raw == raw


@pytest.mark.parametrize("software", [None, "OtherTool"])
def test_software_field_is_required_for_detection(metadata, software):
    metadata["Prompt"] = "RuinedFooocus logo"
    metadata["software"] = software

    assert read_parameters(json.dumps(metadata)).tool == "A1111 webUI"


@pytest.mark.parametrize("raw", ['{"software": "RuinedFooocus",', "[]", "null"])
def test_invalid_json_payload_returns_format_error(raw):
    parser = RuinedFooocus(raw=raw)

    assert parser.parse() == BaseFormat.Status.FORMAT_ERROR
    assert parser.raw == raw
