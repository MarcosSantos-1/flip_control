# Alertas e detecção de erros (lista pronta)

**Alertas imediatos**

* SAC demandante com `time_since_creation > 24h` (animal morto e entulho) → notificar supervisor (email + push)
* SAC em `aguardando agendamento` > 72h (entulho) → alerta vermelho
* CNC com `time_remaining <= 50%` → mudar para `urgente` + notificar
* Fotos ausentes (antes/depois) em SAC com status `executado` → marcar para revistoria
* SAC com `lat/lng` faltando ou subprefeitura incompatível com endereço → `flag_erro_regional`
* Agendamento incorreto (ex.: agendado >30 dias para escalonado) → alerta e log do usuário que agendou
* Duplicados detectados (mesmo endereço+tipo em x horas) → agrupar sugestão

**Regras de notificação**

* Nível amarelo: envio para fiscal e operador por slack/email
* Nível vermelho: enviar SMS + criar tarefa imediata no dashboard
* Summaries: relatório diário com SACs críticos por subprefeitura
