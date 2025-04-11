def parse_rect(parts):
    if len(parts) < 4:
        return None, parts  # Not enough parts for RECT
    try:
        x = int(parts[0])
        y = int(parts[1])
        width = int(parts[2])
        height = int(parts[3])
        rect = {"x": x, "y": y, "width": width, "height": height}
        return rect, parts[4:]
    except ValueError:
        return None, parts  # Non-integer value found where integer expected


def parse_style(style_string):
    style_dict = {}
    if not style_string:
        return style_dict

    pairs = style_string.split(",")
    for pair in pairs:
        pair = pair.strip()
        if "=" in pair:
            key, value = pair.split("=", 1)  # Split only on the first '='
            key = key.strip()
            value = value.strip()
            if key:  # Ensure key is not empty
                style_dict[key] = value
        # Silently ignore parts without '=' or empty keys
    return style_dict


def parse_mqtt_message(message):
    if not message:
        print("Error: Empty message received.")
        return None

    parts = message.strip().split()

    if len(parts) < 2:
        print(
            f"Error: Message too short. Expected '<NAMESPACE> <COMMAND> ...', got '{message}'"
        )
        return None

    namespace = parts[0].lower()
    command = parts[1].lower()
    param_parts = parts[2:]

    if namespace != "display":
        print(f"Error: Unknown namespace '{parts[0]}'. Expected 'display'.")
        return None

    parsed_data = {"namespace": namespace, "command": command, "params": {}}

    if command == "clear":
        if len(param_parts):
            print(
                f"Error: Command 'clear' does not accept parameters, got '{remaining_params_str}'"
            )
            return None
        # No parameters needed for clear
        return parsed_data

    elif command == "rect":
        rect_data, remaining_parts = parse_rect(param_parts)
        if rect_data is None:
            print(
                f"Error: Invalid RECT format in 'rect' command. "
                f"Expected 'X Y WIDTH HEIGHT', got parameters starting with: '{' '.join(param_parts[:4])}'"
            )
            return None

        parsed_data["params"]["rect"] = rect_data

        # The rest should be the STYLE string
        style_string = " ".join(remaining_parts)
        parsed_data["params"]["style"] = parse_style(style_string)

        return parsed_data

    elif command == "text":
        # Expected structure: display text [RECT] [STYLE] [CONTENT]
        rect_data, remaining_parts_after_rect = parse_rect(param_parts)

        if rect_data is None:
            print(
                f"Error: Invalid RECT format in 'text' command. "
                f"Expected 'X Y WIDTH HEIGHT', got parameters starting with: '{' '.join(param_parts[:4])}'"
            )
            return None

        parsed_data["params"]["rect"] = rect_data

        # Now separate STYLE and CONTENT
        style_parts = []
        content_parts = []
        parsing_style = True

        for i, part in enumerate(remaining_parts_after_rect):
            # Style parts must contain '=' and come before any non-style part
            # If we encounter a part without '=' it must be the start of content.
            if parsing_style and "=" in part:
                # Basic check: does it look like key=value? Allow '=' within value.
                # More robust check could use regex if needed: re.match(r"^[a-zA-Z0-9_]+=.*", part)
                if part.index("=") > 0:  # Ensure '=' is not the first character
                    style_parts.append(part)
                else:  # Part starts with '=', assume it's content
                    parsing_style = False
                    content_parts.append(part)
            else:
                parsing_style = False
                content_parts.append(part)

        # Reconstruct style string (comma separated) and content string (space separated)
        style_string = ",".join(
            style_parts
        )  # Already split by space, now join with comma for parser
        content_string = " ".join(content_parts)

        parsed_data["params"]["style"] = parse_style(style_string)
        parsed_data["params"]["content"] = content_string

        return parsed_data

    else:
        print(f"Error: Unknown command '{command}' for namespace '{namespace}'.")
        return None
