"""Local, deterministic Anthropic-compatible fixture; not a production model.

It returns tool_use blocks to s19's normal agent loop, never calls MCP itself,
and chooses the fetch URL and final excerpt from the tool results s19 sends.
Only the Python standard library is needed. Bind to localhost only.
"""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import re

PREFIX = "mcp__parallel-search__search__"
SEARCH = {
    "objective": "Find an official Rust learning resource",
    "search_queries": ["official Rust learn rust-lang.org"],
}
FETCH_OBJECTIVE = "Extract guidance for starting to learn Rust"


def tool_result(messages, tool):
    """Require the exact tool_use/result pairing, successful MCP payload and content."""
    calls = {}
    for message in messages:
        content = message.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if block.get("type") == "tool_use":
                calls[block["id"]] = block
            elif block.get("type") == "tool_result":
                call = calls.get(block["tool_use_id"], {})
                if call.get("name") != PREFIX + tool:
                    continue
                payload = json.loads(block["content"])
                if (payload.get("status") != "ok" or payload.get("source") != "mcp"
                        or payload.get("server") != "parallel-search__search"
                        or payload.get("tool") != tool or not payload.get("preview")):
                    raise ValueError("Tool failed, was denied, or returned no usable preview")
                return call["input"], payload["preview"]
    raise ValueError("Missing paired " + tool + " result")


def first_url(preview):
    # s19 deliberately sends only a 500-character preview. Fail if no URL survives.
    for match in re.finditer(r'https?://[^\s<>"\\]+', preview):
        if match.end() == len(preview):
            continue  # The preview may have cut the URL off mid-path.
        url = match.group().rstrip('.,;)]}')
        if url.startswith("https://"):
            return url
    raise ValueError("No complete HTTPS URL in search preview; cannot choose fetch target")


def reply(request):
    names = {tool["name"] for tool in request.get("tools", [])}
    if not {PREFIX + "web_search", PREFIX + "web_fetch"} <= names:
        raise ValueError("Both Parallel tools must be discovered by s19")
    messages = request["messages"]
    results = [block for message in messages
               if isinstance(message.get("content"), list)
               for block in message["content"] if block.get("type") == "tool_result"]
    if not results:
        content = [{"type": "tool_use", "id": "parallel_search_1",
                    "name": PREFIX + "web_search", "input": SEARCH}]
    else:
        search_input, search_preview = tool_result(messages, "web_search")
        if search_input != SEARCH:
            raise ValueError("Unexpected search arguments")
        url = first_url(search_preview)
        fetch_input = {"urls": [url], "objective": FETCH_OBJECTIVE}
        if len(results) == 1:
            content = [{"type": "tool_use", "id": "parallel_fetch_1",
                        "name": PREFIX + "web_fetch", "input": fetch_input}]
        elif len(results) == 2:
            actual_input, fetched = tool_result(messages, "web_fetch")
            if actual_input != fetch_input:
                raise ValueError("Fetch must use the URL chosen from actual search results")
            content = [{"type": "text", "text":
                        "Local fixture reply using fetched content from " + url
                        + ":\n" + fetched
                        + "\nThis is a deterministic excerpt demonstration, not a production model answer."}]
        else:
            raise ValueError("Unexpected extra tool results")
    return {"id": "msg_parallel_fixture", "type": "message", "role": "assistant",
            "model": "parallel-local-fixture", "content": content,
            "stop_reason": "tool_use" if content[0]["type"] == "tool_use" else "end_turn",
            "stop_sequence": None, "usage": {"input_tokens": 0, "output_tokens": 0}}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/messages":
            self.send_error(404)
            return
        try:
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            response = reply(request)
        except (ValueError, KeyError, TypeError) as error:
            self.send_error(400, str(error))
            return
        # Log the conversation, not headers/API keys. These contain live web excerpts.
        print(json.dumps({"request": request, "response": response}), flush=True)
        data = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print("Local model fixture on http://127.0.0.1:" + str(args.port), flush=True)
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
