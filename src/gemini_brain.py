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

    def buscar_noticias_reais_na_internet(self, historico_urls: list) -> str:
        print("🔍 Iniciando varredura em tempo real na internet (Google Search Grounding)...")
        
        # Filtra as últimas 30 URLs para otimizar o prompt de exclusão
        historico_str = "\n".join(historico_urls[-30:]) if historico_urls else "Nenhum histórico recente."
        
        prompt_pesquisa = f"""
        Você é um pesquisador e curador de conteúdo experiente no nicho de LegalTech, IA Jurídica e automação para advogados no Brasil.
        Sua tarefa é fazer uma varredura profunda na internet hoje e trazer as 5 principais novidades, tendências ou insights de mercado mais recentes.
        
        Siga estritamente esta ordem de prioridade de curadoria:
        1. Novidades virais dos Influenciadores: Danilo Gato, Maestros da IA, Gabriel Adamuchi e Bernardo Azevedo.
        2. Fatos e regulações nos Portais Nacionais: Jota, ConJur, Migalhas, Jurídico Ágil, Gustavo Rocha, Bruno Feigelson.
        3. Movimentações globais em Portais Internacionais: Artificial Lawyer.
        
        REGRA CRÍTICA DE FILTRO: Não aborde assuntos ou links que já estejam listados no histórico abaixo:
        {historico_str}
        
        Retorne um relatório estruturado contendo o resumo de cada fato marcante, as ferramentas de IA envolvidas e, obrigatoriamente, a URL de origem da notícia.
        """
        
        try:
            # Seleciona o primeiro modelo estável homologado na lista de cascata
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
        Sua missão é ler o conteúdo coletado da internet e criar 3 posts individuais.
        
        Use obrigatoriamente as diretrizes de voz e estilo abaixo:
        {ESTILO_COPY_PROPRIO}
        
        Regras de Negócio Cruciais:
        1. SEJA PROFUNDO: A legenda deve conter de 3 a 4 parágrafos bem desenvolvidos.
        2. FONTE OBRIGATÓRIA: No final da legenda, pule uma linha e escreva "Fonte: [Link da Notícia]".
        3. HASHTAGS OBRIGATÓRIAS: Adicione #LegalTech #IAJurídica #lawtech #artificiallawyer + 2 tags do tema.
        
        DIRETRIZES VISUAIS CONDICIONAIS (CASCATA):
        - Avalie se a notícia cita nominalmente uma Inteligência Artificial específica (ex: Claude, ChatGPT, Harvey, Jus IA, Llama, Copilot, Ross, Jusbrasil).
        - Se SIM, configure "contem_ia_nominal": true. O prompt_imagem deve descrever de forma conceitual e elegante o logotipo ou a representação visual moderna dessa IA citada.
        - Se NÃO, configure "contem_ia_nominal": false. O prompt_imagem deve ser um conceito visual abstrato de tecnologia jurídica futurista.

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
                contents=f"Aqui está o conteúdo recente minerado da internet:\n\n{conteudo_bruto_web}\n\nEscreva os posts respeitando as regras.",
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
                return path
        except:
            pass
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
                return path
        except:
            pass
        return ""

    def _gerar_imagem_pollinations(self, prompt: str, path: str) -> str:
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1080&height=1080&nologo=true"
            data = requests.get(url, timeout=15).content
            with open(path, "wb") as f:
                f.write(data)
            return path
        except:
            pass
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
                return path
        except:
            pass
        return ""
