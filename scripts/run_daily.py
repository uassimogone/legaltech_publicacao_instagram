#!/usr/bin/env python3
"""
run_daily.py — Executa às 07:30 — busca conteúdo do Telegram e salva JSON
"""

import sys
import asyncio
import logging
import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fetch_from_telegram import buscar_conteudo_de_hoje
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


def main():
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    log.info("=" * 60)
    log.info(f"🤖 Buscando conteúdo do dia — {hoje}")
    log.info("=" * 60)

    try:
        conteudo = asyncio.run(buscar_conteudo_de_hoje())
        slides = conteudo["slides"]
        log.info(f"✅ {len(slides)} slides carregados do Telegram")

        notificar_telegram(
            f"✅ Conteúdo do dia carregado!\n"
            f"📅 {hoje}\n"
            f"🖼️ {len(slides)} slides prontos\n\n"
            f"Publicações agendadas:\n"
            f"  • 08:00 — Slide 1\n"
            f"  • 12:00 — Slide 2\n"
            f"  • 15:30 — Slide 3\n"
            f"  • 18:00 — Slide 4\n"
            f"  • 20:00 — Slide 5"
        )

        print(f"\n✅ JSON salvo em /tmp/legaltech_today.json")
        print(f"Aguardando horários de publicação...")

    except Exception as e:
        log.error(f"❌ Falha ao buscar conteúdo: {e}")
        notificar_telegram(f"❌ ERRO ao buscar conteúdo do Telegram:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
