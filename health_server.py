# Health check endpoint para Railway
from fastapi import FastAPI
import uvicorn
import threading

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "OK", "service": "telegram-bot"}

@app.get("/")
async def root():
    return {"message": "Bot Telegram IA Financeiro está rodando!"}

def start_health_server():
    """Iniciar servidor de health check em thread separada"""
    import os
    PORT = int(os.getenv('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")

if __name__ == "__main__":
    # Iniciar em thread para não bloquear o bot
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()