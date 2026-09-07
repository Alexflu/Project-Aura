"""Shared additive joint motion, independent of artwork and model pixel size."""
import math

DURATION = 3.2


def envelope(t):
    value = max(0, min(1, t / .6, (DURATION - t) / .6))
    return value * value * (3 - 2 * value)


def angles(names, t, motion, clock):
    blend = envelope(t) if motion != 'idle' else 0
    result = {'chest': math.sin(clock * 1.7) * 1.1, 'head': math.sin(clock * .8) * 2}
    if motion == 'wave':
        result.update(right_upper_arm=-135 * blend,
                      right_forearm=(35 + math.sin(t * 9) * 18) * blend,
                      right_hand=math.sin(t * 9) * 13 * blend)
        for i, name in enumerate(('thumb', 'index', 'middle', 'ring')):
            result['right_' + name] = math.sin(t * 8 + i * .4) * 5 * blend
    elif motion == 'inspect':
        result['head'] += math.sin(min(1, max(0, t / DURATION)) * math.pi) * 17
    elif motion == 'bow':
        result['chest'] += 22 * blend
        result['head'] += 12 * blend
        result.update(left_upper_arm=15 * blend, right_upper_arm=-15 * blend,
                      left_forearm=-12 * blend, right_forearm=12 * blend)
    elif motion == 'cast':
        result['chest'] -= 5 * blend
        result['head'] -= 7 * blend
        result.update(left_upper_arm=110 * blend, left_forearm=-35 * blend,
                      left_hand=-20 * blend, right_upper_arm=-12 * blend)
        for i, name in enumerate(('thumb', 'index', 'middle', 'ring')):
            result['left_' + name] = (-12 + i * 5) * blend
    # Optional semantic roles. Parent hierarchy supplies attachment and scale.
    # These are bounded procedural offsets, not a collision or cloth simulation.
    for name in names:
        role = name.split('_', 1)[0]
        if role not in ('hair', 'cloth', 'gear'):
            continue
        phase = sum(map(ord, name)) * .07
        amplitude = {'hair': 3.0, 'cloth': 2.0, 'gear': 1.4}[role]
        result[name] = amplitude * (math.sin(clock * 1.8 + phase) +
                                   .3 * math.sin(clock * 3.1 + phase))
        result[name] += blend * amplitude * math.sin(t * 4.5 + phase)
    return {name: value for name, value in result.items() if name in names}
