#! /usr/bin/python
# -*- coding: utf-8 -*-

import base64
import os
import subprocess
import time
import requests

from helpers import db
from helpers import log

TEAMVIEWER_URL = "https://cdn.e-nobet.com/app/teamviewer_qs.tar.gz"
DOWNLOAD_DIR = "/home/farma/enobet/"
EXTRACT_DIR = "/home/farma/enobet/"
TEAMVIEWER_PROCESS = "TeamViewer"
TEAMVIEWER_DIR = os.path.join(EXTRACT_DIR, "teamviewerqs")
ARCHIVE_PATH = os.path.join(DOWNLOAD_DIR, "teamviewer_qs.tar.gz")
SCREENSHOT_PATH = os.path.join(DOWNLOAD_DIR, "screenshot.png")


def clean_directories():
    log.writelog("Teamviewer klasör ve dosyalar temizleniyor.")
    if os.path.exists(ARCHIVE_PATH):
        subprocess.run(["sudo", "rm", "-f", ARCHIVE_PATH], check=True)
        subprocess.run(["sudo", "rm", "-rf", TEAMVIEWER_DIR], check=True)


def download_teamviewer():
    try:
        log.writelog("Teamviewer tar.gz indiriliyor.")
        subprocess.run(["wget", "-O", ARCHIVE_PATH, TEAMVIEWER_URL])
    except Exception as e:
        log.writelog("Teamviewer tar.gz indirme sırasında hata oluştu:" + str(e))


def extract_teamviewer():
    try:
        log.writelog("Teamviewer tar.gz çıkartılıyor.")
        if not os.path.exists(ARCHIVE_PATH):
            log.writelog("Teamviewer tar.gz bulunamadı: " + ARCHIVE_PATH)
        else:
            subprocess.run(["tar", "-xzf", ARCHIVE_PATH, "-C", EXTRACT_DIR], check=True)
    except Exception as e:
        log.writelog("Teamviewer tar.gz çıkartma sırasında hata oluştu: " + str(e))


def run_teamviewer():
    try:
        subprocess.call(["sudo", "/home/farma/enobet/permission.sh"])
        log.writelog("Teamviewer çalıştırılıyor.")
        teamviewer_path = os.path.join(TEAMVIEWER_DIR, "teamviewer")

        if not os.path.exists(teamviewer_path):
            log.writelog("Teamviewer çalıştırmak için uygulama bulunamadı.")
        else:
            subprocess.Popen(["./teamviewer"], cwd="/home/farma/enobet/teamviewerqs")
    except Exception as e:
        log.writelog("Teamviewer çalıştırılamadı hata oluştu: " + str(e))


def is_teamviewer_running():
    try:
        result = subprocess.run(["pgrep", "-f", TEAMVIEWER_PROCESS], stdout=subprocess.PIPE)
        if result.returncode == 0:
            log.writelog("Teamviewer çalışıyor.")
        else:
            log.writelog("Teamviewer çalışmıyor.")
        return result.returncode == 0
    except Exception as e:
        log.writelog("Teamviewer çalıştırılamadı hata oluştu: " + str(e))


def capture_screenshot():
    try:
        subprocess.call(["sudo", "/home/farma/enobet/permission.sh"])

        if os.path.exists(SCREENSHOT_PATH):
            os.remove(SCREENSHOT_PATH)

        config = db.read_config_json()
        clientCode = config.get("clientCode")

        while not is_teamviewer_running():
            time.sleep(1)

        log.writelog("Ekran görüntüsü alınıyor.")

        subprocess.Popen(["scrot", "/home/farma/enobet/screenshot.png"], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE).communicate()
        time.sleep(1)

        if os.path.exists(SCREENSHOT_PATH):
            with open(SCREENSHOT_PATH, "rb") as image_file:
                base64_string = base64.b64encode(image_file.read()).decode("utf-8")

            params = {"id": clientCode, "screenshot": "image/png," + base64_string}
            response = requests.post("https://api.e-nobet.com/api/Client/SaveScreenshot", json=params)
            log.writelog(response.json())
        else:
            log.writelog("Ekran görüntüsü dosyası bulunamadı.")
    except Exception as e:
        log.writelog("Ekran görüntürü alınırken hata oluştu: " + str(e))


def main():
    subprocess.call(["sudo", "/home/farma/enobet/permission.sh"])
    clean_directories()
    download_teamviewer()
    extract_teamviewer()
    run_teamviewer()
    capture_screenshot()


if __name__ == "__main__":
    main()
