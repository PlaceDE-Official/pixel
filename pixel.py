import argparse
import base64
import json
import logging
import pathlib
from io import BytesIO
from typing import Optional

import toml
from PIL import Image

from logger import CustomFormatter
logger = logging.getLogger("Pixel")
logger.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

ch.setFormatter(CustomFormatter())

logger.addHandler(ch)


class Config:
    """
    one config for doing work
    """
    min_prio: int
    max_prio: int
    png_is_base64: bool
    png_path_or_prefix: str | None
    prio_is_base64: bool
    prio_path_or_prefix: str | None
    both_is_base64: bool
    both_path_or_prefix: str | None
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
        if self.max_prio < self.min_prio:
            logger.error(f"'min_prio' muss <= 'max_prio' sein! Konfig: '{self.cfg}'")
            exit(4)
        self.png_is_base64 = cfg[2].startswith("base64:")
        self.png_path_or_prefix = None if not cfg[2] else cfg[2].removeprefix("base64:")
        self.prio_is_base64 = cfg[3].startswith("base64:")
        self.prio_path_or_prefix = None if not cfg[3] else cfg[3].removeprefix("base64:")
        self.both_is_base64 = cfg[4].startswith("base64:")
        self.both_path_or_prefix = None if not cfg[4] else cfg[4].removeprefix("base64:")
        self.json_is_base64 = cfg[5].startswith("base64:")
        self.json_path_or_prefix = None if not cfg[5] else cfg[5].removeprefix("base64:")
        self.is_overlay = cfg[6] == "1"
        self.ignore_prio = cfg[7] == "1"
        self.allow_overwrites = cfg[8] == "1"
        self.clamp_max_prio = cfg[9] == "1"


def get_nearest_color(hex_color: str) -> str:
    rgb = hex_to_col(hex_color)
    distance = 10 ** 30
    new_hex = None
    for k, v in allowed_colors_dict.items():
        new_distance = sum([abs(f - g) for f, g in zip(rgb, k)])
        if new_distance < distance:
            new_hex = v
            distance = new_distance
    return new_hex


def hex_to_col(hex_str) -> tuple[int, int, int]:
    """
    convert hex to rgb
    """
    assert hex_str[0] == "#" and len(hex_str) == 7 or len(hex_str) == 6

    def conv(s):
        return int(s, 16)

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
        logger.critical(f"Path '{pathlib.Path(path_or_prefix).parent}' does not exist!")
        exit(1)


def path_exists(path_or_prefix, is_file=True):
    """
    check if given path exists (for opening files)
    """
    if not pathlib.Path(path_or_prefix).exists():
        logger.critical(f"Path '{pathlib.Path(path_or_prefix)}' does not exist!")
        exit(1)
    if is_file and not pathlib.Path(path_or_prefix).is_file():
        logger.critical(f"Path '{pathlib.Path(path_or_prefix)}' is not a file!")
        exit(1)
    if not is_file and not pathlib.Path(path_or_prefix).is_dir():
        logger.critical(f"Path '{pathlib.Path(path_or_prefix)}' is not a directory!")
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
    if isinstance(data, Image.Image):
        if is_base64:
            buffered = BytesIO()
            data.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("ascii")
            print(f"{path_or_prefix}:{img_str}")
        else:
            parent_path_exists(path_or_prefix)
            data.save(path_or_prefix, bitmap_format="png", format="PNG")
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


def work_config(cfg: str, picture_folder: str):
    """
    do the work for one of the configs
    :param cfg: str to parse
    :param picture_folder: folder for input pictures
    :return:
    """
    logger.info(f"Working config\n    {cfg}")
    cfg = Config(cfg)

    # init images
    prio_img = None
    both_img = None
    if not cfg.is_overlay:
        img = Image.new("RGBA", (width, height), "#00000000")

        def shift_coord(c: int):
            return c

        if not cfg.ignore_prio:
            prio_img = Image.new("RGBA", (width, height), "#00000000")
            both_img = Image.new("RGBA", (width, height), "#00000000")
    else:
        img = Image.new("RGBA", (width * 3, height * 3), "#00000000")

        def shift_coord(c: int):
            return c * 3 + 1

        if not cfg.ignore_prio:
            prio_img = Image.new("RGBA", (width * 3, height * 3), "#00000000")
            both_img = Image.new("RGBA", (width * 3, height * 3), "#00000000")

    pixels_json = {}

    # fill images with stuff
    # if this returns false we overwrote some pixels without permission
    success = generate_data(img, prio_img, both_img, cfg, pixels_json, shift_coord, picture_folder)

    # save all the generated stuff
    save(cfg.png_is_base64, cfg.png_path_or_prefix, img)
    if not cfg.ignore_prio:
        save(cfg.prio_is_base64, cfg.prio_path_or_prefix, prio_img)
        save(cfg.both_is_base64, cfg.both_path_or_prefix, both_img)
    save(cfg.json_is_base64, cfg.json_path_or_prefix, pixels_json)

    # error if illegal overwrite
    if not success:
        logger.error(f"Overwrite occurred with config '{cfg.cfg}'")
        exit(2)
    logger.info("DONE with config")


