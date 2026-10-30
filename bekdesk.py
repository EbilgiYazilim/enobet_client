#! /usr/bin/python
# -*- coding: utf-8 -*-
"""BEKdesk gözetimsiz (unattended) ajan kurulumu. TeamViewer'ın yerini alır.

Akış: token sunucudan alınır (repoda sabit tutulmaz) -> .deb indirilir/kurulur -> `bekdesk agent install`
ile kaydolur. Zaten kayıtlıysa tekrar kaydetmez. Teknisyen BEKdesk konsolundan parolasız bağlanır.
"""
import os
import re
import subprocess

from helpers import api
from helpers import db
from helpers import log

SERVER = "https://desk.bek.org.tr"
DEB_URL = SERVER + "/download/BEKDesk.deb"
DEB_PATH = "/home/farma/enobet/BEKDesk.deb"


def _run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


def is_installed():
    return _run(["which", "bekdesk"]).returncode == 0


def is_enrolled():
    if not is_installed():
        return False
    # `agent status` kayıt yoksa sıfırdan farklı döner.
    return _run(["bekdesk", "agent", "status"]).returncode == 0


def install_deb():
    log.writelog("BEKdesk .deb indiriliyor.")
    if _run(["wget", "-q", "-O", DEB_PATH, DEB_URL]).returncode != 0:
        log.writelog("BEKdesk .deb indirilemedi.")
        return False
    # Bağımlılıkları da çözmesi için apt ile kur; dpkg eksik bağımlılıkta patlayabilir.
    if _run(["sudo", "apt-get", "install", "-y", DEB_PATH]).returncode != 0:
        _run(["sudo", "dpkg", "-i", DEB_PATH])
        _run(["sudo", "apt-get", "install", "-f", "-y"])
    return is_installed()


def set_hostname(short_code):
    # Konsolda kolay bulunması için sabit, güvenli bir ad: enobet-<shortCode>.
    if not short_code:
        return
    ad = "enobet-" + re.sub(r"[^A-Za-z0-9-]", "", str(short_code))
    try:
        mevcut = _run(["hostname"]).stdout.decode("utf-8", "ignore").strip()
        if mevcut != ad:
            _run(["sudo", "hostnamectl", "set-hostname", ad])
            log.writelog("Hostname ayarlandı: " + ad)
    except Exception as e:
        log.writelog("Hostname ayarlanamadı: " + str(e))


def ensure_agent():
    config = db.read_config_json()
    if not config:
        log.writelog("config.json yok; BEKdesk kurulumu atlandı.")
        return
    client_code = config.get("clientCode")
    short_code = config.get("shortCode")

    if is_enrolled():
        log.writelog("BEKdesk ajanı zaten kayıtlı.")
        return

    token = api.get_bekdesk_token(client_code)
    if not token:
        log.writelog("BEKdesk token alınamadı; kurulum ertelendi.")
        return

    if not is_installed() and not install_deb():
        log.writelog("BEKdesk kurulamadı.")
        return

    set_hostname(short_code)

    log.writelog("BEKdesk ajanı kaydediliyor.")
    sonuc = _run(["sudo", "bekdesk", "agent", "install", "--server", SERVER, "--token", token])
    if sonuc.returncode == 0:
        log.writelog("BEKdesk ajanı kuruldu.")
    else:
        log.writelog("BEKdesk ajan kaydı başarısız: " + sonuc.stderr.decode("utf-8", "ignore")[:200])


if __name__ == "__main__":
    ensure_agent()
