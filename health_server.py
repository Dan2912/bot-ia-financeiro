# Health check endpoint simples para Railway
import http.server
import socketserver
import json
import os
from urllib.parse import urlparse

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {"status": "OK", "service": "telegram-bot"}
            self.wfile.write(json.dumps(response).encode())
        elif parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {"message": "Bot Telegram IA Financeiro está rodando!"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        # Silenciar logs do servidor HTTP
        pass

def start_health_server():
    """Iniciar servidor HTTP simples para health check"""
    PORT = int(os.getenv('PORT', 8080))
    
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), HealthHandler) as httpd:
            print(f"Health server running on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Health server error: {e}")

if __name__ == "__main__":
    # Iniciar em thread para não bloquear o bot
    import threading
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()