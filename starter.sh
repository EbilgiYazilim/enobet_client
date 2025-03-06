#!/bin/bash

MASTER_PATH="/home/farma/enobet"

sudo rm -f /home/farma/log.log /home/farma/enobet/nohup.out

if [ ! -d "$MASTER_PATH/.git" ]; then
    echo "Uygulama bulunamadı, klonlanıyor..."
    git clone https://github.com/EbilgiYazilim/enobet_client.git "$MASTER_PATH"
else
    sudo chmod -R +x /home/farma/enobet/
    sudo chmod -R 777 /home/farma/enobet/

    echo "Güncellemeler kontrol ediliyor..."
    cd "$MASTER_PATH"
    git reset --hard origin/main
    git pull origin main
fi

sudo chmod -R +x /home/farma/enobet/
sudo chmod -R 777 /home/farma/enobet/

if [ $? -eq 0 ]; then
    echo "Güncelleme tamamlandı, başlatılıyor..."
    python3 /home/farma/enobet/setup.py
else
    echo "Güncelleme hatası veya güncel sürüm kullanılıyor."
    python3 /home/farma/enobet/setup.py
fi