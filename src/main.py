from interstate75 import Interstate75, SWITCH_A, SWITCH_B
from mqtt_as import MQTTClient, config
from compat import wifi_led, blue_led
import uasyncio as asyncio
import machine
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


# Global text scaling factor (adjust this to change text size)
TEXT_SCALE = 2

# Global screen speed factor: increase to slow down scrolling, decrease to speed up.
GLOBAL_SCREEN_SPEED = 0.5

# Constants for controlling scrolling text
BACKGROUND_COLOUR = (0, 0, 0)  # Black background
HOLD_TIME = 0.0  # Seconds before scrolling starts
BLANK_SCREEN_TIME = 0  # Seconds to hold blank screen after scroll off
BUFFER_PIXELS = 2  # Extra buffer to ensure full scroll off
SCROLL_STEP = 1  # Scroll 1 pixel at a time
SCROLL_DELAY = 0.01 * GLOBAL_SCREEN_SPEED  # Delay in seconds for each scroll step

# Brightness settings
brightness = 100  # Initial brightness (0 to 100)

# State constants
STATE_PRE_SCROLL = 0
STATE_SCROLLING = 1
STATE_POST_SCROLL = 2
STATE_BLANK_SCREEN = 3

# Configuration
config["ssid"] = WIFI_SSID
config["wifi_pw"] = WIFI_PASSWORD
config["server"] = MQTT_HOST
config["port"] = MQTT_PORT
config["user"] = MQTT_USERNAME
config["password"] = MQTT_PASSWORD
# config["client_id"] = MQTT_CLIENT_ID

print("BOOT")

# Create Interstate75 object and graphics surface for drawing
i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_128X128)
graphics = i75.display
width = i75.width
height = i75.height

print("DISPLAY")

# Function to scale colors based on brightness
def scale_color(color, brightness):
    return tuple(int(c * brightness / 100) for c in color)


# Initialize colors with brightness scaling
def initialize_colors(brightness):
    black = graphics.create_pen(0, 0, 0)
    red = graphics.create_pen(*scale_color((255, 0, 0), brightness))
    green = graphics.create_pen(*scale_color((0, 255, 0), brightness))
    blue = graphics.create_pen(*scale_color((0, 0, 255), brightness))
    yellow = graphics.create_pen(*scale_color((255, 255, 0), brightness))
    orange = graphics.create_pen(*scale_color((255, 165, 0), brightness))
    white = graphics.create_pen(*scale_color((255, 255, 255), brightness))
    return black, red, green, blue, yellow, orange, white


black, red, green, blue, yellow, orange, white = initialize_colors(brightness)


# Function to update display with new colors
def update_display():
    graphics.set_pen(black)
    graphics.clear()
    i75.update(graphics)


# Function to set brightness manually
def set_brightness(level):
    global brightness, black, red, green, blue, yellow, orange, white
    brightness = level  # Use level directly (0 to 100)
    black, red, green, blue, yellow, orange, white = initialize_colors(brightness)
    update_display()


# Set initial brightness and background
set_brightness(brightness)
graphics.set_pen(black)
graphics.clear()
i75.update(graphics)
i75.set_led(0, 0, 0)


# --------------------- Drawing Helper Functions ---------------------
def set_background(color):
    graphics.set_pen(color)
    graphics.clear()


def draw_text_with_outline_multiline(
    text, x, y, scale=TEXT_SCALE, text_color=white, outline_color=black, line_height=8
):
    # Use a font that supports scaling; here we assume "bitmap8" is available.
    graphics.set_font("bitmap8")
    lines = text.split("\n")
    scaled_line_height = line_height * scale
    for line_num, line in enumerate(lines):
        y_offset = y + (line_num * scaled_line_height)
        # Draw an outline for better contrast.
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        graphics.set_pen(outline_color)
        for dx, dy in offsets:
            graphics.text(line, x + dx, y_offset + dy, -1, scale)
        graphics.set_pen(text_color)
        graphics.text(line, x, y_offset, -1, scale)


def _parse_rect(parts):
    """
    Attempts to parse RECT (X Y WIDTH HEIGHT) from the beginning of a list of parts.

    Args:
        parts: A list of string parts from the MQTT message parameters.

    Returns:
        A tuple containing:
        - A dictionary representing the RECT if parsing is successful, else None.
        - The remaining list of parts after consuming the RECT components.
        If parsing fails (not enough parts or non-integer values), returns (None, original_parts).
    """
    if len(parts) < 4:
        return None, parts  # Not enough parts for RECT

    try:
        x = int(parts[0])
        y = int(parts[1])
        width = int(parts[2])
        height = int(parts[3])
        rect = {'x': x, 'y': y, 'width': width, 'height': height}
        return rect, parts[4:]
    except ValueError:
        return None, parts # Non-integer value found where integer expected


def _parse_style(style_string):
    """
    Parses a STYLE string (comma-delimited key=value pairs).

    Args:
        style_string: The string containing style information (e.g., "font=1,color=#ff0000").

    Returns:
        A dictionary of parsed style keys and values. Invalid pairs are ignored.
    """
    style_dict: Dict[str, str] = {}
    if not style_string:
        return style_dict

    pairs = style_string.split(',')
    for pair in pairs:
        pair = pair.strip()
        if '=' in pair:
            key, value = pair.split('=', 1) # Split only on the first '='
            key = key.strip()
            value = value.strip()
            if key: # Ensure key is not empty
                style_dict[key] = value
        # Silently ignore parts without '=' or empty keys
    return style_dict

