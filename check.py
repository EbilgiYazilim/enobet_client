#! /usr/bin/python
# -*- coding: utf-8 -*-
import subprocess
from datetime import datetime

from helpers import api
from helpers import db
from helpers import log

config = db.read_config_json()
clientCode = config.get("clientCode")
RESTART_TIMES = {"04:00", "08:00", "13:00", "18:00", "23:00"}


def restart_pc():
    subprocess.Popen(
        ["sudo sh /home/farma/enobet/reboot.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    ).communicate()


def get_command_from_server():
    try:
        # Saat kontrolü (PC saati)
        now_str = datetime.now().strftime("%H:%M")
        if now_str in RESTART_TIMES:
            log.writelog(f"Zamanlanan restart ({now_str}) tetiklendi.")
            restart_pc()
            return  # Zamanlı restart yapıldıysa başka komut çalıştırma

        check_internet = api.get_connection_status()
        if check_internet:
            commandId, commandText = api.get_command(clientCode)
            if commandId < 1:
                return

            if commandId == 1:
                restart_pc()
            elif commandId == 2:
                subprocess.Popen(["python3", "/home/farma/enobet/teamviewer.py"], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            elif commandId == 3:
                subprocess.run(commandText, shell=True, check=True)
            else:
                log.writelog("unknown command")
        else:
            restart_pc()
    except Exception as e:
        log.writelog("get_command_from_server hata oluştu: " + str(e))


if __name__ == "__main__":
    get_command_from_server()
