"""Regression checks for the result-dependent fixture, not live MCP validation."""
import copy
import json
import unittest
from model_fixture import PREFIX, SEARCH, reply


def request():
    return {"tools": [{"name": PREFIX + name} for name in ["web_search", "web_fetch"]],
            "messages": [{"role": "user", "content": "Find Rust learning resources"}]}


def append_result(req, response, tool, preview, status="ok"):
    req["messages"].append({"role": "assistant", "content": response["content"]})
    req["messages"].append({"role": "user", "content": [{"type": "tool_result",
        "tool_use_id": response["content"][0]["id"], "content": json.dumps({
            "status": status, "source": "mcp", "server": "parallel-search__search",
            "tool": tool, "preview": preview})}]})


class FixtureTests(unittest.TestCase):
    def test_fetch_and_final_reply_depend_on_each_result(self):
        for url, text in [("https://example.org/one", "Try the Rust book"),
                          ("https://example.org/two", "Practice with Rustlings")]:
            req = request()
            search = reply(req)
            self.assertEqual(search["content"][0]["input"], SEARCH)
            append_result(req, search, "web_search", "URL: " + url + "\nExcerpt")
            fetch = reply(req)
            self.assertEqual(fetch["content"][0]["input"]["urls"], [url])
            append_result(req, fetch, "web_fetch", text)
            final = reply(req)
            self.assertEqual(final["stop_reason"], "end_turn")
            self.assertIn(url, final["content"][0]["text"])
            self.assertIn(text, final["content"][0]["text"])
            broken = copy.deepcopy(req)
            broken["messages"][-2]["content"][0]["input"]["urls"] = ["https://wrong.example"]
            with self.assertRaises(ValueError):
                reply(broken)

    def test_denied_missing_or_unusable_results_fail(self):
        for preview, status in [("Permission denied", "error"), ("no URL", "ok"),
                                ("https://example.org/cut", "ok")]:
            req = request()
            append_result(req, reply(req), "web_search", preview, status)
            with self.assertRaises(ValueError):
                reply(req)
        req = request()
        append_result(req, reply(req), "web_search", "https://example.org/one\n")
        req["messages"][-1]["content"][0]["tool_use_id"] = "unpaired"
        with self.assertRaises(ValueError):
            reply(req)
        req = request()
        req["tools"].pop()
        with self.assertRaises(ValueError):
            reply(req)


if __name__ == "__main__":
    unittest.main()
