# Esquema de dados (tabelas principais)

Vou listar as tabelas principais e campos essenciais. Indexe campos usados em filtros/joins (ajuste o que precisar).

### `sacs`

* `id` UUID (PK)
* `protocolo` string
* `tipo_servico` enum (ex: `capina`, `entulho`, `animal_morto`, `mutirao`, `varricao`, ...)
* `status` enum (11 statuses que você listou)
* `subprefeitura` enum (`CV`, `JT`, `ST`, `MG`)
* `endereco_text` string
* `lat` float, `lng` float (nullable)
* `bairro` string
* `domicilio_id` nullable
* `protocolo_origem` (se veio de outra base)
* `data_criacao` timestamp
* `data_vistoria` timestamp nullable
* `data_agendamento` timestamp nullable
* `data_execucao` timestamp nullable
* `data_encerramento` timestamp nullable
* `prazo_max_hours` int (calcula por tipo)
* `fiscal_id` FK -> `fiscais.id` (quem vistoriou / executou)
* `fotos_before` json[] (url + gps + timestamp)
* `fotos_after` json[]
* `evidencias` json
* `flag_erro_regional` boolean (detectado)
* `inserted_from_csv` boolean
* indexes: `(status)`, `(subprefeitura)`, `gist (lat, lng)` para queries proximidade

### `cnc` (BFS)

* `id` UUID
* `bfs` string (protocolo)
* `subprefeitura`
* `data_abertura` timestamp
* `prazo_hours` int
* `status` enum (`pendente`, `urgente`)
* `fotos` json[]
* `descricao` text
* `aplicou_multa` boolean

### `ouvidorias`

* `id`, `sac_id` FK, `data_abertura`, `status`, `fluxo`, `fiscal_resposta`, `fotos`

### `acic`

* `id` , `cnc_id(BFS)`, `valor_multa`, `data_lancamento`, `status,desc,sub`

### `fiscais`

* `id`, `nome`, `subprefeitura`, `turno`, `email`, `telefone`, `ativo`, `last_location` (lat/lng/time)

### `indicadores` (snapshot por dia/mês)

* `id`, `tipo` (IR D / IA / IF / IPT), `valor`, `periodo_inicial`, `periodo_final`, `subprefeitura`, `calculated_at`

### `logs_status`

* histórico de alterações de `sacs` (quem, quando, de para, motivo)
