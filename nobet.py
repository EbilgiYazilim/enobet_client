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
                # Kiosk sağlamlaştırma: Chromium kiosk bayraklarının Firefox karşılıkları.
                satirlar = [
                    'user_pref("browser.startup.homepage", "https://e-nobet.com/' + shortCode + '");',
                    'user_pref("browser.fullscreen.autohide", true);',
                    'user_pref("browser.fullscreen.animate", false);',
                    'user_pref("toolkit.startup.max_resumed_crashes", -1);',
                    # Çökme/oturum geri yükleme balonu ve ilk-çalıştırma sayfası kapalı.
                    'user_pref("browser.sessionstore.resume_from_crash", false);',
                    'user_pref("browser.shell.checkDefaultBrowser", false);',
                    'user_pref("browser.startup.homepage_override.mstone", "ignore");',
                    # Disk + medya önbelleği ~150 MB (akıllı boyut kapalı, sabit kapasite).
                    'user_pref("browser.cache.disk.enable", true);',
                    'user_pref("browser.cache.disk.smart_size.enabled", false);',
                    'user_pref("browser.cache.disk.capacity", 153600);',
                    'user_pref("media.cache_size", 153600);',
                    # Parola kaydı, bildirim, hesap senkronu kapalı.
                    'user_pref("signon.rememberSignons", false);',
                    'user_pref("dom.webnotifications.enabled", false);',
                    'user_pref("permissions.default.desktop-notification", 2);',
                    'user_pref("identity.fxaccounts.enabled", false);',
                    # Arka plan ağ trafiği: telemetri, prefetch, arama güncellemesi kapalı.
                    'user_pref("toolkit.telemetry.enabled", false);',
                    'user_pref("datareporting.healthreport.uploadEnabled", false);',
                    'user_pref("datareporting.policy.dataSubmissionEnabled", false);',
                    'user_pref("app.update.enabled", false);',
                    'user_pref("app.update.auto", false);',
                    'user_pref("extensions.update.enabled", false);',
                    'user_pref("network.prefetch-next", false);',
                    'user_pref("browser.search.update", false);',
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
        "DisableAppUpdate": true,
        "DisableFirefoxAccounts": true,
        "DisableTelemetry": true,
        "DisableFirefoxStudies": true,
        "OfferToSaveLogins": false,
        "DisablePocket": true,
        "DontCheckDefaultBrowser": true,
        "OverrideFirstRunPage": "",
        "OverridePostUpdatePage": "",
        "DisableProfileImport": true,
        "ExtensionUpdate": false,
        "Permissions": { "Notifications": { "BlockNewRequests": true } }
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
