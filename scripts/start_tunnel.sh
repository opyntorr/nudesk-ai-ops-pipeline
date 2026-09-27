#!/usr/bin/env bash
# nuDesk Operations Studio - Remote HTTPS Tunnel
# Exposes local Streamlit (port 8501) to a secure HTTPS URL for mobile/remote testing.

echo "=========================================================="
echo "nuDesk Operations Studio - Remote HTTPS Tunnel"
echo "=========================================================="
echo "Launching Cloudflare Tunnel on http://localhost:8501..."
echo "A public HTTPS URL (e.g. https://*.trycloudflare.com) will appear below."
echo "Use that URL to test on your phone (iOS / Android) or any Mac."
echo "Press Ctrl+C to terminate the tunnel."
echo "=========================================================="

docker run --rm -it --net=host cloudflare/cloudflared:latest tunnel --url http://localhost:8501
