"""Endpoints para upload de CSVs."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import tempfile
import os

from app.database import get_db
from app.services.csv_processor import CSVProcessor

router = APIRouter()


@router.post("/upload/sacs-csv")
async def upload_sacs_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Upload e processamento de CSV de SACs."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    # Salvar arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        processor = CSVProcessor(db)
        resultado = processor.processar_sacs_csv(tmp_path)
        return {
            "success": True,
            "message": "CSV processado com sucesso",
            **resultado
        }
    except Exception as e:
        error_msg = str(e)
        # Melhorar mensagem de erro para duplicados
        if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
            error_msg = "Erro: Registros duplicados encontrados. Alguns registros já existem no banco de dados."
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        # Remover arquivo temporário
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/upload/cnc-csv")
async def upload_cnc_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Upload e processamento de CSV de CNCs."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        processor = CSVProcessor(db)
        resultado = processor.processar_cnc_csv(tmp_path)
        return {
            "success": True,
            "message": "CSV processado com sucesso",
            **resultado
        }
    except Exception as e:
        error_msg = str(e)
        # Melhorar mensagem de erro para duplicados
        if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
            error_msg = "Erro: Registros duplicados encontrados. Alguns registros já existem no banco de dados."
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/upload/acic-csv")
async def upload_acic_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Upload e processamento de CSV de ACICs."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        processor = CSVProcessor(db)
        resultado = processor.processar_acic_csv(tmp_path)
        return {
            "success": True,
            "message": "CSV processado com sucesso",
            **resultado
        }
    except Exception as e:
        error_msg = str(e)
        # Melhorar mensagem de erro para duplicados
        if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
            error_msg = "Erro: Registros duplicados encontrados. Alguns registros já existem no banco de dados."
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/upload/ouvidoria-csv")
async def upload_ouvidoria_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Upload e processamento de CSV de Ouvidorias."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser CSV")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        processor = CSVProcessor(db)
        resultado = processor.processar_ouvidoria_csv(tmp_path)
        return {
            "success": True,
            "message": "CSV processado com sucesso",
            **resultado
        }
    except Exception as e:
        error_msg = str(e)
        # Melhorar mensagem de erro para duplicados
        if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
            error_msg = "Erro: Registros duplicados encontrados. Alguns registros já existem no banco de dados."
        raise HTTPException(status_code=500, detail=error_msg)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

