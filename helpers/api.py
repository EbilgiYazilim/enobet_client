#! /usr/bin/python
# -*- coding: utf-8 -*-

import requests
from helpers import log


def get_short_code(id):
    try:
        req = requests.post("https://api.e-nobet.com/api/Client/GetClientInfoFromOldSystem?id=" + id)
        if req.status_code == 200:
            response = req.json()
            log.writelog("API'den dönen yanıt: " + str(response))
            if response.get('data'):
                extra_data = response.get('extraData', {})
                log.writelog("API'den dönen extradata: " + str(extra_data))
                if extra_data:
                    log.writelog("Kısa kod: " + list(extra_data.values())[0])
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
