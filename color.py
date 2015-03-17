# -*- coding: utf-8 -*-
"""
    >>> from cStringIO import StringIO
    >>> stream = StringIO('''
    ... [
    ...     {
    ...      "rgb": {"r": 255, "g": 0, "b": 0},
    ...      "hsv": {"h": 0, "s": 100, "v": 100},
    ...      "hex": "FF0000"
    ...     },
    ...     {
    ...      "rgb": {"r": 0, "g": 0, "b": 0},
    ...      "hsv": {"h": 0, "s": 0, "v": 0},
    ...      "hex": "000000"
    ...     }
    ... ]
    ... ''')
    >>> colors = list(load_colors(stream))
    >>> print colors[0]
    <Color hex=FF0000>
    >>> stream = StringIO()
    >>> dump_colors(stream, colors)
    >>> stream.seek(0)
    >>> list(load_colors(stream)) == colors
    True
"""

import json

class Color(object):
    def __init__(self, rgb=None, hsv=None, hex=None):
        self.rgb = tuple(rgb[x] for x in ['r', 'g', 'b'])
        self.hsv = tuple(hsv[x] for x in ['h', 's', 'v'])
        self.hex = hex

    def __str__(self):
        return '<Color hex={0}>'.format(self.hex)

    def __hash__(self):
        return hash(self.hex)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

def load_colors(stream):
    for kwargs in json.load(stream):
        yield Color(**kwargs)

def dump_colors(stream, colors):
    obj = []
    for color in colors:
        obj.append({
            'rgb': {'r': color.rgb[0], 'g': color.rgb[1], 'b': color.rgb[2]},
            'hsv': {'h': color.hsv[0], 's': color.hsv[1], 'v': color.hsv[2]},
            'hex': color.hex
        })
    json.dump(obj, stream),

if __name__ == '__main__':
    import doctest
    doctest.testmod()