def generate_data(img: Image, prio_img: Optional[Image.Image], both_img: Optional[Image.Image], cfg: Config,
                  pixels_json: dict, shift_coord, picture_folder: str):
    """
    generate all stuff for one config
    :param img: will contain pixels later
    :param prio_img: will container prio map in black / white later
    :param both_img: will contain pixels later, with assigned prios
    :param cfg: instance of config class
    :param pixels_json: dict to put pixels into, will be saved as json file later
    :param shift_coord: function to shift coord for overlay images
    :param picture_folder: folder for input pictures
    :return:
    """
    # store already present pixels
    coords: dict[(int, int), (str, int)] = {}
    # strucutres
    structures: dict[str, dict[(int, int), (str, int)]] = {}
    # guard for illegal overwrites
    success = True
    for struct in reversed(pixel_config["structure"]):
        struct2: dict[(int, int), (str, int)] = {}
        # open stuff and prepare
        file = struct["file"]
        priority = max(int(struct.get("priority", default_prio)), 255)
        priority_file = struct.get("priority_file", None)
        startx = int(struct.get("startx")) + add_x
        assert startx >= 0
        starty = int(struct.get("starty")) + add_y
        assert starty >= 0
        name = struct["name"]
        logger.info(f"Adding file {file} for structure {name}")
        ignore_alpha_channel = struct.get("ignore_prio_in_picture", False)
        if struct.get("overlay_only", False) and not cfg.is_overlay:
            logger.info(f"Skipping {name} because it should be skipped on overlays!")
            continue
        wrong_colors = set()
        out_of_image = False

        p = pathlib.Path(picture_folder).joinpath(file)
        path_exists(p)
        input_img = Image.open(p)
        input_prio = None
        if priority_file and not cfg.ignore_prio:
            p_file = pathlib.Path(picture_folder).joinpath(priority_file)
            input_prio = Image.open(p_file)

        # for each pixel
        for x in range(input_img.size[0]):
            x1 = x + startx
            for y in range(input_img.size[1]):
                y1 = y + starty
                if x1 >= img.width or y1 >= img.height:
                    out_of_image = True
                # get color as hex (for json later)
                color = input_img.getpixel((x, y))
                hex_color = col_to_hex(color[0], color[1], color[2])
                if hex_color not in allowed_colors:
                    wrong_colors.add(hex_color)
                    hex_color = get_nearest_color(hex_color)
                if hex_color in ignored_colors:
                    continue
                # get prio if needed
                prio = 255
                if not cfg.ignore_prio:
                    if ignore_alpha_channel:
                        if len(color) > 3:
                            if cfg.min_prio <= color[3] <= cfg.max_prio:
                                prio = priority
                            else:
                                continue
                        else:
                            prio = priority
                    else:
                        prio = color[3] if len(color) > 3 else priority
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
                if data := coords.get((x1, y1)):
                    if not cfg.allow_overwrites and cfg.ignore_prio:
                        logger.error(f"Illegal overwrite of pixel ({x1}, {y1}) with image: '{file}'")
                        success = False
                    else:
                        if data[1] >= prio:
                            continue
                # store pixel
                coords.update({(x1, y1): (hex_color, prio)})
                struct2.update({(x1, y1): (hex_color, prio)})
        structures.update({name: struct2})
        if wrong_colors:
            logger.warning(f"\"{name}\" has wrong_colors colors!\n    {', '.join(wrong_colors)}")
        if out_of_image:
            logger.warning(f"Ran out of normal image with config: '{cfg.cfg}', image: \"{name}\"")

    # generate json and put pixels into images
    for name, struct_data in structures.items():
        temp = {}
        for coord, data in struct_data.items():
            temp.update({",".join(map(str, coord)): {"color": data[0], "prio": data[1]}})
            shifted_coords = (shift_coord(coord[0]), shift_coord(coord[1]))
            if shifted_coords[0] >= img.width or shifted_coords[1] >= img.height:
                logger.error(
                    f"Pixel {shifted_coords} outside of image width size of {img.width}x{img.height}!\nStructure: {name}")
                exit(1)
            img.putpixel(shifted_coords, hex_to_col(data[0]))
            if not cfg.ignore_prio:
                p = hex_to_col(data[0])[0]
                prio_img.putpixel(shifted_coords, (p, p, p))
                both_img.putpixel(shifted_coords, (*hex_to_col(data[0]), p))
        pixels_json.update({name: temp})
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("picture_folder", type=pathlib.Path)
    parser.add_argument("pixel_config", type=pathlib.Path)
    parser.add_argument("--config", type=str, action='append')
    args = parser.parse_args()

    path_exists(args.pixel_config)
    path_exists(args.picture_folder, False)
    pixel_config = toml.load(args.pixel_config)
    ignored_colors = list(pixel_config["ignored_colors"])
    allowed_colors = list(map(str.lower, map(lambda x: f"#{x}", pixel_config["allowed_colors"])))
    allowed_colors_dict = {hex_to_col(f): f for f in allowed_colors}
    width, height = int(pixel_config["width"]), int(pixel_config["height"])
    add_x, add_y = int(pixel_config["add-x"]), int(pixel_config["add-y"])
    default_prio = int(pixel_config["default_prio"] or 0)

    for cfg in args.config:
        work_config(cfg, args.picture_folder)
