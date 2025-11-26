# Roteirização (heurística prática, fácil de implementar)

Objetivo: juntar SACs próximos e atender prazos.

**Entrada por roteirizador**

* Lista de SACs aprovados para agendamento no dia
* Cada SAC com lat/lng, tempo estimado de serviço (padrão 20–60 min), prioridade (urgente, demandante, escalonado), janela de execução (data_agendamento se existir)

**Algoritmo sugerido (prático)**

1. **Cluster por subprefeitura e dia** (k-d tree / DBSCAN com raio 500–1000m)
2. **Ordenar por prioridade** : (urgente, prazo menor em horas → demandantes → escalonados)
3. **Greedy nearest neighbour** com restrição de tempo de jornada:
   * Para cada fiscal, iniciando na sua última posição, pegar o próximo SAC mais próximo que caiba no tempo.
4. **Simples otimização local** : 2-opt swap para remover ineficiências na rota.
5. **Output** : roteiro com ordem, tempo estimado, link para abrir no maps tudo em mensagem (para jogar no whatsapp em lista por enquanto, depois criaremos uma página para o fiscal)

 **Tecnologia** : use `turf.js` para distância/haversine no Node ou `geolib`. Para roteamento mais avançado, integrar com APIs de roteamento (OSRM, Graphhopper, Google Directions).
