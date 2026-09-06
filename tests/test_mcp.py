"""Real SDK client -> subprocess -> SQLite -> local approval integration test."""
import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest
from aura.core import Store, DEFAULT_LOOK

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


@unittest.skipUnless(HAS_MCP, "Install requirements-mcp.txt to test the optional adapter")
class McpTests(unittest.TestCase):
    def test_real_stdio_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Store(Path(temp) / "state.db")
            async def run():
                params = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).resolve().parents[1] / "run_aura.py"), "--mcp", "--data", str(store.path)])
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as client:
                        await client.initialize()
                        tools = await client.list_tools()
                        names = {t.name for t in tools.tools}
                        self.assertEqual(names, {"aura_status", "aura_propose_appearance", "aura_request_notepad", "aura_request_status", "aura_propose_performance", "aura_propose_cue"})
                        self.assertNotIn("aura_approve", names)
                        denied = await client.call_tool("aura_status", {})
                        self.assertTrue(denied.is_error)
                        store.preferences(["music"], "ocean", False, True, False, False)
                        result = await client.call_tool("aura_propose_appearance", {"hair": "bob", "palette": "ocean", "outfit": "stealth"})
                        self.assertFalse(result.is_error)
                        data = json.loads(result.content[0].text)
                        self.assertEqual(store.read()["look"]["hair"], DEFAULT_LOOK["hair"])
                        store.resolve(data["request_id"], True, lambda _: self.fail("Must not launch"))
                        status = await client.call_tool("aura_request_status", {"request_id": data["request_id"]})
                        self.assertEqual(json.loads(status.content[0].text)["status"], "applied")
                        self.assertEqual(store.read()["look"]["hair"], "bob")
                        self.assertEqual(store.read()["look"]["outfit"], "stealth")
                        bad = await client.call_tool("aura_propose_appearance", {"palette": "javascript:alert(1)"})
                        self.assertTrue(bad.is_error)
                        proposed = await client.call_tool("aura_propose_performance", {"text": "Hello Alex", "mood": "happy"})
                        self.assertFalse(proposed.is_error)
                        perf = json.loads(proposed.content[0].text)
                        played = []
                        store.resolve(perf["request_id"], True, lambda _: None, lambda payload: played.append(payload) or "queued")
                        self.assertEqual(played, [{"text": "Hello Alex", "mood": "happy"}])
                        proposed_cue = await client.call_tool("aura_propose_cue", {"cue": "entrance"})
                        self.assertFalse(proposed_cue.is_error)
                        cue = json.loads(proposed_cue.content[0].text)
                        self.assertEqual(store.request_status(cue["request_id"])["status"], "pending")
                        for motion in ("wave", "inspect", "draw"):
                            rig_cue = await client.call_tool("aura_propose_cue", {"cue": motion})
                            self.assertFalse(rig_cue.is_error)
                            request_id = json.loads(rig_cue.content[0].text)["request_id"]
                            self.assertEqual(store.request_status(request_id)["status"], "pending")
                        denied_cue = await client.call_tool("aura_propose_cue", {"cue": "execute"})
                        self.assertTrue(denied_cue.is_error)
                        store.set_paused(True)
                        denied = await client.call_tool("aura_request_notepad", {})
                        self.assertTrue(denied.is_error)
            asyncio.run(run())

