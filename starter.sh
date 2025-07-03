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

#git'ten projeyi çekelim. Daha önce çekilmişse silip yeniden çekelim.
if [ ! -d "$MASTER_PATH/.git" ]; then
    echo "Uygulama bulunamadı, klonlanıyor..."
    git clone https://github.com/EbilgiYazilim/enobet_client.git "$MASTER_PATH"
    git pull origin main
    sync
else
    echo "Uygulama dizini silinip yeniden klonlanıyor..."
    sudo rm -rf "$MASTER_PATH"
    git clone https://github.com/EbilgiYazilim/enobet_client.git "$MASTER_PATH"
    git pull origin main
    sync
fi

#git'ten proje çekilemezse devam etmesin.
if [ ! -d "$MASTER_PATH/.git" ]; then
    echo "❌ Klonlama başarısız oldu! Çıkılıyor."
    exit 1
fi

#yedeklenmiş config.json varsa geri yükleyelim.
if [ -f "$BACKUP_CONFIG" ]; then
    mv "$BACKUP_CONFIG" "$CONFIG_FILE"
    echo "config.json geri yüklendi."
fi

sudo chmod -R +x "$MASTER_PATH"
sudo chmod -R 777 "$MASTER_PATH"

if [ $? -eq 0 ]; then
    echo "Güncelleme tamamlandı, başlatılıyor..."
    python3 /home/farma/enobet/setup.py
else
    echo "Güncelleme hatası veya güncel sürüm kullanılıyor."
    python3 /home/farma/enobet/setup.py
fi