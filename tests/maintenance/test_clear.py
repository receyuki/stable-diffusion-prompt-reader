from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from sd_prompt_reader.image_data_reader import ImageDataReader
from sd_prompt_reader.app import App

ROOT = Path(__file__).resolve().parents[2]


def test_save_failure_propagates(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (16, 16)).save(source)
    with pytest.raises(OSError):
        ImageDataReader.save_image(source, tmp_path / "missing" / "out.png", "PNG")


def test_clear_stealth(tmp_path):
    source = ROOT / "tests/novelai/stealth1.png"
    if not source.exists():
        pytest.skip("Local legacy NovelAI fixture unavailable")
    dest = tmp_path / "clear.png"
    ImageDataReader.save_image(source, dest, "PNG")
    result = ImageDataReader(dest)
    assert not result.positive
    with Image.open(source) as before, Image.open(dest) as after:
        assert before.convert("RGB").tobytes() == after.convert("RGB").tobytes()
        assert (
            max(
                abs(a - b)
                for a, b in zip(
                    before.getchannel("A").getdata(), after.getchannel("A").getdata()
                )
            )
            <= 1
        )


def test_clear_normal_rgba_preserves_pixels(tmp_path):
    source = tmp_path / "source.png"
    info = PngInfo()
    info.add_text("parameters", "example")
    Image.new("RGBA", (32, 32), (1, 2, 3, 127)).save(source, pnginfo=info)
    ImageDataReader.save_image(source, source, "PNG")
    with Image.open(source) as result:
        assert "parameters" not in result.info
        assert result.getpixel((0, 0)) == (1, 2, 3, 127)


def test_gui_clear_failure_does_not_report_success(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (16, 16)).save(source)
    reader = Mock(format="PNG")
    reader.save_image.side_effect = OSError("read-only destination")
    app = SimpleNamespace(file_path=source, image_data=reader, status_bar=Mock())
    App.remove_data(app)
    app.status_bar.success.assert_not_called()
    app.status_bar.warning.assert_called_once()


def test_no_metadata_raw_is_empty(tmp_path):
    path = tmp_path / "empty.png"
    Image.new("RGB", (16, 16)).save(path)
    reader = ImageDataReader(path)
    assert reader.status.name == "UNREAD"
    assert reader.raw == ""


def test_drawthings_preserves_input_metadata():
    from sd_prompt_reader.format import DrawThings

    data = {"c": "positive", "uc": "negative", "size": "32x24"}
    parser = DrawThings(info=data)
    assert parser.parse().name == "READ_SUCCESS"
    assert data == {"c": "positive", "uc": "negative", "size": "32x24"}
    assert "'c': 'positive'" in parser.raw
    assert "'uc': 'negative'" in parser.raw


@pytest.mark.parametrize("fmt,suffix", [("JPEG", ".jpg"), ("WEBP", ".webp")])
def test_clear_exif_metadata(tmp_path, fmt, suffix):
    import piexif
    import piexif.helper

    source = tmp_path / ("source" + suffix)
    exif = piexif.dump(
        {"Exif": {piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump("secret")}}
    )
    Image.new("RGB", (32, 32)).save(source, format=fmt, exif=exif)
    dest = tmp_path / ("clear" + suffix)
    ImageDataReader.save_image(source, dest, fmt)
    with Image.open(dest) as result:
        assert not result.getexif()
        assert result.size == (32, 32)
