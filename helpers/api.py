#! /usr/bin/python
# -*- coding: utf-8 -*-
import socket

import requests
from helpers import log

BASE = "https://api.e-nobet.com/api/Client"
# Tüm ağ çağrılarında zaman aşımı: ağ yarı-açık kalırsa cron süreci asılı kalmasın.
TIMEOUT = 10


# İstemci makinanın internet bağlantısını kontrol eder. Zaman aşımlı ve soketi kapatır.
def get_connection_status():
    try:
        conn = socket.create_connection(("www.google.com", 80), timeout=5)
        conn.close()
        return True
    except OSError:
        return False


# OK
def get_short_code(id):
    try:
        req = requests.post(BASE + "/GetClientInfoFromOldSystem?id=" + str(id), timeout=TIMEOUT)
        if req.status_code == 200:
            response = req.json()
            if response.get('data'):
                extra_data = response.get('extraData', {})
                if extra_data:
                    return list(extra_data.values())[0]
        return ""
    except Exception as ee:
        log.writelog("get_short_code hata: " + str(ee))
        return ""


# OK
def get_client_code(shortcode):
    try:
        req = requests.get(BASE + "/GetDeviceLink/" + str(shortcode), timeout=TIMEOUT)
        if req.status_code == 200:
            response = req.json()
            log.writelog(str(response))
            return response.get('data') or ""
        return ""
    except Exception as ee:
        log.writelog("get_client_code hata: " + str(ee))
        return ""


# BEKdesk kayıt (enrollment) token'ı sunucudan alınır; repoda/cihazda sabit tutulmaz.
def get_bekdesk_token(clientId):
    try:
        req = requests.post(BASE + "/GetBekdeskToken?clientId=" + str(clientId), timeout=TIMEOUT)
        if req.status_code == 200:
            return req.json().get('data') or ""
        return ""
    except Exception as ee:
        log.writelog("get_bekdesk_token hata: " + str(ee))
        return ""


# Her zaman (commandId, commandText) ikilisi döner; hata/komut-yok durumunda (-1, "").
def get_command(clientId):
    try:
        req = requests.post(BASE + "/GetClientCommand?clientId=" + str(clientId), timeout=TIMEOUT)
        if req.status_code != 200:
            return -1, ""
        response = req.json()
        data = response.get('data')
        if data is None:
            return -1, ""
        commandId = int(data)
        command_text = ""
        if commandId == 3:
            extra_data = response.get('extraData', [])
            if isinstance(extra_data, list):
                for item in extra_data:
                    if isinstance(item, dict) and "CommandText" in item:
                        command_text = item["CommandText"] or ""
                        break
        return commandId, command_text
    except Exception as ee:
        log.writelog("get_command hata: " + str(ee))
        return -1, ""
