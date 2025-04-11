def scale_color(color, brightness):
    return tuple(int(c * brightness / 100) for c in color)


def hex_to_rgb(hex_color):
    # Remove leading '#' if exists
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]
    # Check if the string has the correct length (6 hex digits)
    if len(hex_color) != 6:
        raise ValueError("Invalid hex color format: Must be 6 hex digits.")
    # Convert hex parts to integers
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError:
        # Catches cases where characters are not valid hex digits (0-9, a-f, A-F)
        raise ValueError("Invalid characters in hex color string.")


"""
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
"""
