# Dashboard: páginas e componentes prioritários

**Landing / Overview**

* KPI cards: IA (percent + pontos), IRD, IF, IPT, ADC total e % do contrato (resultado da regra de desconto)
* Sparkline / trend 30 dias para cada indicador
* Totais do dia: novos SACs, SACs vencidos, CNCs urgentes

**SACs – Tela principal (listagem)**

* Filtros: status, tipo_servico, subprefeitura, data range, proximidade (mapa)
* Colunas: protocolo, tipo, endereco, prazo restante (horas), status, fotos, ação rápida (agendar, revistoria)
* Botão: “Gerar roteiro” (seleciona SACs e gera rota otimizada)

**Mapa**

* Heatmap por subprefeitura / clusters de SACs (por tipo)
* Markers com prioridade/cores

**CNC / BFS**

* Lista de CNCs pendentes / urgentes
* Alerta automático quando `prazo_hours / 2` ultrapassado → muda para urgente

**Roteiros Diários**

* Gerar roteiros por fiscal, por turno, por subprefeitura
* Otimização por proximidade + prioridade + janelas (ex.: prazo mais curto primeiro)

**Erro / QA**

* Página com detecções automáticas: `flag_erro_regional`, `agendamento_incorreto`, `fotos_missing`, `duplicados`
* Logs de quem errou (usuário do sistema) e opção de corrigir em lote

**Admin / Indicadores**

* Painel para inserir IF e IPT manualmente (upload csv / formulário)
* Histórico por mês com simulações de groso/descontos
