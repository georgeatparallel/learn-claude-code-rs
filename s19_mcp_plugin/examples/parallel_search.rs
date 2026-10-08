//! Run from examples/parallel so the normal plugin loader finds its manifest.
use anyhow::{Context, Result, ensure};
use s19_mcp_plugin::load_mcp_router;
use serde_json::json;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    tokio::time::timeout(Duration::from_secs(180), run())
        .await
        .context("Parallel example timed out")?
}

async fn run() -> Result<()> {
    let mut router = load_mcp_router().await?;
    let result = async {
        let tools = router.all_tools();
        for name in ["web_search", "web_fetch"] {
            ensure!(
                tools.iter().any(|tool| tool.name == format!("mcp__parallel-search__search__{name}")),
                "Missing {name}; run from s19_mcp_plugin/examples/parallel and check the connection log"
            );
        }
        let search = router.call(
            "mcp__parallel-search__search__web_search",
            json!({"objective": "Find the official Rust getting started guide", "search_queries": ["Rust getting started official rust-lang.org"]}),
        ).await?;
        println!("Search:\n{search}");
        let fetch = router.call(
            "mcp__parallel-search__search__web_fetch",
            json!({"urls": ["https://www.rust-lang.org/learn"], "objective": "Extract the Rust learning resources"}),
        ).await?;
        println!("Fetch:\n{fetch}");
        Ok(())
    }.await;
    router.disconnect_all().await;
    result
}
