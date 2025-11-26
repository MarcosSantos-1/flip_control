================================================================================
GUIA RAPIDO DE DEPLOY - FLIP CONTROL
================================================================================

DEPLOY AUTOMATICO VIA GITHUB (SEM CLI)
================================================================================

BACKEND (Fly.io):
-----------------
1. Crie conta em: https://fly.io
2. Crie app: https://fly.io/dashboard > New App > Nome: flip-control-backend
3. Crie banco: Databases > Create Database > flip-control-db
4. Anexe banco ao app: Settings > Attach Database
5. Configure secrets: Settings > Secrets:
   - CORS_ORIGINS = https://seu-app.vercel.app (atualize depois)
   - ENVIRONMENT = production
   - DEBUG = false
6. Obtenha token: https://fly.io/dashboard/personal/api_tokens
7. GitHub Secrets: Settings > Secrets > Actions > FLY_API_TOKEN
8. Push para GitHub = Deploy automatico!

FRONTEND (Vercel):
------------------
1. Acesse: https://vercel.com
2. Import Project > Selecione seu repositorio GitHub
3. Configure:
   - Root Directory: web
   - Framework: Next.js
4. Environment Variables:
   - NEXT_PUBLIC_API_URL = https://flip-control-backend.fly.dev
5. Deploy!
6. Copie URL do frontend e atualize CORS_ORIGINS no Fly.io

VARIAVEIS IMPORTANTES:
----------------------
Fly.io Secrets:
- DATABASE_URL (automatico ao anexar banco)
- CORS_ORIGINS = URL do frontend Vercel
- ENVIRONMENT = production
- DEBUG = false

Vercel Environment Variables:
- NEXT_PUBLIC_API_URL = URL do backend Fly.io

GitHub Secrets (para Actions):
- FLY_API_TOKEN = Token do Fly.io

VERIFICAR DEPLOY:
-----------------
Backend: https://flip-control-backend.fly.dev/health
Frontend: URL fornecida pela Vercel

Veja DEPLOY_GITHUB.txt para instrucoes detalhadas!

================================================================================

