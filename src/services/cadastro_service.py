"""
Serviço de cadastro de novos clientes no JETTAX
"""
import time
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from ..models.empresa import Empresa
from ..core.api_client import JettaxAPI
from ..services.regime_mapper import obter_regime_object_id
from ..utils.logger import get_logger
from ..utils.cnpj_utils import formatar_cnpj, somente_digitos

logger = get_logger()


class CadastroService:
    """Serviço para cadastro de novos clientes"""
    
    def __init__(self, api_client: JettaxAPI, dry_run: bool = False):
        """
        Inicializa o serviço
        
        Args:
            api_client: Cliente da API JETTAX
            dry_run: Se True, não faz alterações reais
        """
        self.api = api_client
        self.dry_run = dry_run
    
    def enriquecer_com_receita(self, empresa: Empresa) -> Tuple[Empresa, Optional[Dict]]:
        """
        Enriquece dados da empresa com consulta à Receita Federal
        
        Args:
            empresa: Empresa da planilha
        
        Returns:
            Tupla (empresa_atualizada, dados_receita)
        """
        logger.debug(f"Consultando Receita Federal para {formatar_cnpj(empresa.cnpj)}")
        
        dados_receita = self.api.consultar_cnpj_receita(empresa.cnpj)
        
        if not dados_receita:
            logger.warning(f"CNPJ {formatar_cnpj(empresa.cnpj)} não encontrado na Receita")
            return empresa, None
        
        # Enriquecer dados
        if not empresa.razao_social or empresa.razao_social == empresa.cnpj:
            razao = dados_receita.get("name") or dados_receita.get("razao_social")
            if razao:
                empresa.razao_social = razao
        
        if not empresa.municipio:
            cidade = dados_receita.get("city") or dados_receita.get("municipio")
            if cidade:
                empresa.municipio = cidade
        
        # CNAEs
        cnae_principal = dados_receita.get("mainActivity") or dados_receita.get("cnae_fiscal")
        cnaes_secundarios = dados_receita.get("secondaryActivities") or dados_receita.get("cnaes_secundarios", [])
        
        cnaes = []
        if cnae_principal:
            cnae_code = cnae_principal if isinstance(cnae_principal, str) else cnae_principal.get("code")
            if cnae_code:
                cnaes.append(somente_digitos(cnae_code))
        
        for cnae in cnaes_secundarios:
            cnae_code = cnae if isinstance(cnae, str) else cnae.get("code")
            if cnae_code:
                cnaes.append(somente_digitos(cnae_code))
        
        if cnaes:
            empresa.cnaes = cnaes
        
        return empresa, dados_receita
    
    def montar_payload_cadastro(
        self,
        empresa: Empresa,
        regime_object_id: str,
        codigo_ibge: int
    ) -> Dict[str, Any]:
        """
        Monta payload para criação de cliente
        
        Args:
            empresa: Dados da empresa
            regime_object_id: ObjectId do regime tributário
            codigo_ibge: Código IBGE da cidade
        
        Returns:
            Payload para POST /api/v1/clients
        """
        payload = {
            "document": empresa.cnpj,
            "name": empresa.razao_social,
            "taxation": regime_object_id,
            "ibgeCode": codigo_ibge,
            "email": empresa.email or "",
            "stateRegistration": "",
            "municipalRegistration": empresa.im or "",
            "isActive": True
        }
        
        # IE: tratar "FALSE" → vazio
        ie_valor = empresa.get_ie_numerico()
        if ie_valor and ie_valor != 0:
            payload["stateRegistration"] = str(ie_valor)
        
        # CNAEs
        if empresa.cnaes:
            payload["cnaes"] = empresa.cnaes
        
        # Credenciais prefeitura (se aplicável)
        if empresa.precisa_credenciais_prefeitura():
            if not empresa.tem_credenciais_completas():
                logger.warning(
                    f"{formatar_cnpj(empresa.cnpj)}: Regime de serviços sem credenciais de prefeitura"
                )
            else:
                payload["login"] = empresa.cpf_prefeitura
                payload["password"] = empresa.senha_prefeitura
        
        return payload
    
    def cadastrar_empresa(self, empresa: Empresa) -> Tuple[bool, str]:
        """
        Cadastra uma empresa no JETTAX
        
        Args:
            empresa: Empresa a ser cadastrada
        
        Returns:
            Tupla (sucesso, mensagem)
        """
        cnpj_formatado = formatar_cnpj(empresa.cnpj)
        
        try:
            # 1. Verificar se já existe
            logger.info(f"[CADASTRO] {cnpj_formatado} - {empresa.razao_social}")
            
            cliente_existente = self.api.buscar_cliente_por_cnpj(empresa.cnpj)
            
            if cliente_existente:
                msg = f"Já cadastrado (ID: {cliente_existente.get('id', 'N/A')})"
                logger.info(f"  ⚠ {msg}")
                return False, msg
            
            # 2. Enriquecer com Receita Federal
            empresa, dados_receita = self.enriquecer_com_receita(empresa)
            
            # 3. Obter regime tributário
            regime_object_id = obter_regime_object_id(empresa.tributacao, self.api)
            
            if not regime_object_id:
                msg = f"Regime '{empresa.tributacao}' não encontrado no JETTAX"
                logger.error(f"  ✗ {msg}")
                return False, msg
            
            # 4. Obter código IBGE
            # Tentar extrair UF da cidade (ex: "SAO PAULO/SP" → "SP")
            uf = "SP"  # Default
            if "/" in empresa.municipio:
                uf = empresa.municipio.split("/")[-1].strip()
            
            cidade_nome = empresa.municipio.split("/")[0].strip()
            
            codigo_ibge = self.api.buscar_codigo_ibge(cidade_nome, uf)
            
            if not codigo_ibge:
                msg = f"Código IBGE não encontrado para {empresa.municipio}"
                logger.warning(f"  ⚠ {msg}")
                # Tentar continuar mesmo sem código IBGE
                codigo_ibge = 0
            
            # 5. Montar payload
            payload = self.montar_payload_cadastro(empresa, regime_object_id, codigo_ibge)
            
            # 6. Criar cliente
            if self.dry_run:
                logger.info(f"  🔍 [DRY-RUN] Criaria cliente com payload: {payload}")
                return True, "Sucesso (dry-run)"
            
            resultado = self.api.criar_cliente(payload)
            
            msg = f"Cadastrado com sucesso (ID: {resultado.get('id', 'N/A')})"
            logger.info(f"  ✓ {msg}")
            
            return True, msg
            
        except Exception as e:
            msg = f"Erro: {str(e)}"
            logger.error(f"  ✗ {msg}")
            return False, msg
    
    def cadastrar_em_lote(
        self,
        empresas: List[Empresa],
        intervalo_segundos: float = 1.0
    ) -> Dict[str, Any]:
        """
        Cadastra múltiplas empresas em lote
        
        Args:
            empresas: Lista de empresas a cadastrar
            intervalo_segundos: Intervalo entre requisições
        
        Returns:
            Estatísticas do processamento
        """
        logger.info(f"Iniciando cadastro em lote de {len(empresas)} empresas...")
        
        stats = {
            "total": len(empresas),
            "sucesso": 0,
            "ja_cadastrados": 0,
            "erros": 0,
            "detalhes": []
        }
        
        for idx, empresa in enumerate(empresas, 1):
            logger.info(f"\n[{idx}/{len(empresas)}]")
            
            sucesso, mensagem = self.cadastrar_empresa(empresa)
            
            if sucesso:
                stats["sucesso"] += 1
            elif "já cadastrado" in mensagem.lower():
                stats["ja_cadastrados"] += 1
            else:
                stats["erros"] += 1
            
            stats["detalhes"].append({
                "cnpj": empresa.cnpj,
                "razao_social": empresa.razao_social,
                "sucesso": sucesso,
                "mensagem": mensagem
            })
            
            # Intervalo entre requisições
            if idx < len(empresas):
                time.sleep(intervalo_segundos)
        
        logger.info("\n" + "=" * 60)
        logger.info("RESUMO DO CADASTRO")
        logger.info("=" * 60)
        logger.info(f"Total: {stats['total']}")
        logger.info(f"✓ Cadastrados: {stats['sucesso']}")
        logger.info(f"⚠ Já existiam: {stats['ja_cadastrados']}")
        logger.info(f"✗ Erros: {stats['erros']}")
        logger.info("=" * 60)
        
        return stats
