import pyperclip as pyperclip
from PIL import Image, ImageTk
from tkinter import TOP, END, Frame, Text, LEFT, Scrollbar, VERTICAL, RIGHT, Y, BOTH, X, Canvas, DISABLED, NORMAL, \
    WORD, BOTTOM, CENTER, Label, ttk
from tkinter.ttk import *
from tkinterdnd2 import *
from os import path

bundle_dir = path.abspath(path.dirname(__file__))


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
    return positive, negative, setting, text


def display_info(event):
    global image, image_tk, image_canvas, info
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
            if image.size[0] > image.size[1]:
                resized = image.resize((int(image.size[0] / image.size[1] * image_frame.winfo_height()),
                                        image_frame.winfo_height()), Image.NEAREST)
            else:
                resized = image.resize((image_frame.winfo_width(),
                                        int(image.size[1] / image.size[0] * image_frame.winfo_width())), Image.NEAREST)
            # display image
            image_tk = ImageTk.PhotoImage(resized)
            image_canvas.create_image(image_frame.winfo_width() / 2, image_frame.winfo_height() / 2, anchor=CENTER,
                                      image=image_tk)
            image_canvas.pack(side=LEFT, fill=BOTH, expand=True)


def resize_image(event):
    # resize image to window size
    global image, image_canvas, image_tk
    if image:
        if image.size[0] > image.size[1]:
            resized = image.resize((int(image.size[0] / image.size[1] * image_frame.winfo_height()),
                                    image_frame.winfo_height()), Image.NEAREST)
        else:
            resized = image.resize((image_frame.winfo_width(),
                                    int(image.size[1] / image.size[0] * image_frame.winfo_width())), Image.NEAREST)
        image_tk = ImageTk.PhotoImage(resized)
        image_canvas.create_image(image_frame.winfo_width() / 2, image_frame.winfo_height() / 2, anchor=CENTER,
                                  image=image_tk)
        # image_canvas.pack(side=LEFT, fill=BOTH, expand=True)


def copy_to_clipboard(event, content):
    pyperclip.copy(content)


window = TkinterDnD.Tk()
window.title('SD Prompt Reader')
# window.geometry("960x540")
window.geometry("1024x450")
# window.attributes('-alpha', 0.95)
# window.config(bg='white')

icon_file = path.join(bundle_dir, "resources/icon.png")
icon_image = ImageTk.PhotoImage(file=icon_file)
window.iconphoto(False, icon_image)

image_frame = Frame(window, width=400, height=400)
image_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
image_canvas = Canvas(image_frame)

image = None
image_tk = None
info = [""] * 4
# image = Image.open("resources/drag-and-drop.png")
# image_tk = ImageTk.PhotoImage(image.resize((50, 50), Image.LANCZOS))
# image_canvas.create_image(50, 50, image=image_tk)
# image_canvas.pack(fill=BOTH, expand=True)

prompt_frame = Frame(window)
prompt_frame.pack(fill=Y, expand=True, padx=(0, 10), pady=10)

positive = LabelFrame(prompt_frame, text="Prompt")
positive.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 10))
positive_box = Text(positive, wrap=WORD)
positive_box.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0), pady=5)
scrollbar_positive = Scrollbar(positive_box, orient=VERTICAL)
scrollbar_positive.pack(side=RIGHT, fill=Y)
positive_box.configure(yscrollcommand=scrollbar_positive.set)
scrollbar_positive.config(command=positive_box.yview)

negative = LabelFrame(prompt_frame, text="Negative Prompt")
negative.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 10))
negative_box = Text(negative, wrap=WORD)
negative_box.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0), pady=5)
scrollbar_negative = Scrollbar(negative_box, orient=VERTICAL)
scrollbar_negative.pack(side=RIGHT, fill=Y)
negative_box.configure(yscrollcommand=scrollbar_negative.set)
scrollbar_negative.config(command=negative_box.yview)

setting = LabelFrame(prompt_frame, text="Settings")
setting.pack(side=TOP, fill=X, pady=(0, 10))
setting_box = Text(setting, height=6, wrap=WORD)
setting_box.pack(side=TOP, fill=X, padx=5, pady=5)

clipboard_file = path.join(bundle_dir, "resources/copy-to-clipboard.png")
clipboard_image = ImageTk.PhotoImage(Image.open(clipboard_file).resize((50, 50), Image.LANCZOS))

button_positive_canvas = Canvas(positive, width=50, height=50)
button_positive_canvas.pack(side=RIGHT, padx=(10, 0))
button_positive = button_positive_canvas.create_image(25, 25, image=clipboard_image)
button_positive_canvas.tag_bind(button_positive, "<Button-1>", lambda event: copy_to_clipboard(event, info[0]))

button_negative_canvas = Canvas(negative, width=50, height=50)
button_negative_canvas.pack(side=RIGHT, padx=(10, 0))
button_negative = button_negative_canvas.create_image(25, 25, image=clipboard_image)
button_negative_canvas.tag_bind(button_negative, "<Button-1>", lambda event: copy_to_clipboard(event, info[1]))

button_prompt_canvas = Canvas(prompt_frame, width=50, height=50)
button_prompt_canvas.pack(side=BOTTOM)
button_prompt = button_prompt_canvas.create_image(25, 25, image=clipboard_image)
button_prompt_canvas.tag_bind(button_prompt, "<Button-1>", lambda event: copy_to_clipboard(event, info[3]))

window.drop_target_register(DND_FILES)
window.dnd_bind("<<Drop>>", display_info)
window.bind("<Configure>", resize_image)

window.mainloop()
