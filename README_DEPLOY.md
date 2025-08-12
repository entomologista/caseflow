# CaseFlow — Deploy simples (Render/Replit)
Agora o banco cria automaticamente na primeira execução (não precisa `db_init`).

**Start Command (Render):** `gunicorn -w 2 -b 0.0.0.0:${PORT} app:app`
