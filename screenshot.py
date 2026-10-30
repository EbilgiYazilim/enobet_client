#! /usr/bin/python
# -*- coding: utf-8 -*-
"""Ekranın görüntüsünü alıp nöbet API'ye gönderir (TeamViewer'dan bağımsız komut)."""
import base64
import os
import subprocess

import requests

from helpers import db
from helpers import log

SCREENSHOT_PATH = "/home/farma/enobet/screenshot.png"


def capture_and_send():
    try:
        config = db.read_config_json()
        if not config:
            log.writelog("config.json yok; ekran görüntüsü atlandı.")
            return
        client_code = config.get("clientCode")

        if os.path.exists(SCREENSHOT_PATH):
            os.remove(SCREENSHOT_PATH)

        log.writelog("Ekran görüntüsü alınıyor.")
        subprocess.run(["scrot", SCREENSHOT_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not os.path.exists(SCREENSHOT_PATH):
            log.writelog("Ekran görüntüsü dosyası oluşmadı.")
            return

        with open(SCREENSHOT_PATH, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read()).decode("utf-8")

        params = {"id": client_code, "screenshot": "data:image/png;base64," + base64_string}
        response = requests.post("https://api.e-nobet.com/api/Client/SaveScreenshot", json=params, timeout=30)
        log.writelog("Ekran görüntüsü gönderildi: " + str(response.status_code))
    except Exception as e:
        log.writelog("Ekran görüntüsü alınırken hata oluştu: " + str(e))


if __name__ == "__main__":
    capture_and_send()
