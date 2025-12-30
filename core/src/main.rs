use tracing::info;

mod wifi;
mod network;
mod packet;
mod crypto;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    info!("Cyper Core Engine starting...");

    // Load configuration
    dotenv::dotenv().ok();
    
    info!("Cyper Core Engine initialized successfully");

    Ok(())
}
