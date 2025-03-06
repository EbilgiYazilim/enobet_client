#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import shutil
import subprocess

from helpers import api
from helpers import log
from helpers import db
from helpers import ping

MASTER_PATH = "/home/farma/enobet/"
CONFIG_INI_PATH = "/home/farma/nobet_ekran/config.ini"
CONFIG_JSON_PATH = os.path.join(MASTER_PATH, "config.json")
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
    result = subprocess.run(["pgrep", "-f", "firefox"], stdout=subprocess.PIPE)
    return result.returncode == 0


def set_resolution_for_all_displays():
    try:
        xrandr_output = subprocess.check_output("xrandr", shell=True).decode("utf-8")
        connected_displays = re.findall(r"(\S+) connected", xrandr_output)

        if not connected_displays:
            log.writelog("Bağlı ekran bulunamadı!")
            return

        for display in connected_displays:
            subprocess.run("xrandr --output " + display + " --mode 1280x720", shell=True, check=True)

    except Exception as e:
        log.writelog("Ekran çözünürlükleri ayarlanırken hata oluştu:" + str(e))


def main():
    try:
        log.writelog("Uygulama başladı.")
        set_resolution_for_all_displays()

        if is_firefox_running():
            return

        newSystemActive = os.path.exists(CONFIG_JSON_PATH)
        if newSystemActive:
            subprocess.Popen(["python3", "/home/farma/enobet/nobet.py"], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            log.writelog("Firefox açıldı, komutlar için server dinleniyor.")
            ping.get_command_from_server()
        else:
            if os.path.exists("/home/farma/enobet/wallpaper.png"):
                shutil.move("/home/farma/enobet/wallpaper.png", "/home/farma/wallpaper.png")

            crm_id = db.get_crm_id(CONFIG_INI_PATH)
            if crm_id > 0:
                resultShortCode = api.get_short_code(str(crm_id))
                if len(resultShortCode) == 4:
                    resultClientCode = api.get_client_code(resultShortCode)
                    if len(resultClientCode) > 10:
                        db.write_config_json(crm_id, resultShortCode, resultClientCode, CONFIG_JSON_PATH)

                        # region nobet_ekran_starter güncellemesi
                        nobet_ekran_starter = "/home/farma/.config/openbox/nobet_ekran_starter.sh"
                        new_script_content = """
#!/bin/bash                
sh ~/.fehbg &
sudo chmod -R +x /home/farma/enobet/
sudo chmod -R 777 /home/farma/enobet/
/home/farma/enobet/starter.sh
"""

                        # Dosyanın içeriğini değiştir
                        with open(nobet_ekran_starter, "w") as file:
                            file.write(new_script_content)
                        # endregion

                        # region Eski sistem klasörünün adını değiştir
                        old_folder = "/home/farma/nobet_ekran"
                        new_folder = "/home/farma/eski_nobet_ekran"
                        os.rename(old_folder, new_folder)
                        # endregion

                        # region Crontab'ı temizler
                        os.system("crontab -r")
                        # endregion

                        log.writelog("Yeni sisteme geçiş tamamlandı.")
                        print("Yeni sisteme geçiş tamamlandı.")
                    else:
                        log.writelog("Client kod alınamadı lütfen daha sonra tekrar deneyiniz.")
                else:
                    log.writelog("Kısa kod alınamadı lütfen daha sonra tekrar deneyiniz.")
            else:
                log.writelog("Dönen crm_id:" + str(crm_id))

    except Exception as e:
        log.writelog("Teknik bir hata meydana geldi: " + str(e))


if __name__ == "__main__":
    main()
