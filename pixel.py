import argparse
import base64
import json
import pathlib
from io import BytesIO
from typing import Optional

import toml
from PIL import Image


class Config:
    """
    sore one config for doing work
    """
    min_prio: int
    max_prio: int
    png_is_base64: bool
    png_path_or_prefix: str | None
    prio_is_base64: bool
    prio_path_or_prefix: str | None
    json_is_base64: bool
    json_path_or_prefix: str | None
    is_overlay: bool
    ignore_prio: bool
    allow_overwrites: bool
    clamp_max_prio: bool
    cfg: str

    def __init__(self, cfg: str):
        self.cfg = cfg
        cfg = cfg.split(";")
        self.min_prio = int(cfg[0] or 10)
        self.max_prio = int(cfg[1] or 250)
        self.png_is_base64 = cfg[2].startswith("base64:")
        self.png_path_or_prefix = None if not cfg[2] else cfg[2].removeprefix("base64:")
        self.prio_is_base64 = cfg[3].startswith("base64:")
        self.prio_path_or_prefix = None if not cfg[3] else cfg[3].removeprefix("base64:")
        self.json_is_base64 = cfg[4].startswith("base64:")
        self.json_path_or_prefix = None if not cfg[4] else cfg[4].removeprefix("base64:")
        self.is_overlay = cfg[5] == "1"
        self.ignore_prio = cfg[6] == "1"
        self.allow_overwrites = cfg[7] == "1"
        self.clamp_max_prio = cfg[8] == "1"


def hex_to_col(hex_str):
    """
    convert hex to rgb
    """
    assert hex_str[0] == "#" and len(hex_str) == 7 or len(hex_str) == 6

    def conv(s):
        return int(s, 16)
    hex_str = hex_str.removeprefix("#")

    return conv(hex_str[1:3]), conv(hex_str[3:5]), conv(hex_str[5:7])


def col_to_hex(r, g, b):
    """
    convert rgb to hex
    """
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def parent_path_exists(path_or_prefix):
    """
    check if parent of given path exists (for saving files)
    """
    if not pathlib.Path(path_or_prefix).parent.exists():
        print(f"Path '{pathlib.Path(path_or_prefix).parent}' does not exist!")
        exit(1)


def path_exists(path_or_prefix):
    """
    check if given path exists (for opening files)
    """
    if not pathlib.Path(path_or_prefix).exists():
        print(f"Path '{pathlib.Path(path_or_prefix)}' does not exist!")
        exit(1)


def string_to_base64(data: str):
    """
    convert string to base64
    """
    return base64.b64encode(data.encode('ascii')).decode('ascii')


def save(is_base64: bool, path_or_prefix: str | None, data):
    """
    save data.
    :param is_base64: if the data should be printed as base64 or saved to file
    :param path_or_prefix: filepath or prefix for base64 string
    :param data: str, (json) dict or PIL.Image
    """
    if path_or_prefix is None:
        return
    if isinstance(data, Image):
        if is_base64:
            buffered = BytesIO()
            data.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
            print(f"{path_or_prefix}:{img_str}")
        else:
            parent_path_exists(path_or_prefix)
            data.save(path_or_prefix)
        return
    if isinstance(data, dict):
        data = json.dumps(data)
    if isinstance(data, str):
        if is_base64:
            print(f"{path_or_prefix}:{string_to_base64(data)}")
        else:
            parent_path_exists(path_or_prefix)
            with open(path_or_prefix, "w+") as f:
                f.write(data)
        return


def work_config(cfg: str, width: int, height: int, default_prio: int, pixel_config: dict, picture_folder: pathlib.Path,
                ignore_colors: list):
    """
    do the work for one of the configs
    :param cfg: str to parse
    :param width: width of image (referred to as x later)
    :param height: height of image (referred to as y later)
    :param pixel_config: config with all structures as dict
    :param picture_folder: path for images
    :param ignore_colors: hex colors to be ignored
    :return:
    """
    cfg = Config(cfg)

    # init images
    prio_img = None
    if not cfg.is_overlay:
        img = Image.new("RGBA", (width, height), "#00000000")

        def shift_coord(c: int):
            return c

        if not cfg.ignore_prio:
            prio_img = Image.new("RGBA", (width, height), "#00000000")
    else:
        img = Image.new("RGBA", (width * 3, height * 3), "#00000000")

        def shift_coord(c: int):
            return c * 3 + 1

        if not cfg.ignore_prio:
            prio_img = Image.new("RGBA", (width * 3, height * 3), "#00000000")

    pixels_json = {}

    # fill images with stuff
    # if this returns false we overwrote some pixels without permission
    success = generate_data(default_prio, img, prio_img, cfg, pixels_json, shift_coord, pixel_config, picture_folder,
                            ignore_colors)

    # save all the generated stuff
    save(cfg.png_is_base64, cfg.png_path_or_prefix, img)
    if not cfg.ignore_prio:
        save(cfg.prio_is_base64, cfg.prio_path_or_prefix, prio_img)
    save(cfg.json_is_base64, cfg.json_path_or_prefix, pixels_json)

    # error if illegal overwrite
    if not success:
        print(f"Overwrite occurred with config '{cfg.cfg}'")
        exit(2)


