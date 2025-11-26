# Requisitos do Sistema - ADC / FLIP - Limpebras (Lote III)

## CONTEXTO

O sistema auxiliará no acompanhamento diário do ADC, geração de roteiros para fiscais, monitoramento de prazos e melhoria dos indicadores IA, IRD, IF e IPT.

## ENTIDADES PRINCIPAIS

- sac: protocolo, tipo_servico, status, subprefeitura, endereco, lat, lng, data_criacao, data_vistoria, data_agendamento, data_execucao, prazo_max_hours, fotos_before, fotos_after, fiscal_id
- cnc: bfs, subprefeitura, data_abertura, prazo_hours, status, fotos, descricao
- acic: cnc_id, valor_multa, data_lancamento, desc, e etc
- fiscales: nome, subprefeitura, turno, last_location
- indicadores: tipo, valor, periodo_inicial, periodo_final, subprefeitura

## PRINCIPAIS REGRAS DE NEGÓCIO

1. Prazo por tipo_servico:
   - entulho (coleta e transporte): 72h
   - animal_morto: 12h
   - papeleiras: 4 dias
   - escalonados: até 30 dias
2. IA = (solicitações demandantes atendidas no prazo / solicitações procedentes demandantes) × 100
3. IRD = (reclamações escalonadas procedentes no mês / nº domicílios) × 1000; nº domicílios = 511093 (130030 + 112924 + 147969 + 120170)
4. IF = (nº de fiscalizações sem irregularidade / total fiscalizações) × 100
5. IPT: manual por enquanto (50% mão de obra + 50% equipamentos)
6. ADC = soma das pontuações (IRD + IA + IF + IPT)

| SUBPREFEITURA   | CV      | JT      | ST      | MG      | Total Domicílios |
| --------------- | ------- | ------- | ------- | ------- | ----------------- |
| Nº DOMICÍLIOS | 130.030 | 112.924 | 147.969 | 120.170 | 511.093           |

## FUNÇÕES-CHAVE PARA IMPLEMENTAR

- Upload diário de CSV e endpoint de ingestão (para SAC em análise e agendados, Ouvidoria, ACIC e CNC do dia anterior)
- Validação e geocoding automático para endereços sem lat/lng
- Staging -> ETL -> inserção no DB com logs
- Cálculo automático de IRD, IA e IF diariamente
- Dashboard com KPIs e gráficos (30 dias)
- Página de erros/QA (agendamentos incorretos, fotos faltando, flags)
- Gerador de roteiros por fiscal (cluster + nearest neighbor + 2-opt)
- Alerts engine (thresholds configuráveis)
- Simulador ADC (rodar simulação mensal com base em dados atuais)

## API ENDPOINTS SUGERIDOS (Fastify)

- POST /upload/sacs-csv
- GET  /sacs?status=&subprefeitura=&tipo=&date_from=&date_to=
- POST /sacs/:id/agendar
- POST /sacs/batch/generate-route
- GET  /cnc/urgent
- GET  /indicators?period=month&subpref=CV
- POST /simulate/adc

## ARQUITETURA SUGERIDA

- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Backend: Node.js + Fastify + Prisma + PostgreSQL (Neon)
- Worker/Queue: BullMQ + Redis (para ETL e notificações)
- Optional analytics worker: Python + pandas (se necessário)

## DESIGN & THEMING

- Paleta: zinc + violet; use gradientes para highlights
- Componentes: Cards dinâmicos, tabelas com ação rápida, painel de roteiros com mapa
- Mobile-first; PWA para fiscais
