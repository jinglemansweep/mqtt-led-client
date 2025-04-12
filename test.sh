#!/bin/bash

mqtt_pub () {
  mosquitto_pub -h "${MQTT_HOST}" -p "${MQTT_PORT:-1883}" -u "${MQTT_USER}" -P "${MQTT_PASSWORD}" -t "i75/test" -m "${1}"
}

mqtt_pub "display clear"
mqtt_pub "display rect 0 0 128 64 color_fg=#0000cc"
mqtt_pub "display rect 2 2 124 60 color_fg=#000000"

while true; do

  mqtt_pub "display rect 2 2 124 60 color_fg=#000000"
  
  mqtt_pub "display text 8 4 0 0 color_fg=#ffff00 Date"
  mqtt_pub "display text 8 12 0 0 color_fg=#ffffff,scale=2 $(date +%D)"

  mqtt_pub "display text 8 28 0 0 color_fg=#ffff00 Time"
  mqtt_pub "display text 8 36 0 0 color_fg=#ffffff,scale=2 $(date +%T)"

  


  
  sleep 10

done


