#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import configparser
import json
from helpers import log


def get_crm_id(config_path):
    log.writelog("config.ini okunuyor.")
    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        crm_id = config.get("DEFAULT", "crm_id")
        log.writelog("crm_id değeri alındı: " + crm_id)
    except Exception as e:
        log.writelog("crm_id değeri alınamadı: " + str(e))
        crm_id = 0

    return int(crm_id)


def write_config_json(crm_id, short_code, json_path):
    try:
        log.writelog("config.json yazılıyor.")
        config_json_data = {"oldCrmId": crm_id, "shortCode": short_code}

        with open(json_path, "w") as json_file:
            json.dump(config_json_data, json_file, indent=4)

        print("config.json oluşturuldu:", config_json_data)
    except Exception as e:
        log.writelog("crm_id değeri alınamadı: " + str(e))


def read_config_json():
    json_path = "/home/farma/nobet_ekran/config.json"

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            return data
    else:
        print("Json dosyası bulunamadı.")
        return None
