#!/usr/bin/env python3
import asyncio, re, struct
import capnp
import toml
import websockets

capnp.remove_import_hook()
schema = capnp.load("tyles_protocol.capnp")

TOML_PATH = "target_config.toml"
ACO_PATH = "outputs/colors.aco"
GPL_PATH = "outputs/colors.gpl"
PDN_PATH = "outputs/colors.txt"


async def fetch_config():
    async with websockets.connect("wss://api.tyles.place/canvas_updates") as ws:
        return await asyncio.wait_for(ws.recv(), timeout=10)


def decode(msg):
    update = schema.CanvasUpdate.from_bytes_packed(msg)
    config = update.config
    colors = [config.colors[i] for i in config.colorMap]
    return colors, (config.sizeX, config.sizeY)


def update_toml(allowed_colors: list[str], dimensions: tuple[int, int]):
    with open(TOML_PATH) as f:
        text = f.read()
    colors_str = "[" + ",".join(f'"{c}"' for c in allowed_colors) + "]"
    text = re.sub(r"(?m)^allowed_colors = \[.*?\]", f"allowed_colors = {colors_str}", text, flags=re.DOTALL)
    text = re.sub(r"(?m)^width = \d+", f"width = {dimensions[0]}", text)
    text = re.sub(r"(?m)^height = \d+", f"height = {dimensions[1]}", text)
    with open(TOML_PATH, "w") as f:
        f.write(text)


def write_aco(colors: list[str]):
    """Write a Photoshop .aco color swatch file (v1 + v2)."""
    parsed = []
    for hex_color in colors:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        parsed.append((r, g, b))

    buf = bytearray()

    # Version 1
    buf += struct.pack(">HH", 1, len(parsed))
    for r, g, b in parsed:
        buf += struct.pack(">HHHHH", 0, r * 257, g * 257, b * 257, 0)

    # Version 2 (with names)
    buf += struct.pack(">HH", 2, len(parsed))
    for i, (r, g, b) in enumerate(parsed):
        buf += struct.pack(">HHHHH", 0, r * 257, g * 257, b * 257, 0)
        name = f"#{colors[i]}"
        encoded = name.encode("utf-16-be") + b"\x00\x00"
        buf += struct.pack(">I", len(name) + 1)
        buf += encoded

    with open(ACO_PATH, "wb") as f:
        f.write(buf)


def write_gpl(colors: list[str]):
    """Write a GIMP .gpl palette file."""
    lines = ["GIMP Palette", "Name: tyles", "#"]
    for hex_color in colors:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        lines.append(f"{r:>3} {g:>3} {b:>3}\t#{hex_color}")
    with open(GPL_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_pdn(colors: list[str]):
    """Write a Paint.NET .txt palette file."""
    lines = [f"FF{hex_color}" for hex_color in colors]
    with open(PDN_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    msg = asyncio.run(fetch_config())
    allowed, dimensions = decode(msg)
    update_toml(allowed, dimensions)
    write_aco(allowed)
    write_gpl(allowed)
    write_pdn(allowed)
    print(f"Updated {TOML_PATH} with {len(allowed)} colors:")
    for c in allowed:
        print(f"  #{c}")
    print(f"Updated size to {dimensions[0]} x {dimensions[1]}")
    print(f"Wrote {ACO_PATH} with {len(allowed)} swatches")
    print(f"Wrote {GPL_PATH} with {len(allowed)} swatches")
    print(f"Wrote {PDN_PATH} with {len(allowed)} swatches")


if __name__ == "__main__":
    main()
