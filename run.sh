#!/usr/bin/env bash

python pixel.py ./pictures ./target_config.toml --config ";;./outputs/overlay_target.png;./outputs/overlay_priorities.png;./outputs/overlay_combined.png;./outputs/overlay_pixels.json;1;0;1;1" --config ";;./outputs/default_target.png;./outputs/default_priorities.png;./outputs/default_combined.png;./outputs/default_pixels.json;0;0;1;1" 