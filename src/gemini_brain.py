import json
import requests
import urllib.parse
import time
import datetime
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from PIL import Image
from src.config import GEMINI_API_KEY, MODELOS_TEXTO, MODELO_IMAGEM, PEXELS_API_KEY
from src.copy_style import ESTILO_COPY_PROPRIO

class GeminiBrain:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("Erro: GEMINI_API_KEY não foi configurada!")
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def buscar_noticias_reais_na_internet(self, historico_urls: list) -> str:
        print("🔍 Iniciando varredura em tempo real na internet (Google Search Grounding)...")
        
        # INJEÇÃO DE RELÓGIO: Força o Google a buscar coisas de hoje
        data_atual = datetime.datetime.now().strftime("%d de %B de %Y")
        
        prompt_pesquisa = f"""
        Você é um pesquisador sênior de Inteligência Artificial e Inovação.
        HOJE É DIA {data_atual}. 
        Sua tarefa é usar o Google Search para encontrar 5 novidades, lançamentos de IA ou ferramentas disruptivas publicadas EXATAMENTE NAS ÚLTIMAS 24 A 48 HORAS.
        
        Diretrizes de Busca (Google):
        1. Busque por "lançamentos inteligência artificial {data_atual}", "novidades agentes autônomos", "legaltech news", etc.
        2. Priorize grandes modelos (OpenAI, Google) e influenciadores de inovação.
        3. IGNORE QUALQUER NOTÍCIA COM DATA ANTERIOR A ESTA SEMANA.
        
        Retorne um resumo técnico detalhado dos avanços e, obrigatoriamente, a URL real de origem.
        """
        
        for modelo_tentativa in MODELOS_TEXTO:
            try:
                print(f"🔄 Tentando pesquisa viva com o modelo {modelo_tentativa} para a data {data_atual}...")
                response = self.client.models.generate_content(
                    model=modelo_tentativa,
                    contents=prompt_pesquisa,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.4 # Aumentamos um pouco a temperatura para forçar buscas diferentes
                    )
                )
                print("✅ Varredura com data dinâmica concluída!")
                return response.text
            except Exception as e:
                print(f"⚠️ Erro 503 com o modelo {modelo_tentativa}. Tentando o próximo...")
                time.sleep(3)
                
        print("❌ Todos os modelos de busca falharam.")
        return ""

    def selecionar_e_redigir_posts(self, conteudo_bruto_web: str, historico_urls: list) -> list:
        # O Histórico fica escondido aqui, apenas como Firewall de exclusão
        historico_str = "\n".join(historico_urls[-40:]) if historico_urls else "Nenhum histórico recente."
        
        system_instruction = f"""
        Você é o Especialista em Copywriting da nossa LegalTech.
        
        Use as diretrizes de estilo abaixo:
        {ESTILO_COPY_PROPRIO}
        
        🚨 FIREWALL DE INEDITISMO 🚨
        Você tem acesso à memória do que já foi postado. Você NUNCA pode gerar um post sobre um assunto ou URL que esteja listado aqui:
        {historico_str}
        
        Se o conteúdo minerado falar sobre temas repetidos desta lista, DESCARTE. Só crie posts de notícias 100% novas.
        
        Regras de Negócio:
        1. SEJA PROFUNDO: 3 a 4 parágrafos robustos.
        2. FONTE: Escreva "Fonte: [Link]" no final.
        3. HASHTAGS: #LegalTech #IAJurídica #lawtech #artificiallawyer + 2 tags do tema.
        
        Responda estritamente em JSON válido:
        [
          {{
            "titulo": "Título de impacto",
            "legenda_completa": "Legenda profunda seguindo o copy",
            "prompt_imagem": "Prompt em inglês focado em design high-tech",
            "pexels_keyword": "keyword simples em inglês",
            "url": "URL real",
            "contem_ia_nominal": true_ou_false
          }}
        ]
        """
        
        try:
            modelo_redacao = MODELOS_TEXTO[0] if MODELOS_TEXTO else "gemini-2.5-flash-lite"
            response = self.client.models.generate_content(
                model=modelo_redacao,
                contents=f"Conteúdo minerado hoje:\n{conteudo_bruto_web}\n\nEscreva os posts. Se tudo for repetido, retorne [].",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"❌ Erro no Redator Gemini: {e}")
            return []

    def _validar_imagem(self, path: str) -> bool:
        try:
            with Image.open(path) as img:
                img.verify()
            return True
        except:
            return False

    def gerar_imagem_ia(self, prompt_visual: str, keyword_pexels: str, url_noticia: str, ia_nominal: bool, output_path: str) -> str:
        if ia_nominal and url_noticia:
            img = self._capturar_imagem_original_noticia(url_noticia, output_path)
            if img: return img
            img = self._gerar_google_imagen(prompt_visual, output_path)
            if img: return img
            img = self._gerar_imagem_pollinations(prompt_visual, output_path)
            if img: return img
            return self._buscar_imagem_pexels(keyword_pexels, output_path)
        else:
            img = self._gerar_google_imagen(prompt_visual, output_path)
            if img: return img
            img = self._gerar_imagem_pollinations(prompt_visual, output_path)
            if img: return img
            return self._buscar_imagem_pexels(keyword_pexels, output_path)

    def _capturar_imagem_original_noticia(self, url: str, path: str) -> str:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200: return ""
            soup = BeautifulSoup(r.text, 'html.parser')
            meta_og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if meta_og and meta_og.get("content"):
                img_data = requests.get(meta_og["content"], timeout=10).content
                with open(path, 'wb') as f: f.write(img_data)
                if self._validar_imagem(path): return path
        except: pass
        return ""

    def _gerar_google_imagen(self, prompt: str, path: str) -> str:
        try:
            result = self.client.models.generate_images(
                model=MODELO_IMAGEM,
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1, output_mime_type="image/jpeg")
            )
            for img in result.generated_images:
                with open(path, "wb") as f: f.write(img.image.image_bytes)
                if self._validar_imagem(path): return path
        except: pass
        return ""

    def _gerar_imagem_pollinations(self, prompt: str, path: str) -> str:
        try:
            url = f"https://image.pollinations.ai/p/{urllib.parse.quote(prompt)}?width=1080&height=1080&nologo=true"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                with open(path, "wb") as f: f.write(r.content)
                if self._validar_imagem(path): return path
        except: pass
        return ""

    def _buscar_imagem_pexels(self, keyword: str, path: str) -> str:
        try:
            url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=1&orientation=square"
            r = requests.get(url, headers={"Authorization": PEXELS_API_KEY}, timeout=10).json()
            if r.get("photos"):
                with open(path, "wb") as f: f.write(requests.get(r["photos"][0]["src"]["large"], timeout=10).content)
                if self._validar_imagem(path): return path
        except: pass
        return ""
