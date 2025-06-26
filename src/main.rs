use anyhow::Result;
use clap::Parser;
use ccmonitor::{monitor::Monitor, cli::Cli};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    // Parse command line arguments
    let cli = Cli::parse();

    // Create and run monitor
    let mut monitor = Monitor::new()?;
    
    if cli.summary {
        monitor.show_summary().await?;
    } else {
        monitor.run().await?;
    }

    Ok(())
}