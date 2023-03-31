import piexif
import pyperclip as pyperclip
from PIL import Image, ImageTk
from tkinter import TOP, END, Frame, Text, LEFT, Scrollbar, VERTICAL, RIGHT, Y, BOTH, X, Canvas, DISABLED, NORMAL, \
    WORD, BOTTOM, CENTER, Label, ttk, PhotoImage
from tkinter.ttk import *
from tkinterdnd2 import *
from os import path, name
from customtkinter import *
from plyer import notification

bundle_dir = path.abspath(path.dirname(__file__))


# Make dnd work with ctk
class Tk(CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


# Modified from:
# https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/22bcc7be428c94e9408f589966c2040187245d81/modules/images.py#L614
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

    #     if items.get("Software", None) == "NovelAI":
    #         try:
    #             json_info = json.loads(items["Comment"])
    #             sampler = sd_samplers.samplers_map.get(json_info["sampler"], "Euler a")
    #
    #             geninfo = f"""{items["Description"]}
    # Negative prompt: {json_info["uc"]}
    # Steps: {json_info["steps"]}, Sampler: {sampler}, CFG scale: {json_info["scale"]}, Seed: {json_info["seed"]}, Size: {image.width}x{image.height}, Clip skip: 2, ENSD: 31337"""
    #         except Exception:
    #             print("Error parsing NovelAI image generation parameters:", file=sys.stderr)
    #             print(traceback.format_exc(), file=sys.stderr)

    return geninfo, items


# Modified from:
# https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/22bcc7be428c94e9408f589966c2040187245d81/modules/images.py#L650
def image_data(file):
    try:
        image = Image.open(file)
        image.info
        textinfo, _ = read_info_from_image(image)
        return textinfo, None
    except Exception:
        pass

    # try:
    #     text = data.decode('utf8')
    #     assert len(text) < 10000
    #     return text, None
    #
    # except Exception:
    #     pass

    return '', None


def image_info_format(text):
    if text:
        prompt_index = [text.index("\nNegative prompt:"),
                        text.index("\nSteps:")]
        positive = text[:prompt_index[0]]
        negative = text[prompt_index[0] + 1 + len("Negative prompt: "):prompt_index[1]]
        setting = text[prompt_index[1] + 1:]
    else:
        positive = negative = setting = "No data detected or unsupported formats"
    return positive, negative, setting, text


def display_info(event):
    global image, image_tk, image_label, info, scaling
    boxes = [positive_box, negative_box, setting_box]
    file_path = event.data.replace("}", "").replace("{", "")
    # clear text
    for box in boxes:
        box.configure(state=NORMAL)
        box.delete("1.0", END)
    if file_path.lower().endswith(".png"):
        with open(file_path, "rb") as f:
            text_line, _ = image_data(f)
            info = image_info_format(text_line)
            # insert prompt
            positive_box.insert(END, info[0])
            negative_box.insert(END, info[1])
            setting_box.insert(END, info[2])

            for box in boxes:
                box.configure(state=DISABLED, text_color=default_text_colour)
            image = Image.open(f)
            image_tk = CTkImage(light_image=image, dark_image=image)
            aspect_ratio = image.size[0] / image.size[1]
            scaling = ScalingTracker.get_window_dpi_scaling(window)
            # resize image to window size
            if image.size[0] > image.size[1]:
                image_tk.configure(size=tuple(num / scaling for num in
                                              (image_frame.winfo_height(), image_frame.winfo_height() / aspect_ratio)))
            else:
                image_tk.configure(size=tuple(num / scaling for num in
                                              (image_label.winfo_height() * aspect_ratio, image_label.winfo_height())))
            # display image
            image_tk.configure()
            image_label.configure(image=image_tk)
    else:
        for box in boxes:
            box.insert(END, "Unsupported formats")


def resize_image(event):
    # resize image to window size
    global image, image_label, image_tk, scaling
    if image:
        aspect_ratio = image.size[0] / image.size[1]
        scaling = ScalingTracker.get_window_dpi_scaling(window)
        # resize image to window size
        if image.size[0] > image.size[1]:
            image_tk.configure(size=tuple(num / scaling for num in
                                          (image_frame.winfo_height(), image_frame.winfo_height() / aspect_ratio)))
        else:
            image_tk.configure(size=tuple(num / scaling for num in
                                          (image_label.winfo_height() * aspect_ratio, image_label.winfo_height())))
        image_label.configure(image=image_tk)


def copy_to_clipboard(content):
    try:
        pyperclip.copy(content)
    except:
        print("Copy error")
    else:
        notification.notify(title="Success",
                            message="copied to clipboard",
                            app_icon=ico_file,
                            timeout=50,
                            toast=True,
                            )


# window = TkinterDnD.Tk()
window = Tk()
window.title("SD Prompt Reader")
window.geometry("1200x650")

# set_appearance_mode("Light")
# deactivate_automatic_dpi_awareness()
# set_widget_scaling(1)
# set_window_scaling(0.8)
# info_font = CTkFont(size=20)
info_font = CTkFont()
scaling = ScalingTracker.get_window_dpi_scaling(window)

icon_file = path.join(bundle_dir, "resources/icon.png")
ico_file = path.join(bundle_dir, "resources/icon.ico")
icon_image = PhotoImage(file=icon_file)
window.iconphoto(False, icon_image)
if name == "nt":
    window.iconbitmap(ico_file)


image_frame = CTkFrame(window)
image_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=20, pady=20)

