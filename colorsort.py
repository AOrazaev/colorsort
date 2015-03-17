# -*- coding: utf-8 -*-

import cPickle
import math
import argparse
import logging
import progressbar
import random

from annealing import run_annealing
from color import load_colors, dump_colors
from to_image import colors_to_image

from functools import wraps
from colormath.color_objects import sRGBColor
from colormath.color_conversions import RGB_to_XYZ, XYZ_to_Lab
from colormath import color_diff

COLOR_DIFF_FUNCTION = color_diff.delta_e_cie1976

def cached(func):
    cache = {}
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = cPickle.dumps({'args': sorted(args), 'kwargs': kwargs})
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper

NEAREST_COLORS = {}

@cached
def colordiff(x, y):
    def lab(color):
        return XYZ_to_Lab(RGB_to_XYZ(sRGBColor(*color.rgb, is_upscaled=True)))
    return COLOR_DIFF_FUNCTION(lab(x), lab(y))

class ColorsortState(object):
    SENSIVITY = 7
    GREED_RATIO = 0.15

    def __init__(self, colors):
        self._colors = list(colors)
        self._energy = None
        self._points_energy = [None for x in self._colors]

    def energy(self):
        if self._energy is None:
            self._energy = self._energy_for_colors(
                range(len(self._colors)),
                with_pbar=True)
        return self._energy

    def take_out_and_insert(self, from_pos, to_pos):
        affected_out = set(
            x % len(self._colors)
            for x in range(from_pos - self.SENSIVITY, from_pos + self.SENSIVITY + 1))
        affected_in = set(
            x % len(self._colors)
            for x in range(to_pos - self.SENSIVITY, to_pos + self.SENSIVITY))
        self._energy -= self._energy_for_colors(affected_out | affected_in)

        # take_out
        c = self._colors[from_pos]
        del self._colors[from_pos]
        if to_pos >= from_pos:
            to_pos -= 1
        affected_out = set(
            x if x < from_pos else (x - 1) % len(self._colors)
            for x in affected_out)
        affected_in = set(
            x if x < from_pos else (x - 1) % len(self._colors)
            for x in affected_in)

        # insert
        self._colors.insert(to_pos, c)
        affected_out = set(
            x if x < to_pos else (x + 1) % len(self._colors)
            for x in affected_out)
        affected_in = set(
            x if x < to_pos else (x + 1) % len(self._colors)
            for x in affected_in)
        affected_in |= set([to_pos])
        self._energy += self._energy_for_colors(affected_out | affected_in)

    def generate_next_state(self):
        state = ColorsortState(self._colors)
        state._energy = self.energy()
        state._points_energy = list(self._points_energy)
        affected_positions = set()

        for _ in range(random.randint(1, 10)):
            worst_indexes = sorted(
                [(e, n) for n, e in enumerate(self._points_energy)],
                reverse=True)[:min(100, int(len(self._colors)*self.GREED_RATIO))]
            i = random.choice(worst_indexes)[1]
            c = random.choice(NEAREST_COLORS[self._colors[i]])
            j = self._colors.index(c) + random.choice([0, 1])
            state.take_out_and_insert(i, j)

        return state

    def _one_color_energy(self, i):
        energy = 0.
        for d in range(self.SENSIVITY):
            energy += colordiff(
                self._colors[i % len(self._colors)],
                self._colors[(i + d + 1) % len(self._colors)]) / self.SENSIVITY
            energy += colordiff(
                self._colors[i % len(self._colors)],
                self._colors[(i - d - 1) % len(self._colors)]) / self.SENSIVITY
        self._points_energy[i % len(self._colors)] = energy
        return energy

    def _energy_for_colors(self, positions, with_pbar=False):
        energy = 0.
        pbar = None
        if with_pbar:
            pbar = progressbar.ProgressBar(maxval=len(positions))
            pbar.start()
        for n, i in enumerate(positions):
            energy += self._one_color_energy(i)
            pbar and pbar.update(n)
        pbar and pbar.finish()
        return energy

    def dump_image(self, path, with_energy=False):
        if with_energy:
            colors_to_image(self._colors, energy=self._points_energy).save(path, format='png')
        else:
            colors_to_image(self._colors).save(path, format='png')

def parse_args():
    parser = argparse.ArgumentParser(
        description='Sort given colors using annealing imitation algorithm')
    parser.add_argument('colors_json', type=argparse.FileType('rt'))
    parser.add_argument('output_png')
    parser.add_argument('--t0', type=float, default=1000, help='initial temperature')
    parser.add_argument('--t-end', type=float, default=0.001, help='end temperature')
    parser.add_argument('-d', '--draw-energy', action='store_true')
    parser.add_argument('--use-cie2000', action='store_true')
    return parser.parse_args()

def calculate_nearest_colors(colors):
    pbar = progressbar.ProgressBar(maxval=len(colors)**2)
    pbar.start()
    for nx, x in enumerate(colors):
        nearest = []
        for ny, y in enumerate(colors):
            nearest.append((colordiff(x, y), y))
            pbar.update(nx*len(colors) + ny)
        nearest.sort()
        last = int(len(nearest) * ColorsortState.GREED_RATIO)
        NEAREST_COLORS[x] = [c for _, c in nearest[1:min(100, int(len(nearest)*0.15))]]

    pbar.finish()

def main(args):
    if args.use_cie2000:
        COLOR_DIFF_FUNCTION = color_diff.delta_e_cie2000
        logging.info('Using cie2000 function as color distance')
    else:
        logging.info('Using cie1976 function as color distance')
    initial_state = ColorsortState(load_colors(args.colors_json))
    logging.info('Data loaded... Heating colordiff function cache')
    calculate_nearest_colors(initial_state._colors)
    logging.info('Computing energy first time.')
    initial_state.energy()
    logging.info('Energy computed... Starting annealing.')

    def step_handle(s):
        s.dump_image(args.output_png + '.tmp.png', args.draw_energy)
        with open('tmp.json', 'w') as f:
            dump_colors(f, s._colors)
    result = run_annealing(
        initial_state,
        ColorsortState.generate_next_state,
        ColorsortState.energy,
        args.t0,
        args.t_end,
        step_handle=step_handle)
    result.dump_image(args.output_png)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] - %(levelname)s - %(message)s')
    main(parse_args())
