# 🔐 Variáveis de Ambiente - FLIP Control

## 📋 Resumo Rápido

### Backend (Fly.io)

```bash
# OBRIGATÓRIAS
DATABASE_URL=postgresql://usuario:senha@host:5432/flip_control
CORS_ORIGINS=https://seu-app.vercel.app

# RECOMENDADAS PARA PRODUÇÃO
ENVIRONMENT=production
DEBUG=false
API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO

# OPCIONAIS
GEOCODING_API_KEY=          # Se usar Google Geocoding API
GEOCODING_PROVIDER=nominatim
```

### Frontend (Vercel)

```
NEXT_PUBLIC_API_URL=https://flip-control-backend.fly.dev
```

---

## 🔧 Backend - Variáveis Detalhadas

### `DATABASE_URL` (OBRIGATÓRIA)
**Descrição**: String de conexão PostgreSQL  
**Formato**: `postgresql://usuario:senha@host:porta/nome_banco`  
**Exemplo Local**: `postgresql://postgres:senha123@localhost:5432/flip_control`  
**Exemplo Fly.io**: `postgresql://usuario:senha@flip-control-db.flycast:5432/flip_control`  
**Exemplo Neon/Supabase**: `postgresql://user:pass@host.neon.tech:5432/dbname`

**Como obter no Fly.io**:
```bash
fly postgres attach flip-control-db --app flip-control-backend
# Isso automaticamente configura DATABASE_URL
```

---

### `CORS_ORIGINS` (OBRIGATÓRIA)
**Descrição**: URLs permitidas para requisições CORS (separadas por vírgula)  
**Exemplo**: `https://flip-control.vercel.app,https://www.seudominio.com`  
**⚠️ IMPORTANTE**: 
- Não inclua trailing slash (`/`)
- Separe múltiplas URLs por vírgula
- Deve incluir a URL exata do frontend na Vercel

**Configurar**:
```bash
fly secrets set CORS_ORIGINS="https://seu-app.vercel.app"
```

---

### `ENVIRONMENT` (RECOMENDADA)
**Descrição**: Ambiente de execução  
**Valores**: `development` | `production` | `staging`  
**Padrão**: `development`  
**Produção**: `production`

---

### `DEBUG` (RECOMENDADA)
**Descrição**: Modo debug do FastAPI  
**Valores**: `true` | `false`  
**Padrão**: `true`  
**Produção**: `false` (desabilita docs automáticos e logs verbosos)

---

### `API_V1_PREFIX` (OPCIONAL)
**Descrição**: Prefixo da API  
**Padrão**: `/api/v1`  
**Não altere** a menos que tenha motivo específico

---

### `LOG_LEVEL` (OPCIONAL)
**Descrição**: Nível de log  
**Valores**: `DEBUG` | `INFO` | `WARNING` | `ERROR` | `CRITICAL`  
**Padrão**: `INFO`  
**Produção**: `INFO` ou `WARNING`

---

### `GEOCODING_API_KEY` (OPCIONAL)
**Descrição**: Chave da API do Google Geocoding  
**Quando usar**: Se quiser usar Google Geocoding em vez de Nominatim  
**Padrão**: Vazio (usa Nominatim gratuito)  
**Limitações**: Nominatim tem rate limit, Google é pago mas mais preciso

---

### `GEOCODING_PROVIDER` (OPCIONAL)
**Descrição**: Provedor de geocoding  
**Valores**: `nominatim` | `google`  
**Padrão**: `nominatim`  
**Nota**: Se usar Google, configure `GEOCODING_API_KEY`

---

### `PORT` (AUTOMÁTICA)
**Descrição**: Porta do servidor  
**Padrão**: `8000`  
**Fly.io**: Configurado automaticamente (não precisa definir)

---

## 🎨 Frontend - Variáveis Detalhadas

### `NEXT_PUBLIC_API_URL` (OBRIGATÓRIA)
**Descrição**: URL base do backend (sem `/api/v1`)  
**Exemplo Local**: `http://localhost:8000`  
**Exemplo Produção**: `https://flip-control-backend.fly.dev`  
**⚠️ IMPORTANTE**: 
- Não inclua `/api/v1` no final
- Use `https://` em produção
- Deve ser acessível publicamente

**Configurar na Vercel**:
1. Vá em **Settings > Environment Variables**
2. Adicione: `NEXT_PUBLIC_API_URL` = `https://seu-backend.fly.dev`
3. Marque para **Production**, **Preview** e **Development**

---

## 📝 Exemplos de Configuração

### Backend - Desenvolvimento Local

Crie `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:senha@localhost:5432/flip_control
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
DEBUG=true
```

### Backend - Produção (Fly.io)

```bash
fly secrets set \
  DATABASE_URL="postgresql://user:pass@host:5432/db" \
  CORS_ORIGINS="https://seu-app.vercel.app" \
  ENVIRONMENT="production" \
  DEBUG="false" \
  LOG_LEVEL="INFO"
```

### Frontend - Desenvolvimento Local

Crie `web/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Frontend - Produção (Vercel)

Na interface da Vercel:
```
NEXT_PUBLIC_API_URL=https://flip-control-backend.fly.dev
```

---

## 🔍 Verificar Variáveis Configuradas

### Backend (Fly.io)

```bash
# Listar todas as secrets
fly secrets list

# Ver logs para debug
fly logs
```

### Frontend (Vercel)

1. Vá em **Settings > Environment Variables**
2. Verifique se `NEXT_PUBLIC_API_URL` está configurada
3. Verifique se está marcada para **Production**

---

## ⚠️ Segurança

1. **NUNCA** commite arquivos `.env` no Git
2. Use secrets do Fly.io/Vercel para dados sensíveis
3. `DATABASE_URL` contém credenciais - trate como secreto
4. `GEOCODING_API_KEY` é secreto se usar Google
5. `CORS_ORIGINS` deve ser específico (não use `*`)

---

## 🐛 Troubleshooting

### Backend não conecta ao banco

```bash
# Verificar DATABASE_URL
fly secrets list | grep DATABASE_URL

# Testar conexão
fly ssh console
python -c "from app.database import engine; print(engine.url)"
```

### CORS Errors

```bash
# Verificar CORS_ORIGINS
fly secrets list | grep CORS

# Certifique-se que a URL do frontend está incluída (sem trailing slash)
```

### Frontend não encontra API

1. Verifique `NEXT_PUBLIC_API_URL` na Vercel
2. Certifique-se que o backend está rodando: `fly status`
3. Teste a URL diretamente: `curl https://seu-backend.fly.dev/health`

---

**Última atualização**: 2025-01-XX

