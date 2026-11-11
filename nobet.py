#! /usr/bin/python
# -*- coding: utf-8 -*-
import os
import shutil
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
                    # Oturum geri yükleme tamamen kapalı: açılışta eski sekmeler geri gelmesin,
                    # kiosk URL'inin üstüne çift sekme oluşmasın. (startup.page 0 = boş; kiosk URL yine açılır)
                    'user_pref("browser.startup.page", 0);',
                    'user_pref("browser.sessionstore.max_resumed_crashes", 0);',
                    'user_pref("browser.sessionstore.resume_session_once", false);',
                    # Geçmiş: "Never remember history" = kalıcı gizli mod. Oturum/geçmiş hiç kaydolmaz;
                    # çift sekme fix'ini de pekiştirir. Not: disk cache ve bazı service worker'lar devre dışı kalabilir.
                    'user_pref("browser.privatebrowsing.autostart", true);',
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


def disable_crash_reporter():
    # Ubuntu apport ("System program problem detected" / "Linux system report") penceresi
    # bir program cokunce /var/crash altina dosya yazip acilista bu diyalogu kiosk ekranin
    # ONUNE getiriyordu. Servisi tamamen kapat, otomatik raporu kapat, bekleyen raporlari
    # sil ve o an acik bir diyalog varsa oldur -> bu pencere bir daha hic cikmasin.
    komutlar = [
        ["sudo", "systemctl", "stop", "apport.service"],
        ["sudo", "systemctl", "disable", "apport.service"],
        ["sudo", "systemctl", "mask", "apport.service"],
        # /etc/default/apport -> enabled=0 (root gerektirir; sudo tee ile yaz).
        ["sudo", "bash", "-c", "echo enabled=0 > /etc/default/apport"],
        # Bekleyen cokme raporlarini temizle (yoksa sorun degil).
        ["sudo", "bash", "-c", "rm -f /var/crash/*"],
        # Bu boot'ta hali hazirda acik olan apport diyalogunu kapat.
        ["pkill", "-f", "apport"],
    ]
    for komut in komutlar:
        try:
            subprocess.call(komut)
        except Exception as e:
            log.writelog("apport kapatma adimi basarisiz (" + " ".join(komut) + "): " + str(e))
    log.writelog("apport (cokme raporlayici) devre disi birakildi.")


def enable_firefox_always_on_top():
    # Apport disinda baska bir uyari penceresi cikarsa (guncelleme, hata diyalogu) kiosk
    # Firefox'un arkasinda kalsin diye openbox'a "Firefox her zaman en ustte" kurali ekle.
    # Idempotent: ayni kural iki kez eklenmez. Hata halinde sessizce gec, Firefox yine acilir.
    rc = os.path.expanduser("~/.config/openbox/rc.xml")
    if not os.path.exists(rc):
        log.writelog("openbox rc.xml bulunamadi, always-on-top atlandi: " + rc)
        return
    try:
        with open(rc, "r", encoding="utf-8", errors="ignore") as f:
            icerik = f.read()
        if "e-nobet-firefox-ontop" in icerik:
            return  # kural zaten mevcut
        kural = (
            "    <!-- e-nobet-firefox-ontop: kiosk Firefox her zaman en ustte -->\n"
            "    <application class=\"*irefox*\">\n"
            "      <focus>yes</focus>\n"
            "      <layer>above</layer>\n"
            "      <fullscreen>yes</fullscreen>\n"
            "    </application>\n"
        )
        if "</applications>" in icerik:
            icerik = icerik.replace("</applications>", kural + "  </applications>", 1)
        elif "</openbox_config>" in icerik:
            icerik = icerik.replace(
                "</openbox_config>",
                "  <applications>\n" + kural + "  </applications>\n</openbox_config>",
                1,
            )
        else:
            icerik = icerik + "\n  <applications>\n" + kural + "  </applications>\n"
        with open(rc, "w", encoding="utf-8") as f:
            f.write(icerik)
        # Calisan openbox'a kurali hemen yeniden yuklet (DISPLAY yoksa sonraki boot'ta etkin olur).
        try:
            subprocess.call(["openbox", "--reconfigure"])
        except Exception:
            pass
        log.writelog("Firefox always-on-top openbox kurali eklendi.")
    except Exception as e:
        log.writelog("always-on-top kurali eklenemedi: " + str(e))


def clear_firefox_session():
    # Açılıştan önce önceki (çoğu zaman temiz olmayan) kapanıştan kalan oturumu sil.
    # pkill/güç kesintisi sonrası Firefox sekmeleri sessionstore'a yazar; sonraki açılışta
    # bunları geri yükler VE komut satırındaki kiosk URL'ini de açar -> çift sekme.
    # Bu dosyaları silince her boot'ta tek sekme garantilenir (prefs ile birlikte çift koruma).
    profile_dir = os.path.expanduser("~/.mozilla/firefox")
    if not os.path.exists(profile_dir):
        return
    hedef_dosyalar = ["sessionstore.jsonlz4", "sessionCheckpoints.json", "recovery.jsonlz4"]
    for folder in os.listdir(profile_dir):
        if folder.endswith(".default") or folder.endswith(".default-release"):
            prof = os.path.join(profile_dir, folder)
            for ad in hedef_dosyalar:
                try:
                    yol = os.path.join(prof, ad)
                    if os.path.exists(yol):
                        os.remove(yol)
                except Exception as e:
                    log.writelog("Oturum dosyasi silinemedi (" + ad + "): " + str(e))
            try:
                yedek = os.path.join(prof, "sessionstore-backups")
                if os.path.isdir(yedek):
                    shutil.rmtree(yedek, ignore_errors=True)
            except Exception as e:
                log.writelog("sessionstore-backups silinemedi: " + str(e))
            break  # İlk uygun profil (set_firefox_homepage ile aynı seçim).
    log.writelog("Firefox oturumu temizlendi (cift sekme onleme).")


def open_firefox_fullscreen():
    # Firefox'u tam ekran olarak açma
    try:
        log.writelog("Firefox kiosk modda açılıyor.")
        subprocess.Popen(["xset", "-dpms"])
        subprocess.Popen(["xset", "s", "off"])
        subprocess.Popen(["xset", "s", "noblank"])
        subprocess.Popen(["sudo", "/home/farma/enobet/mirdsp.sh"])
        #subprocess.Popen(["xrandr", "--output", "VGA-1", "--same-as", "HDMI-1"])
        clear_firefox_session()  # çift sekme önleme: kalan oturumu sil, sonra tek sekme aç
        subprocess.Popen(["firefox", "--kiosk", "https://e-nobet.com/" + shortCode])
        log.writelog("Firefox opened in fullscreen (kiosk) mode.")
    except Exception as e:
        log.writelog("Error opening Firefox in fullscreen mode: " + str(e))


if __name__ == "__main__":
    log.writelog("firefox işlemleri başladı")
    # Set homepage, disable updates, and open Firefox fullscreen
    set_firefox_homepage()  # Uncomment to enable homepage set
    disable_firefox_updates()  # Uncomment to disable updates
    disable_crash_reporter()  # apport "Linux system report" penceresini kalici kapat
    enable_firefox_always_on_top()  # Firefox'u her zaman en ustte tut (uyari pencereleri arkada kalsin)
    open_firefox_fullscreen()  # Uncomment to open Firefox in fullscreen mode
