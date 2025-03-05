#! /usr/bin/python
# -*- coding: utf-8 -*-
import os
import subprocess
import requests
import time
import json

from helpers import db
from helpers import log


def get_firestore_documents():
    config = db.read_config_json()
    clientCode = config.get("clientCode")

    BASE_URL = ("https://firestore.googleapis.com/v1/projects/nobetekranlari/databases/("
                "default)/documents/Clients/" + clientCode + "/ClientCommands/")

    response = requests.get(BASE_URL)
    if response.status_code == 200:
        return response.json().get("documents", [])
    return []


def listen_firestore(interval=10):
    log.writelog("firebase dinlemesi başladı.")

    config = db.read_config_json()
    clientCode = config.get("clientCode")

    BASE_URL = ("https://firestore.googleapis.com/v1/projects/nobetekranlari/databases/("
                "default)/documents/Clients/" + clientCode + "/ClientCommands/")

    while True:
        try:
            docs = get_firestore_documents()
            if docs:
                latest_doc = docs[-1]
                document_id = latest_doc["name"].split("/")[-1]
                log.writelog(document_id)
                requests.delete(BASE_URL + document_id)
                commandId = int(latest_doc["fields"]["Command"]["integerValue"])

                # Reboot PC
                if commandId == 1:
                    subprocess.Popen(["sudo sh /home/farma/enobet/reboot.sh"], stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, shell=True).communicate()
                # Open Teamviewer
                elif commandId == 2:
                    subprocess.Popen(["python3", "/home/farma/enobet/helpers/teamviewer.py"], stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, shell=False)
                else:
                    log.writelog("unknown command")

        except Exception as e:
            log.writelog(str(e))

        time.sleep(interval)
