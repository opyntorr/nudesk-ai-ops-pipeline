#!/usr/bin/env bash
# nuDesk Operations Studio - Remote HTTPS Tunnel & Mobile QR Hub
# Exposes local Streamlit (port 8501) to a secure HTTPS URL for mobile/remote testing.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if command -v python3 &>/dev/null && [ -f "$SCRIPT_DIR/tunnel_runner.py" ]; then
    exec python3 "$SCRIPT_DIR/tunnel_runner.py"
else
    echo "=========================================================="
    echo "nuDesk Operations Studio - Remote HTTPS Tunnel"
    echo "=========================================================="
    echo "Launching Cloudflare Tunnel on http://localhost:8501..."
    docker run --rm -it --net=host cloudflare/cloudflared:latest tunnel --url http://localhost:8501
fi
