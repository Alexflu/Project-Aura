"""Time-based, bounded motion state shared by the sprite renderers."""
import math
from dataclasses import dataclass


def ease(current, target, dt, speed):
    return target + (current - target) * math.exp(-speed * dt)


@dataclass
class Motion:
    time: float = 0
    mouth: float = 0
    gaze: float = 0
    blink: float = 0

    def update(self, dt, level=None, demo=False, gaze=0, still=False, mood="neutral"):
        dt = max(0, min(.1, dt))
        if still:
            self.mouth = self.blink = self.gaze = 0
            return
        self.time += dt
        if level is None:
            target = max(0, math.sin(self.time * 13)) * .8 if demo else 0
        else:
            target = 0 if level < .06 else min(1, math.sqrt(level))
        self.mouth = ease(self.mouth, target, dt, 24 if target > self.mouth else 18)
        self.gaze = ease(self.gaze, max(-1, min(1, gaze)), dt, 5)
        # A brief close/open with a second blink in the longer cycle.
        phase = self.time % 9.7
        distance = min(abs(phase - 3.1), abs(phase - 8.0))
        self.blink = max(0, 1 - distance / .11)
        if mood == "sleepy":
            self.blink = max(.65, self.blink)

    def offset(self, y, strength=1, mood="neutral"):
        """Inverse deformation: feet remain planted while torso/head breathe."""
        weight = max(0, min(1, (480 - y) / 340))
        pace = .8 if mood == "sleepy" else 1
        sway = math.sin(self.time * 1.15 * pace) * 4.8
        head = max(0, min(1, (165 - y) / 65))
        dx = (sway * weight + self.gaze * head * 3) * strength
        dy = math.sin(self.time * 1.8 * pace) * 2.6 * weight * strength
        # Small independent head tilt rather than translating the whole card.
        dx += math.sin(self.time * .72) * (100 - y) * .025 * head * strength
        return dx, dy

    def secondary_offset(self, x, y, center, hair, outfit):
        """Very small edge motion; keeps face center, joints and feet stable."""
        side = max(0, min(1, (abs(x-center) - 18) / 18))
        hair_end = 215 if hair == "long" else 125
        hair_weight = max(0, min(1, (y-50)/55)) * max(0, min(1, (hair_end-y)/35))
        dx = math.sin(self.time*1.7-y*.025) * 1.6 * side * hair_weight
        cloth_weight = max(0, 1-abs(y-245)/90) * max(0, min(1, (abs(x-center)-26)/22))
        dx += math.sin(self.time*1.2+y*.018) * cloth_weight * (1.2 if outfit == "tactical" else .7)
        return dx, math.sin(self.time*1.4) * .5 * cloth_weight
