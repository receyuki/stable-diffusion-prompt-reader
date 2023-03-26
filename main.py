import base64
import io

from PIL import Image, ImageTk
from tkinter import TOP, END, Frame, Text, LEFT, Scrollbar, VERTICAL, RIGHT, Y, BOTH, X, Canvas, DISABLED, NORMAL, WORD, \
    Button, font
from tkinterdnd2 import *
from os import path
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM, shapes


def read_info_from_image(image):
    items = image.info or {}
    geninfo = items.pop('parameters', None)
    if "exif" in items:
        exif = piexif.load(items["exif"])
        exif_comment = (exif or {}).get("Exif", {}).get(piexif.ExifIFD.UserComment, b'')
        try:
            exif_comment = piexif.helper.UserComment.load(exif_comment)
        except ValueError:
            exif_comment = exif_comment.decode('utf8', errors="ignore")

        if exif_comment:
            items['exif comment'] = exif_comment
            geninfo = exif_comment

        for field in ['jfif', 'jfif_version', 'jfif_unit', 'jfif_density', 'dpi', 'exif',
                      'loop', 'background', 'timestamp', 'duration']:
            items.pop(field, None)

    if items.get("Software", None) == "NovelAI":
        try:
            json_info = json.loads(items["Comment"])
            sampler = sd_samplers.samplers_map.get(json_info["sampler"], "Euler a")

            geninfo = f"""{items["Description"]}
Negative prompt: {json_info["uc"]}
Steps: {json_info["steps"]}, Sampler: {sampler}, CFG scale: {json_info["scale"]}, Seed: {json_info["seed"]}, Size: {image.width}x{image.height}, Clip skip: 2, ENSD: 31337"""
        except Exception:
            print("Error parsing NovelAI image generation parameters:", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)

    return geninfo, items


def image_data(file):
    try:
        image = Image.open(file)
        image.info
        textinfo, _ = read_info_from_image(image)
        return textinfo, None
    except Exception:
        pass

    try:
        text = data.decode('utf8')
        assert len(text) < 10000
        return text, None

    except Exception:
        pass

    return '', None


def image_info_format(text):
    prompt_index = [text.index("\nNegative prompt:"),
                    text.index("\nSteps:")]
    positive = text[:prompt_index[0]]
    negative = text[prompt_index[0] + 1 + len("Negative prompt: "):prompt_index[1]]
    setting = text[prompt_index[1] + 1:]
    return positive, negative, setting


def display_info(event):
    global image, image_tk, image_canvas
    # clear text
    positive_box.config(state=NORMAL)
    negative_box.config(state=NORMAL)
    setting_box.config(state=NORMAL)
    positive_box.delete("1.0", END)
    negative_box.delete("1.0", END)
    setting_box.delete("1.0", END)
    if event.data.endswith(".png"):
        with open(event.data, "rb") as f:
            text_line, _ = image_data(f)
            info = image_info_format(text_line)
            # insert prompt
            positive_box.insert(END, info[0])
            negative_box.insert(END, info[1])
            setting_box.insert(END, info[2])
            positive_box.config(state=DISABLED)
            negative_box.config(state=DISABLED)
            setting_box.config(state=DISABLED)
            image = Image.open(f)
            # resize image to window size
            if image.size[0] < image.size[1]:
                resized = image.resize((int(image.size[0] / image.size[1] * image_frame.winfo_height()),
                                        image_frame.winfo_height()), Image.LANCZOS)
            else:
                resized = image.resize((image_frame.winfo_width(),
                                        int(image.size[1] / image.size[0] * image_frame.winfo_width())), Image.LANCZOS)
            # display image
            image_tk = ImageTk.PhotoImage(resized)
            image_canvas.create_image(image_frame.winfo_width() / 2, 0, anchor="n", image=image_tk)
            image_canvas.pack(side=LEFT, fill=BOTH, expand=True)


def resize_image(event):
    # resize image to window size
    global image, image_canvas, image_tk
    if image:
        if image.size[0] < image.size[1]:
            resized = image.resize((int(image.size[0] / image.size[1] * image_frame.winfo_height()),
                                    image_frame.winfo_height()), Image.NEAREST)
        else:
            resized = image.resize((image_frame.winfo_width(),
                                    int(image.size[1] / image.size[0] * image_frame.winfo_width())), Image.NEAREST)
        image_tk = ImageTk.PhotoImage(resized)
        image_canvas.create_image(image_frame.winfo_width() / 2, 0, anchor="n", image=image_tk)
        # image_canvas.pack(fill=BOTH)


