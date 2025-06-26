use ccmonitor::{claude_logs::load_sessions_in_timerange, timeline_monitor::TimelineMonitor};
use clap::Parser;
use chrono::{Duration, Local};

fn format_number(num: u32) -> String {
    // Simple number formatting with commas
    let num_str = num.to_string();
    let len = num_str.len();
    let mut result = String::new();
    
    for (i, ch) in num_str.chars().enumerate() {
        if i > 0 && (len - i) % 3 == 0 {
            result.push(',');
        }
        result.push(ch);
    }
    
    result
}

fn is_wsl_or_problematic_terminal() -> bool {
    // Check for WSL environment
    if std::env::var("WSL_DISTRO_NAME").is_ok() {
        return true;
    }
    
    // Check for other problematic environments
    match std::env::var("TERM") {
        Ok(term) => {
            // Some terminals have issues with raw mode
            term.contains("dumb") || term.contains("unknown")
        }
        Err(_) => true, // No TERM variable suggests problematic environment
    }
}

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

    /// Use simple text output instead of TUI
    #[arg(long)]
    simple: bool,

    /// Force TUI mode (may fail in some environments)
    #[arg(long)]
    tui: bool,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();

    // Default to simple mode unless TUI is explicitly requested
    let use_simple = args.simple || (!args.tui && is_wsl_or_problematic_terminal());
    
    if use_simple {
        // Simple text output mode
        let now = Local::now();
        let end_time = now;
        let start_time = end_time - Duration::days(args.days);

        eprintln!("Loading Claude sessions from the last {} days...", args.days);
        if let Some(ref project) = args.project {
            eprintln!("Filtering by project: {}", project);
        }

        let timelines = load_sessions_in_timerange(
            start_time,
            end_time,
            args.project.as_deref(),
            args.threads,
        )?;

        if timelines.is_empty() {
            println!("No Claude sessions found in the specified time range.");
            return Ok(());
        }

        // Simple text output
        println!("\n📊 Claude Project Timeline");
        println!("Time range: {} - {}", 
            start_time.format("%m/%d/%Y %H:%M"), 
            end_time.format("%m/%d/%Y %H:%M")
        );
        println!("Projects found: {}\n", timelines.len());

        for timeline in &timelines {
            let project_display = if let Some(ref _parent) = timeline.parent_project {
                format!(" └─{}", timeline.project_name)
            } else {
                timeline.project_name.clone()
            };

            let input_tokens = if timeline.total_input_tokens > 0 {
                format_number(timeline.total_input_tokens)
            } else {
                "-".to_string()
            };
            
            let output_tokens = if timeline.total_output_tokens > 0 {
                format_number(timeline.total_output_tokens)
            } else {
                "-".to_string()
            };

            println!("Project: {}", project_display);
            println!("  Events: {}", timeline.events.len());
            println!("  Input tokens: {}", input_tokens);
            println!("  Output tokens: {}", output_tokens);
            println!("  Duration: {}m", timeline.active_duration_minutes);
            println!("  Time: {} - {}", 
                timeline.start_time.format("%H:%M"), 
                timeline.end_time.format("%H:%M")
            );
            println!();
        }

        // Summary
        let total_events: usize = timelines.iter().map(|t| t.events.len()).sum();
        let total_projects = timelines.len();
        
        if let Some(most_active) = timelines.iter().max_by_key(|t| t.events.len()) {
            let avg_duration: f64 = timelines
                .iter()
                .map(|t| t.active_duration_minutes as f64)
                .sum::<f64>() / total_projects as f64;

            println!("Summary Statistics:");
            println!("  • Total Projects: {}", total_projects);
            println!("  • Total Events: {}", total_events);
            println!("  • Average Duration: {:.1} minutes", avg_duration);
            println!("  • Most Active Project: {} ({} events)", 
                most_active.project_name, most_active.events.len());
        }
    } else {
        // TUI mode
        let monitor = TimelineMonitor::new(args.days, args.project, args.threads);
        
        match monitor.run().await {
            Ok(()) => {
                eprintln!("👋 Exiting.");
            }
            Err(e) => {
                eprintln!("❌ TUI Error: {}", e);
                eprintln!("Try running with --simple flag for text output");
                std::process::exit(1);
            }
        }
    }

    Ok(())
}