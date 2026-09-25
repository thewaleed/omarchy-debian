#!/bin/bash

# Rotate the built-in display from accelerometer events (iio-sensor-proxy).
# Keeps the current mode and scale; only the transform changes.
set -u

MONITOR=$(hyprctl monitors -j | jq -r '.[0].name')

monitor-sensor | while read -r line; do
  [[ $line == *orientation* ]] || continue
  orientation=${line##* }
  case $orientation in
    normal) transform=2 ;;
    left-up) transform=3 ;;
    right-up) transform=1 ;;
    bottom-up) transform=0 ;;
    *) continue ;;
  esac
  scale=$(hyprctl monitors -j | jq -r --arg m "$MONITOR" '.[] | select(.name == $m) | .scale')
  hyprctl eval "hl.monitor({ output = \"$MONITOR\", mode = \"preferred\", position = \"auto\", scale = ${scale:-1.5}, transform = $transform })" >/dev/null
done
