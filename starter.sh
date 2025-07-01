#!/bin/bash

MASTER_PATH="/home/farma/enobet"

while true; do
    if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
        echo "✅ İnternet bağlantısı var."
        break
    else
        echo "❌ İnternet bağlantısı yok. 30 saniye bekleniyor..."
        sleep 30
    fi
done

sudo rm -f /home/farma/log.log /home/farma/enobet/nohup.out

if [ ! -d "$MASTER_PATH/.git" ]; then
    echo "Uygulama bulunamadı, klonlanıyor..."
    git clone https://github.com/EbilgiYazilim/enobet_client.git "$MASTER_PATH"
else
    sudo chmod -R +x /home/farma/enobet/
    sudo chmod -R 777 /home/farma/enobet/

    echo "Güncellemeler kontrol ediliyor..."
    cd "$MASTER_PATH"
    #git reset --hard origin/main
    #git checkout origin/main -- .
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
