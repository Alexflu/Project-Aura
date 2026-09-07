import copy
import math
import unittest
from aura.model_library import REFERENCE
from aura.models import Model, load_pack
from aura.rig_motion import angles, envelope
from aura.equipment import BUILTINS


class SharedMotionTests(unittest.TestCase):
    def setUp(self):
        self.model,_=load_pack(REFERENCE)

    def test_gestures_blend_back_to_continuous_idle(self):
        for motion in ('wave','bow','cast','inspect'):
            for t in (0,3.2):
                actual=self.model.pose(t,motion,clock=17)
                expected=self.model.pose(17,'idle',clock=17)
                for name in actual:
                    for a,b in zip(actual[name],expected[name]):self.assertAlmostEqual(a,b,places=8)
        self.assertLess(envelope(.001),.00001)

    def test_shared_motion_scales_with_custom_body_proportions(self):
        data=copy.deepcopy(self.model.data)
        for bone in data['bones']:bone['position']=[v*.6 for v in bone['position']]
        for socket in data['sockets'].values():socket['position']=[v*.6 for v in socket['position']]
        smaller=Model(data,self.model.images)
        for motion in ('bow','cast','wave','draw'):
            first=self.model.pose(1.2,motion);second=smaller.pose(1.2,motion)
            for name in first:
                for i in (0,1):self.assertAlmostEqual(first[name][i]*.6,second[name][i],places=5)
                self.assertAlmostEqual(first[name][2],second[name][2],places=5)

    def test_optional_joints_are_bounded_and_do_not_require_new_schema(self):
        names={'root','head','chest','hair_custom','cloth_custom','gear_custom'}
        for t in (0,.1,1,3.2,10000):
            result=angles(names,t,'cast',t)
            self.assertLessEqual(set(result),names)
            for name in names-{'root','head','chest'}:
                self.assertLessEqual(abs(result[name]),7)
        basic=Model(dict(self.model.data,bones=[b for b in self.model.data['bones'] if b['name'] in ('root','chest','head')]),{})
        self.assertNotIn('cast',basic.capabilities)
        self.assertEqual(basic.pose(1,'cast'),basic.pose(1,'idle'))

    def test_pause_freezes_secondary_motion_props_and_spells(self):
        items=BUILTINS[:4]
        self.assertEqual(self.model.render(1,'cast',still=True,equipment=items,cast=1).tobytes(),
                         self.model.render(15,'wave',still=True,equipment=items,cast=2).tobytes())
        self.assertNotEqual(self.model.render(.5,'cast',equipment=items,cast=.5).tobytes(),
                            self.model.render(1.5,'cast',equipment=items,cast=1.5).tobytes())
