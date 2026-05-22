#!/usr/bin/env python3
"""
publish_tiktok_post.py — Publica um post de foto no TikTok via Content Posting API

Uso:
    python publish_tiktok_post.py --slide 2   # publica slide 2 (10:00)
    python publish_tiktok_post.py --slide 3   # publica slide 3 (12:00)
    ...até slide 6

Lê os dados de /tmp/legaltech_today.json (gerado pelo run_daily.py)
"""

import os
import sys
import json
import time
import base64
import logging
import argparse
import requests

log = logging.getLogger(__name__)

# ── Configurações TikTok ──────────────────────────────────────────────────────
TIKTOK_ACCESS_TOKEN  = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_REFRESH_TOKEN = os.environ.get("TIKTOK_REFRESH_TOKEN", "")
TIKTOK_CLIENT_KEY    = os.environ.get("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "")
TIKTOK_PRIVACY       = os.environ.get("TIKTOK_PRIVACY", "PUBLIC_TO_EVERYONE")

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"
DATA_FILE       = "/tmp/legaltech_today.json"


# ── Gerenciamento de token ────────────────────────────────────────────────────

def renovar_access_token() -> str:
    """Renova o access token usando o refresh token."""
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key":     TIKTOK_CLIENT_KEY,
            "client_secret":  TIKTOK_CLIENT_SECRET,
            "grant_type":     "refresh_token",
            "refresh_token":  TIKTOK_REFRESH_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if "access_token" not in data:
        raise ValueError(f"Falha ao renovar token: {data}")

    novo_token = data["access_token"]

    # Salva o novo token no .env (opcional — comentar se preferir gerenciar manualmente)
    log.info("✅ Token TikTok renovado com sucesso")
    return novo_token


# ── Upload de imagem ──────────────────────────────────────────────────────────

def hospedar_imagem_para_tiktok(image_path: str) -> str:
    """
    Hospeda imagem no imgbb para obter URL pública.
    TikTok aceita URLs HTTPS públicas no método PULL_FROM_URL.
    """
    IMGBB_API_KEY = os.environ["IMGBB_API_KEY"]

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
        raise ValueError(f"imgbb upload falhou: {data}")

    return data["data"]["url"]


# ── TikTok Content Posting API ────────────────────────────────────────────────

def criar_post_foto_tiktok(
    photo_url: str,
    caption: str,
    access_token: str,
) -> dict:
    """
    Cria um photo post no TikTok via Content Posting API.

    Args:
        photo_url: URL pública da imagem
        caption: texto do post (até 2200 chars)
        access_token: token de acesso TikTok

    Returns:
        dict com publish_id
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    payload = {
        "post_info": {
            "title": caption[:2200],
            "privacy_level": TIKTOK_PRIVACY,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "auto_add_music": True,
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_images": [photo_url],
            "photo_cover_index": 0,
        },
        "post_mode": "DIRECT_POST",
        "media_type": "PHOTO",
    }

    resp = requests.post(
        f"{TIKTOK_API_BASE}/post/publish/content/init/",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("error", {}).get("code") != "ok":
        raise ValueError(f"TikTok API erro: {data}")

    return data.get("data", {})


def verificar_status_publicacao(publish_id: str, access_token: str) -> str:
    """Verifica o status de uma publicação TikTok."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    payload = {"publish_id": publish_id}

    resp = requests.post(
        f"{TIKTOK_API_BASE}/post/publish/status/fetch/",
        headers=headers,
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", {}).get("status", "UNKNOWN")


# ── Função principal ──────────────────────────────────────────────────────────

def publicar_post_tiktok(slide_num: int) -> dict:
    """
    Publica o post TikTok referente ao slide N (2 a 6).

    Lê os dados de /tmp/legaltech_today.json e publica
    a imagem com a legenda correspondente.
    """
    # Lê dados do dia
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Arquivo {DATA_FILE} não encontrado. "
            "Execute run_daily.py às 09:00 primeiro."
        )

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        conteudo = json.load(f)

    # Valida slide_num
    if slide_num < 2 or slide_num > 6:
        raise ValueError(f"slide_num deve ser entre 2 e 6, recebeu: {slide_num}")

    # Pega o slide correspondente (índice = slide_num - 1)
    slide = conteudo["slides"][slide_num - 1]
    arquivo_png = slide.get("arquivo", f"/tmp/slide-{slide_num:02d}.png")

    if not os.path.exists(arquivo_png):
        raise FileNotFoundError(f"PNG não encontrado: {arquivo_png}")

    legenda = slide.get("legenda", slide.get("resumo", slide["titulo"]))
    titulo  = slide["titulo"]

    log.info(f"🎵 Publicando TikTok — Slide {slide_num}: '{titulo}'")

    # Hospedar imagem
    log.info("  ⬆️  Hospedando imagem...")
    photo_url = hospedar_imagem_para_tiktok(arquivo_png)
    log.info(f"  ✅ URL: {photo_url}")

    # Publicar no TikTok
    token = TIKTOK_ACCESS_TOKEN
    log.info("  🚀 Enviando para TikTok...")
    resultado = criar_post_foto_tiktok(photo_url, legenda, token)
    publish_id = resultado.get("publish_id", "—")
    log.info(f"  ✅ Publicado! publish_id: {publish_id}")

    # Verificar status após alguns segundos
    time.sleep(10)
    status = verificar_status_publicacao(publish_id, token)
    log.info(f"  📊 Status: {status}")

    return {
        "slide_num": slide_num,
        "titulo": titulo,
        "publish_id": publish_id,
        "status": status,
    }


# ── Notificação Telegram ──────────────────────────────────────────────────────

def notificar_tiktok_publicado(resultado: dict):
    """Envia notificação Telegram após publicação TikTok."""
    from send_telegram import notificar_telegram
    msg = (
        f"🎵 TikTok publicado!\n"
        f"📌 Slide {resultado['slide_num']}/6\n"
        f"📝 {resultado['titulo']}\n"
        f"🆔 {resultado['publish_id']}\n"
        f"📊 Status: {resultado['status']}"
    )
    notificar_telegram(msg)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("/tmp/legaltech_automation.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    parser = argparse.ArgumentParser(description="Publica post TikTok do slide N")
    parser.add_argument(
        "--slide",
        type=int,
        required=True,
        choices=[2, 3, 4, 5, 6],
        help="Número do slide a publicar (2 a 6)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula a publicação sem chamar a API",
    )
    args = parser.parse_args()

    if args.dry_run:
        print(f"🧪 DRY RUN — Slide {args.slide} (nenhuma chamada à API)")
        with open(DATA_FILE) as f:
            dados = json.load(f)
        slide = dados["slides"][args.slide - 1]
        print(f"  Título: {slide['titulo']}")
        print(f"  Arquivo: {slide.get('arquivo', f'/tmp/slide-{args.slide:02d}.png')}")
        print(f"  Legenda: {slide.get('legenda', '')[:100]}...")
        sys.exit(0)

    try:
        resultado = publicar_post_tiktok(args.slide)
        notificar_tiktok_publicado(resultado)
        print(f"✅ Post TikTok slide {args.slide} publicado com sucesso!")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao publicar TikTok slide {args.slide}: {e}")
        log.exception("Erro TikTok")
        sys.exit(1)