def generate_data(default_prio: int, img: Image, prio_img: Optional[Image], cfg: Config, pixels_json: dict, shift_coord,
                  pixel_config: dict, picture_folder: pathlib.Path, ignore_colors: list):
    """
    generate all stuff for one config
    :param default_prio: default prio for all structures if structure does not have own prio
    :param img: will containe pixels later
    :param prio_img: will container prio map in black / white later
    :param cfg: instance of config class
    :param pixels_json: dict to put pixels into, will be saved as json file later
    :param shift_coord: function to shift coord for overlay images
    :param pixel_config: contains structures
    :param picture_folder: path for the pictures
    :param ignore_colors: list of hex colors to ignore
    :return:
    """
    # store aalready present pixels
    coords: dict[(int, int), (str, int)] = {}
    # guard for illegal overwrites
    success = True
    for struct in reversed(pixel_config["structure"]):
        # open stuff and prepare
        file = struct["file"]
        priority = int(struct.get("priority"), default_prio)
        priority_file = struct.get("priority_file", None)
        name = struct["name"]
        print(f"Adding file {file} for structure {name}")

        p = pathlib.Path(picture_folder).joinpath(file)
        path_exists(p)
        input_img = Image.open(p)
        input_prio = None
        if priority_file and not cfg.ignore_prio:
            p_file = pathlib.Path(picture_folder).joinpath(priority_file)
            input_prio = Image.open(p_file)

        # for each pixel
        for x in range(input_img.size[0]):
            for y in range(input_img.size[1]):
                if x >= img.width or y >= img.height:
                    print(f"Ran out of normal image with config: '{cfg.cfg}', Pixel: ({x}, {y}), image: {file}")
                    exit(3)
                # get color as hex (for json later)
                color = input_img.getpixel((x, y))
                hex_color = col_to_hex(color[0], color[1], color[2])
                if hex_color in ignore_colors:
                    continue
                # get prio if needed
                prio = 255
                if not cfg.ignore_prio:
                    prio = color[4] if len(color) >= 3 else priority
                    if input_prio:
                        prio = input_prio.getpixel((x, y))[0]
                    if prio < cfg.min_prio:
                        continue
                    if prio > cfg.max_prio:
                        if cfg.clamp_max_prio:
                            prio = cfg.max_prio
                        else:
                            continue
                if prio <= 0:
                    continue
                # check for (illegal) overwrites
                if data := coords.get((x, y)):
                    if not cfg.allow_overwrites and not cfg.ignore_prio:
                        print(f"Illegal overwrite of pixel ({x}, {y}) with image: '{file}'")
                        success = False
                    else:
                        if data[1] >= prio:
                            continue
                # store pixel
                coords.update({(x, y): (hex_color, prio)})

    # generate json and put pixels into images
    for coord, data in coords.items():
        pixels_json.update({coord: {"color": data[0], "prio": data[1]}})
        img.putpixel((shift_coord(coord[0]), shift_coord(coord[1])), hex_to_col(data[0]))
        if not cfg.ignore_prio:
            p = hex_to_col(data[0])[0]
            prio_img.putpixel((shift_coord(coord[0]), shift_coord(coord[1])), (p, p, p))
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("picture_folder", type=pathlib.Path)
    parser.add_argument("pixel_config", type=pathlib.Path)
    parser.add_argument("--config", type=str, action='append')
    args = parser.parse_args()

    path_exists(args.pixel_config)
    pixel_config = toml.load(args.pixel_config)
    ignore_colors = list(pixel_config["ignore_colors"])
    width, height = int(pixel_config["width"]), int(pixel_config["height"])
    default_prio = int(pixel_config["default_prio"] or 0)

    for cfg in args.config:
        work_config(cfg, width, height, default_prio, pixel_config, args.picture_folder, ignore_colors)
