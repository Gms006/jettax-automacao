"""
Utilitários para manipulação de datas
"""
from datetime import datetime, date
from typing import Optional, Union
import re


def parse_date(valor: any) -> Optional[date]:
    """
    Converte diversos formatos de data para objeto date
    
    Formatos suportados:
    - yyyy-mm-dd
    - dd/mm/yyyy
    - yyyy-mm-dd HH:MM:SS
    - Objetos datetime
    - Objetos date
    
    Args:
        valor: Valor a ser convertido
    
    Returns:
        Objeto date ou None se inválido
    """
    if not valor:
        return None
    
    # Já é um objeto date
    if isinstance(valor, date):
        return valor
    
    # É um datetime
    if isinstance(valor, datetime):
        return valor.date()
    
    # Converter para string
    texto = str(valor).strip()
    
    # Remover parte de hora se existir
    texto = texto.split(" ")[0]
    
    # Tentar formato yyyy-mm-dd
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Tentar formato dd/mm/yyyy
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        pass
    
    # Tentar formato dd-mm-yyyy
    try:
        return datetime.strptime(texto, "%d-%m-%Y").date()
    except ValueError:
        pass
    
    return None


def formatar_data_br(data: Optional[Union[date, datetime]]) -> str:
    """
    Formata data no padrão brasileiro dd/mm/yyyy
    
    Args:
        data: Objeto date ou datetime
    
    Returns:
        Data formatada ou string vazia
    """
    if not data:
        return ""
    
    if isinstance(data, datetime):
        data = data.date()
    
    return data.strftime("%d/%m/%Y")


def formatar_data_iso(data: Optional[Union[date, datetime]]) -> str:
    """
    Formata data no padrão ISO yyyy-mm-dd
    
    Args:
        data: Objeto date ou datetime
    
    Returns:
        Data formatada ou string vazia
    """
    if not data:
        return ""
    
    if isinstance(data, datetime):
        data = data.date()
    
    return data.strftime("%Y-%m-%d")


def data_para_jettax(data: Optional[Union[date, datetime]]) -> str:
    """
    Formata data para o formato esperado pela API JETTAX (dd/mm/yyyy)
    
    Args:
        data: Objeto date ou datetime
    
    Returns:
        Data formatada ou string vazia
    """
    return formatar_data_br(data)
