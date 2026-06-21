# loop-creator

## Sub-project 2 — macOS Tauri App

A native macOS desktop app that provides a Warp-themed GUI for the loop-creator.

### Prerequisites

- Rust (stable) — `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Node.js 20+
- Tauri CLI — `cargo install tauri-cli --version "^2"`
- Python 3.11+

### Build

```bash
cd tauri-app

# 1. Bundle Python server
bash scripts/build.sh

# 2. Build and launch the Tauri app
cargo tauri dev   # dev mode (requires npm run dev running in tauri-app/web/)
# or
cargo tauri build # production .app + .dmg
```

### Development

```bash
# Terminal 1 — Python server (hot reload)
cd tauri-app && pip install -e ../ fastapi uvicorn
python run_server.py --port 5001

# Terminal 2 — React frontend
cd tauri-app/web && npm run dev

# Terminal 3 — Tauri shell (points at Vite dev server)
cd tauri-app/src-tauri && cargo tauri dev
```

### Running tests

```bash
# Python server tests
cd tauri-app && python -m pytest tests/server/ -v

# React component tests
cd tauri-app/web && npm test
```
