#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::net::TcpListener;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::{Duration, Instant};
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

struct SidecarState(Mutex<Option<Child>>);

fn find_free_port() -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind port 0");
    listener.local_addr().unwrap().port()
}

fn wait_for_server(port: u16, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if TcpListener::bind(format!("127.0.0.1:{}", port)).is_err() {
            // Port is in use — server is up
            std::thread::sleep(Duration::from_millis(200));
            return true;
        }
        std::thread::sleep(Duration::from_millis(400));
    }
    false
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(SidecarState(Mutex::new(None)))
        .setup(|app| {
            let port = find_free_port();

            // Locate sidecar next to our own executable
            let exe_dir = std::env::current_exe()
                .unwrap()
                .parent()
                .unwrap()
                .to_path_buf();
            let sidecar = exe_dir.join("loop_creator_server");

            let child = Command::new(&sidecar)
                .arg("--port")
                .arg(port.to_string())
                .spawn()
                .unwrap_or_else(|e| panic!("Failed to start loop_creator_server: {e}"));

            *app.state::<SidecarState>().0.lock().unwrap() = Some(child);

            if !wait_for_server(port, Duration::from_secs(15)) {
                eprintln!("loop_creator_server did not start in time");
            }

            // Build window programmatically so we can inject __LC_PORT__ before
            // the page executes any JS — WebviewWindowBuilder::initialization_script
            // runs before any page content loads, avoiding the timing issues that
            // window.eval() after load would have.
            WebviewWindowBuilder::new(
                app,
                "main",
                WebviewUrl::App("index.html".into()),
            )
            .title("Forge")
            .inner_size(1280.0, 840.0)
            .initialization_script(&format!("window.__LC_PORT__ = {};", port))
            .build()?;

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(mut child) =
                    app.state::<SidecarState>().0.lock().unwrap().take()
                {
                    let _ = child.kill();
                }
            }
        });
}
