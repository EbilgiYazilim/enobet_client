#! /usr/bin/python
# -*- coding: utf-8 -*-
"""BEKdesk gözetimsiz (unattended) headless ajan kurulumu. TeamViewer'ın yerini alır.

Cihaz filosu Ubuntu 16.04 (X11 kiosk) olduğundan, masaüstü (Tauri/webkit) paketi değil, BEK'in
**headless ajan** paketi (`bekdesk-agent`, GUI/webkit yok, eski glibc uyumlu) kurulur. Akış: token
sunucudan alınır (repoda sabit tutulmaz) -> .deb indirilir/kurulur -> kiosk X erişimi için ortam dosyası
yazılır -> `bekdesk-agent install` ile kaydolur ve systemd servisi kurulur. Zaten kayıtlıysa tekrar
kaydetmez. Teknisyen BEKdesk konsolundan parolasız bağlanır.
"""
import os
import re
import subprocess

from helpers import api
from helpers import db
from helpers import log

SERVER = "https://desk.bek.org.tr"
DEB_URL = SERVER + "/download/bekdesk-agent-linux.deb"
DEB_PATH = "/home/farma/enobet/bekdesk-agent.deb"
# Kiosk X oturumuna (DISPLAY :0, farma kullanıcısı) bağlanabilmesi için ajan servisinin okuduğu ortam dosyası.
ENV_FILE = "/etc/bek-desk/agent.env"
KIOSK_DISPLAY = ":0"
KIOSK_XAUTHORITY = "/home/farma/.Xauthority"


def _run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)


def is_installed():
    return _run(["which", "bekdesk-agent"]).returncode == 0


def is_enrolled():
    if not is_installed():
        return False
    # `status` kayıt yoksa sıfırdan farklı döner.
    return _run(["bekdesk-agent", "status"]).returncode == 0


def _deb_gecerli():
    # 0 bayt / bozuk indirme (CDN negatif önbellek, kesik aktarım) kuruluma gitmesin.
    try:
        if os.path.getsize(DEB_PATH) < 100000:
            return False
        with open(DEB_PATH, "rb") as f:
            return f.read(8).startswith(b"!<arch>")
    except OSError:
        return False


def install_deb():
    log.writelog("BEKdesk ajanı (.deb) indiriliyor.")
    # wget HTTP hatasında sıfırdan farklı döner; ama boş gövdeyle 200 gelirse 0 döner → ayrıca boyut/sihir denetle.
    if _run(["wget", "-q", "-O", DEB_PATH, DEB_URL]).returncode != 0 or not _deb_gecerli():
        boyut = os.path.getsize(DEB_PATH) if os.path.exists(DEB_PATH) else 0
        log.writelog("BEKdesk .deb gecersiz/eksik indi (%d bayt); kurulum atlandi, sonra tekrar denenecek." % boyut)
        return False
    # Bağımlılıkları da çözmesi için apt ile kur; dpkg eksik bağımlılıkta patlayabilir.
    if _run(["sudo", "apt-get", "install", "-y", DEB_PATH]).returncode != 0:
        _run(["sudo", "dpkg", "-i", DEB_PATH])
        _run(["sudo", "apt-get", "install", "-f", "-y"])
    return is_installed()


def write_env_file():
    # Ajan servisi gözetimsiz çalışırken kiosk X oturumuna erişmek için DISPLAY/XAUTHORITY'yi bilmeli.
    # /etc kök yetkisi ister; farma'da parolasız sudo var.
    icerik = "DISPLAY={}\nXAUTHORITY={}\n".format(KIOSK_DISPLAY, KIOSK_XAUTHORITY)
    try:
        p = _run(["sudo", "tee", ENV_FILE], input=icerik.encode("utf-8"))
        if p.returncode != 0:
            log.writelog("Ajan ortam dosyası yazılamadı: " + p.stderr.decode("utf-8", "ignore")[:200])
    except Exception as e:
        log.writelog("Ajan ortam dosyası yazılırken hata: " + str(e))


def ensure_hosts_entry(ad):
    # hostnamectl /etc/hosts'u güncellemez; 127.0.1.1 <ad> yoksa ekle. Yoksa ad çözümlemesi (getaddrinfo)
    # takılır ve ajan `error sending request` ile kayıt olamaz (manuel testte yaşandı).
    try:
        with open("/etc/hosts", "r", encoding="utf-8", errors="ignore") as f:
            mevcut = f.read()
        if ("127.0.1.1 " + ad) in mevcut:
            return
        p = _run(["sudo", "tee", "-a", "/etc/hosts"], input=("127.0.1.1 " + ad + "\n").encode("utf-8"))
        if p.returncode != 0:
            log.writelog("/etc/hosts guncellenemedi: " + p.stderr.decode("utf-8", "ignore")[:200])
    except Exception as e:
        log.writelog("/etc/hosts kontrolunde hata: " + str(e))


def ensure_unique_machine_id():
    # Kiosk cihazları tek imajdan klonlandığı için /etc/machine-id hepsinde aynı olabilir; sunucu
    # kaydı machine-id'ye göre eşlediğinden ikinci cihaz "zaten kayıtlı" (409) alır. Cihaz başına
    # BİR KEZ (işaret dosyası) benzersiz machine-id üret. Yalnız kayıtsız cihazda çağrılır.
    marker = "/home/farma/enobet/.machineid_fixed"
    if os.path.exists(marker):
        return
    try:
        _run(["sudo", "rm", "-f", "/etc/machine-id", "/var/lib/dbus/machine-id"])
        if _run(["sudo", "systemd-machine-id-setup"]).returncode != 0:
            # systemd-machine-id-setup yoksa UUID'den 32 hex yaz.
            yeni = _run(["cat", "/proc/sys/kernel/random/uuid"]).stdout.decode("utf-8", "ignore")
            yeni = re.sub(r"[^0-9a-f]", "", yeni.lower())[:32]
            _run(["sudo", "tee", "/etc/machine-id"], input=(yeni + "\n").encode("utf-8"))
        _run(["sudo", "dbus-uuidgen", "--ensure"])
        open(marker, "w").close()
        log.writelog("machine-id benzersiz olarak yeniden uretildi (klon duzeltmesi).")
    except Exception as e:
        log.writelog("machine-id yenilenemedi: " + str(e))


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
        # Ad değişmese de /etc/hosts satırını garanti et (eski kurulumlarda eksik olabilir).
        ensure_hosts_entry(ad)
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
        log.writelog("BEKdesk ajanı kurulamadı.")
        return

    # Kayıttan ÖNCE: klon imajlardan gelen yinelenen machine-id'yi benzersiz yap (bir kez).
    ensure_unique_machine_id()
    set_hostname(short_code)
    write_env_file()

    log.writelog("BEKdesk ajanı kaydediliyor.")
    # `install` hem kaydolur hem systemd servisini kurup başlatır.
    sonuc = _run(["sudo", "bekdesk-agent", "install", "--server", SERVER, "--token", token])
    if sonuc.returncode == 0:
        log.writelog("BEKdesk ajanı kuruldu.")
    else:
        log.writelog("BEKdesk ajan kaydı başarısız: " + sonuc.stderr.decode("utf-8", "ignore")[:200])


if __name__ == "__main__":
    ensure_agent()
