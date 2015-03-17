# -*- coding: utf-8 -*-

import random
import math
import logging


def run_annealing(state, generate_next_state, compute_energy, t0, t_end,
                  step_handle=None):
    """Simulate annealing.

    :param state: state of our system
    :param generate_next_state: function which takes state and returns new.
    :param compute_energy: function which takes state and returns energy of
                           system in this state
    :param t0: temperature in the begining
    :param t_end: temperature at end
    :param step_handle: function which takes state.
                        It will be called in end of each step.
    """
    cauchy = lambda k: float(t0) / k
    cauchy_end = math.ceil(t0 / t_end)

    k = 1
    k_end = cauchy_end
    t = cauchy(k)
    energy = compute_energy(state)

    best = state
    best_energy = energy

    event = ''
    change_probability = 0.
    while t > t_end:
        t = cauchy(k)
        event = ''
        next_state = generate_next_state(state)
        next_energy = compute_energy(next_state)
        try:
            change_probability = math.exp((energy - next_energy) / t)
        except OverflowError:
            change_probability = int(energy > next_energy)
        if change_probability > random.random():
            if best_energy > next_energy:
                best = next_state
                best_energy = next_energy
            event = '$' if energy < next_energy else '+'
            state = next_state
            energy = next_energy
        logging.info('({0})\tT={1:.5f}\tE={2:.2f}\tNE={6:.2f}\tB={3:.2f}\tp={4:.2f}\t{5}'.format(
            k, t, energy, best_energy, change_probability, event, next_energy))
        k += 1
        step_handle and step_handle(state)

    return best
