use ccmonitor::timeline_monitor::TimelineMonitor;
use clap::Parser;

#[derive(Parser)]
#[command(
    name = "ccmonitor",
    about = "Claude Session Timeline - Claudeセッションの時系列可視化ツール",
    version
)]
struct Args {
    /// Number of days to look back (default: 1)
    #[arg(long, default_value = "1")]
    days: i64,

    /// Filter by specific project
    #[arg(long)]
    project: Option<String>,

    /// Show projects as threads (separate similar repos)
    #[arg(long)]
    threads: bool,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();

    let monitor = TimelineMonitor::new(args.days, args.project, args.threads);
    
    match monitor.run().await {
        Ok(()) => {
            eprintln!("👋 Exiting.");
        }
        Err(e) => {
            eprintln!("❌ Error: {}", e);
            std::process::exit(1);
        }
    }

    Ok(())
}
