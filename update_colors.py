#!/usr/bin/env python3
import asyncio, re
import capnp
import toml
import websockets

capnp.remove_import_hook()
schema = capnp.load("tyles_protocol.capnp")

TOML_PATH = "target_config.toml"


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


def main():
    msg = asyncio.run(fetch_config())
    allowed, dimensions = decode(msg)
    update_toml(allowed, dimensions)
    print(f"Updated {TOML_PATH} with {len(allowed)} colors:")
    for c in allowed:
        print(f"  #{c}")
    print(f"Updated size to {dimensions[0]} x {dimensions[1]}")


if __name__ == "__main__":
    main()
