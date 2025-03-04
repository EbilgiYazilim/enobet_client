import subprocess

import requests
import json
import time

from helpers import log

PROJECT_ID = "nobetekranlari"
CLIENT_ID = "F4A7CED7-D2EB-419E-9F5D-002723F81645"
BASE_URL = ("https://firestore.googleapis.com/v1/projects/nobetekranlari/databases/("
            "default)/documents/Clients/F4A7CED7-D2EB-419E-9F5D-002723F81645/ClientCommands/")


def get_firestore_documents():
    response = requests.get(BASE_URL)
    if response.status_code == 200:
        return response.json().get("documents", [])
    return []


def listen_firestore(interval=10):
    log.writelog("firebase dinlemesi başladı.")
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
                elif commandId == 2:
                    subprocess.call(["python3", "/home/farma/enobet/helpers/teamviewer.py"])
                elif commandId == 3:
                    log.writelog("command 3")
                else:
                    log.writelog("unknown command")

        except Exception as e:
            log.writelog(str(e))

        time.sleep(interval)
