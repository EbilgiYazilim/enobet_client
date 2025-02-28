#!/bin/bash

# Ekran güç yönetimini kapat
xset -dpms
xset s off
xset s noblank

# Ekran yansıtma ayarları (VGA-1 ve HDMI-1 aynı görüntü)
xrandr --output VGA-1 --same-as HDMI-1

# Firefox'u kiosk modunda başlat (shortCode değişkenini kullanarak)
SHORTCODE="ABC"  # Burada kısa kodu güncelle
firefox --kiosk "https://e-nobet.com/a269"
