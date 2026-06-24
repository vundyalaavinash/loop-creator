#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT/.pids"
LOG_DIR="$ROOT/.logs"

SERVER_PID="$PID_DIR/server.pid"
WEB_PID="$PID_DIR/web.pid"
SERVER_LOG="$LOG_DIR/server.log"
WEB_LOG="$LOG_DIR/web.log"

GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; DIM="\033[2m"; RESET="\033[0m"

_ok()  { echo -e "${GREEN}✓${RESET}  $*"; }
_info(){ echo -e "${DIM}→${RESET}  $*"; }
_warn(){ echo -e "${YELLOW}!${RESET}  $*"; }
_err() { echo -e "${RED}✗${RESET}  $*"; }

mkdir -p "$PID_DIR" "$LOG_DIR"

# ── helpers ───────────────────────────────────────────────────────────────────

_is_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null
}

_kill_pid() {
  local pid_file="$1" label="$2"
  if _is_running "$pid_file"; then
    kill "$(cat "$pid_file")" 2>/dev/null && _ok "Stopped $label"
  else
    _info "$label not running"
  fi
  rm -f "$pid_file"
}

_check_deps() {
  local missing=()
  command -v python3 &>/dev/null || missing+=("python3")
  command -v npm    &>/dev/null || missing+=("npm")
  (( ${#missing[@]} == 0 )) && return
  _err "Missing: ${missing[*]}"
  exit 1
}

# Kill any process occupying a port that isn't one we own.
# This prevents another project's dev server from hijacking our port.
_clear_port() {
  local port="$1" our_pid_file="${2:-}"
  local pids
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  [[ -z "$pids" ]] && return

  # If the only process holding this port is our own tracked one, leave it.
  if [[ -n "$our_pid_file" && -f "$our_pid_file" ]]; then
    local our_pid; our_pid=$(cat "$our_pid_file")
    if [[ "$pids" == "$our_pid" ]]; then
      return
    fi
  fi

  for pid in $pids; do
    local cmd; cmd=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
    _warn "Port $port occupied by PID $pid ($cmd) — killing it"
    kill "$pid" 2>/dev/null || true
  done
  sleep 0.3
}

# Source rustup's env — fixes PATH when Rust is installed but the current
# shell hasn't been restarted since installation.
_load_cargo_env() {
  [[ -f "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"
}

_ensure_rust() {
  _load_cargo_env
  if command -v cargo &>/dev/null; then
    _ensure_tauri_cli
    return
  fi
  command -v curl &>/dev/null || { _err "curl required to install Rust"; exit 1; }
  _info "Rust not found — installing via rustup (~2 min)…"
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --no-modify-path
  _load_cargo_env
  command -v cargo &>/dev/null || {
    _err "cargo still not found after install — open a new terminal and retry"
    exit 1
  }
  _ok "Rust installed ($(cargo --version))"
  _ensure_tauri_cli
}

_ensure_tauri_cli() {
  cargo tauri --version &>/dev/null 2>&1 && return
  _info "Installing tauri-cli (~3 min on first run)…"
  cargo install tauri-cli --version "^2" --locked
  _ok "tauri-cli installed"
}

# Create a shell-script stub at the path Tauri's build script requires.
# In dev mode the Rust binary launches this stub, which delegates to the
# Python server. In production, scripts/build.sh replaces it with the real
# PyInstaller bundle.
_ensure_stub() {
  local arch
  arch=$(uname -m | sed 's/arm64/aarch64/')
  local stub="$ROOT/tauri-app/src-tauri/binaries/loop_creator_server-${arch}-apple-darwin"
  mkdir -p "$(dirname "$stub")"
  [[ -x "$stub" ]] && return

  cat > "$stub" <<'STUB'
#!/usr/bin/env bash
# Dev stub — delegates to the Python server.
# Replaced by the real binary when running: bash tauri-app/scripts/build.sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/../../../run_server.py" "$@"
STUB
  chmod +x "$stub"
  _ok "Created dev stub: src-tauri/binaries/$(basename "$stub")"
  _warn "For production use scripts/build.sh to replace this with a real binary."
}

# ── services ──────────────────────────────────────────────────────────────────

_start_server() {
  if _is_running "$SERVER_PID"; then
    _warn "API server already running (pid $(cat "$SERVER_PID"))"
    return
  fi
  _clear_port 5001 "$SERVER_PID"
  _info "Starting API server on :5001"
  cd "$ROOT/tauri-app"
  python3 run_server.py --port 5001 >"$SERVER_LOG" 2>&1 &
  echo $! > "$SERVER_PID"
  cd "$ROOT"
  _ok "API server started  (log: .logs/server.log)"
}

_start_web() {
  if _is_running "$WEB_PID"; then
    _warn "Vite dev server already running (pid $(cat "$WEB_PID"))"
    return
  fi
  _clear_port 5173 "$WEB_PID"
  _info "Starting Vite dev server on :5173"
  cd "$ROOT/tauri-app/web"
  npm run dev >"$WEB_LOG" 2>&1 &
  echo $! > "$WEB_PID"
  cd "$ROOT"
  _ok "Vite dev server started  (log: .logs/web.log)"
}

_stop_all() {
  _kill_pid "$WEB_PID"    "Vite dev server"
  _kill_pid "$SERVER_PID" "API server"
}

# ── commands ──────────────────────────────────────────────────────────────────

cmd_start() {
  _check_deps
  _start_server
  _start_web
  echo ""
  echo -e "  ${DIM}API:${RESET}  http://localhost:5001"
  echo -e "  ${DIM}App:${RESET}  http://localhost:5173"
}

cmd_tauri() {
  _check_deps
  _ensure_rust    # installs Rust + tauri-cli if missing
  _ensure_stub    # creates stub binary if missing
  _clear_port 5173  # evict any foreign app occupying our Vite port
  _start_server   # API server in background (Tauri doesn't manage this)
  echo ""
  _info "Launching Tauri — Vite will start automatically, then the app window opens."
  _info "Press Ctrl+C to stop."
  echo ""
  # Run in the foreground so build output is visible.
  # cargo tauri dev starts Vite itself via beforeDevCommand in tauri.conf.json.
  cd "$ROOT/tauri-app"
  cargo tauri dev
}

cmd_stop() {
  _stop_all
}

cmd_restart() {
  _stop_all
  sleep 0.5
  _check_deps
  _start_server
  _start_web
  echo ""
  echo -e "  ${DIM}API:${RESET}  http://localhost:5001"
  echo -e "  ${DIM}App:${RESET}  http://localhost:5173"
}

cmd_status() {
  for pair in "API server:$SERVER_PID" "Vite dev:$WEB_PID"; do
    local label="${pair%%:*}" pid_file="${pair#*:}"
    if _is_running "$pid_file"; then
      _ok "$label  (pid $(cat "$pid_file"))"
    else
      _info "$label  not running"
    fi
  done
}

cmd_logs() {
  local target="${1:-all}"
  case "$target" in
    server) tail -f "$SERVER_LOG" ;;
    web)    tail -f "$WEB_LOG" ;;
    all)    tail -f "$SERVER_LOG" "$WEB_LOG" 2>/dev/null || tail -f "$SERVER_LOG" ;;
    *)      _err "Unknown log target: $target (server|web|all)"; exit 1 ;;
  esac
}

cmd_help() {
  cat <<EOF

  Usage: ./dev.sh <command> [options]

  Commands:
    start         Start API server + Vite in background (open http://localhost:5173)
    restart       Stop everything, then start
    stop          Stop background processes
    tauri         Build and open the native macOS app
                  (auto-installs Rust, tauri-cli, and stub binary if needed)
    status        Show what is running
    logs [target] Tail logs — server | web | all (default: all)
    help          Show this message

EOF
}

# ── dispatch ──────────────────────────────────────────────────────────────────

case "${1:-help}" in
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  restart) cmd_restart ;;
  tauri)   cmd_tauri ;;
  status)  cmd_status ;;
  logs)    cmd_logs "${2:-all}" ;;
  help|-h|--help) cmd_help ;;
  *)
    _err "Unknown command: $1"
    cmd_help
    exit 1
    ;;
esac
