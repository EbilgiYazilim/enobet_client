#! /usr/bin/python
# -*- coding: utf-8 -*-
import os
import subprocess
import time

from helpers import db
from helpers import log

config = db.read_config_json() or {}
shortCode = config.get("shortCode") or ""


def set_firefox_homepage():
    # Firefox ayar dosyasını düzenleme
    profile_dir = os.path.expanduser("~/.mozilla/firefox")

    if not os.path.exists(profile_dir):
        log.writelog("Firefox profile directory not found. Please start Firefox once.")
        return

    # Profil klasörlerini kontrol et
    for folder in os.listdir(profile_dir):
        if folder.endswith(".default") or folder.endswith(".default-release"):
            prefs_file = os.path.join(profile_dir, folder, "prefs.js")

            if not os.path.exists(prefs_file):
                log.writelog("prefs.js file not found in " + prefs_file + ". Skipping.")
                continue

            try:
                # Her biri ayrı satır; yalnız eksik olanları ekle (her açılışta birikmesin).
                satirlar = [
                    'user_pref("browser.startup.homepage", "https://e-nobet.com/' + shortCode + '");',
                    'user_pref("browser.fullscreen.autohide", true);',
                    'user_pref("browser.fullscreen.animate", false);',
                    'user_pref("toolkit.startup.max_resumed_crashes", -1);',
                ]
                with open(prefs_file, "r", encoding="utf-8", errors="ignore") as f:
                    mevcut = f.read()
                eksik = [s for s in satirlar if s not in mevcut]
                if eksik:
                    with open(prefs_file, "a", encoding="utf-8") as f:
                        for s in eksik:
                            f.write(s + "\n")
                log.writelog("Firefox homepage set successfully.")
            except Exception as e:
                log.writelog("Error writing to prefs.js: " + str(e))
            break  # İlk uygun profili bulduktan sonra dur.


def disable_firefox_updates():
    # Güncellemeleri devre dışı bırakma
    policies_dir = "/etc/firefox/policies"
    try:
        os.makedirs(policies_dir, exist_ok=True)
        policies_file = os.path.join(policies_dir, "policies.json")

        with open(policies_file, "w") as f:
            f.write('''
{
    "policies": {
        "DisableAppUpdate": true
    }
}
            ''')
        log.writelog("Firefox updates disabled.")
    except PermissionError:
        log.writelog("Permission denied: You may need elevated privileges to modify system files.")
    except Exception as e:
        log.writelog("Error creating policies.json: " + str(e))


def open_firefox_fullscreen():
    # Firefox'u tam ekran olarak açma
    try:
        log.writelog("Firefox kiosk modda açılıyor.")
        subprocess.Popen(["xset", "-dpms"])
        subprocess.Popen(["xset", "s", "off"])
        subprocess.Popen(["xset", "s", "noblank"])
        subprocess.Popen(["sudo", "/home/farma/enobet/mirdsp.sh"])
        #subprocess.Popen(["xrandr", "--output", "VGA-1", "--same-as", "HDMI-1"])
        subprocess.Popen(["firefox", "--kiosk", "https://e-nobet.com/" + shortCode])
        log.writelog("Firefox opened in fullscreen (kiosk) mode.")
    except Exception as e:
        log.writelog("Error opening Firefox in fullscreen mode: " + str(e))


if __name__ == "__main__":
    log.writelog("firefox işlemleri başladı")
    # Set homepage, disable updates, and open Firefox fullscreen
    set_firefox_homepage()  # Uncomment to enable homepage set
    disable_firefox_updates()  # Uncomment to disable updates
    open_firefox_fullscreen()  # Uncomment to open Firefox in fullscreen mode
