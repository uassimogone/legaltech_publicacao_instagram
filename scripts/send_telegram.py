#!/usr/bin/env python3
"""send_telegram.py — Envia notificações via Telegram Bot"""

import os
import requests
import logging

log = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
BASE_URL  = f"https://api.telegram.org/bot{BOT_TOKEN}"


def notificar_telegram(texto: str) -> bool:
    """Envia mensagem de texto pelo Telegram. Retorna True se bem-sucedido."""
    if not BOT_TOKEN or not CHAT_ID:
        log.warning("Telegram não configurado — skipping notificação")
        return False
    try:
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": CHAT_ID, "text": texto, "parse_mode": "HTML"},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        log.error(f"Falha ao enviar Telegram: {e}")
        return False


def enviar_foto_telegram(image_path: str, caption: str = "") -> bool:
    """Envia uma imagem pelo Telegram."""
    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                f"{BASE_URL}/sendPhoto",
                data={"chat_id": CHAT_ID, "caption": caption},
                files={"photo": f},
                timeout=30,
            )
        resp.raise_for_status()
        return True
    except Exception as e:
        log.error(f"Falha ao enviar foto Telegram: {e}")
        return False
