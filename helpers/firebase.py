import requests
import json
import time

from helpers import log

PROJECT_ID = "nobetekranlari"
CLIENT_ID = "F4A7CED7-D2EB-419E-9F5D-002723F81645"
BASE_URL = ("https://firestore.googleapis.com/v1/projects/nobetekranlari/databases/("
            "default)/documents/Clients/F4A7CED7-D2EB-419E-9F5D-002723F81645/ClientCommands/")

last_seen_doc_create_time = None


def get_firestore_documents():
    response = requests.get(BASE_URL)
    log.writelog("get_firestore_documents response: " + str(response))
    if response.status_code == 200:
        return response.json().get("documents", [])
    return []


def listen_firestore(interval=10):
    log.writelog("firebase dinlemesi başladı.")
    global last_seen_doc_create_time
    while True:
        docs = get_firestore_documents()
        if docs:
            latest_doc = docs[-1]
            new_doc_create_time = time.strptime(latest_doc["createTime"])
            if last_seen_doc_create_time is None:
                last_seen_doc_create_time = new_doc_create_time
            elif last_seen_doc_create_time != new_doc_create_time:
                print("Yeni kayıt eklendi:", latest_doc["fields"])
                last_seen_doc_create_time = new_doc_create_time
        time.sleep(interval)
