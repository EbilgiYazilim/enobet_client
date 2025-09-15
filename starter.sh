#!/bin/bash
set -euo pipefail

MASTER_PATH="/home/farma/enobet"
CONFIG_FILE="$MASTER_PATH/config.json"
BACKUP_CONFIG="/tmp/config_backup.json"
VERSION_FILE="$MASTER_PATH/.version"

# --- CDN ayarları ---
VERSION_JSON_URL="https://cdn.e-nobet.com/app/version.json"
TMP_VERSION_JSON="/tmp/enobet_version.json"
TMP_ZIP="/tmp/enobet_update.zip"
TMP_EXTRACT="/tmp/enobet_new"

# --- JSON alanı çek (python3 ile) ---
json_get() {
  local file="$1" key="$2"
  python3 - <<PY
import json
with open("$file","r",encoding="utf-8") as f:
    d=json.load(f)
v=d.get("$key","")
print(v if isinstance(v,str) else ("" if v is None else str(v)))
PY
}

# --- İnternet kontrolü ---
while true; do
  if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ İnternet bağlantısı var."
    break
  else
    echo "❌ İnternet yok. 30 sn bekleniyor..."
    sleep 30
  fi
done

# wget kontrolü
if ! command -v wget >/dev/null 2>&1; then
  echo "❌ 'wget' bulunamadı. Kurmak için: sudo apt-get update && sudo apt-get install -y wget"
  exit 1
fi

# Nohup temizle
[ -d "$MASTER_PATH" ] && sudo rm -f "$MASTER_PATH/nohup.out" || true

# config.json yedekle
if [ -f "$CONFIG_FILE" ]; then
  [ -f "$BACKUP_CONFIG" ] && rm -f "$BACKUP_CONFIG"
  cp "$CONFIG_FILE" "$BACKUP_CONFIG"
  echo "🛡️ config.json yedeklendi."
fi

sleep 2

# Mevcut versiyon oku (yoksa 0 kabul). Dosyada semver yazıyorsa sadece rakamları alır.
CURRENT_VERSION=0
if [ -f "$VERSION_FILE" ]; then
  CV="$(tr -dc '0-9' < "$VERSION_FILE" || true)"
  [ -n "$CV" ] && CURRENT_VERSION="$CV"
fi
echo "📦 Mevcut versiyon: $CURRENT_VERSION"

# CDN'den version.json çek (wget)
echo "🌐 Versiyon bilgisi indiriliyor: $VERSION_JSON_URL"
# -q sessiz, -O çıktı dosyası, --tries ve --waitretry basit retry davranışı
wget -q --tries=3 --waitretry=3 -O "$TMP_VERSION_JSON" "$VERSION_JSON_URL"

REMOTE_VERSION_STR="$(json_get "$TMP_VERSION_JSON" "version")"
ZIP_URL="$(json_get "$TMP_VERSION_JSON" "zip_url")"

# version integera dönüştür
if ! [[ "$REMOTE_VERSION_STR" =~ ^[0-9]+$ ]]; then
  echo "❌ version.json 'version' alanı tamsayı değil: '$REMOTE_VERSION_STR'"
  exit 1
fi
REMOTE_VERSION="$REMOTE_VERSION_STR"

if [ -z "$ZIP_URL" ]; then
  echo "❌ version.json 'zip_url' alanı boş."
  exit 1
fi

echo "🆕 Uzak versiyon: $REMOTE_VERSION"
echo "🧩 Zip URL: $ZIP_URL"

# Sayısal karşılaştırma
if [ "$REMOTE_VERSION" -le "$CURRENT_VERSION" ]; then
  echo "✅ Zaten en güncel veya daha yeni bir sürüm kullanılıyor ($CURRENT_VERSION >= $REMOTE_VERSION). Başlatıyorum."
  sudo chmod -R +x "$MASTER_PATH" || true
  sudo chmod -R 777 "$MASTER_PATH" || true
  python3 /home/farma/enobet/setup.py
  exit 0
fi

# Yeni sürüm indir (wget)
echo "⬇️  Yeni sürüm indiriliyor..."
wget -q --tries=3 --waitretry=3 --max-redirect=10 -O "$TMP_ZIP" "$ZIP_URL"

# unzip kontrol
if ! command -v unzip >/dev/null 2>&1; then
  echo "ℹ️  'unzip' yok. Kur: sudo apt-get update && sudo apt-get install -y unzip"
  exit 1
fi

# Geçici klasörleri hazırla
rm -rf "$TMP_EXTRACT"
mkdir -p "$TMP_EXTRACT"

echo "📦 Arşiv açılıyor..."
unzip -q "$TMP_ZIP" -d "$TMP_EXTRACT"

# Tek kök klasör varsa onu root al
NEW_ROOT="$TMP_EXTRACT"
DIRCOUNT=$(find "$TMP_EXTRACT" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
if [ "$DIRCOUNT" -eq 1 ]; then
  NEW_ROOT="$(find "$TMP_EXTRACT" -mindepth 1 -maxdepth 1 -type d)"
fi

sleep 2

# Eski uygulamayı kaldır
if [ -d "$MASTER_PATH" ]; then
  echo "🧽 Eski uygulama dizini kaldırılıyor..."
  sudo rm -rf "$MASTER_PATH"
fi

# Yeni uygulamayı taşı
sudo mkdir -p "$(dirname "$MASTER_PATH")"
sudo mv "$NEW_ROOT" "$MASTER_PATH"

# config.json geri yükle
if [ -f "$BACKUP_CONFIG" ]; then
  mv "$BACKUP_CONFIG" "$CONFIG_FILE"
  echo "🔁 config.json geri yüklendi."
fi

# .version güncelle (tamsayı)
echo -n "$REMOTE_VERSION" | sudo tee "$VERSION_FILE" >/dev/null

# izinler
sudo chmod -R +x "$MASTER_PATH" || true
sudo chmod -R 777 "$MASTER_PATH" || true

echo "🚀 Güncelleme tamamlandı ($CURRENT_VERSION → $REMOTE_VERSION), başlatılıyor..."
python3 /home/farma/enobet/setup.py
