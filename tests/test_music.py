import copy
from pathlib import Path
import unittest
from aura.music import Reaction,Transition,angles
from aura.models import Model,load_pack


class MusicTests(unittest.TestCase):
    def test_style_changes_pass_through_neutral_and_stop_resets(self):
        transition=Transition()
        for _ in range(40):result=transition.update('read',.025,.8)
        self.assertEqual(result,('read',.8,1))
        weights=[]
        for _ in range(60):
            result=transition.update('dance',.025,.8)
            weights.append(0 if result is None else result[2])
        self.assertIn(0,weights)
        self.assertEqual(result,('dance',.8,1))
        self.assertLess(max(abs(b-a) for a,b in zip(weights,weights[1:])),.12)
        transition.reset();self.assertIsNone(transition.update('off',.025,1))

    def test_gesture_boundaries_preserve_music_pose(self):
        model,_=load_pack(Path(__file__).resolve().parents[1]/'aura/assets/aura-illustrated-rig/model.json')
        for motion in ('wave','bow','cast'):
            for t in (0,3.2):
                first=model.pose(t,motion,clock=20,music=('read',.8))
                second=model.pose(20,clock=20,music=('read',.8))
                for name in first:
                    for a,b in zip(first[name],second[name]):self.assertAlmostEqual(a,b)
    def test_loudness_smoothing_silence_and_disconnect(self):
        meter=Reaction()
        first=meter.update(1,.025)
        self.assertGreater(first,0);self.assertLess(first,1)
        for _ in range(100):meter.update(1,.025)
        self.assertGreater(meter.energy,.99)
        for _ in range(200):meter.update(0,.025)
        self.assertLess(meter.energy,.001)
        self.assertEqual(meter.update(1,.025,False),0)
        self.assertEqual(meter.update(float('nan'),.025),0)

    def test_quiet_music_is_still_and_movement_is_bounded(self):
        for mode in ('gentle','dance','headbang'):
            for clock in (0,.1,1,20,10000):
                self.assertTrue(all(v==0 for v in angles(mode,0,clock).values()))
                self.assertTrue(all(abs(v)<=30 for v in angles(mode,1,clock).values()))

    def test_actions_and_pause_override_reactions(self):
        model,_=load_pack(Path(__file__).resolve().parents[1]/'aura/assets/aura-illustrated-rig/model.json')
        for mode in ('dance','headbang','read'):
            self.assertEqual(model.render(1,'wave',music=(mode,1)).tobytes(),model.render(1,'wave').tobytes())
            self.assertEqual(model.render(1,still=True,music=(mode,1)).tobytes(),model.render(0,still=True).tobytes())
        self.assertNotEqual(model.render(1,music=('read',1)).tobytes(),model.render(1).tobytes())

    def test_music_pose_retains_cross_model_scale(self):
        model,_=load_pack(Path(__file__).resolve().parents[1]/'aura/assets/aura-illustrated-rig/model.json')
        data=copy.deepcopy(model.data)
        for bone in data['bones']:bone['position']=[v*.5 for v in bone['position']]
        smaller=Model(data,model.images)
        for mode in ('gentle','dance','headbang','read'):
            first=model.pose(.4,music=(mode,.7));second=smaller.pose(.4,music=(mode,.7))
            for name in first:
                self.assertAlmostEqual(first[name][0]*.5,second[name][0])
                self.assertAlmostEqual(first[name][1]*.5,second[name][1])
                self.assertAlmostEqual(first[name][2],second[name][2])
