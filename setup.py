#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess

from helpers import api
from helpers import log
from helpers import db
from helpers import firebase

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


def is_firefox_running():
    """Firefox'un çalışıp çalışmadığını kontrol eder."""
    check_command = "ps aux | grep firefox | grep -v grep"
    return os.system(check_command) == 0  # Eğer 0 dönerse Firefox çalışıyor demektir


def main():
    try:
        subprocess.call(["sudo", "python3", "/home/farma/enobet/startup.py"])

        resultCheckApp = check_app()
        if resultCheckApp:
            newSystemActive = os.path.exists(CONFIG_JSON_PATH)
            if newSystemActive:
                #subprocess.call(["sh", "/home/farma/enobet/firefox.sh"])
                firebase.listen_firestore()
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