# --- Main Parsing Function ---

def parse_mqtt_message(message):
    """
    Parses an MQTT message string according to the defined protocol.

    Args:
        message: The raw MQTT message payload string.

    Returns:
        A dictionary containing the parsed structure ('namespace', 'command', 'params')
        if parsing is successful.
        Returns None if the message format is invalid or violates the protocol.
    """
    if not message:
        print("Error: Empty message received.")
        return None

    parts = message.strip().split()

    if len(parts) < 2:
        print(f"Error: Message too short. Expected '<NAMESPACE> <COMMAND> ...', got '{message}'")
        return None

    print(parts)
    namespace = parts[0].lower()
    command = parts[1].lower()
    param_parts = parts[2:]
    print(param_parts)
    
    # --- Validate Namespace and Command ---
    if namespace != "display":
        print(f"Error: Unknown namespace '{parts[0]}'. Expected 'display'.")
        return None

    parsed_data = {
        "namespace": namespace,
        "command": command,
        "params": {}
    }

    # --- Command-Specific Parsing ---
    if command == "clear":
        if remaining_params_str.strip():
            print(f"Error: Command 'clear' does not accept parameters, got '{remaining_params_str}'")
            return None
        # No parameters needed for clear
        return parsed_data

    elif command == "rect":
        # Expected structure: display rect [RECT] [STYLE]
        rect_data, remaining_parts = _parse_rect(param_parts)
        print(param_parts)

        if rect_data is None:
            print(f"Error: Invalid RECT format in 'rect' command. "
                  f"Expected 'X Y WIDTH HEIGHT', got parameters starting with: '{' '.join(param_parts[:4])}'")
            return None

        parsed_data["params"]["rect"] = rect_data

        # The rest should be the STYLE string
        style_string = " ".join(remaining_parts)
        parsed_data["params"]["style"] = _parse_style(style_string)

        return parsed_data

    elif command == "text":
        # Expected structure: display text [RECT] [STYLE] [CONTENT]
        rect_data, remaining_parts_after_rect = _parse_rect(param_parts)

        if rect_data is None:
            print(f"Error: Invalid RECT format in 'text' command. "
                  f"Expected 'X Y WIDTH HEIGHT', got parameters starting with: '{' '.join(param_parts[:4])}'")
            return None

        parsed_data["params"]["rect"] = rect_data

        # Now separate STYLE and CONTENT
        style_parts = []
        content_parts = []
        parsing_style = True

        for i, part in enumerate(remaining_parts_after_rect):
            # Style parts must contain '=' and come before any non-style part
            # If we encounter a part without '=' it must be the start of content.
            if parsing_style and '=' in part:
                 # Basic check: does it look like key=value? Allow '=' within value.
                 # More robust check could use regex if needed: re.match(r"^[a-zA-Z0-9_]+=.*", part)
                 if part.index('=') > 0: # Ensure '=' is not the first character
                    style_parts.append(part)
                 else: # Part starts with '=', assume it's content
                     parsing_style = False
                     content_parts.append(part)
            else:
                parsing_style = False
                content_parts.append(part)

        # Reconstruct style string (comma separated) and content string (space separated)
        style_string = ",".join(style_parts) # Already split by space, now join with comma for parser
        content_string = " ".join(content_parts)

        parsed_data["params"]["style"] = _parse_style(style_string)
        parsed_data["params"]["content"] = content_string

        return parsed_data

    else:
        print(f"Error: Unknown command '{command}' for namespace '{namespace}'.")
        return None


# --------------------- MQTT Message and Scrolling ---------------------
def sub_cb(topic, msg, retained):
    global STATE_PRE_SCROLL, STATE_SCROLLING, STATE_POST_SCROLL, STATE_BLANK_SCREEN, width, height
    print(f'Topic: "{topic.decode()}" Message: "{msg.decode()}" Retained: {retained}')
    message = msg.decode("utf-8")
    try:
        parsed = parse_mqtt_message(message)
            
        time_ms = time.ticks_ms()    
        black, red, green, blue, yellow, orange, white = initialize_colors(brightness)

        print(parsed)
    except Exception as e:
        raise(e)
        print(e)
    
        pass
    i75.update(graphics)
    time.sleep(SCROLL_DELAY)

# --------------------- Async Helper Functions ---------------------
async def heartbeat():
    s = True
    while True:
        await asyncio.sleep_ms(500)
        blue_led(s)
        s = not s


async def wifi_han(state):
    wifi_led(not state)
    print("Wifi is", "up" if state else "down")
    await asyncio.sleep(1)


async def conn_han(client):
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
config["subs_cb"] = sub_cb
config["wifi_coro"] = wifi_han
config["connect_coro"] = conn_han
config["clean"] = True

MQTTClient.DEBUG = True  # Optional debug output
client = MQTTClient(config)

asyncio.create_task(heartbeat())

try:
    asyncio.run(main(client))
finally:
    client.close()
    asyncio.new_event_loop()

