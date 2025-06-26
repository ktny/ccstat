use clap::Parser;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    /// Show summary only (no real-time monitoring)
    #[arg(short, long)]
    pub summary: bool,
}