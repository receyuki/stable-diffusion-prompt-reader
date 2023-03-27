import pyperclip as pyperclip
from PIL import Image, ImageTk
from tkinter import TOP, END, Frame, Text, LEFT, Scrollbar, VERTICAL, RIGHT, Y, BOTH, X, Canvas, DISABLED, NORMAL, \
    WORD, BOTTOM, CENTER, Label, ttk
from tkinter.ttk import *
from tkinterdnd2 import *
from os import path
from customtkinter import *

bundle_dir = path.abspath(path.dirname(__file__))


# Make dnd work with ctk
class Tk(CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


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
    global image, image_tk, image_label, info
    # clear text
    positive_box.configure(state=NORMAL)
    negative_box.configure(state=NORMAL)
    setting_box.configure(state=NORMAL)
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
            positive_box.configure(state=DISABLED)
            negative_box.configure(state=DISABLED)
            setting_box.configure(state=DISABLED)
            image = Image.open(f)
            image_tk = CTkImage(light_image=image, dark_image=image, size=(50, 50))
            aspect_ratio = image.size[0] / image.size[1]

            # resize image to window size
            if image.size[0] > image.size[1]:
                print("width")
                print(image_label.winfo_height())
                # resized = image.resize((int(image.size[0] / image.size[1] * image_frame.winfo_height()),
                #                         image_frame.winfo_height()), Image.NEAREST)
                image_tk.configure(size=(int(aspect_ratio*image_label.winfo_height()),
                                         image_label.winfo_height()))
            else:
                print("height")
                print(image_label.winfo_width())
                # resized = image.resize((image_frame.winfo_width(),
                #                         int(image.size[1] / image.size[0] * image_frame.winfo_width())), Image.NEAREST)
                image_tk.configure(size=(image_label.winfo_width(),
                                         int(1/aspect_ratio*image_label.winfo_width())))
            # display image
            # image_tk = ImageTk.PhotoImage(resized)
            # image_canvas.create_image(image_frame.winfo_width() / 2, image_frame.winfo_height() / 2, anchor=CENTER,
            #                           image=image_tk)
            # image_canvas.pack(side=LEFT, fill=BOTH, expand=True)
            image_label.configure(image=image_tk)


def resize_image(event):
    # resize image to window size
    global image, image_label, image_tk
    if image:
        if image.size[0] > image.size[1]:
            # resized = image.resize((int(image.size[0] / image.size[1] * image_frame.winfo_height()),
            #                         image_frame.winfo_height()), Image.NEAREST)
            image_tk.configure(size=(int(image.size[0] / image.size[1] * image_frame.winfo_height()),
                                     image_frame.winfo_height()))
        else:
            # resized = image.resize((image_frame.winfo_width(),
            #                         int(image.size[1] / image.size[0] * image_frame.winfo_width())), Image.NEAREST)
            image_tk.configure(size=(image_frame.winfo_width(),
                                     int(image.size[1] / image.size[0] * image_frame.winfo_width())))
        # image_tk = ImageTk.PhotoImage(resized)
        # image_canvas.create_image(image_frame.winfo_width() / 2, image_frame.winfo_height() / 2, anchor=CENTER,
        #                           image=image_tk)
        # image_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        image_label.configure(image=image_tk)


def copy_to_clipboard(content):
    pyperclip.copy(content)


# window = TkinterDnD.Tk()
window = Tk()
window.title('SD Prompt Reader')
# window.geometry("960x540")
window.geometry("1200x600")
# window.geometry("1024x450")
# window.attributes('-alpha', 0.95)
# window.config(bg='white')
# set_appearance_mode("Light")
deactivate_automatic_dpi_awareness()
# temp

icon_file = path.join(bundle_dir, "resources/icon.png")
icon_image = ImageTk.PhotoImage(file=icon_file)
window.iconphoto(False, icon_image)

image_frame = CTkFrame(window)
image_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=20, pady=20)
# image_canvas = CTkCanvas(image_frame)

drop_file = path.join(bundle_dir, "resources/drag-and-drop.png")
drop_image = CTkImage(light_image=Image.open(drop_file), dark_image=Image.open(drop_file), size=(100, 100))
image_label = CTkLabel(image_frame, text="", image=drop_image)
image_label.pack(side=LEFT, fill=BOTH, expand=True)

