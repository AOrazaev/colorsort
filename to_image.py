#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image
from PIL.ImageDraw import ImageDraw

import argparse

from color import load_colors


def parse_args():
    parser = argparse.ArgumentParser(
        description='Tool for converting colos.json to png')

    parser.add_argument('input_json', type=argparse.FileType('rt'))
    parser.add_argument('output_png')
    return parser.parse_args()

def colors_to_image(colors, height=80, energy=None):
    if energy is not None:
        energy = list(energy)
        max_energy = max(energy)
        height *= 2
    image = Image.new('RGB', (len(colors), height), (0,0,0))
    draw = ImageDraw(image)
    for n, color in enumerate(colors):
        draw.line((n, 0, n, height / ((energy is not None) + 1)), fill=color.rgb)
        if energy is not None:
            c = 255 * (1 - float(energy[n]) / max_energy)
            draw.line(
                (n, height / 2, n, height),
                fill=(255, c, c))
    return image

def main(args):
    colors = list(load_colors(args.input_json))
    image = colors_to_image(colors)
    image.save(args.output_png, format='png')

if __name__ == '__main__':
    main(parse_args())
