#!/bin/bash

MASTER_PATH="/home/farma/enobet"

if [ ! -d "$MASTER_PATH/.git" ]; then
    echo "Uygulama bulunamadı, klonlanıyor..."
    git clone https://github.com/EbilgiYazilim/enobet_client.git "$MASTER_PATH"
else
    echo "Güncellemeler kontrol ediliyor..."
    cd "$MASTER_PATH"
    git reset --hard origin/main
    git pull origin main
fi

sudo chmod -R +x /home/farma/enobet/

if [ $? -eq 0 ]; then
    echo "Güncelleme tamamlandı, başlatılıyor..."
    sh "$MASTER_PATH/setup.sh"
else
    echo "Güncelleme hatası veya güncel sürüm kullanılıyor."
    sh "$MASTER_PATH/setup.sh"
fi