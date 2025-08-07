#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"🌐 Servidor frontend rodando em http://localhost:{PORT}")
        print("📝 Abra o navegador e acesse o endereço acima para testar a interface")
        print("⚠️  Certifique-se de que a API esteja rodando em http://localhost:8000")
        print("\n🛑 Pressione Ctrl+C para parar o servidor")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Servidor parado.")
            sys.exit(0)

if __name__ == "__main__":
    main()