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


def write_env_file(display, xauthority):
    # Ajan servisi gözetimsiz çalışırken kiosk X oturumuna erişmek için DISPLAY/XAUTHORITY'yi bilmeli.
    # /etc kök yetkisi ister; farma'da parolasız sudo var.
    icerik = "DISPLAY={}\nXAUTHORITY={}\n".format(display, xauthority)
    try:
        _run(["sudo", "mkdir", "-p", os.path.dirname(ENV_FILE)])  # /etc/bek-desk yoksa oluştur
        p = _run(["sudo", "tee", ENV_FILE], input=icerik.encode("utf-8"))
        if p.returncode != 0:
            log.writelog("Ajan ortam dosyası yazılamadı: " + p.stderr.decode("utf-8", "ignore")[:200])
    except Exception as e:
        log.writelog("Ajan ortam dosyası yazılırken hata: " + str(e))


def _tespit_display_xauth():
    # Ajan servisi X oturumunun DIŞINDA (systemd) çalıştığından DISPLAY/XAUTHORITY'yi miras almaz.
    # Doğru değerleri CANLI oturumdan bul: önce Xorg process'inin argümanları (en güvenilir -auth yolu),
    # sonra bu process'in ortamı (setup.py X içinde koşar), en sonda bilinen yollar.
    display = ""
    xauth = ""
    try:
        p = _run(["ps", "-eo", "args"])
        for satir in p.stdout.decode("utf-8", "ignore").splitlines():
            dusuk = satir.lower()
            if ("xorg" in dusuk or "/usr/bin/x " in dusuk or dusuk.startswith("x ")) and "-auth" in satir:
                parcalar = satir.split()
                for t in parcalar:
                    if re.match(r"^:\d+$", t):
                        display = t  # ör. ":0"
                if "-auth" in parcalar:
                    i = parcalar.index("-auth")
                    if i + 1 < len(parcalar):
                        xauth = parcalar[i + 1]  # Xorg'un gerçek yetki dosyası
                break
    except Exception as e:
        log.writelog("X tespiti (ps) hata: " + str(e))
    if not display:
        display = os.environ.get("DISPLAY") or KIOSK_DISPLAY
    if not xauth or not os.path.exists(xauth):
        adaylar = [os.environ.get("XAUTHORITY") or "", KIOSK_XAUTHORITY,
                   "/var/run/lightdm/root/" + display, "/run/user/1000/gdm/Xauthority"]
        xauth = next((a for a in adaylar if a and os.path.exists(a)), KIOSK_XAUTHORITY)
    return display, xauth


def _agent_unit():
    # bekdesk ajanının systemd birim adını bul (.deb'e göre değişebilir); bulunamazsa makul varsayılan.
    try:
        p = _run(["systemctl", "list-unit-files", "--no-legend", "--type=service"])
        for satir in p.stdout.decode("utf-8", "ignore").splitlines():
            parcalar = satir.split()
            if parcalar and "bekdesk" in parcalar[0].lower():
                return parcalar[0]
    except Exception as e:
        log.writelog("Ajan birim adı tespiti hata: " + str(e))
    return "bekdesk-agent.service"


