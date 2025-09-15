#!/bin/bash

MASTER_PATH="/home/farma/enobet"
CONFIG_FILE="$MASTER_PATH/config.json"
BACKUP_CONFIG="/tmp/config_backup.json"

#İnternet Kontrülü
while true; do
    if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
        echo "✅ İnternet bağlantısı var."
        break
    else
        echo "❌ İnternet bağlantısı yok. 30 saniye bekleniyor..."
        sleep 30
    fi
done

[ -d "$MASTER_PATH" ] && sudo rm -f "$MASTER_PATH/nohup.out"

#Varsa önce config.json yedekleyelim.
if [ -f "$CONFIG_FILE" ]; then
    [ -f "$BACKUP_CONFIG" ] && rm -f "$BACKUP_CONFIG"
    cp "$CONFIG_FILE" "$BACKUP_CONFIG"
    echo "🛡️ config.json yedeklendi."
fi

sleep 2

# varsa dizini sil
if [ -d "$MASTER_PATH" ]; then
    echo "Mevcut uygulama dizini siliniyor..."
    sudo rm -rf "$MASTER_PATH"
fi

sleep 10

while true; do
    echo "GitHub'dan proje klonlanıyor..."
    if git clone https://github.com/EbilgiYazilim/enobet_client.git "$MASTER_PATH"; then
        sleep 30
        echo "Klonlama başarılı."
        break
    else
        echo "Klonlama başarısız oldu. 5 saniye sonra tekrar deneniyor..."
        sleep 5
    fi
done

#yedeklenmiş config.json varsa geri yükleyelim.
if [ -f "$BACKUP_CONFIG" ]; then
    mv "$BACKUP_CONFIG" "$CONFIG_FILE"
    echo "config.json geri yüklendi."
fi

sleep 2

sudo chmod -R +x "$MASTER_PATH"
sudo chmod -R 777 "$MASTER_PATH"

if [ $? -eq 0 ]; then
    echo "Güncelleme tamamlandı, başlatılıyor..."
    python3 /home/farma/enobet/setup.py
else
    echo "Güncelleme hatası veya güncel sürüm kullanılıyor."
    python3 /home/farma/enobet/setup.py
fi