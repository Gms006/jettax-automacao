"""
Utilitários para manipulação de CNPJ/CPF
"""
import re
from typing import Optional


def somente_digitos(valor: Optional[str]) -> str:
    """Remove todos os caracteres não numéricos"""
    if valor is None:
        return ""
    return re.sub(r"\D", "", str(valor))


def normalizar_cnpj(cnpj: Optional[str]) -> str:
    """
    Normaliza CNPJ para formato de 14 dígitos
    
    Args:
        cnpj: CNPJ com ou sem máscara
    
    Returns:
        CNPJ com 14 dígitos ou string vazia
    """
    digitos = somente_digitos(cnpj)
    
    if not digitos:
        return ""
    
    if len(digitos) == 14:
        return digitos.zfill(14)
    
    return digitos


def formatar_cnpj(cnpj: Optional[str]) -> str:
    """
    Formata CNPJ no padrão 00.000.000/0000-00
    
    Args:
        cnpj: CNPJ apenas com dígitos
    
    Returns:
        CNPJ formatado ou string original se inválido
    """
    digitos = somente_digitos(cnpj)
    
    if len(digitos) != 14:
        return cnpj or ""
    
    return f"{digitos[0:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:14]}"


def validar_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ (verifica formato e dígitos verificadores)
    
    Args:
        cnpj: CNPJ com ou sem máscara
    
    Returns:
        True se válido, False caso contrário
    """
    digitos = somente_digitos(cnpj)
    
    # Verifica se tem 14 dígitos
    if len(digitos) != 14:
        return False
    
    # Verifica se não é sequência repetida (ex: 11111111111111)
    if len(set(digitos)) == 1:
        return False
    
    # Validação dos dígitos verificadores
    def calcular_digito(cnpj_parcial: str, pesos: list) -> int:
        soma = sum(int(digitos[i]) * pesos[i] for i in range(len(pesos)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    
    # Primeiro dígito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digito1 = calcular_digito(digitos[:12], pesos1)
    
    if digito1 != int(digitos[12]):
        return False
    
    # Segundo dígito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digito2 = calcular_digito(digitos[:13], pesos2)
    
    if digito2 != int(digitos[13]):
        return False
    
    return True


def normalizar_cpf(cpf: Optional[str]) -> str:
    """
    Normaliza CPF para formato de 11 dígitos
    
    Args:
        cpf: CPF com ou sem máscara
    
    Returns:
        CPF com 11 dígitos ou string vazia
    """
    digitos = somente_digitos(cpf)
    
    if not digitos:
        return ""
    
    if len(digitos) == 11:
        return digitos.zfill(11)
    
    return digitos


def formatar_cpf(cpf: Optional[str]) -> str:
    """
    Formata CPF no padrão 000.000.000-00
    
    Args:
        cpf: CPF apenas com dígitos
    
    Returns:
        CPF formatado ou string original se inválido
    """
    digitos = somente_digitos(cpf)
    
    if len(digitos) != 11:
        return cpf or ""
    
    return f"{digitos[0:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:11]}"