def _env_okundu():
    # Mevcut agent.env içeriği (idempotentlik için; gereksiz restart olmasın). /etc 644 → sudosuz okunur.
    try:
        with open(ENV_FILE, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def repair_agent_display():
    # Ajanın X sunucusuna bağlanabilmesi için DISPLAY/XAUTHORITY'yi canlı oturumdan tespit edip agent.env'e
    # yaz, systemd drop-in ile servise okut ve gerekiyorsa yeniden başlat. Her boot'ta idempotent çalışır:
    # "X11 sunucusuna bağlanılamadı / DISPLAY ayarlı değil" hatasını kalıcı giderir, sahadaki KAYITLI
    # cihazlar da kendiliğinden düzelir. Değerler zaten doğruysa hiçbir şey yapmaz (restart yok).
    if not is_installed():
        return
    try:
        display, xauth = _tespit_display_xauth()
        unit = _agent_unit()
        dropin_dir = "/etc/systemd/system/" + unit + ".d"
        dropin = dropin_dir + "/10-enobet-display.conf"
        istenen_env = "DISPLAY={}\nXAUTHORITY={}\n".format(display, xauth)

        env_dogru = _env_okundu().strip() == istenen_env.strip()
        dropin_var = os.path.exists(dropin)
        if env_dogru and dropin_var:
            return  # zaten doğru; gereksiz yazma/restart yok

        write_env_file(display, xauth)
        if not dropin_var:
            # Servis agent.env'i okumuyorsa drop-in ekle ('-' = dosya yoksa hata verme).
            _run(["sudo", "mkdir", "-p", dropin_dir])
            icerik = "[Service]\nEnvironmentFile=-{}\n".format(ENV_FILE)
            p = _run(["sudo", "tee", dropin], input=icerik.encode("utf-8"))
            if p.returncode != 0:
                log.writelog("systemd drop-in yazılamadı: " + p.stderr.decode("utf-8", "ignore")[:200])
            _run(["sudo", "systemctl", "daemon-reload"])
        _run(["sudo", "systemctl", "restart", unit])
        log.writelog("BEKdesk ekran erişimi onarıldı (DISPLAY=" + display + ", XAUTHORITY=" + xauth + ").")
    except Exception as e:
        log.writelog("BEKdesk ekran onarımı hata: " + str(e))


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


def _client_code_to_machine_id(client_code):
    # /etc/machine-id biçimi: tam 32 küçük harf hex. clientCode sunucuda Cihaz_Id = GUID olduğundan
    # tireleri atıp küçük harfe çevirince tam 32 hex olur → doğrudan machine-id olarak kullanılabilir.
    h = re.sub(r"[^0-9a-fA-F]", "", str(client_code or "")).lower()
    return h if len(h) == 32 else ""


def set_machine_id_from_client(client_code):
    # Kiosk cihazları tek imajdan klonlandığı için /etc/machine-id hepsinde aynı olabilir; sunucu
    # kaydı machine-id'ye göre eşlediğinden ikinci cihaz "zaten kayıtlı" (409) alır. Rastgele üretmek
    # yerine cihazın ZATEN benzersiz kimliği olan clientCode'u (GUID) machine-id yaparız: hem benzersiz
    # hem DETERMİNİSTİK — imaj/kimlik silinse bile aynı id üretilir (sunucuda hayalet cihaz oluşmaz) ve
    # bek-desk machine-id'si ile e-nobet Cihaz_Id'si birebir eşleşir. Yalnız kayıtsız cihazda çağrılır.
    mid = _client_code_to_machine_id(client_code)
    if not mid:
        log.writelog("clientCode GUID'den machine-id uretilemedi; atlandi.")
        return
    try:
        mevcut = ""
        if os.path.exists("/etc/machine-id"):
            with open("/etc/machine-id", "r", encoding="utf-8", errors="ignore") as f:
                mevcut = f.read().strip()
        if mevcut == mid:
            return  # zaten doğru; gereksiz yazma/churn yok.
        _run(["sudo", "rm", "-f", "/var/lib/dbus/machine-id"])
        _run(["sudo", "tee", "/etc/machine-id"], input=(mid + "\n").encode("utf-8"))
        # dbus makine kimliğini /etc/machine-id'den tazele (varsa oradan kopyalar).
        _run(["sudo", "dbus-uuidgen", "--ensure"])
        log.writelog("machine-id clientCode'dan ayarlandi (klon duzeltmesi).")
    except Exception as e:
        log.writelog("machine-id ayarlanamadi: " + str(e))


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
        repair_agent_display()  # Her boot: X erişimini (DISPLAY/XAUTHORITY) onar; kayıtlı cihazlar da düzelir.
        return

    token = api.get_bekdesk_token(client_code)
    if not token:
        log.writelog("BEKdesk token alınamadı; kurulum ertelendi.")
        return

    if not is_installed() and not install_deb():
        log.writelog("BEKdesk ajanı kurulamadı.")
        return

    # Kayıttan ÖNCE: machine-id'yi cihazın benzersiz clientCode'undan (GUID) deterministik olarak ayarla.
    set_machine_id_from_client(client_code)
    set_hostname(short_code)
    display, xauth = _tespit_display_xauth()
    write_env_file(display, xauth)

    log.writelog("BEKdesk ajanı kaydediliyor.")
    # `install` hem kaydolur hem systemd servisini kurup başlatır.
    sonuc = _run(["sudo", "bekdesk-agent", "install", "--server", SERVER, "--token", token])
    if sonuc.returncode == 0:
        log.writelog("BEKdesk ajanı kuruldu.")
        repair_agent_display()  # Yeni servise drop-in + doğru env uygula, X erişimini garanti et.
    else:
        log.writelog("BEKdesk ajan kaydı başarısız: " + sonuc.stderr.decode("utf-8", "ignore")[:200])


if __name__ == "__main__":
    ensure_agent()
