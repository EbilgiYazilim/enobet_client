#! /usr/bin/python
# -*- coding: utf-8 -*-
import os
import subprocess
import time

from helpers import api
from helpers import db
from helpers import log

config = db.read_config_json()
clientCode = config.get("clientCode")


def get_command_from_server():
    flagNdx = 1
    while True:
        try:
            check_internet = api.get_connection_status()
            if check_internet:
                commandId, commandText = api.get_command(clientCode)
                if commandId < 1:
                    return

                # Reboot PC
                if commandId == 1:
                    subprocess.Popen(["sudo sh /home/farma/enobet/reboot.sh"], stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, shell=True).communicate()
                # Open Teamviewer
                elif commandId == 2:
                    os.system("nohup sh /home/farma/enobet/teamviewer.sh &")
                # Run Command
                elif commandId == 3:
                    subprocess.run(commandText, shell=True, check=True)
                else:
                    log.writelog("unknown command")
            else:
                if flagNdx > 3:
                    subprocess.Popen(["sudo sh /home/farma/enobet/reboot.sh"], stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, shell=True).communicate()
                else:
                    flagNdx = flagNdx + 1
        except Exception as e:
            print(e)

        time.sleep(60)
