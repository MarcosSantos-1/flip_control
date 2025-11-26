# 🚀 Guia de Deploy - FLIP Control

Este documento contém instruções completas para fazer deploy do sistema FLIP Control em produção.

## 📋 Arquitetura de Deploy

- **Backend (FastAPI)**: Fly.io
- **Frontend (Next.js)**: Vercel
- **Banco de Dados**: PostgreSQL (Fly.io Postgres ou externo)

---

## 🔧 BACKEND - Deploy no Fly.io

### Pré-requisitos

1. Instalar Fly CLI:
   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   
   # Ou baixar de: https://fly.io/docs/hands-on/install-flyctl/
   ```

2. Fazer login no Fly.io:
   ```bash
   fly auth login
   ```

### Passo 1: Criar App no Fly.io

```bash
cd backend
fly apps create flip-control-backend
```

### Passo 2: Criar Banco de Dados PostgreSQL

```bash
# Criar banco PostgreSQL gerenciado pelo Fly.io
fly postgres create --name flip-control-db --region gru --vm-size shared-cpu-1x --volume-size 10

# Ou usar banco externo (Neon, Supabase, etc.)
# Nesse caso, pule para o Passo 3
```

**Se criou banco no Fly.io**, anexe ao app:
```bash
fly postgres attach flip-control-db --app flip-control-backend
```

### Passo 3: Configurar Variáveis de Ambiente

```bash
# Configurar variáveis de ambiente no Fly.io
fly secrets set \
  DATABASE_URL="postgresql://usuario:senha@host:5432/flip_control" \
  CORS_ORIGINS="https://seu-app.vercel.app" \
  ENVIRONMENT="production" \
  DEBUG="false" \
  API_V1_PREFIX="/api/v1" \
  LOG_LEVEL="INFO"
```

**⚠️ IMPORTANTE**: Substitua:
- `DATABASE_URL`: URL completa do seu banco PostgreSQL
- `CORS_ORIGINS`: URL do seu frontend na Vercel (será configurado depois)

### Passo 4: Deploy do Backend

```bash
# Deploy inicial
fly deploy

# Ver logs
fly logs

# Ver status
fly status
```

### Passo 5: Rodar Migrações do Banco

```bash
# Conectar ao app e rodar migrations
fly ssh console -C "cd /app && alembic upgrade head"
```

Ou criar um script de release (recomendado):

```bash
# Criar arquivo: backend/fly.toml (já criado)
# Adicionar seção [deploy]:
```

Edite `backend/fly.toml` e adicione:

```toml
[deploy]
  release_command = "alembic upgrade head"
```

---

## 🎨 FRONTEND - Deploy na Vercel

### Pré-requisitos

1. Conta na Vercel: https://vercel.com
2. Vercel CLI (opcional, pode usar interface web):
   ```bash
   npm i -g vercel
   ```

### Passo 1: Conectar Repositório

1. Acesse https://vercel.com/new
2. Conecte seu repositório GitHub/GitLab
3. Selecione a pasta `web` como raiz do projeto

### Passo 2: Configurar Variáveis de Ambiente

Na interface da Vercel, vá em **Settings > Environment Variables** e adicione:

```
NEXT_PUBLIC_API_URL = https://flip-control-backend.fly.dev
```

**⚠️ IMPORTANTE**: Substitua `flip-control-backend.fly.dev` pela URL real do seu backend no Fly.io.

### Passo 3: Configurar Build Settings

Na Vercel, configure:
- **Framework Preset**: Next.js
- **Root Directory**: `web`
- **Build Command**: `npm run build` (padrão)
- **Output Directory**: `.next` (padrão)
- **Install Command**: `npm install` (padrão)

### Passo 4: Deploy

1. Faça commit e push das alterações
2. A Vercel fará deploy automaticamente
3. Ou use CLI:
   ```bash
   cd web
   vercel --prod
   ```

### Passo 5: Atualizar CORS no Backend

Após obter a URL do frontend na Vercel, atualize o CORS no backend:

```bash
fly secrets set CORS_ORIGINS="https://seu-app.vercel.app"
```

---

## 🔐 Variáveis de Ambiente Completas

### Backend (Fly.io)

```bash
# OBRIGATÓRIAS
DATABASE_URL=postgresql://usuario:senha@host:5432/flip_control
CORS_ORIGINS=https://seu-app.vercel.app

# RECOMENDADAS
ENVIRONMENT=production
DEBUG=false
API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO

# OPCIONAIS
GEOCODING_API_KEY=          # Se usar Google Geocoding
GEOCODING_PROVIDER=nominatim
```

### Frontend (Vercel)

```
NEXT_PUBLIC_API_URL=https://flip-control-backend.fly.dev
```

---

## 📊 Verificação Pós-Deploy

### Backend

1. **Health Check**:
   ```bash
   curl https://flip-control-backend.fly.dev/health
   # Deve retornar: {"status":"ok"}
   ```

2. **API Docs**:
   ```
   https://flip-control-backend.fly.dev/docs
   ```

3. **Ver logs**:
   ```bash
   fly logs
   ```

### Frontend

1. Acesse a URL fornecida pela Vercel
2. Verifique se consegue fazer requisições para a API
3. Teste upload de CSV
4. Verifique se os gráficos carregam

---

## 🔄 Atualizações Futuras

### Backend

```bash
cd backend
fly deploy
```

### Frontend

- Push para o repositório conectado na Vercel
- Deploy automático ou manual via CLI:
  ```bash
  cd web
  vercel --prod
  ```

---

## 🐛 Troubleshooting

### Backend não conecta ao banco

1. Verifique `DATABASE_URL`:
   ```bash
   fly secrets list
   ```

2. Teste conexão:
   ```bash
   fly ssh console
   # Dentro do console:
   python -c "from app.database import engine; engine.connect()"
   ```

### CORS Errors no Frontend

1. Verifique `CORS_ORIGINS` no backend:
   ```bash
   fly secrets list
   ```

2. Certifique-se que a URL do frontend está incluída (sem trailing slash)

### Migrations não rodam

```bash
fly ssh console -C "cd /app && alembic upgrade head"
```

### Frontend não encontra API

1. Verifique `NEXT_PUBLIC_API_URL` na Vercel
2. Certifique-se que o backend está rodando:
   ```bash
   fly status
   ```

---

## 💰 Custos Estimados

### Fly.io
- **Backend**: ~$5-10/mês (máquina compartilhada)
- **PostgreSQL**: ~$3-5/mês (banco pequeno) ou usar externo gratuito

### Vercel
- **Frontend**: Gratuito (Hobby plan) até 100GB bandwidth/mês

**Total estimado**: ~$8-15/mês

---

## 📚 Recursos Adicionais

- [Fly.io Docs](https://fly.io/docs/)
- [Vercel Docs](https://vercel.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

---

## ✅ Checklist de Deploy

- [ ] Backend criado no Fly.io
- [ ] Banco de dados PostgreSQL configurado
- [ ] Variáveis de ambiente do backend configuradas
- [ ] Backend deployado e health check OK
- [ ] Migrations rodadas no banco
- [ ] Frontend conectado na Vercel
- [ ] Variável `NEXT_PUBLIC_API_URL` configurada
- [ ] Frontend deployado
- [ ] CORS atualizado com URL do frontend
- [ ] Testes funcionais realizados
- [ ] Logs monitorados

---

**Última atualização**: 2025-01-XX

