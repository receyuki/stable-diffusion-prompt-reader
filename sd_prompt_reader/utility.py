__author__ = "receyuki"
__filename__ = "utility.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

# Make the Image Data Reader capable of running in a minimal environment.
from pathlib import Path

try:
    from PIL import Image
    from customtkinter import CTkImage, filedialog
    import pyperclip
except ImportError:
    pass

from .constants import *


def load_icon(icon_file, size):
    return (
        CTkImage(Image.open(icon_file[0]), size=size),
        CTkImage(Image.open(icon_file[1]), size=size),
    )


def get_images(dir_path: Path):
    images = [
        image.resolve()
        for image in dir_path.rglob("*")
        if image.suffix in SUPPORTED_FORMATS
    ]
    return images


def select_image(file_path=None):
    initial_dir = file_path.parent if file_path else "/"
    return filedialog.askopenfilename(
        title="Select your image file",
        initialdir=initial_dir,
        filetypes=(("image files", "*.png *.jpg *jpeg *.webp"),),
    )


def copy_to_clipboard(status_bar, content):
    try:
        pyperclip.copy(content)
    except:
        print("Copy error")
    else:
        status_bar.clipboard()


def get_canvas_total_size(canvas):
    # Get the actual width and height of the canvas
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    # Use the bbox() method to get the bounding box information of all elements
    all_elements_bbox = canvas.bbox("all")

    if all_elements_bbox:
        # Get the maximum X and Y coordinates from the bounding box information of all elements to get the total size
        total_size = max(all_elements_bbox[2], canvas_width), max(
            all_elements_bbox[3], canvas_height
        )
    else:
        # If there are no elements, return the actual width and height of the canvas
        total_size = canvas_width, canvas_height

    return total_size


def get_frame_displayed_coordinates(frame):
    # Get the current viewport position information in both horizontal and vertical directions
    xview_info = frame.winfo_xview()
    yview_info = frame.winfo_yview()

    # Parse the viewport information to get the current displayed coordinate range
    x_start, x_end = map(float, xview_info)
    y_start, y_end = map(float, yview_info)

    # Calculate the coordinates of the currently displayed part based on the viewport information
    frame_width = frame.winfo_width()
    frame_height = frame.winfo_height()

    x_min = int(x_start * frame_width)
    x_max = int(x_end * frame_width)
    y_min = int(y_start * frame_height)
    y_max = int(y_end * frame_height)

    return x_min, y_min, x_max, y_max


def ease_in(t, b, c, d, ease_type="cubic"):
    # t: Current time (elapsed time since the animation started).
    # b: Initial value (starting position).
    # c: Change in value (target value minus initial value).
    # d: Duration (total duration of the animation).
    if ease_type == "cubic":
        t /= d
        return c * t * t * t + b
    elif ease_type == "quad":
        t /= d
        return c * t * t + b


def ease_out(t, b, c, d, ease_type="cubic"):
    # t: Current time (elapsed time since the animation started).
    # b: Initial value (starting position).
    # c: Change in value (target value minus initial value).
    # d: Duration (total duration of the animation).
    if ease_type == "cubic":
        t /= d
        t -= 1
        return c * (t * t * t + 1) + b
    elif ease_type == "quad":
        t /= d
        return -c * t * (t - 2) + b


def ease_in_out(t, b, c, d):
    # cubic
    t /= d / 2
    if t < 1:
        return c / 2 * t * t * t + b
    t -= 2
    return c / 2 * (t * t * t + 2) + b


def merge_str_to_tuple(item1, item2):
    if not isinstance(item1, tuple):
        item1 = (item1,)
    if not isinstance(item2, tuple):
        item2 = (item2,)
    return item1 + item2


def merge_dict(dict1, dict2):
    dict3 = dict1.copy()
    for k, v in dict2.items():
        dict3[k] = merge_str_to_tuple(v, dict3[k]) if k in dict3 else v
    return dict3


def remove_quotes(string):
    return str(string).replace('"', "").replace("'", "")


def add_quotes(string):
    return '"' + str(string) + '"'
