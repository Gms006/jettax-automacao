"""
Serviço de comparação entre dados da planilha e JETTAX
"""
from typing import Dict, Any, List, Tuple
from ..models.empresa import Empresa
from ..utils.logger import get_logger
from ..utils.cnpj_utils import somente_digitos

logger = get_logger()


class ComparacaoService:
    """Serviço para comparar dados entre planilha e JETTAX"""
    
    # Campos que devem ser comparados
    CAMPOS_COMPARACAO = [
        "razao_social",
        "tributacao", 
        "ie",
        "im",
        "email",
        "municipio"
    ]
    
    def __init__(self):
        """Inicializa o serviço"""
        pass
    
    def comparar_empresa(
        self,
        empresa_planilha: Empresa,
        cliente_jettax: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Compara dados de uma empresa entre planilha e JETTAX
        
        Args:
            empresa_planilha: Objeto Empresa da planilha
            cliente_jettax: Dados do cliente retornados pela API
        
        Returns:
            Tupla (tem_diferenças, lista_de_diferenças)
        """
        diferencas = []
        
        # Razão Social
        razao_planilha = empresa_planilha.razao_social.strip().upper()
        razao_jettax = str(cliente_jettax.get("name", "")).strip().upper()
        
        if razao_planilha != razao_jettax:
            diferencas.append(
                f"Razão Social: '{razao_jettax}' → '{razao_planilha}'"
            )
        
        # Tributação
        tributacao_planilha = empresa_planilha.tributacao.strip()
        
        # Regime no JETTAX pode estar em 'taxation' ou 'taxRegime.name'
        regime_jettax = cliente_jettax.get("taxation", {})
        if isinstance(regime_jettax, dict):
            tributacao_jettax = regime_jettax.get("name", "")
        else:
            tributacao_jettax = str(regime_jettax)
        
        tributacao_jettax = str(tributacao_jettax).strip()
        
        if tributacao_planilha != tributacao_jettax:
            diferencas.append(
                f"Tributação: '{tributacao_jettax}' → '{tributacao_planilha}'"
            )
        
        # IE
        ie_planilha = empresa_planilha.get_ie_numerico()
        ie_jettax = cliente_jettax.get("stateRegistration")
        
        # Converter para string para comparação
        ie_planilha_str = str(ie_planilha) if ie_planilha else ""
        ie_jettax_str = str(ie_jettax) if ie_jettax else ""
        
        if ie_planilha_str != ie_jettax_str:
            diferencas.append(
                f"IE: '{ie_jettax_str}' → '{ie_planilha_str}'"
            )
        
        # IM
        im_planilha = empresa_planilha.im or ""
        im_jettax = str(cliente_jettax.get("municipalRegistration", ""))
        
        if im_planilha.strip() != im_jettax.strip():
            diferencas.append(
                f"IM: '{im_jettax}' → '{im_planilha}'"
            )
        
        # E-mail
        email_planilha = empresa_planilha.email or ""
        email_jettax = str(cliente_jettax.get("email", ""))
        
        if email_planilha.strip().lower() != email_jettax.strip().lower():
            diferencas.append(
                f"E-mail: '{email_jettax}' → '{email_planilha}'"
            )
        
        # Município
        municipio_planilha = empresa_planilha.municipio.strip().upper()
        
        cidade_jettax = cliente_jettax.get("city", {})
        if isinstance(cidade_jettax, dict):
            municipio_jettax = cidade_jettax.get("name", "")
        else:
            municipio_jettax = str(cidade_jettax)
        
        municipio_jettax = municipio_jettax.strip().upper()
        
        if municipio_planilha != municipio_jettax:
            diferencas.append(
                f"Município: '{municipio_jettax}' → '{municipio_planilha}'"
            )
        
        tem_diferencas = len(diferencas) > 0
        
        return tem_diferencas, diferencas
    
    def aplicar_atualizacoes_no_cliente(
        self,
        empresa_planilha: Empresa,
        cliente_completo: Dict[str, Any],
        regime_object_id: str
    ) -> Dict[str, Any]:
        """
        Aplica atualizações da planilha no objeto COMPLETO do cliente
        
        IMPORTANTE: Este método modifica o objeto completo retornado por GET /api/v1/clients/{id}
        A API do JETTAX precisa receber o objeto COMPLETO no PUT, não apenas campos alterados.
        
        Args:
            empresa_planilha: Dados da planilha
            cliente_completo: Objeto COMPLETO do cliente (59 campos do GET)
            regime_object_id: ObjectId do regime tributário
        
        Returns:
            Objeto cliente modificado (pronto para PUT)
        """
        # 1. Tributação - usar taxRegime (não taxation)
        if regime_object_id:
            cliente_completo["taxRegime"] = regime_object_id
        
        # 2. Inscrição Municipal - está em municipalIntegration.municipalRegistration
        if not cliente_completo.get("municipalIntegration"):
            cliente_completo["municipalIntegration"] = {}
        
        if empresa_planilha.im and empresa_planilha.im.strip():
            cliente_completo["municipalIntegration"]["municipalRegistration"] = empresa_planilha.im.strip()
        
        # 3. Credenciais Prefeitura (se aplicável)
        if empresa_planilha.precisa_credenciais_prefeitura():
            if empresa_planilha.cpf_prefeitura and empresa_planilha.cpf_prefeitura.strip():
                cliente_completo["municipalIntegration"]["login"] = empresa_planilha.cpf_prefeitura.strip()
            
            if empresa_planilha.senha_prefeitura and empresa_planilha.senha_prefeitura.strip():
                cliente_completo["municipalIntegration"]["password"] = empresa_planilha.senha_prefeitura.strip()
        
        # Atualizar inscrição estadual (IE) se houver
        ie_valor = empresa_planilha.get_ie_numerico() if hasattr(empresa_planilha, 'get_ie_numerico') else None
        if ie_valor:
            cliente_completo["stateRegistration"] = str(ie_valor)
        elif hasattr(cliente_completo, "stateRegistration"):
            cliente_completo["stateRegistration"] = ""
        
        return cliente_completo
    
    def detectar_empresas_divergentes(
        self,
        empresas_planilha: List[Empresa],
        clientes_jettax: List[Dict[str, Any]]
    ) -> List[Tuple[Empresa, Dict[str, Any], List[str]]]:
        """
        Detecta empresas com divergências entre planilha e JETTAX
        
        Args:
            empresas_planilha: Lista de empresas da planilha
            clientes_jettax: Lista de clientes do JETTAX
        
        Returns:
            Lista de tuplas (empresa, cliente, diferenças)
        """
        logger.info("Detectando divergências entre planilha e JETTAX...")
        
        # Criar índice por CNPJ
        jettax_por_cnpj = {}
        for cliente in clientes_jettax:
            cnpj = somente_digitos(str(cliente.get("document", "")))
            jettax_por_cnpj[cnpj] = cliente
        
        divergentes = []
        
        for empresa in empresas_planilha:
            cnpj = somente_digitos(empresa.cnpj)
            
            # Verificar se existe no JETTAX
            if cnpj not in jettax_por_cnpj:
                continue  # Não está cadastrado
            
            cliente = jettax_por_cnpj[cnpj]
            
            # Comparar
            tem_diferencas, diferencas = self.comparar_empresa(empresa, cliente)
            
            if tem_diferencas:
                divergentes.append((empresa, cliente, diferencas))
        
        logger.info(f"✓ {len(divergentes)} empresas com divergências detectadas")
        
        return divergentes
