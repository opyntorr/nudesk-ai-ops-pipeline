#!/usr/bin/env python3
"""
nuDesk Operations Studio - Remote Tunnel & Multi-Device Access Runner
Provides:
1. Local LAN WiFi IP detection for devices on the same wireless network.
2. Secure Cloudflare HTTPS tunnel for global access (cellular data, iOS/Android).
3. Terminal ASCII QR code generation for 2-second smartphone camera scanning.
4. Direct URL shortcuts pre-configured for each operational role.
"""
import sys
import os
import re
import socket
import subprocess
import signal
import time
import urllib.request


def get_local_ip() -> str:
    """Detect active local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def print_ascii_qr(url: str):
    """Fetch and print an ANSI ASCII QR code to the terminal for easy smartphone scanning."""
    try:
        req = urllib.request.Request(
            f"https://qrenco.de/{url}",
            headers={"User-Agent": "curl/7.68.0"}
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            qr_content = response.read().decode("utf-8")
            print("\nScan this QR code with your phone camera to open nuDesk:\n")
            print(qr_content)
    except Exception:
        # Graceful fallback if qrenco.de is unreachable
        pass


def run_tunnel():
    local_ip = get_local_ip()
    local_url = f"http://{local_ip}:8501"

    print("=" * 72)
    print("nuDesk Operations Studio — Remote Multi-Device Connectivity Hub")
    print("=" * 72)
    print(f"\n[CANAL 1: RED LOCAL WIFI (Misma red en celular o laptop)]")
    print(f"URL Base:       {local_url}")
    print(f" - Ejecutivo:   {local_url}/?role=executive")
    print(f" - Credito:     {local_url}/?role=credit_underwriter")
    print(f" - Ventas BDR:  {local_url}/?role=commercial_sales")
    print(f" - Talento RH:  {local_url}/?role=hr_recruiter")
    print(f" - Sistemas IT: {local_url}/?role=it_admin")

    print("\n" + "-" * 72)
    print("[CANAL 2: TUNEL GLOBAL SEGURO HTTPS (Cloudflare Tunnel)]")
    print("Iniciando contenedor Cloudflare Tunnel hacia http://localhost:8501...")
    print("No requiere abrir puertos en el router ni configurar IP publica.")

    cmd = [
        "docker", "run", "--rm", "--net=host",
        "cloudflare/cloudflared:latest",
        "tunnel", "--url", "http://localhost:8501"
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    except Exception as exc:
        print(f"Error al iniciar cloudflared Docker: {exc}")
        sys.exit(1)

    url_found = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Read output until URL is found
    for line in iter(proc.stdout.readline, ""):
        match = url_pattern.search(line)
        if match:
            url_found = match.group(0)
            break

    if url_found:
        print("\n" + "=" * 72)
        print("TUNEL HTTPS ACTIVO Y LISTO PARA DISPOSITIVOS MOVILES")
        print("=" * 72)
        print(f"URL Publica Segura: {url_found}\n")
        print("Enlaces directos por rol para su presentacion / demo:")
        print(f" - Cockpit Ejecutivo (Movil): {url_found}/?role=executive")
        print(f" - Mesa de Credito:           {url_found}/?role=credit_underwriter")
        print(f" - Prospeccion Ventas BDR:    {url_found}/?role=commercial_sales")
        print(f" - Atraccion de Talento RH:   {url_found}/?role=hr_recruiter")
        print(f" - Consola de Sistemas IT:    {url_found}/?role=it_admin")

        # Print terminal QR code
        print_ascii_qr(f"{url_found}/?role=executive")

        print("Presione Ctrl+C en cualquier momento para cerrar el tunel.")
        print("=" * 72 + "\n")
    else:
        print("Esperando conexion del tunel...")

    # Keep tunnel alive
    try:
        for _ in iter(proc.stdout.readline, ""):
            pass
    except KeyboardInterrupt:
        print("\nCerrando tunel de Cloudflare...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Tunel cerrado exitosamente.")


if __name__ == "__main__":
    run_tunnel()
