use clap::Parser;
use std::io::{self, Write};
use std::process::Command;
use std::thread::sleep;
use std::time::Duration;

use crossterm::{
    cursor::MoveTo,
    execute,
    terminal::{Clear, ClearType},
};

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    #[arg(short, long, default_value_t = 2)]
    interval: u64,

    #[arg(long)]
    flush: bool,
}

fn main() {
    let args = Args::parse();
    let interval = Duration::from_secs(args.interval);
    let flush = args.flush;

    loop {
        let mut stdout = io::stdout();

        if flush {
            execute!(stdout, Clear(ClearType::All), MoveTo(0, 0)).unwrap();
        }

        let output = Command::new("gpustat").arg("--color").output();

        match output {
            Ok(output) => {
                io::stdout().write_all(&output.stdout).unwrap();
            }
            Err(e) => {
                eprintln!("Error: {}", e);
                break;
            }
        }

        io::stdout().flush().unwrap();

        sleep(interval);
    }
}
