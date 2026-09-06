import unittest
from aura.motion import Motion
from aura.illustrated import frame


class MotionTests(unittest.TestCase):
    def test_response_is_independent_of_frame_rate(self):
        a, b = Motion(), Motion()
        for _ in range(30):
            a.update(1 / 30, level=.6, gaze=.8)
        for _ in range(60):
            b.update(1 / 60, level=.6, gaze=.8)
        self.assertAlmostEqual(a.mouth, b.mouth, places=6)
        self.assertAlmostEqual(a.gaze, b.gaze, places=6)

    def test_silence_closes_mouth_without_instant_snap(self):
        motion = Motion()
        for _ in range(30):
            motion.update(1 / 30, level=1)
        motion.update(1 / 30, level=0)
        self.assertGreater(motion.mouth, 0)
        self.assertLess(motion.mouth, .9)
        for _ in range(10):
            motion.update(1 / 30, level=0)
        self.assertLess(motion.mouth, .01)

    def test_pause_stops_clock_and_face(self):
        motion = Motion(time=3, mouth=1, gaze=1)
        motion.update(1, level=1, still=True)
        self.assertEqual(motion.time, 3)
        self.assertEqual((motion.mouth, motion.gaze, motion.blink), (0, 0, 0))

    def test_deformation_keeps_boots_planted(self):
        motion = Motion(time=2.3, gaze=1)
        self.assertEqual(motion.offset(500), (0, 0))
        self.assertNotEqual(motion.offset(100), (0, 0))

    def test_dark_clothes_survive_backdrop_key(self):
        image = frame(0, "idle", "violet", 256, 520)
        self.assertEqual(image.getpixel((5, 200))[3], 0)
        self.assertEqual(image.getpixel((100, 180))[3], 255)
        for column in range(4):
            image = frame(column, "idle", "violet", 256, 520)
            self.assertEqual(image.getpixel((0, 0))[3], 0)

    def test_large_stall_does_not_jump_animation(self):
        motion = Motion()
        motion.update(30, level=1)
        self.assertLessEqual(motion.time, .1)
