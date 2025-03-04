#! /usr/bin/python
# -*- coding: utf-8 -*-

import requests
from helpers import log


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


def get_client_code(shortcode):
    try:
        req = requests.post("https://api.e-nobet.com/api/Client/GetDeviceLink/" + shortcode)
        if req.status_code == 200:
            response = req.json()
            log.writelog(response)
            return response['data']
        else:
            return ""
    except Exception as ee:
        log.writelog(ee)
        return ""