drop_file = path.join(bundle_dir, "resources/drag-and-drop.png")
drop_image = CTkImage(light_image=Image.open(drop_file), dark_image=Image.open(drop_file), size=(100, 100))
image_label = CTkLabel(image_frame, text="", image=drop_image)
image_label.pack(fill=BOTH, expand=True)

image = None
image_tk = None
info = [""] * 4


prompt_frame = CTkFrame(window, fg_color="transparent")
prompt_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(0, 20), pady=20)

positive = CTkFrame(prompt_frame, fg_color="transparent")
positive.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 20))
positive_box = CTkTextbox(positive, wrap=WORD)
positive_box.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))
default_text_colour = positive_box._text_color
positive_box.insert(END, "Prompt")
positive_box.configure(state=DISABLED, text_color="gray", font=info_font)

negative = CTkFrame(prompt_frame, fg_color="transparent")
negative.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 20))
negative_box = CTkTextbox(negative, wrap=WORD)
negative_box.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))
negative_box.insert(END, "Negative Prompt")
negative_box.configure(state=DISABLED, text_color="gray", font=info_font)

setting = CTkFrame(prompt_frame, fg_color="transparent")
setting.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 10))
setting_box = CTkTextbox(setting, wrap=WORD, height=100)
setting_box.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 85))
setting_box.insert(END, "Setting")
setting_box.configure(state=DISABLED, text_color="gray", font=info_font)

clipboard_file = path.join(bundle_dir, "resources/copy-to-clipboard.png")
clipboard_image = CTkImage(light_image=Image.open(clipboard_file), dark_image=Image.open(clipboard_file), size=(50, 50))


button_positive = CTkButton(positive, width=50, height=50, image=clipboard_image, text="",
                            command=lambda: copy_to_clipboard(info[0]))
button_positive.pack(side=RIGHT, padx=(20, 0))

button_negative = CTkButton(negative, width=50, height=50, image=clipboard_image, text="",
                            command=lambda: copy_to_clipboard(info[1]))
button_negative.pack(side=RIGHT, padx=(20, 0))

button_prompt = CTkButton(prompt_frame, width=50, height=50, image=clipboard_image, text="Raw Data", font=info_font,
                          command=lambda: copy_to_clipboard(info[3]))
button_prompt.pack(side=BOTTOM)


window.drop_target_register(DND_FILES)
window.dnd_bind("<<Drop>>", display_info)
window.bind("<Configure>", resize_image)

window.mainloop()
