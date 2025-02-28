#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

from helpers import api
from helpers import log
from helpers import db

MASTER_PATH = "/home/farma/enobet/"
CONFIG_INI_PATH = "/home/farma/nobet_ekran/config.ini"
CONFIG_JSON_PATH = os.path.join(MASTER_PATH, "config.json")
VERSION_URL = "https://cdn.e-nobet.com/updates/version.json"
RC_LOCAL_PATH = "/etc/rc.local"
GIT_REPO = "https://github.com/EbilgiYazilim/enobet_client.git"


def check_app():
    try:
        log.writelog("Uygulama kontrolü yapılıyor.")

        if not os.path.exists(os.path.join(MASTER_PATH, ".git")):
            log.writelog("Uygulama bulunamadı, ana dizin siliniyor.")
            shutil.rmtree(MASTER_PATH)
            log.writelog("Uygulama klonlanıyor.")
            subprocess.call(["git", "clone", GIT_REPO, MASTER_PATH])
            log.writelog("Uygulama klonlandı.")
            return True
        else:
            log.writelog("Güncellemeler kontrol ediliyor.")
            os.chdir(MASTER_PATH)
            # subprocess.call(["git", "reset", "--hard", "origin/main"])  # Yerel değişiklikleri sıfırla
            subprocess.call(["git", "pull", "origin", "main"])  # Güncellemeleri al
            log.writelog("Güncellemeler tamamlandı.")
            return True
    except Exception as e:
        log.writelog("Uygulama kontrolünde hata oluştu: " + str(e))
        return False


def add_to_startup():
    try:
        log.writelog("Açılış komutları kontrol ediliyor.")
        # Eklenmesi gereken komutlar
        startup_commands = [
            "sh /home/farma/setup.sh &\n"
        ]

        # Mevcut /etc/rc.local içeriğini oku
        with open(RC_LOCAL_PATH, "r") as file:
            lines = file.readlines()

        # Komutların olup olmadığını kontrol et
        updated = False
        for command in startup_commands:
            if command not in "".join(lines):
                updated = True

        # Eğer eksik komut varsa güncelle
        if updated:
            with open(RC_LOCAL_PATH, "w") as file:
                for line in lines:
                    if line.strip() == "exit 0":
                        # exit 0'dan önce başlatma komutlarını ekle
                        for command in startup_commands:
                            if command not in "".join(lines):
                                file.write(command)
                    file.write(line)

            log.writelog("Açılışa komutları eklendi.")

        log.writelog("Açılışa komutları kontrol edildi.")
    except Exception as e:
        log.writelog("Açılışa komutları eklenemedi: " + str(e))


def main():
    try:
        add_to_startup()
        resultCheckApp = check_app()
        if resultCheckApp:
            newSystemActive = os.path.exists(CONFIG_JSON_PATH)
            if newSystemActive:
                subprocess.call(["python3", "/home/farma/enobet/nobet.py"])
            else:
                crm_id = db.get_crm_id(CONFIG_INI_PATH)
                if crm_id > 0:
                    resultShortCode = api.get_short_code(str(crm_id))
                    if len(resultShortCode) == 4:
                        db.write_config_json(crm_id, resultShortCode, CONFIG_JSON_PATH)
                    else:
                        log.writelog("Kısa kod alınamadı lütfen daha sonra tekrar deneyiniz.")
                else:
                    log.writelog("Dönen crm_id:" + str(crm_id))
        else:
            log.writelog("Uygulama kontrolünde hata oluştu.")
    except Exception as e:
        log.writelog("Teknik bir hata meydana geldi: " + str(e))


if __name__ == "__main__":
    main()
