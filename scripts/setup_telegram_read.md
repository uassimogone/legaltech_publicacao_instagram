# Guia de Configuração — Leitura do Telegram via Telethon

> ⏱️ Tempo estimado: 15 minutos
> Por que Telethon? A Bot API só recebe mensagens enviadas AO bot.
> Para ler o histórico (mensagens que o bot ENVIOU), precisamos
> acessar o Telegram como usuário via MTProto.

---

## Passo 1 — Criar um App Telegram

1. Acesse [my.telegram.org](https://my.telegram.org)
2. Faça login com seu número de telefone
3. Clique em **API development tools**
4. Preencha:
   - **App title**: `LegalTech Publisher`
   - **Short name**: `legaltechpub`
   - **Platform**: `Other`
5. Clique em **Create application**
6. Anote:
   - `App api_id` → será `TELEGRAM_API_ID`
   - `App api_hash` → será `TELEGRAM_API_HASH`

---

## Passo 2 — Preencher o .env

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_CHAT_ID=8718762229       # já configurado
TELEGRAM_BOT_TOKEN=8553173816:... # já configurado
```

---

## Passo 3 — Autenticação inicial (uma vez só)

```bash
cd /home/claude/legaltech-automation
pip install telethon
python3 scripts/fetch_from_telegram.py --setup
```

O terminal vai pedir:
1. Seu número de telefone (com DDI: `+5511999999999`)
2. O código que o Telegram vai enviar no seu app
3. Sua senha de dois fatores (se tiver ativada)

Após isso, um arquivo `telegram_session.session` é criado.
**Guarde esse arquivo — a automação usa ele para rodar sem pedir senha.**

---

## Passo 4 — Testar a leitura

```bash
python3 scripts/fetch_from_telegram.py
```

Deve exibir algo como:
```
✅ 5 slides carregados do Telegram
  Slide 1: /tmp/legaltech_hoje/slide-01.png
    Legenda: 4 em cada 10 escritórios já usam IA — e o seu?...
  Slide 2: /tmp/legaltech_hoje/slide-02.png
    Legenda: O prazo que ninguém viu chegar...
  ...
Dados salvos em: /tmp/legaltech_today.json
```

---

## Como funciona o pareamento PNG ↔ Legenda

O script identifica os pares pela sequência de mensagens no Telegram:

```
[foto PNG]                     ← detectado como slide
📝 LEGENDA — SLIDE 2          ← texto logo após = legenda
[título hook]
---
[legenda completa]
---
```

Se o seu pipeline de geração enviar em formato diferente, ajuste
a função `_extrair_pares_slide()` em `fetch_from_telegram.py`.

---

## Segurança

- O arquivo `.session` equivale à sua sessão autenticada do Telegram
- Nunca compartilhe esse arquivo
- Adicione ao `.gitignore`:
  ```
  *.session
  .env
  /tmp/
  ```

---

## Solução de problemas

**"No module named 'telethon'"**
```bash
pip install telethon
```

**"Session file not found"**
→ Rode `--setup` novamente.

**"0 slides encontrados hoje"**
→ Verifique se o conteúdo foi enviado ao chat correto hoje.
→ Confirme que `TELEGRAM_CHAT_ID` é o ID correto do chat.
→ Para descobrir o ID de um chat: encaminhe uma mensagem dele
  para @userinfobot no Telegram.

**"FloodWaitError"**
→ Muitas requisições seguidas. Aguarde alguns minutos e tente novamente.
