# Pipeline de ingestão (CSV → DB) — fluxo prático requerido do sistema

1. **Upload diário** : usuário arrasta o CSV do FLIP para a interface (por meio de cards dragdrop dinâmicos). Alguns outros dados ser
2. **Validação imediata** (Fastify endpoint):
   * Campos obrigatórios (protocolo, data, endereco, tipo_servico)
   * Conversão de tipos (datas, floats)
   * Geocoding (se lat/lng ausente, rodar reverse geocode com Google / Nominatim em batch) — opcional.
   * Deteção de duplicados (protocolo ou combinação de endereço+data+tipo)
3. **Transformação** : definir `prazo_max_hours` pelo `tipo_servico` (ex.: entulho=72, animal_morto=12, etc.).
4. **Inserção em staging table** (`sacs_staging`) para auditoria.
5. **ETL Job** (queue): promover para `sacs` com logs e marcação `inserted_from_csv`.
6. **Após inserção** : recalcular indicadores do dia e enviar alertas se thresholds ultrapassados.

Agendamento: rodar import diariamente (por webhook) e permitir import manual.
