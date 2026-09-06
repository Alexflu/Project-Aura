import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from aura.models import load_pack, import_pack
from aura.tray import Preferences, Instance
from aura.core import AuraError
from aura.app_audio import AppMeter

REFERENCE=Path(__file__).resolve().parents[1]/'aura/assets/rig-reference/model.json'

class RigTests(unittest.TestCase):
    def test_shared_motions_and_contact(self):
        model,_=load_pack(REFERENCE)
        self.assertEqual(set(model.capabilities),{'idle','inspect','wave','draw'})
        idle=model.render(0)
        wave=model.render(1,'wave')
        self.assertNotEqual(idle.tobytes(),wave.tobytes())
        for t in (.7,2.6):
            pose=model.pose(t,'draw');hand=model.socket('hand_right',pose);holster=model.socket('holster_right',pose)
            self.assertLess(math.hypot(hand[0]-holster[0],hand[1]-holster[1]),1)
        self.assertEqual(model.render(1,'wave',still=True).tobytes(),idle.tobytes())

    def test_import_copies_validated_assets_and_rejects_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            copied,model=import_pack(REFERENCE,Path(temp)/'models')
            self.assertTrue(copied.exists())
            second,_=load_pack(copied)
            self.assertEqual(second.data,model.data)
            raw=json.loads(copied.read_text());raw['layers'][0]['asset']='../outside.png';copied.write_text(json.dumps(raw))
            with self.assertRaises(AuraError):load_pack(copied)

    def test_cycles_nan_unknown_fields_rejected(self):
        for mutate in (lambda d:d.update(script='run()'),lambda d:d['bones'][0].update(parent='head'),
                       lambda d:d['bones'][1].update(position=[float('nan'),0]),lambda d:d['bones'][1].update(parent=[]), lambda d:d['sockets']['mouth'].update(bone=[]),
                       lambda d:d['layers'][0].update(bone={})):
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/'model.json';data=json.loads(REFERENCE.read_text());mutate(data);path.write_text(json.dumps(data))
                with self.assertRaises(AuraError):load_pack(path)

class TrayTests(unittest.TestCase):
    def test_visibility_persists_and_invalid_settings_recover_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'ui.json';settings=Preferences(path)
            settings.save(False);self.assertFalse(Preferences(path).tray_visible)
            path.write_text('{broken');self.assertTrue(Preferences(path).tray_visible)
            self.assertEqual(path.read_text(),'{broken')

    def test_relaunch_signals_existing_profile(self):
        import os
        if os.name!='nt':self.skipTest('Windows recovery primitive')
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'state.db';first=Instance(path)
            try:
                second=Instance(path)
                try:self.assertFalse(second.primary);self.assertTrue(first.requested());self.assertFalse(first.requested())
                finally:second.close()
            finally:first.close()
            third=Instance(path)
            try:self.assertTrue(third.primary)
            finally:third.close()

class MeterTests(unittest.TestCase):
    def test_levels_are_bounded_and_pid_reuse_disconnects(self):
        meter=AppMeter.__new__(AppMeter);meter.process=Mock();meter.created=1
        meter.process.is_running.return_value=True;meter.process.create_time.return_value=1
        meter.meter=Mock()
        for raw,want in ((.2,.5),(4,1),(-1,0),(float('nan'),0)):
            meter.meter.GetPeakValue.return_value=raw;self.assertEqual(meter.level(),want)
        meter.process.create_time.return_value=2
        with self.assertRaises(AuraError):meter.level()

if __name__=='__main__':unittest.main()
