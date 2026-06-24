#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT/.pids"
LOG_DIR="$ROOT/.logs"

SERVER_PID="$PID_DIR/server.pid"
WEB_PID="$PID_DIR/web.pid"
TAURI_PID="$PID_DIR/tauri.pid"
SERVER_LOG="$LOG_DIR/server.log"
WEB_LOG="$LOG_DIR/web.log"
TAURI_LOG="$LOG_DIR/tauri.log"

GREEN="\033[32m"; YELLOW="\033[33m"; RED="\033[31m"; DIM="\033[2m"; RESET="\033[0m"

_ok()  { echo -e "${GREEN}✓${RESET}  $*"; }
_info(){ echo -e "${DIM}→${RESET}  $*"; }
_warn(){ echo -e "${YELLOW}!${RESET}  $*"; }
_err() { echo -e "${RED}✗${RESET}  $*"; }

mkdir -p "$PID_DIR" "$LOG_DIR"

# ── helpers ──────────────────────────────────────────────────────────────────

_is_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null
}

_kill_pid() {
  local pid_file="$1" label="$2"
  if _is_running "$pid_file"; then
    kill "$(cat "$pid_file")" 2>/dev/null && _ok "Stopped $label"
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

# ── start/stop individual services ───────────────────────────────────────────

_start_server() {
  if _is_running "$SERVER_PID"; then
    _warn "Server already running (pid $(cat "$SERVER_PID"))"
    return
  fi
  _info "Starting API server on :5001"
  cd "$ROOT/tauri-app"
  python3 run_server.py --port 5001 >"$SERVER_LOG" 2>&1 &
  echo $! > "$SERVER_PID"
  cd "$ROOT"
  _ok "API server started  (log: .logs/server.log)"
}

_start_web() {
  if _is_running "$WEB_PID"; then
    _warn "Web dev server already running (pid $(cat "$WEB_PID"))"
    return
  fi
  _info "Starting Vite dev server on :5173"
  cd "$ROOT/tauri-app/web"
  npm run dev >"$WEB_LOG" 2>&1 &
  echo $! > "$WEB_PID"
  cd "$ROOT"
  _ok "Vite dev server started  (log: .logs/web.log)"
}

_start_tauri() {
  if _is_running "$TAURI_PID"; then
    _warn "Tauri dev already running (pid $(cat "$TAURI_PID"))"
    return
  fi
  command -v cargo &>/dev/null || { _err "cargo not found — install Rust first"; exit 1; }
  _info "Starting Tauri dev shell"
  cd "$ROOT/tauri-app"
  cargo tauri dev >"$TAURI_LOG" 2>&1 &
  echo $! > "$TAURI_PID"
  cd "$ROOT"
  _ok "Tauri dev started  (log: .logs/tauri.log)"
}

_stop_all() {
  _kill_pid "$TAURI_PID"  "Tauri dev"
  _kill_pid "$WEB_PID"    "Vite dev server"
  _kill_pid "$SERVER_PID" "API server"
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

# ── commands ─────────────────────────────────────────────────────────────────

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
  _start_server
  _start_web
  _start_tauri
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
  local any=false
  for pair in "API server:$SERVER_PID" "Vite dev:$WEB_PID" "Tauri dev:$TAURI_PID"; do
    local label="${pair%%:*}" pid_file="${pair#*:}"
    if _is_running "$pid_file"; then
      _ok "$label  (pid $(cat "$pid_file"))"
      any=true
    else
      _info "$label  not running"
    fi
  done
  $any || echo ""
}

cmd_logs() {
  local target="${1:-all}"
  case "$target" in
    server) tail -f "$SERVER_LOG" ;;
    web)    tail -f "$WEB_LOG" ;;
    tauri)  tail -f "$TAURI_LOG" ;;
    all)    tail -f "$SERVER_LOG" "$WEB_LOG" 2>/dev/null || tail -f "$SERVER_LOG" ;;
    *)      _err "Unknown log target: $target (server|web|tauri|all)"; exit 1 ;;
  esac
}

cmd_help() {
  cat <<EOF

  Usage: ./dev.sh <command> [options]

  Commands:
    start         Start API server + Vite dev server (browser mode)
    restart       Stop everything, then start
    stop          Stop all running processes
    tauri         Start API + Vite + Tauri native shell
    status        Show what is running
    logs [target] Tail logs — server | web | tauri | all (default: all)
    help          Show this message

  After start, open http://localhost:5173 in a browser.
  For the native macOS app, use: ./dev.sh tauri

EOF
}

# ── dispatch ─────────────────────────────────────────────────────────────────

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
