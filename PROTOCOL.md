# Protocol

Protocol is based on MQTT protocol.

## Signature

The signature of the MQTT command message is as follows:

    <NAMESPACE> <COMMAND> <PARAMETERS>

- `NAMESPACE` - namespace of the command, case insensitive
- `COMMAND` - command name, case insensitive
- `PARAMETERS` - command parameters

## Structures

### `RECT`

The coordinates (from top-left) and dimensions (width and height) to draw the object.

    <X> <Y> <WIDTH> <HEIGHT>

### `STYLE`

The style of the object, expressed as comma delimited key-value pairs, e.g:

    font=1,color=#ff0000

### `CONTENT`

The content of the object. This always comes last to avoid parsing/escaping issues in the content.

#### Attributes

TBC

- `font_num` - font number (default=0)
- `font_size` - font size (default=8)
- `color_fg` - color in hexadecimal format (default=transparent)
- `color_bg` - color in hexadecimal format (default=transparent)
- `color_outline` - color in hexadecimal format (default=transparent)
- `outline` - outline width in pixels (default=0)
- `align` - alignment, one of `left`, `center`, `right` (default=`left`)
- `valign` - vertical alignment, one of `top`, `middle`, `bottom` (default=`top`)
- `wrap` - wrap text, one of `true`, `false` (default=`false`)

## Namespaces

By default only one namespace is available: `display`

## Commands

### `clear`

Clear the display.

    display clear

### `rect`

Draw a rectangle.

    display rect [RECT] [STYLE]

Examples:

    # Draw a rectangle from top-left (0,0) to bottom-right (128,64) with a red outline and transparent background
    display rect 0 0 128 64 outline=1,color_outline=#ff0000

### `text`

Display text.

    display text [RECT] [STYLE] [CONTENT]

Examples:

    # Display text from top-left (0,0) to bottom-right (128,64) with a red font and transparent background
    display text 0 0 128 64 font_num=1,color_fg=#ff0000 Hello world!
