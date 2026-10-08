# Parallel Search MCP example

This opt-in example loads free, keyless [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp) through s19's existing plugin discovery and agent loop. The pinned `mcp-remote@0.14.3` bridge connects the stdio client to `https://search.parallel.ai/mcp` using Streamable HTTP and sends `User-Agent: learn-claude-code-rs/0.1.0`. The root plugin manifest stays unchanged.

Install Rust (stable) and Node.js 22 or newer, including npm/npx. Configure `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL` and `ANTHROPIC_MODEL` for your Anthropic-compatible model as in the chapter. Model inference is separate from anonymous Parallel access. From the repository root:

```bash
cd s19_mcp_plugin/examples/parallel
cargo run -p s19_mcp_plugin --example parallel_search
```

Run in an interactive terminal from this directory so the loader discovers its `.claude-plugin/plugin.json`. On first use, npx downloads the pinned bridge from npm. Both installation and MCP calls need network access.

The example checks discovery of both tools, then asks the model to search for Rust learning resources, fetch a URL from the search results and answer using fetched content. It uses the same `LoopState::agent_loop`, native tool pool and permission manager as s19. `Default` mode is retained: these `web_*` names require approval under the chapter's existing classifier. Review each requested tool and its arguments, and choose **allow once** for each call. Do not switch modes or choose **always allow** to reproduce per-call approval. A 180-second asynchronous timeout bounds the example; interactive prompts still require a response. Model choices and answers vary.

For the chapter's full interactive UI, run `cargo run -p s19_mcp_plugin` here, choose **default**, then ask:

> Use Parallel web_search to find an official Rust learning resource. Then use web_fetch on a URL from those search results and explain how to start learning Rust using the fetched content. Include the source URL.

The current chapter sends a 500-character tool-result preview to the model. Long results may lose URLs or useful excerpts. Connection failures, denied permissions and remote tool errors must not be interpreted as successful research. Anonymous access has rate limits; see the service documentation for current limits.

## Reproduce the conversation with a local model fixture

A deterministic, result-dependent Anthropic-compatible fixture is included to exercise the normal agent path without external model credentials. It is **not a production model** and does not measure model answer quality. It never calls MCP itself: s19 executes real Parallel search and fetch after the normal permission prompts. The fixture chooses the fetch URL from the actual search preview and includes the actual fetched preview in its final reply. It fails if required tools or paired successful results are missing, or if no HTTPS URL survives the preview.

In one terminal, from this directory:

```bash
python3 model_fixture.py
```

In another terminal, also from this directory:

```bash
ANTHROPIC_API_KEY=local-fixture-placeholder \
ANTHROPIC_BASE_URL=http://127.0.0.1:8765/v1 \
ANTHROPIC_MODEL=parallel-local-fixture \
cargo run -p s19_mcp_plugin --example parallel_search
```

The placeholder is only for the localhost fixture. No Parallel API key is needed. Use **allow once** at both prompts. You can use the same environment with `cargo run -p s19_mcp_plugin` to exercise the full UI, selecting **default** and entering the task above. Use a fresh `MCP_REMOTE_CONFIG_DIR` and unset `PARALLEL_API_KEY` to isolate saved bridge credentials when checking anonymous access. The fixture logs model request/response bodies, including web excerpts, to its terminal; stop it with Ctrl-C after use. It binds only to localhost and requires only Python's standard library.

Fixture regressions (no network) can be run here with `python3 -m unittest test_model_fixture`. These checks do not replace a live, interactive agent conversation.
