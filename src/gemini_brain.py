import json
import requests
import urllib.parse
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
        
        # Filtra as últimas 30 URLs para otimizar o prompt de exclusão
        historico_str = "\n".join(historico_urls[-30:]) if historico_urls else "Nenhum histórico recente."
        
        prompt_pesquisa = f"""
        Você é um caçador de tendências e pesquisador sênior focado em Inteligência Artificial, Big Techs, Agentes Autônomos e Inovação Tecnológica Global.
        Sua tarefa é fazer uma varredura profunda na internet hoje e trazer as 5 principais novidades, lançamentos ou insights mais impactantes e disruptivos do mundo tech.
        
        Siga estritamente estes critérios de curadoria para a busca:
        1. Priorize lançamentos de grandes modelos (OpenAI, Google, Anthropic, Meta), novas ferramentas de automação extrema, LLMs locais, agentes autônomos funcionais e avanços de IA generativa.
        2. Busque ativamente o que está viralizando no cruzamento de tecnologia avançada e mercado legal consultando referências de inovação (Danilo Gato, Maestros da IA, Gabriel Adamuchi, Bernardo Azevedo, Artificial Lawyer).
        3. Elimine conteúdos burocráticos, notícias lentas de rotina de tribunais, artigos puramente acadêmicos ou decisões administrativas enfadonhas. O foco é inovação viva, tecnológica e disruptiva.
        
        REGRA CRÍTICA DE FILTRO: Não aborde assuntos ou links que já estejam listados no histórico abaixo:
        {historico_str}
        
        Retorne um relatório estruturado contendo o resumo técnico do avanço tecnológico, as ferramentas de IA envolvidas e, obrigatoriamente, la URL de origem da notícia.
        """
        
        try:
            modelo_pesquisa = MODELOS_TEXTO[1] if len(MODELOS_TEXTO) > 1 else "gemini-2.5-flash"
            
            response = self.client.models.generate_content(
                model=modelo_pesquisa,
                contents=prompt_pesquisa,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.3
                )
            )
            print("✅ Varredura e filtragem de ineditismo concluídas com sucesso!")
            return response.text
        except Exception as e:
            print(f"❌ Erro na varredura ativa da internet: {e}")
            return ""

    def selecionar_e_redigir_posts(self, conteudo_bruto_web: str, historico_urls: list) -> list:
        system_instruction = f"""
        Você é o Especialista em Copywriting e Diretor de Arte da nossa LegalTech.
        Sua missão é ler o conteúdo coletado da internet e criar 3 posts individuais extremamente magnéticos.
        
        Use obrigatoriamente as diretrizes de voz, ganchos e estilo contidos abaixo:
        {ESTILO_COPY_PROPRIO}
        
        Regras de Negócio Cruciais:
        1. SEJA PROFUNDO: A legenda deve conter de 3 a 4 parágrafos robustos e muito bem explicados.
        2. FONTE OBRIGATÓRIA: No final da legenda, pule uma linha e escreva "Fonte: [Link da Notícia]".
        3. HASHTAGS OBRIGATÓRIAS: Adicione #LegalTech #IAJurídica #lawtech #artificiallawyer + 2 tags focadas no tema específico do post.
        
        DIRETRIZES VISUAIS CONDICIONAIS (CASCATA):
        - Avalie se a notícia cita nominalmente uma Inteligência Artificial específica (ex: Claude, ChatGPT, Harvey, Jus IA, Llama, Copilot, Ross, Jusbrasil).
        - Se SIM, configure "contem_ia_nominal": true. O prompt_imagem deve descrever de forma conceitual e elegante o logotipo ou a representação visual moderna dessa IA citada. Se possível colocar o próprio logotipo da Inteligência Artificial específica (ex: Claude, ChatGPT, Harvey, Jus IA, Llama, Copilot, Ross, Jusbrasil). 
        - Se NÃO, configure "contem_ia_nominal": false. O prompt_imagem deve ser um conceito visual abstrato de tecnologia avançada futurista, que tenha apelo visual.

        Responda estritamente em formato JSON válido. O formato deve ser uma lista de objetos contendo exatamente estes campos:
        [
          {{
            "titulo": "Título de impacto curto para a imagem",
            "legenda_completa": "Legenda profunda seguindo o ESTILO_COPY_PROPRIO, respeitando as quebras de parágrafo, fontes e hashtags",
            "prompt_imagem": "Prompt detalhado em inglês focado em design corporativo moderno high-tech",
            "pexels_keyword": "palavra-chave simples em inglês para fallback de busca de imagem",
            "url": "A URL real da notícia extraída",
            "contem_ia_nominal": true_ou_false
          }}
        ]
        """
        
        try:
            modelo_redacao = MODELOS_TEXTO[0] if MODELOS_TEXTO else "gemini-2.5-flash-lite"
            response = self.client.models.generate_content(
                model=modelo_redacao,
                contents=f"Aqui está o conteúdo recente minerado da internet:\n\n{conteudo_bruto_web}\n\nEscreva os posts respeitando rigorosamente as novas regras estabelecidas.",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.5
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"❌ Erro na geração/parsing de copywriting do Gemini: {e}")
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
            print("🌐 NOTÍCIA COM IA NOMINAL DETECTADA")
            print("👉 [Plano A] Acionando Raspador de Sites...")
            img = self._capturar_imagem_original_noticia(url_noticia, output_path)
            if img: return img
            
            print("👉 [Plano B] Acionando IA Google...")
            img = self._gerar_google_imagen(prompt_visual, output_path)
            if img: return img
            
            print("👉 [Plano C] Acionando IA Pollinations...")
            img = self._gerar_imagem_pollinations(prompt_visual, output_path)
            if img: return img
            
            print("👉 [Plano D] Acionando Pexels...")
            return self._buscar_imagem_pexels(keyword_pexels, output_path)
            
        else:
            print("🌐 NOTÍCIA GERAL DE TECNOLOGIA (Sem IA Nominal)")
            print("👉 [Plano A] Acionando IA Google...")
            img = self._gerar_google_imagen(prompt_visual, output_path)
            if img: return img
            
            print("👉 [Plano B] Acionando IA Pollinations...")
            img = self._gerar_imagem_pollinations(prompt_visual, output_path)
            if img: return img
            
            print("👉 [Plano C] Acionando Pexels...")
            return self._buscar_imagem_pexels(keyword_pexels, output_path)

    def _capturar_imagem_original_noticia(self, url: str, path: str) -> str:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200: return ""
            soup = BeautifulSoup(r.text, 'html.parser')
            meta_og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
            if meta_og and meta_og.get("content"):
                img_url = meta_og["content"]
                img_data = requests.get(img_url, timeout=10).content
                with open(path, 'wb') as f:
                    f.write(img_data)
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
            for generated_image in result.generated_images:
                with open(path, "wb") as f:
                    f.write(generated_image.image.image_bytes)
                if self._validar_imagem(path): return path
        except: pass
        return ""

    def _gerar_imagem_pollinations(self, prompt: str, path: str) -> str:
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1080&nologo=true"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
                if self._validar_imagem(path): return path
        except: pass
        return ""

    def _buscar_imagem_pexels(self, keyword: str, path: str) -> str:
        try:
            url = f"https://api.pexels.com/v1/search?query={keyword}&per_page=1&orientation=square"
            headers = {"Authorization": PEXELS_API_KEY}
            r = requests.get(url, headers=headers, timeout=10).json()
            if r.get("photos"):
                img_url = r["photos"][0]["src"]["large"]
                data = requests.get(img_url, timeout=10).content
                with open(path, "wb") as f:
                    f.write(data)
                if self._validar_imagem(path): return path
        except: pass
        return ""
