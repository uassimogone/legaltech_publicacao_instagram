import os
import sys
from src.config import TOTAL_POSTS
from src.drive_manager import DriveManager
from src.gemini_manager import GeminiManager
from src.telegram_bot import TelegramBot

def simular_captura_noticias():
    """Simula ou busca a captura de notícias do feed."""
    # Retorna uma estrutura básica para o robô processar o post de teste
    return [{
        "titulo": "Inovação e Inteligência Artificial no Setor Jurídico",
        "link": "https://legaltech.example.com/teste-nuvem-sucesso",
        "conteudo": "O uso de automação e modelos de linguagem avança rapidamente na gestão de escritórios e análise de documentos contratuais."
    }]

def main():
    print("🤖 Iniciando o Robô LegalTech na Nuvem...")
    
    # Inicializa os gerenciadores
    drive = DriveManager()
    gemini = GeminiManager()
    telegram = TelegramBot()

    # FORCEI O HISTÓRICO VAZIO AQUI PARA O SEU TESTE FUNCIONAR AGORA!
    historico = []
    
    print("📰 Capturando notícias do dia...")
    noticias = simular_captura_noticias()
    
    posts_enviados = 0
    
    for noticia in noticias:
        if posts_enviados >= TOTAL_POSTS:
            break
            
        url = noticia.get("link")
        print(f"Analisando notícia: {url}")
        
        # Como o histórico está vazio, ele vai passar direto por aqui
        if url not in historico:
            print("✨ Nova notícia detectada! Gerando post conceitual...")
            
            # Executa a geração do texto com o Gemini
            texto_formatado = gemini.gerar_texto_legaltech(noticia["titulo"], noticia["conteudo"])
            
            if texto_formatado:
                print("📲 Enviando para o Telegram...")
                # Envia o post direto para o seu celular
                sucesso = telegram.enviar_mensagem(texto_formatado)
                
                if sucesso:
                    print("✅ Post enviado com sucesso!")
                    # Grava no histórico para não repetir amanhã
                    drive.salvar_no_historico(url)
                    posts_enviados += 1
                else:
                    print("❌ Falha ao enviar mensagem para o Telegram.")
        else:
            print("⏭️ Notícia já publicada anteriormente. Pulando...")

    print(f"🏁 Execução finalizada. Total de posts enviados: {posts_enviados}")

if __name__ == "__main__":
    main()
