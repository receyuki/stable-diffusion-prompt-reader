__author__ = "receyuki"
__filename__ = "update_checker.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import threading

import requests
from packaging import version

from .__version__ import VERSION
from .constants import URL


class UpdateChecker:
    def __init__(self, status_bar):
        self._update_check = True
        self.status_bar = status_bar
        self.update_thread = threading.Thread(target=self.check_update)
        self.update_thread.start()

    # check update from GitHub release
    def check_update(self):
        try:
            response = requests.get(URL["release"], timeout=3).json()
        except Exception:
            print("Github api connection error")
        else:
            latest = response["name"]
            if version.parse(latest) > version.parse(VERSION):
                download_url = response["html_url"]
                self.status_bar.link(download_url, is_update=True)

    # clean up threads that are no longer in use
    def close_thread(self):
        if self._update_check:
            self._update_check = False
            self.status_bar.unbind()
            self.update_thread.join()