window = TkinterDnD.Tk()
window.title('SD Prompt Reader')
window.geometry("800x400")
# window.attributes('-alpha', 0.95)
# window.config(bg='white')

prompt_frame = Frame(window)
prompt_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=10, pady=10)

positive = Frame(prompt_frame, height=10)
positive.pack(side=TOP, fill=BOTH, expand=True)
positive_box = Text(positive, wrap=WORD)
positive_box.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar_positive = Scrollbar(positive_box, orient=VERTICAL)
scrollbar_positive.pack(side=RIGHT, fill=Y)
positive_box.configure(yscrollcommand=scrollbar_positive.set)
scrollbar_positive.config(command=positive_box.yview)

# clipboard_svg = '<?xml version="1.0" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg t="1679843751623" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="5425" xmlns:xlink="http://www.w3.org/1999/xlink" width="200" height="200"><path d="M819.2 819.2v-68.266667h68.266667c40.96 0 68.266667-27.306667 68.266666-68.266666V136.533333c0-40.96-27.306667-68.266667-68.266666-68.266666H341.333333c-40.96 0-68.266667 27.306667-68.266666 68.266666v68.266667H204.8V136.533333c0-75.093333 61.44-136.533333 136.533333-136.533333h546.133334c75.093333 0 136.533333 61.44 136.533333 136.533333v546.133334c0 75.093333-61.44 136.533333-136.533333 136.533333h-68.266667z" fill="#777777" p-id="5426"></path><path d="M136.533333 204.8h546.133334c75.093333 0 136.533333 61.44 136.533333 136.533333v546.133334c0 75.093333-61.44 136.533333-136.533333 136.533333H136.533333c-75.093333 0-136.533333-61.44-136.533333-136.533333V341.333333c0-75.093333 61.44-136.533333 136.533333-136.533333z m0 68.266667c-40.96 0-68.266667 27.306667-68.266666 68.266666v546.133334c0 40.96 27.306667 68.266667 68.266666 68.266666h546.133334c40.96 0 68.266667-27.306667 68.266666-68.266666V341.333333c0-40.96-27.306667-68.266667-68.266666-68.266666H136.533333z" fill="#777777" p-id="5427"></path><path d="M238.933333 477.866667h341.333334c20.48 0 34.133333 13.653333 34.133333 34.133333s-13.653333 34.133333-34.133333 34.133333h-341.333334c-20.48 0-34.133333-13.653333-34.133333-34.133333s13.653333-34.133333 34.133333-34.133333zM238.933333 682.666667h341.333334c20.48 0 34.133333 13.653333 34.133333 34.133333s-13.653333 34.133333-34.133333 34.133333h-341.333334c-20.48 0-34.133333-13.653333-34.133333-34.133333s13.653333-34.133333 34.133333-34.133333z" fill="#777777" p-id="5428"></path></svg>'
# clipboard_file = io.BytesIO()
# renderPM.drawToFile(svg2rlg(io.StringIO(clipboard_svg)), clipboard_file)

# clipboard_image = ImageTk.PhotoImage(Image.open(clipboard_file).resize((50, 50), Image.LANCZOS))
bundle_dir = path.abspath(path.dirname(__file__))
path_to_dat = path.join(bundle_dir, "resources/clipboard.png")
clipboard_image = ImageTk.PhotoImage(Image.open(path_to_dat).resize((50, 50), Image.LANCZOS))
button_positive = Button(positive, image=clipboard_image)
button_positive.pack(side=RIGHT)

negative_box = Text(prompt_frame, height=10, wrap=WORD)
negative_box.pack(side=TOP, fill=BOTH, expand=True)
scrollbar_negative = Scrollbar(negative_box, orient=VERTICAL)
scrollbar_negative.pack(side=RIGHT, fill=Y)
negative_box.configure(yscrollcommand=scrollbar_negative.set)
scrollbar_negative.config(command=negative_box.yview)

setting_box = Text(prompt_frame, height=5, wrap=WORD)
setting_box.pack(side=TOP, fill=BOTH, expand=True)

image_frame = Frame(window)
image_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
image_canvas = Canvas(image_frame)

image = None
image_tk = None
# image = Image.open("dnd.png")
# image_tk = ImageTk.PhotoImage(image)
# image_canvas.create_image(0, 0, anchor="nw", image=image_tk)
# image_canvas.pack(fill=BOTH, expand=True)

window.drop_target_register(DND_FILES)
window.dnd_bind('<<Drop>>', display_info)
window.bind("<Configure>", resize_image)

window.mainloop()
