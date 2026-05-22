import os
from pathlib import Path
from dotenv import load_dotenv

# Encontra a raiz do projeto de forma absoluta (para testes locais no Mac)
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = os.path.join(BASE_DIR, ".env")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path, override=True)

# Credenciais de APIs (Mapeadas exatamente para o padrão Nuvem / GitHub Secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# Trata o Fallback caso local use BOT_TOKEN ou TOKEN puro
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_BOT_TOKEN = TELEGRAM_TOKEN
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Parâmetros de Negócio Fixos para Automação em Nuvem
TOTAL_POSTS = int(os.getenv("TOTAL_POSTS", 3))

# Sistema de Fallback (Cascata) de Modelos de Texto homologado para 2026
MODELOS_TEXTO = [
    "gemini-2.5-flash-lite", # 1º: Versão 'Lite' (Leve) - Ideal para automações rápidas
    "gemini-2.5-flash",      # 2º: Versão padrão
    "gemini-2.0-flash-lite", # 3º: Backup
    "gemini-2.5-pro"         # 4º: Versão Pro para análises pesadas
]

MODELO_IMAGEM = "imagen-3.0-generate-002"
