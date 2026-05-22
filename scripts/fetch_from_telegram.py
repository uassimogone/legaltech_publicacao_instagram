#!/usr/bin/env python3
"""
fetch_from_telegram.py — Baixa os PNGs e legendas de hoje do Telegram via Telethon

Por que Telethon e não Bot API?
  A Bot API só recebe mensagens enviadas AO bot.
  Para ler o histórico de um chat (mensagens que o bot ENVIOU),
  é necessário acessar o Telegram como usuário via MTProto.

Pré-requisito: rodar `python fetch_from_telegram.py --setup` uma vez
para autenticar com seu número de telefone.

Formato esperado no chat Telegram (gerado pelo pipeline de conteúdo):
  [foto PNG do slide]          ← photo message
  📝 LEGENDA — SLIDE 2        ← text message logo após
  [título hook]
  ---
  [legenda completa]
  ---
"""

import os
import re
import sys
import json
import asyncio
import logging
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

try:
    from telethon import TelegramClient
    from telethon.tl.types import MessageMediaPhoto
except ImportError:
    print("❌ Telethon não instalado. Execute: pip install telethon")
    sys.exit(1)

log = logging.getLogger(__name__)

# ── Configurações ──────────────────────────────────────────────────────────────
TELEGRAM_API_ID     = int(os.environ["TELEGRAM_API_ID"])
TELEGRAM_API_HASH   = os.environ["TELEGRAM_API_HASH"]
TELEGRAM_CHAT_ID    = int(os.environ.get("TELEGRAM_CONTENT_CHAT_ID", os.environ["TELEGRAM_CHAT_ID"]))
SESSION_FILE        = str(Path(__file__).parent.parent / "telegram_session")
OUTPUT_DIR          = Path(__file__).parent.parent / "slides_hoje"
DATA_FILE           = Path(__file__).parent.parent / "legaltech_today.json"

# Número de slides esperados por dia
TOTAL_SLIDES = 5


# ── Autenticação (rodar uma vez) ───────────────────────────────────────────────

