#!/bin/bash
outputs=$(xrandr | grep " connected" | awk '{print $1}')
primary=$(echo "$outputs" | head -n 1)
resolution="1280x720" # İstenen çözünürlüğü buraya girin
for output in $outputs; do
    if [ "$output" != "$primary" ]; then
        xrandr --output "$output" --same-as "$primary" --mode "$resolution"
    fi
done
