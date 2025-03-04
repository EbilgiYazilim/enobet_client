#! /usr/bin/python
# -*- coding: utf-8 -*-

import base64
import os
import subprocess
import time

import requests

TEAMVIEWER_URL = "https://cdn.e-nobet.com/app/teamviewer_qs.tar.gz"
DOWNLOAD_DIR = "/home/farma/enobet/"
EXTRACT_DIR = "/home/farma/enobet/"
TEAMVIEWER_DIR = os.path.join(EXTRACT_DIR, "teamviewerqs")
ARCHIVE_PATH = os.path.join(DOWNLOAD_DIR, "teamviewer_qs.tar.gz")
SCREENSHOT_PATH = os.path.join(DOWNLOAD_DIR, "screenshot.png")


def clean_directories():
    if os.path.exists(ARCHIVE_PATH):
        subprocess.run(["sudo", "rm", "-f", ARCHIVE_PATH], check=True)
        subprocess.run(["sudo", "rm", "-rf", TEAMVIEWER_DIR], check=True)


def download_teamviewer():
    try:
        subprocess.run(["wget", TEAMVIEWER_URL], check=True)
    except Exception as e:
        print(e)


def extract_teamviewer():
    if not os.path.exists(ARCHIVE_PATH):
        raise FileNotFoundError("Dosya indirilemedi: " + ARCHIVE_PATH)

    subprocess.run(["tar", "-xzf", ARCHIVE_PATH, "-C", EXTRACT_DIR], check=True)


def run_teamviewer():
    teamviewer_path = os.path.join(TEAMVIEWER_DIR, "teamviewer")

    if not os.path.exists(teamviewer_path):
        raise FileNotFoundError("Çalıştırılabilir dosya bulunamadı: " + teamviewer_path)

    # subprocess.run([teamviewer_path], check=True)
    subprocess.Popen([teamviewer_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def capture_screenshot():
    try:
        subprocess.run(["scrot", SCREENSHOT_PATH])

        if os.path.exists(SCREENSHOT_PATH):
            with open(SCREENSHOT_PATH, "rb") as image_file:
                base64_string = base64.b64encode(image_file.read()).decode("utf-8")

            os.remove(SCREENSHOT_PATH)
            params = {"id": "F4A7CED7-D2EB-419E-9F5D-002723F81645", "screenshot": "image/png," + base64_string}
            response = requests.post("https://api.e-nobet.com/api/Client/SaveScreenshot", json=params)
            print(response.json())
    except Exception as e:
        print("Failed to capture screenshot:", e)


def main():
    clean_directories()
    download_teamviewer()
    extract_teamviewer()
    run_teamviewer()
    time.sleep(5)
    capture_screenshot()


if __name__ == "__main__":
    main()
