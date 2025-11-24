"""
Serviço de mapeamento de regimes tributários
"""
from typing import Dict, Optional
from ..utils.logger import get_logger

logger = get_logger()


# Mapeamento de regimes da planilha para nomes no JETTAX
# Baseado na análise: 12 regimes únicos na planilha
REGIME_MAPPING = {
    # Simples Nacional
    "Simples Nacional - Serviços": "Simples Nacional",
    "Simples Nacional - Comércio": "Simples Nacional",
    "Simples Nacional - Indústria": "Simples Nacional",
    "Simples Nacional - Comércio e Industria": "Simples Nacional",
    
    # Lucro Presumido
    "Lucro Presumido - Serviços": "Lucro Presumido",
    "Lucro Presumido - Comércio": "Lucro Presumido",
    "Lucro Presumido - Indústria": "Lucro Presumido",
    
    # Lucro Real
    "Lucro Real - Serviços": "Lucro Real",
    "Lucro Real - Comércio": "Lucro Real",
    "Lucro Real - Indústria": "Lucro Real",
    
    # Simei
    "Simei": "SIMEI",
    
    # MEI
    "MEI": "MEI",
    
    # Presumido Arbitrado (caso específico)
    "Presumido Arbitrado": "Lucro Presumido"
}


# ObjectIds conhecidos dos regimes (extraídos dos arquivos de captura)
REGIME_OBJECT_IDS = {
    "Simples Nacional": "60d53314200e556dc277ac20",
    "Lucro Presumido": "62d9471420ba2a79cd31c162",
    "Lucro Real": "62d9471420ba2a79cd31c163",
    "SIMEI": "60d53314200e556dc277ac21",  # Aproximação
    "MEI": "60d53314200e556dc277ac22"  # Aproximação
}


# Cache de ObjectIds (será preenchido dinamicamente)
_regime_cache: Dict[str, str] = {}


def normalizar_nome_regime(nome: str) -> str:
    """
    Normaliza nome do regime para busca
    
    Args:
        nome: Nome do regime
    
    Returns:
        Nome normalizado
    """
    return nome.strip().lower()


def mapear_regime_planilha_para_jettax(regime_planilha: str) -> str:
    """
    Mapeia regime da planilha para nome no JETTAX
    
    Trata variações: Filial, Imune, SN, LP, LR, etc.

    Args:
        regime_planilha: Nome do regime na planilha

    Returns:
        Nome do regime no JETTAX
    """
    if not regime_planilha:
        return ""
    
    regime = regime_planilha.strip().upper()
    
    # Filiais usam o regime da matriz
    if "FILIAL" in regime:
        return "Simples Nacional"  # Default para filial
    
    # Imune/Isento = Simples Nacional
    if "IMUNE" in regime or "ISENT" in regime:
        return "Simples Nacional"
    
    # Simples Nacional
    if "SIMPLES" in regime or regime == "SN":
        return "Simples Nacional"
    
    # Lucro Presumido
    if "PRESUMIDO" in regime or regime == "LP":
        return "Lucro Presumido"
    
    # Lucro Real
    if "REAL" in regime or regime == "LR":
        return "Lucro Real"
    
    # SIMEI
    if "SIMEI" in regime:
        return "SIMEI"
    
    # MEI
    if "MEI" in regime and "SIMEI" not in regime:
        return "MEI"
    
    # Arbitrado = Lucro Presumido
    if "ARBITRADO" in regime:
        return "Lucro Presumido"
    
    # Se não reconhecer, logar e retornar Simples Nacional como fallback
    logger.warning(f"Regime '{regime_planilha}' não reconhecido, usando Simples Nacional")
    return "Simples Nacional"
def obter_regime_object_id(
    regime_planilha: str,
    api_client
) -> Optional[str]:
    """
    Obtém ObjectId de um regime tributário
    
    Args:
        regime_planilha: Nome do regime na planilha
        api_client: Instância do JettaxAPI
    
    Returns:
        ObjectId do regime ou None se não encontrado
    """
    # Verificar cache
    if regime_planilha in _regime_cache:
        return _regime_cache[regime_planilha]
    
    # Mapear nome
    regime_jettax = mapear_regime_planilha_para_jettax(regime_planilha)
    
    # Tentar obter do dicionário de ObjectIds conhecidos
    object_id = REGIME_OBJECT_IDS.get(regime_jettax)
    
    if object_id:
        # Salvar no cache
        _regime_cache[regime_planilha] = object_id
        logger.debug(f"Regime '{regime_planilha}' → '{regime_jettax}' → ObjectId: {object_id}")
        return object_id
    
    # Se não encontrar nos conhecidos, tentar buscar na API
    logger.debug(f"Regime '{regime_jettax}' não encontrado nos ObjectIds conhecidos, tentando API...")
    object_id = api_client.buscar_regime_por_nome(regime_jettax)
    
    if object_id:
        # Salvar no cache
        _regime_cache[regime_planilha] = object_id
        logger.debug(f"Regime '{regime_planilha}' → ObjectId: {object_id}")
    else:
        logger.warning(f"Regime '{regime_planilha}' não encontrado")
    
    return object_id


def limpar_cache():
    """Limpa o cache de regimes"""
    global _regime_cache
    _regime_cache = {}


def regime_exige_credenciais_prefeitura(regime: str) -> bool:
    """
    Verifica se o regime exige credenciais de prefeitura
    
    Args:
        regime: Nome do regime
    
    Returns:
        True se exige credenciais
    """
    # Regimes de serviços exigem credenciais de prefeitura
    keywords = ["serviço", "servico", "service"]
    
    regime_lower = normalizar_nome_regime(regime)
    
    return any(keyword in regime_lower for keyword in keywords)
