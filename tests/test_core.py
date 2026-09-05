import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from concurrent.futures import ThreadPoolExecutor
from aura.core import Store, AuraError, DEFAULT_LOOK, validate_look, parse_request
from aura.bridge import launch


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / "aura.db")

    def prefs(self, **kwargs):
        args = dict(interests=["making", "music"], favorite="ocean", adapt=False, bridge=True, share=False, reduced_motion=False)
        args.update(kwargs)
        self.store.preferences(**args)

    def test_default_is_private(self):
        s = self.store.read()
        self.assertFalse(s["bridge"] or s["share"] or s["adapt"])
        with self.assertRaises(AuraError):
            self.store.public_state()
        with self.assertRaises(AuraError):
            self.store.enqueue("launch", {"app": "notepad"})

    def test_arbitrary_model_properties_rejected(self):
        for value in ({"script": "run.exe"}, {"palette": "#bad"}, {"outfit": ["tactical"]}, {}, None):
            with self.subTest(value=value), self.assertRaises(AuraError):
                validate_look(value, partial=True)

    def test_persistence_and_undo(self):
        look = dict(DEFAULT_LOOK, hair="bob")
        self.store.apply(look)
        reopened = Store(self.store.path)
        self.assertEqual(reopened.read()["look"], look)
        reopened.undo()
        self.assertEqual(self.store.read()["look"], DEFAULT_LOOK)

    def test_history_is_bounded(self):
        for i in range(30):
            self.store.apply(dict(DEFAULT_LOOK, hair="bob" if i%2 else "pixie"))
        with self.store.connection() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM history").fetchone()[0], 20)

    def test_only_explicit_activity_drives_adaptation(self):
        self.prefs()
        self.store.record_activity("music")
        self.assertEqual(self.store.read()["look"], DEFAULT_LOOK)
        self.prefs(adapt=True)
        self.store.record_activity("music")
        self.assertEqual(self.store.read()["look"]["accessory"], "headphones")
        self.assertEqual(self.store.read()["look"]["palette"], "ocean")
        self.store.undo()
        self.assertEqual(self.store.read()["look"], DEFAULT_LOOK)

    def test_unshared_habits_stay_private(self):
        self.prefs()
        self.store.record_activity("music")
        self.assertNotIn("preferences", self.store.public_state())
        self.prefs(share=True)
        self.assertEqual(self.store.public_state()["preferences"]["interests"], ["making", "music"])
        self.assertNotIn("habits", self.store.public_state())

    def test_not_selected_interest_cannot_be_recorded(self):
        with self.assertRaises(AuraError):
            self.store.record_activity("gaming")

    def test_pending_proposal_does_not_change_appearance(self):
        self.prefs(adapt=True)
        req = self.store.enqueue("appearance", {"hair": "pixie"})
        self.assertEqual(self.store.read()["look"], DEFAULT_LOOK)
        self.assertEqual(req["status"], "pending")
        self.store.resolve(req["request_id"], True, Mock())
        self.assertEqual(self.store.read()["look"]["hair"], "pixie")
        self.assertEqual(self.store.request_status(req["request_id"])["status"], "applied")

    def test_rejection_never_launches(self):
        self.prefs()
        fn = Mock()
        req = self.store.enqueue("launch", {"app": "notepad"})
        self.store.resolve(req["request_id"], False, fn)
        fn.assert_not_called()

    def test_launch_at_most_once(self):
        self.prefs()
        fn = Mock(return_value="Submitted")
        req = self.store.enqueue("launch", {"app": "notepad"})
        self.store.resolve(req["request_id"], True, fn)
        with self.assertRaises(AuraError):
            self.store.resolve(req["request_id"], True, fn)
        fn.assert_called_once_with("notepad")
        self.assertEqual(self.store.request_status(req["request_id"])["status"], "submitted")

    def test_concurrent_review_does_not_duplicate_launch(self):
        self.prefs()
        req = self.store.enqueue("launch", {"app": "notepad"})
        fn = Mock(return_value="Submitted")
        def accept():
            try:
                return self.store.resolve(req["request_id"], True, fn)
            except AuraError:
                return "already claimed"
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: accept(), range(2)))
        fn.assert_called_once()

    def test_launch_failure_is_reported_without_retry(self):
        self.prefs()
        fn = Mock(side_effect=OSError("failure"))
        req = self.store.enqueue("launch", {"app": "notepad"})
        self.store.resolve(req["request_id"], True, fn)
        self.assertEqual(self.store.request_status(req["request_id"])["status"], "failed")
        fn.assert_called_once()

    def test_pause_blocks_mutation_and_cancels_queue(self):
        self.prefs(adapt=True)
        req = self.store.enqueue("launch", {"app": "notepad"})
        self.store.set_paused(True)
        self.assertEqual(self.store.pending(), [])
        for action in (lambda: self.store.apply(DEFAULT_LOOK), lambda: self.store.record_activity("music"),
                       lambda: self.store.enqueue("appearance", {"hair": "bob"}),
                       lambda: self.store.resolve(req["request_id"], True, Mock())):
            with self.assertRaises(AuraError):
                action()
        self.assertEqual(self.store.request_status(req["request_id"])["status"], "cancelled")

    def test_disconnect_cancels_pending(self):
        self.prefs()
        req = self.store.enqueue("appearance", {"hair": "bob"})
        self.prefs(bridge=False)
        self.assertEqual(self.store.request_status(req["request_id"])["status"], "cancelled")

    def test_expired_request_cannot_execute(self):
        self.prefs()
        req = self.store.enqueue("launch", {"app": "notepad"})
        with self.store.connection() as db:
            db.execute("UPDATE requests SET created=0")
        self.assertEqual(self.store.pending(), [])
        with self.assertRaises(AuraError):
            self.store.resolve(req["request_id"], True, Mock())

    def test_queue_limit(self):
        self.prefs()
        for _ in range(10):
            self.store.enqueue("appearance", {"hair": "bob"})
        with self.assertRaises(AuraError):
            self.store.enqueue("appearance", {"hair": "bob"})

    def test_unknown_commands_and_paths_rejected(self):
        self.prefs()
        for kind, payload in (("shell", {"command": "echo hi"}), ("launch", {"app": "cmd"}),
                              ("launch", {"app": "notepad", "args": "file"})):
            with self.assertRaises(AuraError):
                self.store.enqueue(kind, payload)
        with self.assertRaises(AuraError):
            launch("../../cmd.exe")

    def test_forget_clears_history_queue_preferences(self):
        self.prefs()
        self.store.apply(dict(DEFAULT_LOOK, hair="bob"))
        self.store.enqueue("appearance", {"hair": "pixie"})
        self.store.forget()
        self.assertEqual(self.store.read(), Store.defaults())
        self.assertEqual(self.store.pending(), [])
        with self.assertRaises(AuraError):
            self.store.undo()

    def test_corrupt_state_not_silently_replaced(self):
        with self.store.connection() as db:
            db.execute("UPDATE state SET value='broken'")
        with self.assertRaises(AuraError):
            Store(self.store.path)
        with self.store.connection() as db:
            self.assertEqual(db.execute("SELECT value FROM state").fetchone()[0], "broken")

    def test_future_schema_not_downgraded(self):
        with self.store.connection() as db:
            db.execute("PRAGMA user_version=99")
        with self.assertRaises(AuraError):
            Store(self.store.path)
        with self.store.connection() as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 99)

    def test_request_parser_is_bounded_and_honest(self):
        self.assertEqual(parse_request("ocean bob with headphones"), {"palette": "ocean", "hair": "bob", "accessory": "headphones"})
        for text in ("not tactical", "violet ocean", "write a story", "a" * 1001):
            with self.assertRaises(AuraError):
                parse_request(text)


if __name__ == "__main__":
    unittest.main()
