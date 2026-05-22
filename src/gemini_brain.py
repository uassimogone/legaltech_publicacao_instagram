import json
import requests
import urllib.parse
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from src.config import GEMINI_API_KEY, MODELOS_TEXTO, MODELO_IMAGEM, PEXELS_API_KEY
from src.copy_style import ESTILO_COPY_PROPRIO

class GeminiBrain:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("Erro: GEMINI_API_KEY não foi configurada!")
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def selecionar_e_redigir_posts(self, conteudo_bruto_web: str, historico_urls: list) -> list:
        system_instruction = f"""
        Você é o Especialista em Copywriting e Diretor de Arte da nossa LegalTech.
        Sua missão é ler o conteúdo coletado da internet e criar 3 posts individuais.
        
        Use obrigatoriamente as diretrizes de voz e estilo abaixo:
        {ESTILO_COPY_PROPRIO}
        
        Regras de Negócio Cruciais:
        1. SEJA PROFUNDO: A legenda deve conter de 3 a 4 parágrafos bem desenvolvidos.
        2. FONTE OBRIGATÓRIA: No final da legenda, pule uma linha e escreva "Fonte: [Link da Notícia]".
        3. HASHTAGS OBRIGATÓRIAS: Adicione #LegalTech #IAJurídica #lawtech #artificiallawyer + 2 tags do tema.
        
        DIRETRIZES VISUAIS CONDICIONAIS:
        4. IA NOMINAL (true): Se a notícia focar numa IA específica (Claude, ChatGPT, Gemini, Manus, etc.), defina "contem_ia_nominal" como true. Crie um "prompt_imagem" focando no LOGO e na INTERFACE dessa IA.
        5. SEM IA NOMINAL (false): Se for genérico, defina como false. Crie um "prompt_imagem" com servidores, redes e dados. PROIBIDO: martelo, balança, rostos humanos.
        6. REGRAS DO PEXELS: O Pexels NÃO sabe o que é Claude ou Manus. A "pexels_keyword" NUNCA DEVE TER O NOME DA IA, apenas conceitos de tecnologia abstrata para evitar fotos concorrentes.
        
        Retorne a resposta RIGOROSAMENTE no formato JSON abaixo:
        [
          {{
            "titulo": "TÍTULO (MÁX 70 CARACT)",
            "legenda_completa": "[Gancho]\\n\\n[Contexto]\\n\\n[Impacto]\\n\\n[Dica]\\n\\nFonte: [URL]\\n\\n#Hashtags...",
            "contem_ia_nominal": true,
            "prompt_imagem": "Prompt detalhado em inglês...",
            "pexels_keyword": "abstract technology network",
            "url": "URL original"
          }}
        ]
        """

        prompt_usuario = f"Conteúdo bruto:\n{conteudo_bruto_web}\nHistórico:\n{historico_urls}\n\nGere 3 posts em JSON."
        response = None
        
        for modelo in MODELOS_TEXTO:
            print(f"🧠 Tentando acionar o modelo de texto: {modelo}...")
            try:
                response = self.client.models.generate_content(
                    model=modelo,
                    contents=prompt_usuario,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.7
                    )
                )
                print(f"✅ Sucesso! O modelo '{modelo}' processou a copy.")
                break 
            except Exception as e:
                erro_curto = str(e).split('.')[0]
                print(f"⚠️ Modelo '{modelo}' falhou ({erro_curto}). Próximo...")

        if not response:
            print("❌ Erro Crítico: Todos os modelos de texto falharam.")
            return []

        try:
            return json.loads(response.text)
        except Exception as e:
            print(f"❌ Erro ao decodificar JSON: {e}")
            return []

    def _capturar_imagem_original_noticia(self, url: str, output_path: str) -> str:
        """Raspador de imagens do portal da notícia."""
        if not url or "http" not in url:
            return None
        print(f"🔍 Buscando imagem oficial direto no site da matéria...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            html = requests.get(url, headers=headers, timeout=12).text
            soup = BeautifulSoup(html, 'html.parser')
            meta_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if meta_img and meta_img.get("content"):
                img_url = meta_img["content"]
                img_data = requests.get(img_url, headers=headers, timeout=12).content
                with open(output_path, "wb") as f:
                    f.write(img_data)
                print("✅ Imagem oficial da notícia capturada com sucesso!")
                return output_path
        except Exception:
            print("⚠️ Sem imagem oficial disponível no link.")
        return None

    def _gerar_google_imagen(self, prompt: str, output_path: str) -> str:
        """Gerador Premium do Google."""
        print(f"🎨 Tentando Google Imagen 3...")
        try:
            result = self.client.models.generate_images(
                model=MODELO_IMAGEM,
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/jpeg", aspect_ratio="4:3")
            )
            for img in result.generated_images:
                with open(output_path, "wb") as f:
                    f.write(img.image.image_bytes)
                print("✅ Arte Google Imagen gerada!")
                return output_path
        except Exception:
            print("⚠️ Google Imagen 3 indisponível ou sem cota.")
        return None

    def _gerar_imagem_pollinations(self, prompt: str, output_path: str) -> str:
        """IA Visual Gratuita Open-Source."""
        print(f"🎨 Acionando Pollinations.ai (Aguarde até 60s)...")
        prompt_otimizado = f"{prompt}, no humans, strictly abstract technology, 8k resolution, highly detailed"
        prompt_encoded = urllib.parse.quote(prompt_otimizado)
        url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=60)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                print("✅ Arte IA gerada via Pollinations!")
                return output_path
        except Exception:
            print("⚠️ Falha no Pollinations.")
        return None

    def _buscar_imagem_pexels(self, keyword: str, output_path: str) -> str:
        """Banco de Imagens (Plano de Salvação Abstrato)."""
        if not PEXELS_API_KEY:
            return None
        print(f"🔍 Buscando no Pexels para: '{keyword}'...")
        headers = {"Authorization": PEXELS_API_KEY}
        params = {"query": keyword, "per_page": 1, "orientation": "landscape", "size": "large"}
        try:
            resp = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
            photos = resp.json().get("photos", [])
            if photos:
                url = photos[0]["src"]["large2x"]
                img_data = requests.get(url, timeout=12).content
                with open(output_path, "wb") as f:
                    f.write(img_data)
                print("✅ Imagem Stock baixada!")
                return output_path
        except Exception:
            print("⚠️ Falha no Pexels.")
        return None

    def gerar_imagem_ia(self, prompt_visual: str, keyword_pexels: str, url_noticia: str, contem_ia_nominal: bool, output_path: str) -> str:
        """Orquestrador visual com lógica condicional precisa."""
        
        if contem_ia_nominal:
            print("🚨 NOTÍCIA COM IA NOMINAL DETECTADA!")
            # 1. Raspador (Para pegar logo original da capa da matéria)
            print("👉 [Plano A] Acionando Raspador de Sites...")
            img = self._capturar_imagem_original_noticia(url_noticia, output_path)
            if img: return img
            
            # 2. IA Google
            print("👉 [Plano B] Acionando IA Google...")
            img = self._gerar_google_imagen(prompt_visual, output_path)
            if img: return img
            
            # 3. IA Pollinations
            print("👉 [Plano C] Acionando IA Pollinations...")
            img = self._gerar_imagem_pollinations(prompt_visual, output_path)
            if img: return img
            
            # 4. Pexels (Focado apenas em cor/abstrato, não no nome da IA)
            print("👉 [Plano D] Acionando Pexels...")
            return self._buscar_imagem_pexels(keyword_pexels, output_path)
            
        else:
            print("🌐 NOTÍCIA GERAL DE TECNOLOGIA (Sem IA Nominal)")
            # 1. IA Google
            print("👉 [Plano A] Acionando IA Google...")
            img = self._gerar_google_imagen(prompt_visual, output_path)
            if img: return img
            
            # 2. IA Pollinations
            print("👉 [Plano B] Acionando IA Pollinations...")
            img = self._gerar_imagem_pollinations(prompt_visual, output_path)
            if img: return img
            
            # 3. Pexels
            print("👉 [Plano C] Acionando Pexels...")
            return self._buscar_imagem_pexels(keyword_pexels, output_path)