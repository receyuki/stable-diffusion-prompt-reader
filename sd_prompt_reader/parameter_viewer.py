__author__ = "receyuki"
__filename__ = "parameter_viewer.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import pyperclip as pyperclip
from customtkinter import CTkFrame, CTkLabel

from .constants import (
    BUTTON_HOVER,
    PARAMETER_PLACEHOLDER,
    PARAMETER_WIDTH,
)


class ParameterViewer:
    def __init__(self, parent, status_bar):
        self.status_bar = status_bar
        self.setting_box_parameter = CTkFrame(parent, fg_color="transparent")
        self.setting_box_parameter.columnconfigure(0, minsize=PARAMETER_WIDTH)

        self.setting_model_frame = CTkFrame(
            self.setting_box_parameter, fg_color="transparent"
        )
        self.setting_model_frame.grid(
            row=0, column=0, sticky="we", padx=10, pady=(1, 2)
        )
        self.setting_model_label = CTkLabel(self.setting_model_frame, text="Model:")
        self.setting_model_label.pack(side="left", padx=(0, 5))
        self.setting_model = CTkLabel(
            self.setting_model_frame,
            text=PARAMETER_PLACEHOLDER,
            fg_color=BUTTON_HOVER,
            corner_radius=5,
            wraplength=300,
        )
        self.setting_model.pack(side="left")
        self.setting_model.bind(
            "<Button-1>",
            lambda e: self.copy_to_clipboard(self.setting_model.cget("text")),
        )

        self.setting_sampler_frame = CTkFrame(
            self.setting_box_parameter, fg_color="transparent"
        )
        self.setting_sampler_frame.grid(row=1, column=0, sticky="we", padx=10, pady=2)
        self.setting_sampler_label = CTkLabel(
            self.setting_sampler_frame, text="Sampler:"
        )
        self.setting_sampler_label.pack(side="left", padx=(0, 5))
        self.setting_sampler = CTkLabel(
            self.setting_sampler_frame,
            text=PARAMETER_PLACEHOLDER,
            fg_color=BUTTON_HOVER,
            corner_radius=5,
            wraplength=300,
        )
        self.setting_sampler.pack(side="left")
        self.setting_sampler.bind(
            "<Button-1>",
            lambda e: self.copy_to_clipboard(self.setting_sampler.cget("text")),
        )

        self.setting_seed_frame = CTkFrame(
            self.setting_box_parameter, fg_color="transparent"
        )
        self.setting_seed_frame.grid(row=2, column=0, sticky="we", padx=10, pady=(2, 1))
        self.setting_seed_label = CTkLabel(self.setting_seed_frame, text="Seed:")
        self.setting_seed_label.pack(side="left", padx=(0, 5))
        self.setting_seed = CTkLabel(
            self.setting_seed_frame,
            text=PARAMETER_PLACEHOLDER,
            fg_color=BUTTON_HOVER,
            corner_radius=5,
            wraplength=300,
        )
        self.setting_seed.pack(side="left")
        self.setting_seed.bind(
            "<Button-1>",
            lambda e: self.copy_to_clipboard(self.setting_seed.cget("text")),
        )

        self.setting_cfg_frame = CTkFrame(
            self.setting_box_parameter, fg_color="transparent"
        )
        self.setting_cfg_frame.grid(row=0, column=1, sticky="we", padx=10)
        self.setting_cfg_label = CTkLabel(self.setting_cfg_frame, text="CFG scale:")
        self.setting_cfg_label.pack(side="left", padx=(0, 5))
        self.setting_cfg = CTkLabel(
            self.setting_cfg_frame,
            text=PARAMETER_PLACEHOLDER,
            fg_color=BUTTON_HOVER,
            corner_radius=5,
            wraplength=300,
        )
        self.setting_cfg.pack(side="left")
        self.setting_cfg.bind(
            "<Button-1>",
            lambda e: self.copy_to_clipboard(self.setting_cfg.cget("text")),
        )

        self.setting_steps_frame = CTkFrame(
            self.setting_box_parameter, fg_color="transparent"
        )
        self.setting_steps_frame.grid(row=1, column=1, sticky="we", padx=10)
        self.setting_steps_label = CTkLabel(self.setting_steps_frame, text="Steps:")
        self.setting_steps_label.pack(side="left", padx=(0, 5))
        self.setting_steps = CTkLabel(
            self.setting_steps_frame,
            text=PARAMETER_PLACEHOLDER,
            fg_color=BUTTON_HOVER,
            corner_radius=5,
            wraplength=300,
        )
        self.setting_steps.pack(side="left")
        self.setting_steps.bind(
            "<Button-1>",
            lambda e: self.copy_to_clipboard(self.setting_steps.cget("text")),
        )

        self.setting_size_frame = CTkFrame(
            self.setting_box_parameter, fg_color="transparent"
        )
        self.setting_size_frame.grid(row=2, column=1, sticky="we", padx=10)
        self.setting_size_label = CTkLabel(self.setting_size_frame, text="Size:")
        self.setting_size_label.pack(side="left", padx=(0, 5))
        self.setting_size = CTkLabel(
            self.setting_size_frame,
            text=PARAMETER_PLACEHOLDER,
            fg_color=BUTTON_HOVER,
            corner_radius=5,
            wraplength=300,
        )
        self.setting_size.pack(side="left")
        self.setting_size.bind(
            "<Button-1>",
            lambda e: self.copy_to_clipboard(self.setting_size.cget("text")),
        )

    def update_text(self, parameter):
        self.setting_model.configure(text=str(parameter["model"]))
        self.setting_sampler.configure(text=str(parameter["sampler"]))
        self.setting_seed.configure(text=str(parameter["seed"]))
        self.setting_cfg.configure(text=str(parameter["cfg"]))
        self.setting_steps.configure(text=str(parameter["steps"]))
        self.setting_size.configure(text=str(parameter["size"]))

    def reset_text(self):
        parameters = [
            self.setting_model,
            self.setting_sampler,
            self.setting_seed,
            self.setting_cfg,
            self.setting_steps,
            self.setting_size,
        ]
        for p in parameters:
            p.configure(text=PARAMETER_PLACEHOLDER)

    def copy_to_clipboard(self, content):
        try:
            pyperclip.copy(content)
        except:
            print("Copy error")
        else:
            self.status_bar.clipboard()
