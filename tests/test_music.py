import copy
from pathlib import Path
import unittest
from aura.music import Reaction,angles
from aura.models import Model,load_pack


class MusicTests(unittest.TestCase):
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