async def setup_autenticacao():
    """
    Autentica com o Telegram via número de telefone.
    Precisa rodar apenas uma vez — cria o arquivo de sessão.
    """
    print("\n🔐 Configuração inicial do Telegram (uma vez só)\n")
    async with TelegramClient(SESSION_FILE, TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
        await client.start()
        me = await client.get_me()
        print(f"✅ Autenticado como: {me.first_name} (@{me.username})")
        print(f"✅ Sessão salva em: {SESSION_FILE}.session")
        print("\nPronto! A automação vai usar essa sessão sem pedir senha novamente.")


# ── Busca de mensagens do dia ──────────────────────────────────────────────────

async def buscar_conteudo_de_hoje() -> dict:
    """
    Busca as últimas 5 fotos + legendas do chat, independente da data.
    Sempre pega o conteúdo mais recente disponível.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hoje = datetime.date.today()

    log.info(f"📱 Buscando últimas 5 fotos no chat {TELEGRAM_CHAT_ID}...")

    slides = []

    async with TelegramClient(SESSION_FILE, TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:
        # Busca apenas as últimas 30 mensagens (suficiente para 5 fotos + 5 legendas)
        mensagens = []
        async for msg in client.iter_messages(TELEGRAM_CHAT_ID, limit=30):
            mensagens.append(msg)

        mensagens.reverse()  # ordem cronológica
        log.info(f"  📨 {len(mensagens)} mensagens carregadas")

        pares = _extrair_pares_slide(mensagens)
        log.info(f"  🖼️  {len(pares)} pares identificados no histórico")

        if not pares:
            raise ValueError(
                "Nenhum par PNG+legenda encontrado. "
                "Verifique se o conteúdo foi enviado ao Telegram."
            )

        # Pega sempre os últimos 5
        pares = pares[-5:]
        log.info(f"  ✅ Usando os últimos {len(pares)} slides")

        # Baixa e renumera de 1 a 5
        for i, par in enumerate(pares, 1):
            output_path = OUTPUT_DIR / f"slide-{i:02d}.png"
            log.info(f"  ⬇️  Baixando slide {i}...")
            await client.download_media(par["photo_msg"], file=str(output_path))
            log.info(f"  ✅ Salvo em {output_path}")

            slides.append({
                "numero":  i,
                "arquivo": f"slide-{i:02d}.png",
                "legenda": par["legenda"],
                "titulo":  par.get("titulo", ""),
            })

    conteudo = {
        "data":   hoje.isoformat(),
        "slides": slides,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)
    log.info(f"✅ Dados salvos em {DATA_FILE}")

    return conteudo


def _extrair_pares_slide(mensagens: list) -> list:
    """
    Identifica slides nas mensagens do Telegram.

    Suporta dois formatos:
    1. Foto com caption "Slide N/7 — Titulo" (formato atual do pipeline)
    2. Foto seguida de mensagem de texto com legenda
    
    Pega apenas slides 2 a 6 (notícias) — ignora capa e encerramento.
    A legenda completa vem da mensagem de texto logo após a foto.
    """
    pares = []

    for i, msg in enumerate(mensagens):
        # Pula se não for foto
        if not msg.media or not isinstance(msg.media, MessageMediaPhoto):
            continue

        caption = msg.text or ""
        numero  = None
        titulo  = ""
        legenda = ""

        # Tenta extrair número do slide do caption da foto
        # Formato: "🖼️ Slide 2/7" ou "Slide 2/7 — Titulo"
        match = re.search(r"[Ss]lide\s+(\d+)\s*/\s*\d+", caption)
        if match:
            numero = int(match.group(1))
            # Ignora capa (1) e encerramento (7)
            if numero in (1, 7):
                continue
            # Converte numeração 2-6 para 1-5
            numero = numero - 1
        else:
            # Fallback: ordem de aparição
            numero = len(pares) + 1

        # Procura legenda na mensagem APÓS a foto
        for j in range(i + 1, min(i + 4, len(mensagens))):
            prox = mensagens[j]
            if prox.text and len(prox.text) > 30:
                legenda = prox.text
                break

        # Se não achou legenda separada, usa o caption da foto
        if not legenda and caption:
            legenda = caption

        # Limpa cabeçalho "📝 LEGENDA — SLIDE N" ou "📝 POST N DE 5" da legenda
        # Mantém apenas o conteúdo após o primeiro "---"
        if "---" in legenda:
            partes = legenda.split("---", 1)
            legenda = partes[1].strip()
        else:
            # Remove linha de cabeçalho se não tiver separador
            linhas_legenda = legenda.strip().split("\n")
            linhas_limpas = []
            for linha in linhas_legenda:
                if re.search(r"(?:LEGENDA|POST)\s*[—-]?\s*(?:SLIDE\s*)?\d+", linha, re.IGNORECASE):
                    continue
                linhas_limpas.append(linha)
            legenda = "\n".join(linhas_limpas).strip()

        # Remove "---" do final se existir
        if legenda.endswith("---"):
            legenda = legenda[:-3].strip()

        pares.append({
            "numero":    numero,
            "photo_msg": msg,
            "legenda":   legenda,
            "titulo":    titulo,
        })

    return pares


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if "--setup" in sys.argv:
        asyncio.run(setup_autenticacao())
        return

    conteudo = asyncio.run(buscar_conteudo_de_hoje())

    print(f"\n✅ {len(conteudo['slides'])} slides carregados do Telegram")
    for slide in conteudo["slides"]:
        print(f"  Slide {slide['numero']}: {slide['arquivo']}")
        print(f"    Legenda: {slide['legenda'][:60]}...")
    print(f"\nDados salvos em: {DATA_FILE}")

    return conteudo


if __name__ == "__main__":
    main()