image = None
image_tk = None
info = [""] * 4
# image = Image.open("resources/drag-and-drop.png")
# image_tk = ImageTk.PhotoImage(image.resize((50, 50), Image.LANCZOS))
# image_canvas.create_image(50, 50, image=image_tk)
# image_canvas.pack(fill=BOTH, expand=True)

prompt_frame = CTkFrame(window, fg_color="transparent")
prompt_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(0, 20), pady=20)

# positive = LabelFrame(prompt_frame, text="Prompt")
positive = CTkFrame(prompt_frame, fg_color="transparent")
positive.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 20))
positive_box = CTkTextbox(positive, wrap=WORD)
positive_box.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))
# scrollbar_positive = CTkScrollbar(positive_box, orient=VERTICAL)
# scrollbar_positive.pack(side=RIGHT, fill=Y)
# positive_box.configure(yscrollcommand=scrollbar_positive.set)
# scrollbar_positive.config(command=positive_box.yview)
# scrollbar_positive = CTkScrollbar(positive_box, command=positive_box.yview)
# positive_box.configure(yscrollcommand=scrollbar_positive.set)


# negative = LabelFrame(prompt_frame, text="Negative Prompt")
negative = CTkFrame(prompt_frame, fg_color="transparent")
negative.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 20))
negative_box = CTkTextbox(negative, wrap=WORD)
negative_box.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))
# scrollbar_negative = CTkScrollbar(negative_box, orient=VERTICAL)
# scrollbar_negative.pack(side=RIGHT, fill=Y)
# negative_box.configure(yscrollcommand=scrollbar_negative.set)
# scrollbar_negative.config(command=negative_box.yview)

# setting = LabelFrame(prompt_frame, text="Settings")
setting = CTkFrame(prompt_frame, fg_color="transparent")
setting.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 10))
setting_box = CTkTextbox(setting, wrap=WORD, height=80)
setting_box.pack(side=TOP, fill=BOTH, expand=True, padx=10)

clipboard_file = path.join(bundle_dir, "resources/copy-to-clipboard.png")
clipboard_image = ImageTk.PhotoImage(Image.open(clipboard_file).resize((50, 50), Image.LANCZOS))

# button_positive_canvas = CTkCanvas(positive, width=50, height=50)
# button_positive_canvas.pack(side=RIGHT, padx=(20, 0))
# button_positive = button_positive_canvas.create_image(25, 25, image=clipboard_image)
# button_positive_canvas.tag_bind(button_positive, "<Button-1>", lambda event: copy_to_clipboard(event, info[0]))
button_positive = CTkButton(positive, width=50, height=50, image=clipboard_image, text="",
                            fg_color="transparent", command=lambda: copy_to_clipboard(info[0]))
button_positive.pack(side=RIGHT, padx=(20, 0))

# button_negative_canvas = CTkCanvas(negative, width=50, height=50)
# button_negative_canvas.pack(side=RIGHT, padx=(20, 0))
# button_negative = button_negative_canvas.create_image(25, 25, image=clipboard_image)
# button_negative_canvas.tag_bind(button_negative, "<Button-1>", lambda event: copy_to_clipboard(event, info[1]))
button_negative = CTkButton(negative, width=50, height=50, image=clipboard_image, text="",
                            fg_color="transparent", command=lambda: copy_to_clipboard(info[1]))
button_negative.pack(side=RIGHT, padx=(20, 0))

# button_prompt_canvas = CTkCanvas(prompt_frame, width=50, height=50)
# button_prompt_canvas.pack(side=BOTTOM)
# button_prompt = button_prompt_canvas.create_image(25, 25, image=clipboard_image)
# button_prompt_canvas.tag_bind(button_prompt, "<Button-1>", lambda event: copy_to_clipboard(event, info[3]))

button_prompt = CTkButton(prompt_frame, width=50, height=50, image=clipboard_image, text="Raw Data",
                          command=lambda: copy_to_clipboard(info[3]))
button_prompt.pack(side=BOTTOM)

window.drop_target_register(DND_FILES)
window.dnd_bind("<<Drop>>", display_info)
# window.bind("<Configure>", resize_image)

window.mainloop()
