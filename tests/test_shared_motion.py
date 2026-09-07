import copy
import math
import unittest
from PIL import Image
from pathlib import Path
from aura.model_library import REFERENCE
from aura.models import Model, load_pack
from aura.rig_motion import angles, envelope
from aura.equipment import BUILTINS


class SharedMotionTests(unittest.TestCase):
    def setUp(self):
        self.model,_=load_pack(REFERENCE)

    def test_translucent_art_preserves_opacity_when_composited(self):
        data=copy.deepcopy(self.model.data)
        data['size']=[64,64]
        data['bones'][0]['position']=[32,32]
        data['layers']=[dict(bone='root',asset='edge.png',pivot=[0,0],z=0)]
        data['sockets']={}
        model=Model(data,{'edge.png':Image.new('RGBA',(8,8),(220,80,150,128))})
        pixel=model.render(0,still=True).getpixel((35,35))
        self.assertEqual(pixel[3],128)
        for actual,expected in zip(pixel[:3],(220,80,150)):
            self.assertLessEqual(abs(actual-expected),1)

    def test_illustrated_actions_and_equipment_fit_authored_frame(self):
        model,_=load_pack(Path(__file__).resolve().parents[1]/'aura/assets/aura-illustrated-rig/model.json')
        width,height=model.data['size']
        for motion in model.capabilities:
            for t in (0,.4,.8,1.6,2.4,2.8,3.2):
                box=model.render(t,motion,equipment=BUILTINS[:4],cast=t if motion=='cast' else -1).getbbox()
                self.assertGreater(box[0],0,(motion,t))
                self.assertGreater(box[1],0,(motion,t))
                self.assertLess(box[2],width,(motion,t))
                self.assertLess(box[3],height,(motion,t))

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

    def test_gaze_is_bounded_and_pause_ignores_it(self):
        first=self.model.pose(0,gaze=-10)['head'][2]
        second=self.model.pose(0,gaze=10)['head'][2]
        self.assertAlmostEqual(second-first,12)
        self.assertEqual(self.model.render(1,still=True,gaze=-1).tobytes(),
                         self.model.render(2,still=True,gaze=1).tobytes())

    def test_pause_freezes_secondary_motion_props_and_spells(self):
        items=BUILTINS[:4]
        self.assertEqual(self.model.render(1,'cast',still=True,equipment=items,cast=1).tobytes(),
                         self.model.render(15,'wave',still=True,equipment=items,cast=2).tobytes())
        self.assertNotEqual(self.model.render(.5,'cast',equipment=items,cast=.5).tobytes(),
                            self.model.render(1.5,'cast',equipment=items,cast=1.5).tobytes())
