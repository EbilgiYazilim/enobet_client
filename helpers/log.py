#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import datetime

log_file = "/home/farma/nobet_ekran/log.log"


def writelog(mesaj):
    try:
        # Log mesajına timestamp (tarih ve saat) ekleyerek daha anlaşılır yap
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = "[{}] - {}".format(timestamp, mesaj)

        # Log dosyasının var olup olmadığını kontrol et, yoksa oluştur
        if not os.path.exists(log_file):
            with open(log_file, "w") as f:
                f.write("=== Log Dosyası Oluşturuldu ===\n")

        # Dosyaya ekleme modunda yaz
        with open(log_file, "a") as f:
            f.write(formatted_message + "\n")

    except Exception as e:
        print("Log yazılırken hata oluştu: {}".format(e))
