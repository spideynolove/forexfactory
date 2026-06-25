#!/bin/bash
set -e

if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

echo ""
echo "Done. Activate with: source .venv/bin/activate"
