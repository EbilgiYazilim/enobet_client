#! /usr/bin/python
# -*- coding: utf-8 -*-

import base64
import os
import subprocess
import shutil
import requests

TEAMVIEWER_URL = "https://cdn.e-nobet.com/app/teamviewer_qs.tar.gz"
DOWNLOAD_DIR = "/home/downloads"
EXTRACT_DIR = "/home/teamqs"
ARCHIVE_PATH = os.path.join(DOWNLOAD_DIR, "teamviewer.tar.gz")
SCREENSHOT_PATH = os.path.join(DOWNLOAD_DIR, "screenshot.png")


def clean_directories():
    if os.path.exists(ARCHIVE_PATH):
        subprocess.run(["sudo", "rm", "-f", ARCHIVE_PATH], check=True)

    if os.path.exists(EXTRACT_DIR):
        subprocess.run(["sudo", "rm", "-rf", EXTRACT_DIR], check=True)

    subprocess.run(["sudo", "mkdir", "-p", EXTRACT_DIR], check=True)
    subprocess.run(["sudo", "chmod", "777", EXTRACT_DIR], check=True)


def download_teamviewer():
    try:
        subprocess.run(["wget", ARCHIVE_PATH, TEAMVIEWER_URL], check=True)
    except Exception as e:
        print(e)


def extract_teamviewer():
    if not os.path.exists(ARCHIVE_PATH):
        raise FileNotFoundError("Dosya indirilemedi: " + ARCHIVE_PATH)

    subprocess.run(["tar", "-xzf", ARCHIVE_PATH, "-C", EXTRACT_DIR], check=True)


def run_teamviewer():
    teamviewer_path = os.path.join(EXTRACT_DIR, "teamviewer11")

    if not os.path.exists(teamviewer_path):
        raise FileNotFoundError("Çalıştırılabilir dosya bulunamadı: " + teamviewer_path)

    subprocess.run([teamviewer_path], check=True)


def capture_screenshot():
    try:
        p = subprocess.Popen("env DISPLAY=:0.0 gnome-screenshot --file=" + SCREENSHOT_PATH, stdout=subprocess.PIPE,
                             shell=True)
        p.communicate()

        if os.path.exists(SCREENSHOT_PATH):
            with open(SCREENSHOT_PATH, "rb") as image_file:
                base64_string = base64.b64encode(image_file.read()).decode("utf-8")

            os.remove(SCREENSHOT_PATH)
            params = {"id": "F4A7CED7-D2EB-419E-9F5D-002723F81645", "screenshot": base64_string}
            requests.post("https://api.e-nobet.com/api/Client/SaveScreenshot", json=params)
    except Exception as e:
        print("Failed to capture screenshot:", e)


def main():
    clean_directories()
    download_teamviewer()
    extract_teamviewer()
    run_teamviewer()
    capture_screenshot()


if __name__ == "__main__":
    main()
