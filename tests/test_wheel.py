"""Keyboard regression checks against real Tk canvas bindings."""
import tkinter as tk
import unittest
from unittest.mock import Mock

from aura.wheel import ControlWheel


class WheelTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.addCleanup(self.root.destroy)
        self.button = tk.Button(self.root, text="Controls")
        self.button.pack()
        self.canvas = tk.Canvas(self.root, width=280, height=540)
        self.canvas.pack()
        self.actions = [Mock(), Mock(), Mock()]
        self.wheel = ControlWheel(self.canvas, list(zip(("Look", "Voice", "Menu"), self.actions)))
        self.wheel.stop()
        self.root.update()
        self.button.focus_force()
        self.root.update()

    def press(self, key):
        self.canvas.event_generate("<KeyPress-" + key + ">")
        self.root.update()

    def test_navigation_wraps_and_enter_activates_once(self):
        self.wheel.toggle()
        self.root.update()
        self.assertEqual(self.root.focus_get(), self.canvas)
        self.press("Left")
        self.assertEqual(self.wheel.selected, 2)
        self.assertEqual(self.canvas.itemcget("wheel-2-outline", "width"), "3.0")
        self.press("Right")
        self.assertEqual(self.wheel.selected, 0)
        self.press("Down")
        self.press("Return")
        self.actions[1].assert_called_once_with()
        self.actions[0].assert_not_called()
        self.actions[2].assert_not_called()
        self.assertFalse(self.canvas.find_withtag("wheel"))
        self.assertEqual(self.root.focus_get(), self.button)

    def test_escape_is_consumed_and_restores_focus(self):
        escaped = Mock()
        self.root.bind("<Escape>", escaped)
        self.wheel.toggle()
        self.root.update()
        self.press("Escape")
        escaped.assert_not_called()
        self.assertFalse(self.wheel.pinned)
        self.assertIsNone(self.wheel.key)
        self.assertEqual(self.root.focus_get(), self.button)
        for action in self.actions:
            action.assert_not_called()

    def test_selection_survives_redraw_and_space_activates(self):
        self.wheel.toggle()
        self.root.update()
        self.press("Up")
        self.canvas.configure(width=320)
        self.root.update()
        self.wheel.show()
        self.assertEqual(self.wheel.selected, 2)
        self.assertEqual(self.canvas.itemcget("wheel-2-outline", "width"), "3.0")
        self.press("space")
        self.actions[2].assert_called_once_with()
        self.wheel.toggle()
        self.assertEqual(self.wheel.selected, 0)
        self.wheel.toggle()
        self.assertFalse(self.wheel.pinned)

    def test_hover_controls_do_not_capture_keyboard(self):
        self.wheel.show()
        self.assertEqual(self.root.focus_get(), self.button)
        event = Mock(keysym="Return", state=0)
        self.assertIsNone(self.wheel.on_key(event))
        for action in self.actions:
            action.assert_not_called()

    def test_control_space_closes_without_activating(self):
        self.root.bind_all("<Control-space>", lambda event: self.wheel.toggle())
        self.wheel.toggle()
        self.root.update()
        self.canvas.event_generate("<Control-KeyPress-space>")
        self.root.update()
        self.assertFalse(self.wheel.pinned)
        for action in self.actions:
            action.assert_not_called()
