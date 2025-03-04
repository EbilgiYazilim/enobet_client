import requests
import json
import time

with open("../firebasekey.json") as f:
    creds = json.load(f)


def get_access_token():
    url = "https://www.googleapis.com/oauth2/v4/token"
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": creds["private_key_id"]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    return response.json().get("access_token", "")


ACCESS_TOKEN = get_access_token()
PROJECT_ID = "nobetekranlari"
CLIENT_ID = "F4A7CED7-D2EB-419E-9F5D-002723F81645"
BASE_URL = f"https://firestore.googleapis.com/v1/projects/nobetekranlari/databases/(default)/documents/Clients/{CLIENT_ID}/ClientCommands/"
HEADERS = {
    "Authorization": "Bearer " + ACCESS_TOKEN,
    "Content-Type": "application/json"
}

last_seen_doc = None


def get_firestore_documents():
    response = requests.get(BASE_URL, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("documents", [])
    return []


def listen_firestore(interval=10):
    global last_seen_doc
    while True:
        docs = get_firestore_documents()
        if docs:
            latest_doc = docs[-1]
            print(latest_doc)
            if last_seen_doc is None:
                last_seen_doc = latest_doc
            elif last_seen_doc["name"] != latest_doc["name"]:
                print("Yeni kayıt eklendi:", latest_doc["fields"])
                last_seen_doc = latest_doc  # Yeni kaydı sakla
        time.sleep(interval)
