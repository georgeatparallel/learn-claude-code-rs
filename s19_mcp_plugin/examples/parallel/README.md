# Parallel Search MCP example

This opt-in example loads free, keyless [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp) through the chapter's existing stdio plugin loader. The pinned `mcp-remote@0.14.3` bridge connects to `https://search.parallel.ai/mcp` with Streamable HTTP and sends `User-Agent: learn-claude-code-rs/0.1.0`. The root plugin manifest stays unchanged.

Install Rust (stable) and Node.js 22 or newer, including npm/npx. From the repository root:

```bash
cd s19_mcp_plugin/examples/parallel
cargo run -p s19_mcp_plugin --example parallel_search
```

On first use, npx downloads the pinned bridge from npm, so network access is required for installation as well as requests. The local `.claude-plugin/plugin.json` is discovered relative to the current directory. Run from this directory, not the repository root.

The Rust example uses `load_mcp_router`, checks that both tools were discovered, then calls `web_search` for Rust learning resources and `web_fetch` for the Rust learning page through `MCPToolRouter`. It prints the returned excerpts and disconnects. A 180-second deadline bounds the example. It does not invoke a model or require an Anthropic or Parallel API key.

Anonymous access is intended for exploration and light use and has rate limits. A connection or missing-tool error causes the example to fail; remote tool errors may appear in the printed output. See the service documentation for current limits. This example exercises tool routing directly, without an agent conversation.
