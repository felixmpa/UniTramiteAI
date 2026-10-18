"""
Adaptador inicial de WhatsApp Business Cloud API.
No está conectado ni listo para producción. Requiere configurar credenciales y
completar la lógica de envío con las políticas actuales de Meta.
"""
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

app = FastAPI(title="UniTramite AI - WhatsApp webhook")

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "cambia-este-token")

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verificación fallida")

@app.post("/webhook")
async def receive_message(request: Request):
    payload = await request.json()
    # TODO: validar firma de Meta, extraer mensaje, llamar a la lógica de core.py
    # y responder mediante la API de WhatsApp Cloud con credenciales seguras.
    # No registrar el contenido completo de mensajes personales en logs.
    return {"received": True, "integration_status": "simulated", "note": "Pendiente completar envío y validación de firma."}
