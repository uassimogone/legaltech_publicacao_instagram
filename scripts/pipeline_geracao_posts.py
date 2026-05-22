#!/usr/bin/env python3
"""
Pipeline LegalTech — Geração diária de posts com Pillow + Telegram.

Estrutura de cada post no dict POSTS:
  n             : número do post (1-5)
  titulo        : hook do título (usado no slide)
  data_noticia  : data da publicação original (DD/MMM/AAAA)
  url_fonte     : URL completa da notícia
  site_nome     : nome do site/veículo
  img_url       : URL da imagem do artigo (og:image); None = usar Pexels
  img_credito   : texto de crédito exibido no slide e na legenda
  pexels_fallback: keywords Pexels (APENAS tech — sem termos jurídicos)
  legenda       : texto completo da legenda para o Telegram/Instagram

Regras de imagem:
  1ª opção: img_url (imagem do próprio artigo — screenshot de interface, tech)
  Fallback : Pexels com keywords tech (NUNCA: lawyer, court, gavel, scales, pillar)

Dependências:
  pip install pillow requests
  curl -L ".../Montserrat-Bold.ttf" -o /tmp/Montserrat-Bold.ttf
  curl -L ".../Montserrat-SemiBold.ttf" -o /tmp/Montserrat-SemiBold.ttf
"""

import requests
import textwrap
from PIL import Image, ImageDraw, ImageFont

PEXELS_API_KEY     = "4C4M3ohwJni4XDy5x5jQ461ScqfRH4Cv9dg2de4AsRfUbRYvMGkt6cSQ"
TELEGRAM_BOT_TOKEN = "8553173816:AAEE3fpEDWgnnhNcph6K54gnRGVofIzPlFI"
TELEGRAM_CHAT_ID   = "8718762229"

# ── Preencher diariamente com as 5 notícias selecionadas ──────────────────────
POSTS = []  # inserir dicts com os 5 posts do dia


# ── Utilitários ────────────────────────────────────────────────────────────────

def baixar_imagem(url, output_path):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(r.content)
    return output_path


def buscar_pexels(keyword, api_key, output_path):
    hdrs   = {"Authorization": api_key}
    params = {"query": keyword, "per_page": 5, "orientation": "landscape", "size": "large"}
    resp   = requests.get("https://api.pexels.com/v1/search", headers=hdrs, params=params, timeout=15)
    photos = resp.json().get("photos", [])
    if not photos:
        return None
    return baixar_imagem(photos[0]["src"]["large2x"], output_path)


def montar_slide(imagem_path, titulo, arquivo_saida, credito=""):
    """Monta slide 1080x1080px com layout padrão legaltech_br."""
    W, H     = 1080, 1080
    TOPO_H   = 648   # altura da imagem do artigo
    FAIXA_Y  = 648   # início da faixa preta
    FAIXA_H  = 86    # altura da faixa @legaltech_br
    TITULO_Y = 734   # início da área de título (azul marinho)
    TITULO_H = 346   # altura da área de título

    fonte_titulo  = ImageFont.truetype("/tmp/Montserrat-Bold.ttf", 50)
    fonte_tag     = ImageFont.truetype("/tmp/Montserrat-SemiBold.ttf", 34)
    fonte_credito = ImageFont.truetype("/tmp/Montserrat-SemiBold.ttf", 18)

    slide = Image.new("RGB", (W, H), (13, 46, 92))  # fundo azul marinho #0D2E5C
    draw  = ImageDraw.Draw(slide)

    # Imagem do topo
    img = Image.open(imagem_path).convert("RGB")
    img = img.resize((W, TOPO_H), Image.LANCZOS)
    slide.paste(img, (0, 0))

    # Crédito discreto (canto inferior direito da foto)
    if credito:
        bb = draw.textbbox((0, 0), credito, font=fonte_credito)
        cx = W - (bb[2] - bb[0]) - 12
        cy = TOPO_H - (bb[3] - bb[1]) - 10
        draw.rectangle([(cx - 6, cy - 4), (W - 6, TOPO_H - 6)], fill=(0, 0, 0))
        draw.text((cx, cy), credito, font=fonte_credito, fill=(200, 200, 200))

    # Faixa preta com @legaltech_br
    draw.rectangle([(0, FAIXA_Y), (W, FAIXA_Y + FAIXA_H)], fill=(0, 0, 0))
    tag = "@legaltech_br"
    bb  = draw.textbbox((0, 0), tag, font=fonte_tag)
    draw.text(
        ((W - (bb[2] - bb[0])) // 2, FAIXA_Y + (FAIXA_H - (bb[3] - bb[1])) // 2),
        tag, font=fonte_tag, fill=(255, 255, 255),
    )

    # Título em maiúsculas, centralizado na área azul
    linhas  = textwrap.wrap(titulo.upper(), width=22)
    line_h  = draw.textbbox((0, 0), "A", font=fonte_titulo)[3] + 14
    bloco_h = line_h * len(linhas)
    text_y  = TITULO_Y + (TITULO_H - bloco_h) // 2

    for linha in linhas:
        bb = draw.textbbox((0, 0), linha, font=fonte_titulo)
        draw.text(((W - (bb[2] - bb[0])) // 2, text_y), linha,
                  font=fonte_titulo, fill=(255, 255, 255))
        text_y += line_h

    slide.save(arquivo_saida, "PNG", dpi=(300, 300))
    print(f"  ✅ Slide: {arquivo_saida}")
    return arquivo_saida


def tg_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text,
                                  "parse_mode": "HTML"}, timeout=15)
    return r.json()


