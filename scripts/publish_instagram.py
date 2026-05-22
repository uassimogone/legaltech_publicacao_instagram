#!/usr/bin/env python3
import os, time, base64, requests, logging, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

log = logging.getLogger(__name__)

IG_USER_ID    = os.environ["INSTAGRAM_USER_ID"]
ACCESS_TOKEN  = os.environ["INSTAGRAM_ACCESS_TOKEN"]
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY", "")
GRAPH_BASE    = "https://graph.instagram.com/v20.0"

def hospedar_imagem_imgbb(image_path):
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    response = requests.post("https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": img_b64}, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        raise ValueError(f"imgbb falhou: {data}")
    return data["data"]["url"]

def criar_media_container(image_url, is_carousel_item=True):
    endpoint = f"{GRAPH_BASE}/{IG_USER_ID}/media"
    params = {"image_url": image_url, "access_token": ACCESS_TOKEN}
    if is_carousel_item:
        params["is_carousel_item"] = "true"
    resp = requests.post(endpoint, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "id" not in data:
        raise ValueError(f"Erro ao criar container: {data}")
    return data["id"]

def criar_carousel_container(media_ids, caption):
    endpoint = f"{GRAPH_BASE}/{IG_USER_ID}/media"
    params = {"media_type": "CAROUSEL", "children": ",".join(media_ids),
              "caption": caption, "access_token": ACCESS_TOKEN}
    resp = requests.post(endpoint, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "id" not in data:
        raise ValueError(f"Erro ao criar carousel: {data}")
    return data["id"]

def aguardar_processamento(container_id, max_tentativas=12):
    endpoint = f"{GRAPH_BASE}/{container_id}"
    params = {"fields": "status_code,status", "access_token": ACCESS_TOKEN}
    for i in range(max_tentativas):
        data = requests.get(endpoint, params=params, timeout=15).json()
        status = data.get("status_code", "")
        if status == "FINISHED":
            return True
        elif status == "ERROR":
            raise ValueError(f"Container com erro: {data}")
        log.info(f"Aguardando... ({i+1}/{max_tentativas}) status={status}")
        time.sleep(5)
    raise TimeoutError("Container nao ficou pronto")

def publicar_carousel(carousel_id):
    endpoint = f"{GRAPH_BASE}/{IG_USER_ID}/media_publish"
    params = {"creation_id": carousel_id, "access_token": ACCESS_TOKEN}
    resp = requests.post(endpoint, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "id" not in data:
        raise ValueError(f"Erro ao publicar: {data}")
    return data

def publicar_carrossel_instagram(slides_paths, caption):
    log.info(f"Iniciando publicacao Instagram - {len(slides_paths)} slides")
    urls = []
    for i, path in enumerate(slides_paths):
        log.info(f"Hospedando slide {i+1}/{len(slides_paths)}...")
        urls.append(hospedar_imagem_imgbb(path))
        time.sleep(1)
    media_ids = []
    for i, url in enumerate(urls):
        log.info(f"Criando container {i+1}/{len(urls)}...")
        media_ids.append(criar_media_container(url))
        time.sleep(2)
    log.info("Criando carousel container...")
    carousel_id = criar_carousel_container(media_ids, caption)
    log.info("Aguardando processamento...")
    aguardar_processamento(carousel_id)
    log.info("Publicando...")
    resultado = publicar_carousel(carousel_id)
    log.info(f"Publicado! Post ID: {resultado['id']}")
    return resultado

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Verificando credenciais Instagram...")
    try:
        resp = requests.get(f"{GRAPH_BASE}/{IG_USER_ID}",
            params={"fields": "id,username", "access_token": ACCESS_TOKEN}, timeout=15)
        data = resp.json()
        if "error" in data:
            print(f"ERRO: {data['error']['message']}")
            sys.exit(1)
        print(f"Conta conectada: @{data.get('username')} (ID: {data.get('id')})")
    except Exception as e:
        print(f"Falha: {e}")
        sys.exit(1)
