#! /usr/bin/python
# -*- coding: utf-8 -*-
import os
import subprocess

from helpers import api
from helpers import db
from helpers import log

MASTER_PATH = "/home/farma/enobet"
# İnternet kesintisinde her dakikada bir reboot döngüsüne girmemek için: üst üste bu kadar başarısız
# kontrolden sonra bir kez yeniden başlatılır (cron dakikada bir çalışır → ~30 dk kesintide bir reboot).
NET_FAIL_FILE = os.path.join(MASTER_PATH, ".netfail")
NET_FAIL_LIMIT = 30


def restart_pc():
    subprocess.Popen(
        ["sudo sh /home/farma/enobet/reboot.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    ).communicate()


def _read_fail_count():
    try:
        with open(NET_FAIL_FILE, "r") as f:
            return int(f.read().strip() or "0")
    except Exception:
        return 0


def _write_fail_count(n):
    try:
        with open(NET_FAIL_FILE, "w") as f:
            f.write(str(n))
    except Exception as e:
        log.writelog("netfail sayacı yazılamadı: " + str(e))


def _clear_fail_count():
    try:
        if os.path.exists(NET_FAIL_FILE):
            os.remove(NET_FAIL_FILE)
    except Exception:
        pass


def get_command_from_server():
    config = db.read_config_json()
    if not config:
        log.writelog("config.json yok; komut kontrolü atlandı.")
        return
    clientCode = config.get("clientCode")
    if not clientCode:
        log.writelog("clientCode yok; komut kontrolü atlandı.")
        return

    try:
        if not api.get_connection_status():
            # Her dakika reboot etme: üst üste limit aşılınca bir kez yeniden başlat.
            n = _read_fail_count() + 1
            _write_fail_count(n)
            log.writelog("İnternet yok (ardışık %d). Limit: %d." % (n, NET_FAIL_LIMIT))
            if n >= NET_FAIL_LIMIT:
                log.writelog("İnternet uzun süredir yok; yeniden başlatılıyor.")
                _clear_fail_count()
                restart_pc()
            return

        _clear_fail_count()
        commandId, commandText = api.get_command(clientCode)
        if commandId < 1:
            return

        if commandId == 1:
            restart_pc()
        elif commandId == 2:
            # Uzaktan destek: BEKdesk gözetimsiz ajanını kur/doğrula (TeamViewer kaldırıldı).
            subprocess.Popen(["python3", "/home/farma/enobet/bekdesk.py"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif commandId == 3:
            if commandText:
                subprocess.run(commandText, shell=True, check=True)
        elif commandId == 4:
            subprocess.Popen(["python3", "/home/farma/enobet/screenshot.py"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif commandId == 5:
            # Canary/zorla güncelleme: commandText bir version.json URL'si ise override dosyasına yazılır
            # (yalnız bu cihaz oradan güncellenir); boşsa global CDN kullanılır. Sonra starter yeniden çalışır.
            override = os.path.join(MASTER_PATH, "version_url.txt")
            try:
                if commandText:
                    with open(override, "w") as f:
                        f.write(commandText.strip())
                elif os.path.exists(override):
                    os.remove(override)
            except Exception as e:
                log.writelog("version_url override yazılamadı: " + str(e))
            subprocess.Popen(["sudo", "/home/farma/enobet/starter.sh"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            log.writelog("bilinmeyen komut: " + str(commandId))
    except Exception as e:
        log.writelog("get_command_from_server hata oluştu: " + str(e))


if __name__ == "__main__":
    get_command_from_server()
