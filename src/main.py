from interstate75 import Interstate75, SWITCH_A, SWITCH_B
from mqtt_as import MQTTClient, config
from compat import wifi_led, blue_led
import uasyncio as asyncio
import machine
import random
import re
import time
from secrets import (
    WIFI_SSID,
    WIFI_PASSWORD,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    MQTT_CLIENT_ID,
)  # type: ignore

from helpers import hex_to_rgb
from mqtt import parse_mqtt_message

FRAME_DELAY = 0.01
BRIGHTNESS = 100

config["ssid"] = WIFI_SSID
config["wifi_pw"] = WIFI_PASSWORD
config["server"] = MQTT_HOST
config["port"] = MQTT_PORT
config["user"] = MQTT_USERNAME
config["password"] = MQTT_PASSWORD
config["client_id"] = MQTT_CLIENT_ID

print("BOOT")

i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_128X128)
graphics = i75.display
width = i75.width
height = i75.height


def create_pen(color):
    return graphics.create_pen(*hex_to_rgb(color))


black = graphics.create_pen(0, 0, 0)
white = graphics.create_pen(255, 255, 255)

graphics.set_pen(black)
graphics.clear()
i75.update(graphics)
i75.set_led(0, 0, 0)


def on_mqtt_message(topic, msg, retained):
    print(f'Topic: "{topic.decode()}" Message: "{msg.decode()}" Retained: {retained}')
    message = msg.decode("utf-8")
    parsed = parse_mqtt_message(message)
    if not parsed:
        return

    print(parsed)

    command = parsed.get("command")
    params = parsed.get("params")
    style = params.get("style", {})
    time_ms = time.ticks_ms()

    if command == "clear":
        print("CLEAR")
        graphics.set_pen(black)
        graphics.clear()

    if command == "rect":
        print("RECT")
        rect = params["rect"]
        if "color_fg" in style:
            graphics.set_pen(create_pen(style["color_fg"]))
        graphics.rectangle(rect["x"], rect["y"], rect["width"], rect["height"])

    if command == "text":
        print("TEXT")
        rect = params["rect"]
        content = params["content"]
        if "color_fg" in style:
            graphics.set_pen(create_pen(style["color_fg"]))
        if "font" in style:
            graphics.set_font(style["font"])
        scale = int(style.get("scale", 1))
        graphics.text(content, rect["x"], rect["y"], scale=scale)

    i75.update(graphics)
    time.sleep(FRAME_DELAY)


async def heartbeat():
    s = True
    while True:
        await asyncio.sleep_ms(500)
        blue_led(s)
        s = not s


async def wifi_handler(state):
    wifi_led(not state)
    print("Wifi is", "up" if state else "down")
    await asyncio.sleep(1)


async def on_mqtt_connect(client):
    await client.subscribe("i75/#", 1)


async def main(client):
    try:
        await client.connect()
    except OSError:
        print("Connection failed.")
        machine.reset()
        return
    while True:
        await asyncio.sleep(5)


# --------------------- MQTT and Scheduler Setup ---------------------
config["subs_cb"] = on_mqtt_message
config["wifi_coro"] = wifi_handler
config["connect_coro"] = on_mqtt_connect
config["clean"] = True

MQTTClient.DEBUG = True  # Optional debug output
client = MQTTClient(config)

asyncio.create_task(heartbeat())

try:
    asyncio.run(main(client))
finally:
    client.close()
    asyncio.new_event_loop()
