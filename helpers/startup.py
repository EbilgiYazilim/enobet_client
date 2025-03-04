#! /usr/bin/python
# -*- coding: utf-8 -*-


def add_to_startup():
    try:
        RC_LOCAL_PATH = "/etc/rc.local"

        # Eklenmesi gereken komutlar
        startup_commands = [
            "sh /home/farma/enobet/starter.sh &\n"
        ]

        # Mevcut /etc/rc.local içeriğini oku
        with open(RC_LOCAL_PATH, "r") as file:
            lines = file.readlines()

        # Komutların olup olmadığını kontrol et
        updated = False
        for command in startup_commands:
            if command not in "".join(lines):
                updated = True

        # Eğer eksik komut varsa güncelle
        if updated:
            with open(RC_LOCAL_PATH, "w") as file:
                for line in lines:
                    if line.strip() == "exit 0":
                        # exit 0'dan önce başlatma komutlarını ekle
                        for command in startup_commands:
                            if command not in "".join(lines):
                                file.write(command)
                    file.write(line)
    except Exception as e:
        print("Açılışa komutları eklenemedi: " + str(e))


if __name__ == "__main__":
    add_to_startup()
