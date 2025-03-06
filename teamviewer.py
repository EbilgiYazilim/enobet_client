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
        subprocess.run(["wget", TEAMVIEWER_URL], check=True)
    except Exception as e:
        print(e)


def extract_teamviewer():
    log.writelog("Extracting Teamviewer QS...")
    if not os.path.exists(ARCHIVE_PATH):
        raise FileNotFoundError("Dosya indirilemedi: " + ARCHIVE_PATH)

    subprocess.run(["tar", "-xzf", ARCHIVE_PATH, "-C", EXTRACT_DIR], check=True)


def run_teamviewer():
    subprocess.call(["sudo", "/home/farma/enobet/permission.sh"])
    log.writelog("Running Teamviewer QS...")
    teamviewer_path = os.path.join(TEAMVIEWER_DIR, "teamviewer")

    if not os.path.exists(teamviewer_path):
        log.writelog("Teamviewer QS not found...")
        raise FileNotFoundError("Çalıştırılabilir dosya bulunamadı: " + teamviewer_path)

    # subprocess.run([teamviewer_path], check=True)
    # subprocess.Popen([teamviewer_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(["./teamviewer"], cwd="/home/farma/enobet/teamviewerqs",
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)


def is_teamviewer_running():
    result = subprocess.run(["pgrep", "-f", TEAMVIEWER_PROCESS], stdout=subprocess.PIPE)
    log.writelog("Checking if Teamviewer QS is running:" + str(result.returncode))
    return result.returncode == 0


def capture_screenshot():
    try:
        if os.path.exists(SCREENSHOT_PATH):
            os.remove(SCREENSHOT_PATH)

        config = db.read_config_json()
        clientCode = config.get("clientCode")

        while not is_teamviewer_running():
            time.sleep(1)

        time.sleep(30)
        log.writelog("Capturing screenshot...")
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
