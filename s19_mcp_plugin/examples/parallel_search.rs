//! Run from examples/parallel so the normal plugin loader finds its manifest.
use anthropic_ai_sdk::types::message::{Message, Role};
use anyhow::{Context, Result, ensure};
use s19_mcp_plugin::{
    LoopState, extract_text, get_llm_client, load_mcp_router,
    permission::{PermissionManager, PermissionMode},
    tool::toolset,
};
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    tokio::time::timeout(Duration::from_secs(180), run())
        .await
        .context("Parallel example timed out")?
}

async fn run() -> Result<()> {
    let client = get_llm_client()?;
    let router = load_mcp_router().await?;
    let mut state = LoopState::new(
        client,
        toolset(),
        router,
        PermissionManager::try_new(PermissionMode::Default)?,
    );
    let result = async {
        let tools = state.mcp_router.all_tools();
        for name in ["web_search", "web_fetch"] {
            ensure!(
                tools.iter().any(|tool| tool.name == format!("mcp__parallel-search__search__{name}")),
                "Missing {name}; run from s19_mcp_plugin/examples/parallel and check the connection log"
            );
        }
        state.context.push(Message::new_text(
            Role::User,
            "Use Parallel web_search to find an official Rust learning resource. Then use \
             web_fetch on a URL from those search results and explain how to start learning \
             Rust using the fetched content. Include the source URL.".to_string(),
        ));
        state.agent_loop().await?;
        if let Some(message) = state.context.last() {
            println!("Final response:\n{}", extract_text(&message.content));
        }
        Ok(())
    }.await;
    state.mcp_router.disconnect_all().await;
    result
}
