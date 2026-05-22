# Rotina Diária — LegalTech Publication Automation

## Descrição
Busca 5 slides + legendas do Telegram às 07:30 e publica
1 post por vez no Instagram (e futuramente TikTok) ao longo do dia.

---

## Agenda Diária (America/Sao_Paulo)

| Horário | Ação |
|---------|------|
| 07:30 | Busca slides do Telegram → salva /tmp/legaltech_today.json |
| 08:00 | Publica slide 1 no Instagram |
| 12:00 | Publica slide 2 no Instagram |
| 15:30 | Publica slide 3 no Instagram |
| 18:00 | Publica slide 4 no Instagram |
| 20:00 | Publica slide 5 no Instagram |

---

## Execução

```bash
# 07:30 — busca conteúdo
python scripts/run_daily.py

# publicações individuais
python scripts/publish_post.py --slide 1  # 08:00
python scripts/publish_post.py --slide 2  # 12:00
python scripts/publish_post.py --slide 3  # 15:30
python scripts/publish_post.py --slide 4  # 18:00
python scripts/publish_post.py --slide 5  # 20:00
```

---

## Arquivos

```
Automacao Claude/
├── CLAUDE.md
├── .env                         ← credenciais
├── telegram_session.session     ← sessão Telethon
├── requirements.txt
├── crontab.txt
└── scripts/
    ├── fetch_from_telegram.py   ← baixa slides do Telegram
    ├── run_daily.py             ← orquestrador 07:30
    ├── publish_post.py          ← publica 1 post (Instagram + TikTok)
    ├── publish_instagram.py     ← funções Instagram
    ├── publish_tiktok_post.py   ← funções TikTok (pendente aprovação)
    └── send_telegram.py         ← notificações
```

---

## Em caso de falha

- Telegram indisponível às 07:30 → notifica e aborta o dia
- Post individual falha → notifica via Telegram, continua nos próximos horários
- Logs em /tmp/legaltech_automation.log