def tg_photo(path):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(path, "rb") as f:
        r = requests.post(url, files={"photo": f}, data={"chat_id": TELEGRAM_CHAT_ID}, timeout=30)
    return r.json()


# ── Pipeline ───────────────────────────────────────────────────────────────────

def main():
    if not POSTS:
        print("❌ POSTS vazio — preencha os 5 posts do dia antes de rodar.")
        return

    print(f"\n{'='*60}\n🚀 PIPELINE LEGALTECH — {POSTS[0].get('data_noticia','')}\n{'='*60}")

    # PASSO 3+4 — Imagens e montagem de slides
    print("\n📸 Obtendo imagens e montando slides...")
    slides = {}
    for post in POSTS:
        n    = post["n"]
        topo = f"/tmp/topo_post_{n}.jpg"
        out  = f"/tmp/post-0{n}.png"
        print(f"\n  Post {n}: {post['titulo'][:55]}")

        if post.get("img_url"):
            try:
                baixar_imagem(post["img_url"], topo)
                print("  ✅ Imagem do artigo")
            except Exception as e:
                print(f"  ⚠️  Artigo falhou ({e}) → Pexels")
                if not buscar_pexels(post["pexels_fallback"], PEXELS_API_KEY, topo):
                    slides[n] = None
                    continue
        else:
            print(f"  ℹ️  Pexels: {post['pexels_fallback'][:50]}")
            if not buscar_pexels(post["pexels_fallback"], PEXELS_API_KEY, topo):
                slides[n] = None
                continue

        montar_slide(topo, post["titulo"], out, post.get("img_credito", ""))
        slides[n] = out

    # PASSO 5 — Telegram
    print("\n📤 Enviando via Telegram...")
    tg_message("🤖 <b>Conteúdo LegalTech pronto!</b>\n📦 5 posts — veja abaixo ↓")

    for post in POSTS:
        n = post["n"]
        slide = slides.get(n)
        if slide:
            r = tg_photo(slide)
            print(f"  Post {n} foto: {'✅' if r.get('ok') else '❌'}")
        msg = (f"📝 <b>POST {n} DE 5</b>\n<b>{post['titulo']}</b>\n\n---\n"
               f"{post['legenda']}\n---")
        r = tg_message(msg)
        print(f"  Post {n} legenda: {'✅' if r.get('ok') else '❌'}")

    tg_message("✅ Tudo entregue! 1 post por dia = semana completa 🚀")

    print("\n✅ CONCLUÍDO")
    for post in POSTS:
        print(f"  {post['n']}. {post['titulo'][:55]} — {post['site_nome']}")


if __name__ == "__main__":
    main()
