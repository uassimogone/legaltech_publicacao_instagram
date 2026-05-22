#!/usr/bin/env python3
"""
publish_post.py — Publica 1 slide (imagem + legenda) no Instagram e TikTok

Uso:
    python publish_post.py --slide 1   # 08:00
    python publish_post.py --slide 2   # 12:00
    python publish_post.py --slide 3   # 15:30
    python publish_post.py --slide 4   # 18:00
    python publish_post.py --slide 5   # 20:00
"""

import os
import sys
import json
import time
import base64
import logging
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from send_telegram import notificar_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/tmp/legaltech_automation.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# Configurações
IG_USER_ID    = os.environ["INSTAGRAM_USER_ID"]
IG_TOKEN      = os.environ["INSTAGRAM_ACCESS_TOKEN"]
IMGBB_API_KEY = os.environ["IMGBB_API_KEY"]
GRAPH_BASE    = "https://graph.instagram.com/v20.0"
DATA_FILE     = str(Path(__file__).parent.parent / "legaltech_today.json")


# ── Hospedagem de imagem ──────────────────────────────────────────────────────

def hospedar_imagem(image_path: str) -> str:
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": img_b64},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise ValueError(f"imgbb falhou: {data}")
    return data["data"]["url"]


# ── Instagram — post único ────────────────────────────────────────────────────

def publicar_instagram(image_url: str, caption: str) -> dict:
    # Cria container
    resp = requests.post(
        f"{GRAPH_BASE}/{IG_USER_ID}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    container_id = resp.json().get("id")
    if not container_id:
        raise ValueError(f"Erro ao criar container: {resp.json()}")

    # Aguarda processamento
    for i in range(12):
        status_resp = requests.get(
            f"{GRAPH_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": IG_TOKEN},
            timeout=15,
        )
        status = status_resp.json().get("status_code", "")
        if status == "FINISHED":
            break
        elif status == "ERROR":
            raise ValueError(f"Erro no container: {status_resp.json()}")
        log.info(f"  Aguardando Instagram... ({i+1}/12)")
        time.sleep(5)

    # Publica
    pub_resp = requests.post(
        f"{GRAPH_BASE}/{IG_USER_ID}/media_publish",
        params={"creation_id": container_id, "access_token": IG_TOKEN},
        timeout=30,
    )
    pub_resp.raise_for_status()
    return pub_resp.json()


# ── Publicação principal ──────────────────────────────────────────────────────

def publicar_post(slide_num: int, dry_run: bool = False):
    # Lê dados do dia
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"{DATA_FILE} não encontrado. "
            "Execute run_daily.py às 07:30 primeiro."
        )

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        conteudo = json.load(f)

    # Encontra o slide pelo índice (slides são numerados 2-6, índice 0-4)
    slides = conteudo["slides"]
    if slide_num < 1 or slide_num > len(slides):
        raise ValueError(f"Slide {slide_num} não existe. Total: {len(slides)}")

    slide    = slides[slide_num - 1]
    slides_dir = Path(__file__).parent.parent / "slides_hoje"
    arquivo  = str(slides_dir / slide["arquivo"])
    legenda  = slide["legenda"]
    titulo   = slide.get("titulo", f"Slide {slide_num}")

    log.info(f"📸 Publicando slide {slide_num}/5: '{titulo}'")

    if dry_run:
        log.info(f"  [DRY RUN] arquivo: {arquivo}")
        log.info(f"  [DRY RUN] legenda: {legenda[:80]}...")
        return

    if not os.path.exists(arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")

    # Hospeda imagem
    log.info("  ⬆️  Hospedando imagem...")
    image_url = hospedar_imagem(arquivo)
    log.info(f"  ✅ URL: {image_url}")

    # Publica no Instagram
    ig_ok = True
    try:
        log.info("  📸 Publicando no Instagram...")
        resultado_ig = publicar_instagram(image_url, legenda)
        log.info(f"  ✅ Instagram publicado! ID: {resultado_ig.get('id')}")
    except Exception as e:
        log.error(f"  ❌ Instagram falhou: {e}")
        ig_ok = False

    # Notifica Telegram
    status_ig = "✅" if ig_ok else "❌"
    notificar_telegram(
        f"{status_ig} Post publicado!\n"
        f"📌 Slide {slide_num}/5\n"
        f"📝 {titulo}\n"
        f"📸 Instagram: {'ok' if ig_ok else 'ERRO'}"
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slide", type=int, required=True, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        publicar_post(args.slide, dry_run=args.dry_run)
    except Exception as e:
        log.error(f"❌ Erro: {e}")
        notificar_telegram(f"❌ ERRO ao publicar slide {args.slide}:\n{e}")
        sys.exit(1)
