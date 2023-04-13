# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'update_checker.py'
__copyright__ = 'Copyright 2023, '
__email__ = 'receyuki@gmail.com'

import threading
import webbrowser

import requests
from packaging import version

from sd_prompt_reader.__version__ import VERSION

RELEASE_URL = "https://api.github.com/repos/receyuki/stable-diffusion-prompt-reader/releases/latest"


class UpdateChecker:
    def __init__(self, status_label, update_image):
        self._update_check = True
        self.status_label = status_label
        self.update_image = update_image
        self.update_thread = threading.Thread(target=self.check_update)
        self.update_thread.start()

    # check update from GitHub release
    def check_update(self):
        try:
            response = requests.get(RELEASE_URL, timeout=3).json()
        except Exception:
            print("Github api connection error")
        else:
            latest = response["name"]
            if version.parse(latest) > version.parse(VERSION):
                download_url = response["html_url"]
                self.status_label.configure(image=self.update_image,
                                            text="A new version is available, click here to download")
                self.status_label.bind("<Button-1>", lambda e: webbrowser.open_new(download_url))

    # clean up threads that are no longer in use
    def close_thread(self):
        if self._update_check:
            self._update_check = False
            self.status_label.unbind("<Button-1>")
            self.update_thread.join()
