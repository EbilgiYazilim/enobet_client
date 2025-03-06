#! /usr/bin/python
# -*- coding: utf-8 -*-
import socket

import requests
from helpers import log


# istemci makinanın internet bağlantısını kontrol etmek için kullanılır update test
def get_connection_status():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False


# OK
def get_short_code(id):
    try:
        req = requests.post("https://api.e-nobet.com/api/Client/GetClientInfoFromOldSystem?id=" + id)
        if req.status_code == 200:
            response = req.json()
            if response.get('data'):
                extra_data = response.get('extraData', {})
                if extra_data:
                    return list(extra_data.values())[0]
                else:
                    return ""
            else:
                return ""
        else:
            return ""
    except Exception as ee:
        log.writelog(ee)
        return ""


# OK
def get_client_code(shortcode):
    try:
        req = requests.get("https://api.e-nobet.com/api/Client/GetDeviceLink/" + shortcode)
        if req.status_code == 200:
            response = req.json()
            log.writelog(response)
            return response['data']
        else:
            return ""
    except Exception as ee:
        log.writelog(ee)
        return ""


# OK
def get_command(clientId):
    try:
        req = requests.post("https://api.e-nobet.com/api/Client/GetClientCommand?clientId=" + clientId)
        if req.status_code == 200:
            response = req.json()
            commandId = int(response['data'])
            if commandId == 3:
                extra_data = response.get('extraData', [])

                if isinstance(extra_data, list) and extra_data:
                    for item in extra_data:
                        if isinstance(item, dict) and "CommandText" in item:
                            return commandId, item["CommandText"]

                return commandId, ""
            else:
                return commandId, ""
        else:
            return -1
    except Exception as ee:
        log.writelog(ee)
        return -1
