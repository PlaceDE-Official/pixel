#!/usr/bin/env python3
import asyncio
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
    return colors


def update_toml(allowed_colors):
    with open(TOML_PATH) as f:
        config = toml.load(f)
    config["allowed_colors"] = allowed_colors
    with open(TOML_PATH, "w") as f:
        toml.dump(config, f)


def main():
    msg = asyncio.run(fetch_config())
    allowed = decode(msg)
    update_toml(allowed)
    print(f"Updated {TOML_PATH} with {len(allowed)} colors:")
    for c in allowed:
        print(f"  #{c}")


if __name__ == "__main__":
    main()
