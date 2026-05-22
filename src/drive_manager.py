import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.appdata', 'https://www.googleapis.com/auth/drive.file']

class DriveManager:
    def __init__(self):
        self.creds = self._autenticar()
        self.service = build('drive', 'v3', credentials=self.creds)
        self.arquivo_historico_nome = "historico_urls_legaltech.json"
        self.file_id = self._obter_ou_criar_arquivo_id()

    def _autenticar(self):
        creds = None
        
        # 1. TENTA LER DO GITHUB SECRETS (String JSON na memória)
        gdrive_token_env = os.getenv("GDRIVE_TOKEN_JSON")
        if gdrive_token_env:
            try:
                print("☁️ Autenticando via String de Token do GitHub Secrets...")
                token_data = json.loads(gdrive_token_env)
                return Credentials.from_authorized_user_info(token_data, SCOPES)
            except Exception as e:
                print(f"⚠️ Falha ao decodificar token do ambiente: {e}")

        # 2. FALLBACK PARA AMBIENTE LOCAL (Procura o arquivo físico)
        if os.path.exists('token.json'):
            print("🖥️ Autenticando via arquivo token.json local...")
            return Credentials.from_authorized_user_file('token.json', SCOPES)
            
        # 3. SE NENHUM EXISTIR, ENTRA NO FLUXO DE LOGIN (Apenas local)
        if os.path.exists('credentials.json'):
            print("🔑 Arquivo de credenciais encontrado. Iniciando fluxo de login...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            return creds
            
        raise FileNotFoundError("Erro Crítico: Nenhuma credencial do Google Drive foi localizada.")

    def _obter_ou_criar_arquivo_id(self):
        try:
            query = f"name = '{self.arquivo_historico_nome}' and trashed = false"
            results = self.service.files().list(q=query, fields="files(id)").execute()
            items = results.get('files', [])
            if items:
                return items[0]['id']
            
            meta = {'name': self.arquivo_historico_nome, 'mimeType': 'application/json'}
            with open('/tmp/vazio.json', 'w') as f:
                json.dump([], f)
            media = MediaFileUpload('/tmp/vazio.json', mimetype='application/json')
            novo_arq = self.service.files().create(body=meta, media_body=media, fields='id').execute()
            return novo_arq.get('id')
        except Exception as e:
            print(f"❌ Erro ao conectar com o Drive: {e}")
            return None

    def ler_historico_urls(self) -> list:
        if not self.file_id: return []
        try:
            conteudo = self.service.files().get_media(fileId=self.file_id).execute()
            return json.loads(conteudo.decode('utf-8'))
        except Exception:
            return []

    def salvar_no_historico(self, url: str):
        if not self.file_id or not url: return
        try:
            historico = self.ler_historico_urls()
            if url not in historico:
                historico.append(url)
                with open('/tmp/update.json', 'w') as f:
                    json.dump(historico, f)
                media = MediaFileUpload('/tmp/update.json', mimetype='application/json')
                self.service.files().update(fileId=self.file_id, media_body=media).execute()
                print(f"✅ URL salva no histórico em nuvem do Drive.")
        except Exception as e:
            print(f"⚠️ Erro ao atualizar histórico no Drive: {e}")