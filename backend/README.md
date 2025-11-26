# Backend ADC/FLIP - Limpebras Lote III

Backend Python (FastAPI) para sistema de controle e monitoramento do ADC (Avaliação de Desempenho da Contratada).

## Tecnologias

- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para PostgreSQL
- **Alembic**: Migrations de banco de dados
- **Pandas**: Processamento de CSVs
- **PostgreSQL (Neon)**: Banco de dados

## Estrutura do Projeto

```
backend/
├── app/
│   ├── main.py              # Aplicação FastAPI
│   ├── config.py            # Configurações
│   ├── database.py          # Conexão com banco
│   ├── models/              # Models SQLAlchemy
│   ├── schemas/             # Schemas Pydantic
│   ├── services/            # Lógica de negócio
│   ├── api/routes/          # Endpoints REST
│   └── utils/               # Utilitários
├── migrations/              # Migrations Alembic
└── requirements.txt         # Dependências
```

## Instalação

1. **Criar ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

2. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

3. **Configurar variáveis de ambiente:**
```bash
cp .env.example .env
# Editar .env com suas configurações
```

4. **Executar migrations:**
```bash
alembic upgrade head
```

## Executar Aplicação

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em `http://localhost:8000`

Documentação interativa: `http://localhost:8000/docs`

## Endpoints Principais

### Upload de CSVs
- `POST /api/v1/upload/sacs-csv` - Upload CSV de SACs
- `POST /api/v1/upload/cnc-csv` - Upload CSV de CNCs
- `POST /api/v1/upload/acic-csv` - Upload CSV de ACICs
- `POST /api/v1/upload/ouvidoria-csv` - Upload CSV de Ouvidorias

### SACs
- `GET /api/v1/sacs` - Lista SACs (com filtros)
- `GET /api/v1/sacs/{id}` - Detalhes de um SAC
- `POST /api/v1/sacs/{id}/agendar` - Agendar SAC
- `GET /api/v1/sacs/urgentes` - SACs urgentes

### CNCs
- `GET /api/v1/cnc` - Lista CNCs
- `GET /api/v1/cnc/urgent` - CNCs urgentes

### Indicadores
- `GET /api/v1/indicadores` - Lista indicadores calculados
- `POST /api/v1/indicadores/calcular/ird` - Calcular IRD
- `POST /api/v1/indicadores/calcular/ia` - Calcular IA
- `POST /api/v1/indicadores/calcular/if` - Calcular IF
- `POST /api/v1/indicadores/calcular/ipt` - Calcular IPT
- `POST /api/v1/indicadores/calcular/adc` - Calcular ADC completo
- `GET /api/v1/dashboard/kpis` - KPIs para dashboard

### Roteirização
- `POST /api/v1/roteiros/gerar` - Gerar roteiro otimizado

## Migrations

**Criar nova migration:**
```bash
alembic revision --autogenerate -m "descrição"
```

**Aplicar migrations:**
```bash
alembic upgrade head
```

**Reverter migration:**
```bash
alembic downgrade -1
```

## Processamento de CSVs

Os CSVs devem estar no formato exportado pelo FLIP:
- Separador: `;`
- Encoding: UTF-8
- Datas no formato brasileiro: `DD/MM/YYYY HH:MM:SS`

## Cálculos de Indicadores

### IRD (Índice de Reclamações Domiciliares)
- Fórmula: `(reclamações escalonadas procedentes / 511093) × 1000`
- Pontuação máxima: 20 pontos

### IA (Índice de Atendimento)
- Fórmula: `(demandantes no prazo / total demandantes procedentes) × 100`
- Pontuação máxima: 20 pontos

### IF (Índice de Fiscalização)
- Fórmula: `(BFS sem irregularidade / total BFS) × 100`
- Pontuação máxima: 20 pontos

### IPT (Índice de Execução dos Planos de Trabalho)
- Fórmula: `(mão de obra × 50%) + (equipamentos × 50%)`
- Pontuação máxima: 40 pontos

### ADC (Avaliação de Desempenho da Contratada)
- Fórmula: `IRD + IA + IF + IPT`
- Pontuação máxima: 100 pontos

## Desenvolvimento

Para desenvolvimento, use:
```bash
uvicorn app.main:app --reload
```

O `--reload` habilita auto-reload quando arquivos são alterados.

## Licença

Proprietário - Limpebras

