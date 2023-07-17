# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'utility.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

from customtkinter import filedialog

from PIL import Image
from customtkinter import CTkImage
from pathlib import Path
from sd_prompt_reader.constants import *


def load_icon(icon_file, size):
    return (CTkImage(Image.open(icon_file[0]), size=size),
            CTkImage(Image.open(icon_file[1]), size=size))


def get_images(dir_path: str):
    images = [image.resolve() for image in Path(dir_path).rglob("*") if image.suffix in SUPPORTED_FORMATS]
    return images


def select_image(file_path=None):
    initial_dir = file_path.parent if file_path else "/"
    return filedialog.askopenfilename(
        title='Select your image file',
        initialdir=initial_dir,
        filetypes=(("image files", "*.png *.jpg *jpeg *.webp"),)
    )
