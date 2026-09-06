import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from aura.core import Store, AuraError, DEFAULT_LOOK
from aura.equipment import Inventory, BUILTINS, validate_item
from aura.showcase import Scene, chapter, DURATION


class EquipmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'equipment.json'
        self.inventory=Inventory(self.path)

    def test_equip_replace_persist_undo_remove(self):
        self.inventory.equip('aura.fire')
        self.inventory.equip('aura.ice')
        self.assertEqual(Inventory(self.path).equipped,{'spell':'aura.ice'})
        self.inventory.undo()
        self.assertEqual(Inventory(self.path).equipped,{'spell':'aura.fire'})
        self.inventory.equip('aura.fire')
        self.assertEqual(Inventory(self.path).selected(),[])

    def test_import_is_declarative_and_attributed(self):
        source=Path(self.temp.name)/'custom.json'
        item=dict(BUILTINS[-1],id='creator.storm',name='Custom storm',author='Example creator',color='#44BBFF')
        source.write_text(json.dumps(item))
        self.inventory.import_item(source)
        self.inventory.equip('creator.storm')
        self.assertEqual(Inventory(self.path).selected()[0],item)
        with self.assertRaises(AuraError):self.inventory.import_item(source)
        for change in ({'script':'evil()'},{'asset':'../../private'},{'slot':'back'},{'color':'red'},{'schema':True},{'author':'Name\nspoof'}):
            with self.subTest(change=change),self.assertRaises(AuraError):validate_item(dict(item,**change))

    def test_corruption_preserved_and_failed_write_rolls_back(self):
        self.path.write_text('{broken')
        with self.assertRaises(AuraError):Inventory(self.path)
        self.assertEqual(self.path.read_text(),'{broken')
        with patch.object(self.inventory,'save',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.inventory.equip('aura.fire')
        self.assertEqual(self.inventory.equipped,{})

    def test_reset_and_oversize_import(self):
        self.inventory.equip('aura.dagger')
        huge=Path(self.temp.name)/'large.json';huge.write_text(' '*8193)
        with self.assertRaises(AuraError):self.inventory.import_item(huge)
        self.inventory.reset()
        self.assertFalse(self.path.exists())
        self.assertFalse(self.inventory.history)

    def test_cue_approval_is_required_and_at_most_once(self):
        store=Store(Path(self.temp.name)/'state.db')
        with self.assertRaises(AuraError):store.enqueue('cue',{'cue':'entrance'})
        store.preferences([], 'violet', False, True, False, False)
        request=store.enqueue('cue',{'cue':'entrance'})
        called=[]
        store.resolve(request['request_id'],True,lambda _:None,lambda p:called.append(p) or 'started')
        self.assertEqual(called,[{'cue':'entrance'}])
        with self.assertRaises(AuraError):store.resolve(request['request_id'],True,lambda _:None,lambda p:called.append(p))
        with self.assertRaises(AuraError):store.enqueue('cue',{'cue':'run shell'})
        store.set_paused(True)
        with self.assertRaises(AuraError):store.enqueue('cue',{'cue':'cast'})


class ShowcaseTests(unittest.TestCase):
    def test_all_chapters_and_boundary_frames_render(self):
        scene=Scene(dict(DEFAULT_LOOK,outfit='stealth',hair='pixie'))
        for t in (0,1.8,5.8,7.1,9,12,16,21,27,30,36,39,42,45,48,57,64):
            with self.subTest(time=t):
                frame=scene.frame(t)
                self.assertEqual(frame.size,(960,540))
                self.assertEqual(frame.mode,'RGB')
        self.assertEqual(chapter(57),6)

    def test_reduced_mode_skips_vehicle_and_preserves_input(self):
        look=dict(DEFAULT_LOOK,outfit='tactical')
        scene=Scene(look,reduced=True)
        with patch.object(scene,'arrival',side_effect=AssertionError('Must skip effects')):
            scene.frame(5)
        self.assertEqual(look,dict(DEFAULT_LOOK,outfit='tactical'))

if __name__=='__main__':unittest.main()
