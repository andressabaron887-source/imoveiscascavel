#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor FastAPI para o Sistema de Imóveis Cascavel/PR
Substitui o server.ps1 com mais recursos e suporte a scraping real.
"""

import json
import asyncio
import subprocess
import sys
import os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "imoveis.json"
PUBLIC_DIR = BASE_DIR / "public"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
}


def load_properties() -> list:
    if DATA_PATH.exists():
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def run_real_scraper() -> dict:
    """Executa o scraper de portais e o scraper de imobiliárias locais com Playwright."""
    scraper_path = BASE_DIR / "scraper_real.py"
    scraper_imob_path = BASE_DIR / "scraper_imobiliarias.py"
    
    print(">>> Executando scraper de portais (VivaReal, OLX, Zap)...")
    res1 = subprocess.run([sys.executable, str(scraper_path)], capture_output=True, text=True, timeout=300)
    print(res1.stdout)
    if res1.returncode != 0:
        print("SCRAPER PORTAIS STDERR:", res1.stderr)
        
    print(">>> Executando scraper das 22 imobiliárias locais de Cascavel...")
    res2 = subprocess.run([sys.executable, str(scraper_imob_path)], capture_output=True, text=True, timeout=300)
    print(res2.stdout)
    if res2.returncode != 0:
        print("SCRAPER IMOBILIÁRIAS STDERR:", res2.stderr)

    return load_properties()


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.command}] {self.path}")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path):
        ext = path.suffix.lower()
        content_type = CONTENT_TYPES.get(ext, "text/plain")
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/imoveis":
            props = load_properties()
            self.send_json(props)
            return

        if path == "/api/stats":
            props = load_properties()
            new_count = sum(1 for p in props if p.get("is_new"))
            self.send_json({"total": len(props), "new": new_count})
            return

        # Static files
        if path == "/":
            path = "/index.html"
        file_path = PUBLIC_DIR / path.lstrip("/")

        if file_path.exists() and file_path.is_file():
            self.send_file(file_path)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        if self.path == "/api/scrape/trigger":
            print("Iniciando scraper real com Playwright...")
            try:
                props = run_real_scraper()
                new_count = sum(1 for p in props if p.get("is_new"))
                self.send_json({
                    "status": "success",
                    "message": f"Raspagem concluída! {new_count} novos imóveis encontrados.",
                    "total": len(props),
                    "new": new_count,
                    "properties": props
                })
            except subprocess.TimeoutExpired:
                self.send_json({"status": "error", "message": "Timeout no scraper."}, 500)
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()


def main():
    port = 8080
    server = HTTPServer(("0.0.0.0", port), RequestHandler)
    print("=" * 55)
    print(f"  Servidor Imóveis Cascavel/PR Rodando!")
    print(f"  Acesse: http://localhost:{port}")
    print("=" * 55)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")


if __name__ == "__main__":
    main()
