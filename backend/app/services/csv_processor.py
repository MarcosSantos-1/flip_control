"""Processamento de CSVs do FLIP."""
import pandas as pd
import pandas.errors
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import csv

from app.models.sac import SAC, TipoServico, StatusSAC, Subprefeitura
from app.models.cnc import CNC, StatusCNC
from app.models.acic import ACIC, StatusACIC
from app.models.ouvidoria import Ouvidoria, StatusOuvidoria
from app.utils.validators import parse_data_brasil, normalizar_subprefeitura, calcular_prazo_max_hours
from app.utils.geocoding import parse_coordenadas, geocode_endereco

logger = logging.getLogger(__name__)


class CSVProcessor:
    """Processador de CSVs do FLIP."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def processar_sacs_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Processa CSV de SACs.
        
        Returns:
            Dict com estatísticas do processamento
        """
        try:
            df = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
            
            # Normalizar nomes de colunas (remover acentos e espaços)
            df.columns = df.columns.str.strip()
            
            # Remover duplicados dentro do próprio CSV
            df = df.drop_duplicates(subset=["Numero_Chamado"], keep="first")
            
            # Buscar todos os protocolos existentes de uma vez (mais eficiente)
            protocolos_list = [str(proto).strip() for proto in df["Numero_Chamado"].dropna().tolist() if str(proto).strip()]
            sacs_existentes = {}
            if protocolos_list:
                sacs_existentes = {
                    sac.protocolo: sac for sac in self.db.query(SAC).filter(
                        SAC.protocolo.in_(protocolos_list)
                    ).all()
                }
            
            processados = 0
            atualizados = 0
            erros = 0
            
            for _, row in df.iterrows():
                try:
                    # Verificar se já existe
                    protocolo = str(row.get("Numero_Chamado", "")).strip()
                    if not protocolo:
                        erros += 1
                        continue
                    
                    # Verificar se já existe no banco
                    sac_existente = sacs_existentes.get(protocolo)
                    
                    # Parse de dados
                    status_str = str(row.get("Status", "")).strip()
                    status = self._parse_status_sac(status_str)
                    
                    tipo_servico_str = str(row.get("Serviço", "")).strip()
                    tipo_servico = self._parse_tipo_servico(tipo_servico_str)
                    
                    subpref_str = str(row.get("Regional", "")).strip()
                    subprefeitura = self._parse_subprefeitura(subpref_str)
                    
                    endereco = str(row.get("Endereço", "")).strip()
                    coordenadas_str = str(row.get("Coordenadas", "")).strip()
                    
                    # Parse coordenadas
                    lat, lng = None, None
                    if coordenadas_str and coordenadas_str != "nan":
                        coords = parse_coordenadas(coordenadas_str)
                        if coords:
                            lat, lng = coords
                    
                    # Se não tem coordenadas, tentar geocoding
                    if not lat or not lng:
                        coords = geocode_endereco(endereco)
                        if coords:
                            lat, lng = coords
                    
                    # Parse datas
                    data_registro = parse_data_brasil(str(row.get("Data_Registro", "")))
                    data_vistoria = parse_data_brasil(str(row.get("Data_Realização_Vistoria", "")))
                    data_agendamento = parse_data_brasil(str(row.get("Data_Acionamento_Agendamento", "")))
                    data_execucao = parse_data_brasil(str(row.get("Data_Execução", "")))
                    
                    # Calcular prazo
                    # IMPORTANTE: Para Cata-Bagulho (Escalonado), sempre usar 720h (30 dias)
                    # mesmo que tenha responsividade de 5h no CSV (esse é só prazo de vistoria)
                    responsividade = row.get("Responsividade")
                    if pd.notna(responsividade):
                        try:
                            responsividade = int(responsividade)
                        except:
                            responsividade = None
                    
                    # Se for Cata-Bagulho, ignorar responsividade e usar 720h
                    if tipo_servico == TipoServico.CATABAGULHO:
                        prazo_max_hours = 720  # 30 dias - Escalonado, não importa prazo
                    else:
                        prazo_max_hours = calcular_prazo_max_hours(tipo_servico_str, responsividade)
                    
                    if sac_existente:
                        # Atualizar SAC existente
                        sac_existente.tipo_servico = tipo_servico
                        sac_existente.status = status
                        sac_existente.subprefeitura = subprefeitura
                        sac_existente.endereco_text = endereco
                        if lat and lng:
                            sac_existente.lat = lat
                            sac_existente.lng = lng
                        if str(row.get("Área", "")).strip():
                            sac_existente.bairro = str(row.get("Área", "")).strip()
                        if data_registro:
                            sac_existente.data_criacao = data_registro
                        if data_vistoria:
                            sac_existente.data_vistoria = data_vistoria
                        if data_agendamento:
                            sac_existente.data_agendamento = data_agendamento
                        if data_execucao:
                            sac_existente.data_execucao = data_execucao
                        sac_existente.prazo_max_hours = prazo_max_hours
                        sac_existente.inserted_from_csv = True
                        
                        # Verificar se foi executado fora do prazo (apenas para demandantes)
                        tipos_demandantes = [TipoServico.ENTULHO, TipoServico.ANIMAL_MORTO, TipoServico.PAPELEIRAS]
                        if tipo_servico in tipos_demandantes and data_execucao and sac_existente.data_criacao:
                            tempo_decorrido_hours = (data_execucao - sac_existente.data_criacao).total_seconds() / 3600
                            if tempo_decorrido_hours > prazo_max_hours:
                                # O cálculo do IA já considera isso automaticamente, mas podemos marcar
                                # que foi executado fora do prazo para referência
                                logger.info(f"SAC {protocolo} executado fora do prazo: {tempo_decorrido_hours:.2f}h > {prazo_max_hours}h")
                        
                        atualizados += 1
                    else:
                        # Criar novo SAC
                        sac = SAC(
                            protocolo=protocolo,
                            tipo_servico=tipo_servico,
                            status=status,
                            subprefeitura=subprefeitura,
                            endereco_text=endereco,
                            lat=lat,
                            lng=lng,
                            bairro=str(row.get("Área", "")).strip() or None,
                            data_criacao=data_registro or datetime.utcnow(),
                            data_vistoria=data_vistoria,
                            data_agendamento=data_agendamento,
                            data_execucao=data_execucao,
                            prazo_max_hours=prazo_max_hours,
                            inserted_from_csv=True,
                        )
                        self.db.add(sac)
                        sacs_existentes[protocolo] = sac  # Adicionar à lista para evitar duplicados no mesmo batch
                        processados += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao processar SAC {protocolo}: {e}")
                    erros += 1
                    continue
            
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Erro ao commitar SACs: {e}")
                raise
            
            return {
                "processados": processados,
                "atualizados": atualizados,
                "erros": erros,
                "total": len(df)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao processar CSV de SACs: {e}")
            raise
    
    def processar_cnc_csv(self, file_path: str) -> Dict[str, Any]:
        """Processa CSV de CNCs."""
        try:
            df = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
            df.columns = df.columns.str.strip()
            
            # Remover duplicados dentro do próprio CSV
            df = df.drop_duplicates(subset=["N_BFS"], keep="first")
            
            # Buscar todos os BFSs existentes de uma vez (mais eficiente)
            bfs_list = [str(bfs).strip() for bfs in df["N_BFS"].dropna().tolist() if str(bfs).strip()]
            bfs_existentes = set()
            if bfs_list:
                bfs_existentes = set(
                    row[0] for row in self.db.query(CNC.bfs).filter(CNC.bfs.in_(bfs_list)).all()
                )
            
            processados = 0
            erros = 0
            duplicados = 0
            
            for _, row in df.iterrows():
                try:
                    bfs = str(row.get("N_BFS", "")).strip()
                    if not bfs:
                        erros += 1
                        continue
                    
                    if bfs in bfs_existentes:
                        duplicados += 1
                        continue
                    
                    # Parse status
                    situacao = str(row.get("Situacao_CNC", "")).strip()
                    status = StatusCNC.PENDENTE
                    if situacao == "Regularizado":
                        status = StatusCNC.REGULARIZADO
                    elif situacao == "Aguardando Vistoria":
                        status = StatusCNC.AGUARDANDO_VISTORIA
                    
                    # Parse datas
                    data_sincronizacao = parse_data_brasil(str(row.get("Data_Sincronizacao", "")))
                    data_fiscalizacao = parse_data_brasil(str(row.get("Data_Fiscalizacao", "")))
                    data_execucao = parse_data_brasil(str(row.get("Data_Execução", "")))
                    
                    # Coordenadas
                    coordenada_str = str(row.get("Coordenada", "")).strip()
                    lat, lng = None, None
                    if coordenada_str and coordenada_str != "nan":
                        coords = parse_coordenadas(coordenada_str)
                        if coords:
                            lat, lng = coords
                    
                    # Prazo
                    responsividade = row.get("Responsividade")
                    prazo_hours = 24  # Padrão
                    if pd.notna(responsividade):
                        try:
                            prazo_hours = int(responsividade)
                        except:
                            pass
                    
                    cnc = CNC(
                        bfs=bfs,
                        n_cnc=str(row.get("N_CNC", "")).strip() or None,
                        subprefeitura=str(row.get("Regional", "")).strip(),
                        area=str(row.get("Area", "")).strip() or None,
                        setor=str(row.get("Setor", "")).strip() or None,
                        turno=str(row.get("Turno", "")).strip() or None,
                        servico=str(row.get("Servico", "")).strip() or None,
                        data_abertura=data_fiscalizacao or datetime.utcnow(),
                        data_sincronizacao=data_sincronizacao,
                        data_fiscalizacao=data_fiscalizacao,
                        data_execucao=data_execucao,
                        prazo_hours=prazo_hours,
                        responsividade=prazo_hours,
                        status=status,
                        situacao_cnc=situacao,
                        endereco=str(row.get("Endereco", "")).strip() or None,
                        coordenada=coordenada_str if coordenada_str != "nan" else None,
                        lat=lat,
                        lng=lng,
                        descricao=None,
                        fiscal_contratada=str(row.get("Fiscal_Contratada", "")).strip() or None,
                        agente_fiscalizador=str(row.get("Fiscal", "")).strip() or None,
                        aplicou_multa=False,
                    )
                    
                    self.db.add(cnc)
                    bfs_existentes.add(bfs)  # Adicionar à lista para evitar duplicados no mesmo batch
                    processados += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao processar CNC {bfs}: {e}")
                    erros += 1
                    continue
            
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Erro ao commitar CNCs: {e}")
                raise
            
            return {
                "processados": processados,
                "erros": erros,
                "duplicados": duplicados,
                "total": len(df)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao processar CSV de CNCs: {e}")
            raise
    
    def processar_acic_csv(self, file_path: str) -> Dict[str, Any]:
        """Processa CSV de ACICs."""
        try:
            # Ler CSV - o arquivo pode ter \n literais dentro dos campos
            # Usar engine Python com tratamento robusto de erros
            # Tentar diferentes estratégias de leitura
            df = None
            errors = []
            
            # Estratégia 1: UTF-8 com engine Python (sem low_memory)
            try:
                df = pd.read_csv(
                    file_path,
                    sep=";",
                    encoding="utf-8",
                    on_bad_lines='skip',
                    engine='python',
                    quotechar='"',
                    skipinitialspace=True,
                )
            except Exception as e:
                errors.append(f"UTF-8: {str(e)}")
            
            # Estratégia 2: Latin-1 se UTF-8 falhou
            if df is None or df.empty:
                try:
                    df = pd.read_csv(
                        file_path,
                        sep=";",
                        encoding="latin-1",
                        on_bad_lines='skip',
                        engine='python',
                        quotechar='"',
                        skipinitialspace=True,
                    )
                except Exception as e:
                    errors.append(f"Latin-1: {str(e)}")
            
            # Estratégia 3: Sem quotechar
            if df is None or df.empty:
                try:
                    df = pd.read_csv(
                        file_path,
                        sep=";",
                        encoding="utf-8",
                        on_bad_lines='skip',
                        engine='python',
                    )
                except Exception as e:
                    errors.append(f"Sem quotechar: {str(e)}")
            
            if df is None or df.empty:
                raise ValueError(f"Não foi possível ler o CSV. Erros: {'; '.join(errors)}")
            
            df.columns = df.columns.str.strip()
            
            # Validar que temos a coluna N_ACIC
            if "N_ACIC" not in df.columns:
                # Tentar encontrar coluna similar (case insensitive)
                acic_cols = [col for col in df.columns if "ACIC" in col.upper()]
                if acic_cols:
                    logger.warning(f"Coluna N_ACIC não encontrada, usando {acic_cols[0]}")
                    df = df.rename(columns={acic_cols[0]: "N_ACIC"})
                else:
                    raise ValueError(f"Coluna N_ACIC não encontrada no CSV. Colunas disponíveis: {list(df.columns)}")
            
            # Remover duplicados dentro do próprio CSV
            df = df.drop_duplicates(subset=["N_ACIC"], keep="first")
            
            # Buscar todos os ACICs existentes de uma vez
            acic_list = [str(acic).strip() for acic in df["N_ACIC"].dropna().tolist() if str(acic).strip()]
            acic_existentes = set()
            if acic_list:
                acic_existentes = set(
                    row[0] for row in self.db.query(ACIC.n_acic).filter(
                        ACIC.n_acic.in_(acic_list)
                    ).all() if row[0]
                )
            
            processados = 0
            erros = 0
            duplicados = 0
            
            for _, row in df.iterrows():
                try:
                    n_acic = str(row.get("N_ACIC", "")).strip()
                    if not n_acic:
                        erros += 1
                        continue
                    
                    if n_acic in acic_existentes:
                        duplicados += 1
                        continue
                    
                    # Parse status
                    status_str = str(row.get("Status", "")).strip()
                    status = None
                    if status_str == "Confirmado":
                        status = StatusACIC.CONFIRMADO
                    elif status_str == "Solicitacao":
                        status = StatusACIC.SOLICITACAO
                    
                    # Parse datas
                    data_fiscalizacao = parse_data_brasil(str(row.get("Data_Fiscalizacao", "")))
                    data_sincronizacao = parse_data_brasil(str(row.get("Data_Sincronizacao", "")))
                    data_execucao = parse_data_brasil(str(row.get("Data_Execução", "")))
                    data_acic = parse_data_brasil(str(row.get("Data_ACIC", "")))
                    data_confirmacao = parse_data_brasil(str(row.get("Data_Confirmacao", "")))
                    
                    # Valor multa
                    valor_multa = None
                    valor_str = str(row.get("Valor_Multa", "")).strip()
                    if valor_str and valor_str != "nan":
                        try:
                            valor_multa = float(valor_str.replace(",", "."))
                        except:
                            pass
                    
                    # Buscar CNC relacionado
                    n_bfs = str(row.get("N_BFS", "")).strip()
                    cnc_id = None
                    if n_bfs:
                        cnc = self.db.query(CNC).filter(CNC.bfs == n_bfs).first()
                        if cnc:
                            cnc_id = cnc.id
                    
                    acic = ACIC(
                        n_acic=n_acic,
                        n_bfs=n_bfs or None,
                        n_cnc=str(row.get("N_CNC", "")).strip() or None,
                        cnc_id=cnc_id,
                        status=status,
                        data_fiscalizacao=data_fiscalizacao,
                        data_sincronizacao=data_sincronizacao,
                        data_execucao=data_execucao,
                        data_acic=data_acic,
                        data_confirmacao=data_confirmacao,
                        servico=str(row.get("Servico", "")).strip() or None,
                        responsavel=str(row.get("Responsavel", "")).strip() or None,
                        agente_fiscalizador=str(row.get("Agente_Fiscalizador", "")).strip() or None,
                        contratada=str(row.get("Contratada", "")).strip() or None,
                        regional=str(row.get("Regional", "")).strip() or None,
                        area=str(row.get("Area", "")).strip() or None,
                        setor=str(row.get("Setor", "")).strip() or None,
                        turno=str(row.get("Turno", "")).strip() or None,
                        descricao=str(row.get("Descricao", "")).strip() or None,
                        valor_multa=valor_multa,
                        clausula_contratual=str(row.get("Clausula_Contratual", "")).strip() or None,
                        observacao=str(row.get("Observacao", "")).strip() or None,
                        endereco=str(row.get("Endereco", "")).strip() or None,
                    )
                    
                    self.db.add(acic)
                    acic_existentes.add(n_acic)  # Adicionar à lista para evitar duplicados no mesmo batch
                    processados += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao processar ACIC {n_acic}: {e}")
                    erros += 1
                    continue
            
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Erro ao commitar ACICs: {e}")
                raise
            
            return {
                "processados": processados,
                "erros": erros,
                "duplicados": duplicados,
                "total": len(df)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao processar CSV de ACICs: {e}")
            raise
    
    def processar_ouvidoria_csv(self, file_path: str) -> Dict[str, Any]:
        """Processa CSV de Ouvidorias."""
        try:
            df = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
            df.columns = df.columns.str.strip()
            
            # Remover duplicados dentro do próprio CSV
            df = df.drop_duplicates(subset=["Numero_Chamado"], keep="first")
            
            # Buscar todos os números existentes de uma vez
            numeros_list = [str(num).strip() for num in df["Numero_Chamado"].dropna().tolist() if str(num).strip()]
            numeros_existentes = set()
            if numeros_list:
                numeros_existentes = set(
                    row[0] for row in self.db.query(Ouvidoria.numero_chamado).filter(
                        Ouvidoria.numero_chamado.in_(numeros_list)
                    ).all()
                )
            
            processados = 0
            erros = 0
            duplicados = 0
            
            for _, row in df.iterrows():
                try:
                    numero_chamado = str(row.get("Numero_Chamado", "")).strip()
                    if not numero_chamado:
                        erros += 1
                        continue
                    
                    if numero_chamado in numeros_existentes:
                        duplicados += 1
                        continue
                    
                    # Parse status
                    status_str = str(row.get("Status", "")).strip()
                    status = None
                    if status_str == "Ouvidoria Encerrada":
                        status = StatusOuvidoria.OUVIDORIA_ENCERRADA
                    elif status_str == "Em Execução":
                        status = StatusOuvidoria.EM_EXECUCAO
                    elif status_str == "Finalizado":
                        status = StatusOuvidoria.FINALIZADO
                    elif status_str == "Executado":
                        status = StatusOuvidoria.EXECUTADO
                    
                    # Parse datas
                    data_registro = parse_data_brasil(str(row.get("Data_Registro", "")))
                    data_execucao = parse_data_brasil(str(row.get("Data_Execução", "")))
                    
                    # Coordenadas
                    coordenadas_str = str(row.get("Coordenadas", "")).strip()
                    
                    ouvidoria = Ouvidoria(
                        numero_chamado=numero_chamado,
                        numero_sei=str(row.get("Número_SEI", "")).strip() or None,
                        status=status,
                        situacao=str(row.get("Situação", "")).strip() or None,
                        contratada=str(row.get("Contratada", "")).strip() or None,
                        origem=str(row.get("Origem", "")).strip() or None,
                        procedente=str(row.get("Procedente", "")).strip() or None,
                        procedente_por_status=str(row.get("Procedente_por_status", "")).strip() or None,
                        regional=str(row.get("Regional", "")).strip() or None,
                        area=str(row.get("Área", "")).strip() or None,
                        servico=str(row.get("Serviço", "")).strip() or None,
                        assunto=str(row.get("Assunto", "")).strip() or None,
                        endereco=str(row.get("Endereço", "")).strip() or None,
                        coordenadas=coordenadas_str if coordenadas_str != "nan" else None,
                        data_registro=data_registro,
                        data_execucao=data_execucao,
                        responsividade=str(row.get("Responsividade", "")).strip() or None,
                    )
                    
                    self.db.add(ouvidoria)
                    numeros_existentes.add(numero_chamado)  # Adicionar à lista para evitar duplicados no mesmo batch
                    processados += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao processar Ouvidoria {numero_chamado}: {e}")
                    erros += 1
                    continue
            
            try:
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Erro ao commitar Ouvidorias: {e}")
                raise
            
            return {
                "processados": processados,
                "erros": erros,
                "duplicados": duplicados,
                "total": len(df)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erro ao processar CSV de Ouvidorias: {e}")
            raise
    
    def _parse_status_sac(self, status_str: str) -> StatusSAC:
        """Parse de status de SAC."""
        status_map = {
            "Aguardando Análise": StatusSAC.AGUARDANDO_ANALISE,
            "Aguardando Agendamento": StatusSAC.AGUARDANDO_AGENDAMENTO,
            "Aguardando Revistoria": StatusSAC.AGUARDANDO_REVISTORIA,
            "Não Procede": StatusSAC.NAO_PROCEDE,
            "Em Execução": StatusSAC.EM_EXECUCAO,
            "Executado": StatusSAC.EXECUTADO,
            "Finalizado": StatusSAC.FINALIZADO,
            "Confirmar Execução": StatusSAC.CONFIRMAR_EXECUCAO,
            "Confirmada Execução": StatusSAC.CONFIRMADA_EXECUCAO,
            "Não Confirmada Execução": StatusSAC.NAO_CONFIRMADA_EXECUCAO,
            "Confirmar Fora de Escopo": StatusSAC.CONFIRMAR_FORA_ESCOPO,
        }
        return status_map.get(status_str, StatusSAC.AGUARDANDO_ANALISE)
    
    def _parse_tipo_servico(self, tipo_str: str) -> TipoServico:
        """
        Parse de tipo de serviço conforme especificações.
        
        Demandantes (com responsividade):
        - Coleta e transporte de entulho e grandes objetos -> ENTULHO (72h)
        - Remoção de animais mortos -> ANIMAL_MORTO (12h)
        - Papeleiras -> PAPELEIRAS (72h)
        
        Escalonados (agendados):
        - Cata-Bagulho -> CATABAGULHO
        - Coleta manual de varrição e feiras -> VARRIACAO_COLETA
        - Mutirão (inclui Capinação, Propaganda, Raspagem, Pintura) -> MUTIRAO
        - Lavagem -> LAVAGEM
        - Limpeza de bueiros -> BUEIRO
        - Varrição manual -> VARRIACAO
        - Varrição de Praças -> VARRIACAO_PRACAS
        - Monumentos -> MONUMENTOS
        - Outros -> OUTROS
        """
        tipo_lower = tipo_str.lower()
        
        # IMPORTANTE: Verificar Escalonados específicos ANTES dos Demandantes genéricos
        # para evitar que "Cata-Bagulho" seja classificado como "entulho"
        
        # Escalonados - verificar casos específicos primeiro (antes dos Demandantes!)
        # Cata-Bagulho: "Coleta programada e transporte de objetos volumosos e de entulho (Cata-Bagulho)"
        # A chave é identificar "programada" ANTES de verificar "entulho"
        if "cata-bagulho" in tipo_lower or "cata bagulho" in tipo_lower:
            return TipoServico.CATABAGULHO
        elif "coleta programada" in tipo_lower:
            # Se tem "coleta programada", é SEMPRE Cata-Bagulho (Escalonado)
            return TipoServico.CATABAGULHO
        
        # Demandantes - verificar depois dos Escalonados específicos
        # Coleta e transporte de entulho e grandes objetos (NÃO programada = Demandante)
        # Texto exato: "Coleta e transporte de entulho e grandes objetos depositados irregularmente nas vias..."
        elif ("coleta e transporte" in tipo_lower or "coleta de entulho" in tipo_lower) and \
             ("entulho" in tipo_lower or "grandes objetos" in tipo_lower) and \
             "programada" not in tipo_lower:  # Garantir que NÃO é programada
            return TipoServico.ENTULHO
        elif ("entulho" in tipo_lower or "grandes objetos" in tipo_lower) and \
             "programada" not in tipo_lower:  # Se tem entulho mas NÃO é programada, é Demandante
            return TipoServico.ENTULHO
        elif (
            ("animal" in tipo_lower or "animais" in tipo_lower) and
            ("morto" in tipo_lower or "mortos" in tipo_lower)
        ):
            return TipoServico.ANIMAL_MORTO
        elif "papeleira" in tipo_lower or "lixeira" in tipo_lower or "equipamentos de recepção" in tipo_lower:
            return TipoServico.PAPELEIRAS
        
        # Escalonados - continuar verificando outros casos específicos
        elif ("coleta manual" in tipo_lower or "coleta de varrição" in tipo_lower) and ("feira" in tipo_lower or "compactador" in tipo_lower):
            return TipoServico.VARRIACAO_COLETA
        elif "varrição de praça" in tipo_lower or "equipe de varrição de praça" in tipo_lower:
            return TipoServico.VARRIACAO_PRACAS
        elif "varrição" in tipo_lower:
            return TipoServico.VARRIACAO
        elif ("mutirão" in tipo_lower or "mutirao" in tipo_lower) or \
             "capinação" in tipo_lower or \
             "propaganda" in tipo_lower or \
             "raspagem" in tipo_lower or \
             "pintura de guia" in tipo_lower or \
             "zeladoria" in tipo_lower:
            return TipoServico.MUTIRAO
        elif "lavagem" in tipo_lower and ("equipamento" in tipo_lower or "público" in tipo_lower):
            return TipoServico.LAVAGEM
        elif "bueiro" in tipo_lower or "boca de lobo" in tipo_lower or "boca de leão" in tipo_lower or "desobstrução" in tipo_lower:
            return TipoServico.BUEIRO
        elif "monumento" in tipo_lower or "conservação de monumento" in tipo_lower:
            return TipoServico.MONUMENTOS
        else:
            return TipoServico.OUTROS
    
    def _parse_subprefeitura(self, subpref_str: str) -> Subprefeitura:
        """Parse de subprefeitura."""
        subpref_normalizada = normalizar_subprefeitura(subpref_str)
        if subpref_normalizada == "CV":
            return Subprefeitura.CV
        elif subpref_normalizada == "JT":
            return Subprefeitura.JT
        elif subpref_normalizada == "ST":
            return Subprefeitura.ST
        elif subpref_normalizada == "MG":
            return Subprefeitura.MG
        else:
            return Subprefeitura.CV  # Default

