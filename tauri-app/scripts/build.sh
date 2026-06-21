#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

echo "→ Creating venv..."
python3 -m venv "$ROOT/.venv-build"
source "$ROOT/.venv-build/bin/activate"

echo "→ Installing dependencies..."
pip install --quiet -e "$ROOT/../"   # SP1 loop-creator
pip install --quiet fastapi uvicorn pyinstaller tiktoken pyyaml httpx rich textual typer

echo "→ Running PyInstaller..."
cd "$ROOT"
pyinstaller loop_creator_server.spec --distpath dist --workpath build-tmp --noconfirm

echo "→ Copying binary to src-tauri/binaries/..."
ARCH=$(python3 -c "import platform; m = platform.machine(); print('aarch64' if m == 'arm64' else m)")
DEST="$ROOT/src-tauri/binaries/loop_creator_server-${ARCH}-apple-darwin"
cp "$ROOT/dist/loop_creator_server" "$DEST"
chmod +x "$DEST"

echo "✓ Built: $DEST"
deactivate
