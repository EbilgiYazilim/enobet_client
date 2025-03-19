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
        log.writelog("Downloading Teamviewer QS...")
        subprocess.run(["wget", "-O", ARCHIVE_PATH, TEAMVIEWER_URL])
    except Exception as e:
        log.writelog("Teamviewer indirme sırasında hata oluştu:" + str(e))


def extract_teamviewer():
    try:
        log.writelog("Extracting Teamviewer QS...")
        if not os.path.exists(ARCHIVE_PATH):
            log.writelog("Teamviewer çıkartma için tar.gz bulunamadı: " + ARCHIVE_PATH)

        subprocess.run(["tar", "-xzf", ARCHIVE_PATH, "-C", EXTRACT_DIR], check=True)
    except Exception as e:
        log.writelog("Teamviewer çıkartma sırasında hata oluştu: " + str(e))


def run_teamviewer():
    try:
        subprocess.call(["sudo", "/home/farma/enobet/permission.sh"])
        log.writelog("Running Teamviewer QS...")
        teamviewer_path = os.path.join(TEAMVIEWER_DIR, "teamviewer")

        if not os.path.exists(teamviewer_path):
            log.writelog("Teamviewer QS not found...")
            raise FileNotFoundError("Çalıştırılabilir dosya bulunamadı: " + teamviewer_path)

        subprocess.Popen(["./teamviewer"], cwd="/home/farma/enobet/teamviewerqs",
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    except Exception as e:
        log.writelog("Teamviewer çalıştırılamadı hata oluştu: " + str(e))


def is_teamviewer_running():
    try:
        result = subprocess.run(["pgrep", "-f", TEAMVIEWER_PROCESS], stdout=subprocess.PIPE)
        if result.returncode == 0:
            log.writelog("Team viewer process is running...")
        else:
            log.writelog("Team viewer process is NOT running...")
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

        log.writelog("Capturing screenshot...")
        subprocess.Popen(["scrot", "screenshot.png"], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE).communicate()
        time.sleep(1)

        subprocess.call(["sudo", "/home/farma/enobet/permission.sh"])

        if os.path.exists(SCREENSHOT_PATH):
            with open(SCREENSHOT_PATH, "rb") as image_file:
                base64_string = base64.b64encode(image_file.read()).decode("utf-8")

            params = {"id": clientCode, "screenshot": "image/png," + base64_string}
            response = requests.post("https://api.e-nobet.com/api/Client/SaveScreenshot", json=params)
            log.writelog(response.json())
        else:
            log.writelog("Screenshot not found...")
    except Exception as e:
        log.writelog("Failed to capture screenshot:" + str(e))


def main():
    subprocess.call(["sudo", "/home/farma/enobet/permission.sh"])
    clean_directories()
    download_teamviewer()
    extract_teamviewer()
    run_teamviewer()
    capture_screenshot()


if __name__ == "__main__":
    main()
