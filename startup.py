#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
from helpers import log

MASTER_PATH = "/home/farma/enobet/"
CONFIG_INI_PATH = "/home/farma/nobet_ekran/config.ini"
CONFIG_JSON_PATH = os.path.join(MASTER_PATH, "config.json")
VERSION_URL = "https://cdn.e-nobet.com/updates/version.json"
RC_LOCAL_PATH = "/etc/rc.local"
GIT_REPO = "https://github.com/EbilgiYazilim/enobet_client.git"


def add_to_startup():
    try:
        log.writelog("Açılış komutları kontrol ediliyor.")
        # Eklenmesi gereken komutlar
        startup_commands = [
            "sh /home/farma/changeSystem.sh &\n"
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


if __name__ == "__main__":
    add_to_startup()
