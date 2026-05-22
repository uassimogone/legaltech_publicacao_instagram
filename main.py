import datetime
from src.config import TOTAL_POSTS
from src.drive_manager import DriveManager
from src.gemini_brain import GeminiBrain
from src.image_manager import ImageManager
from src.telegram_bot import TelegramBot

def simular_captura_noticias():
    return """
    - Portal Jota: OAB regulamenta uso de ferramentas de Inteligência Artificial Generativa para confecção de petições iniciais. Decisão visa coibir alucinações de fatos jurídicos. URL: https://www.jota.info/tecnologia/oab-regulamenta-ia-peticoes-2026
    - Danilo Gato Post: Testei o Claude 3.5 Sonnet para criar estruturas de contestação trabalhista e o resultado foi 4x mais rápido que o padrão. O segredo está no prompt que isola a causa de pedir. URL: https://danilogato.com.br/prompts-trabalhistas-ia
    - Gabriel Adamuchi: Lançamento de nova extensão de agente autônomo focado em fazer varredura diária no Diário Oficial e gerar insights preditivos de perdas e danos. URL: https://youtube.com/@GabrielAdamuchi/agentes-diario-oficial
    - LegalTech Space: Pesquisa aponta que 65% dos escritórios de advocacia de médio porte no Brasil adotaram alguma licença de IA corporativa no primeiro trimestre de 2026. URL: https://legaltechspace.substack.com/dados-mercado-brasil-2026
    """

def executar_pipeline_diario():
    print(f"⏰ [{datetime.datetime.now().strftime('%H:%M:%S')}] Iniciando Pipeline...")
    
    drive = DriveManager()
    brain = GeminiBrain()
    img_render = ImageManager()
    telegram = TelegramBot()

    historico = drive.ler_historico_urls()
    historico = []  # Força o histórico a ficar vazio para o teste
    conteudo_bruto = simular_captura_noticias()

    print("🧠 Analisando notícias com Gemini...")
    posts_selecionados = brain.selecionar_e_redigir_posts(conteudo_bruto, historico)

    if not posts_selecionados:
        print("☕ Nenhuma novidade relevante para hoje. Encerrando.")
        return

    posts_enviados_com_sucesso = 0
    for index, post in enumerate(posts_selecionados[:TOTAL_POSTS], start=1):
        print(f"🎬 Processando Post {index}/{len(posts_selecionados)}...")

        titulo = post.get("titulo", "Novidade Tech")
        legenda = post.get("legenda_completa", "")
        prompt_vis = post.get("prompt_imagem", "Modern abstract corporate technology background")
        keyword_pex = post.get("pexels_keyword", "technology")
        url_noticia = post.get("url", "")
        ia_nominal = post.get("contem_ia_nominal", False)

        tmp_img_ia = f"/tmp/topo_gerado_{index}.jpg"
        img_final_png = f"/tmp/post_pronto_{index}.png"

        img_resolvida = brain.gerar_imagem_ia(prompt_vis, keyword_pex, url_noticia, ia_nominal, tmp_img_ia)

        if not img_resolvida:
            print(f"⏭️ ALERTA: Nenhuma imagem obtida na cascata. Abortando Post {index}.")
            continue

        img_render.montar_slide(img_resolvida, titulo, img_final_png)
        telegram.enviar_post(img_final_png, index, legenda, titulo)
        posts_enviados_com_sucesso += 1

        if url_noticia:
            drive.salvar_no_historico(url_noticia)

    if posts_enviados_com_sucesso > 0:
        telegram.enviar_mensagem(f"✅ *Produção concluída!* {posts_enviados_com_sucesso} posts gerados.")

if __name__ == "__main__":
    executar_pipeline_diario()
