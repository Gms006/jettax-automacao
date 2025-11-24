"""
Serviço de configuração de módulos JETTAX (Federal e Serviços)
"""
from typing import Dict, Any, Optional
from datetime import datetime

from ..models.empresa import Empresa
from ..core.api_client import JettaxAPI
from ..utils.logger import get_logger
from ..utils.cnpj_utils import formatar_cnpj

logger = get_logger()


class ModuloService:
    """Serviço para ativação e configuração de módulos"""
    
    def __init__(self, api_client: JettaxAPI, dry_run: bool = False):
        """
        Inicializa o serviço
        
        Args:
            api_client: Cliente da API JETTAX
            dry_run: Se True, não faz alterações reais
        """
        self.api = api_client
        self.dry_run = dry_run
    
    def empresa_tem_certificado(self, empresa: Empresa, cliente_jettax: Dict[str, Any]) -> bool:
        """
        Verifica se a empresa possui certificado digital válido
        
        Args:
            empresa: Dados da planilha
            cliente_jettax: Dados do cliente no JETTAX
        
        Returns:
            True se tem certificado válido
        """
        # Verificar no JETTAX se tem certificado válido
        certificado = cliente_jettax.get("certificate", {})
        
        if not certificado:
            return False
        
        # Verificar status e validade
        status = certificado.get("status")
        validade = certificado.get("validity") or certificado.get("expirationDate")
        
        if status == "valid" or status == "active":
            return True
        
        if validade:
            try:
                # Verificar se ainda não expirou
                if isinstance(validade, str):
                    exp_date = datetime.fromisoformat(validade.replace("Z", "+00:00"))
                    if exp_date > datetime.now():
                        return True
            except:
                pass
        
        return False
    
    def configurar_modulo_federal(
        self,
        client_id: str,
        empresa: Empresa,
        tem_certificado: bool
    ) -> bool:
        """
        Configura módulo Federal para uma empresa
        
        Args:
            client_id: ID do cliente no JETTAX
            empresa: Dados da empresa
            tem_certificado: Se a empresa tem certificado digital
        
        Returns:
            True se configurado com sucesso
        """
        cnpj_formatado = formatar_cnpj(empresa.cnpj)
        
        try:
            # Configuração do módulo Federal
            payload = {
                "clientId": client_id,
                "module": "federal",
                "settings": {
                    # Ativar módulo Federal se tem certificado
                    "enabled": tem_certificado,
                    
                    # Configurações específicas (sempre ativar se tem certificado)
                    "aplicarCorrecaoSubstituicoesTributarias": tem_certificado,
                    "aplicarCorrecaoPisCofins": tem_certificado,
                    
                    # Buscar NF-e emitidas (só funciona com certificado)
                    "buscarNFeEmitidas": tem_certificado
                }
            }
            
            if self.dry_run:
                logger.info(
                    f"  🔍 [DRY-RUN] Configuraria Módulo Federal para {cnpj_formatado}: "
                    f"enabled={tem_certificado}"
                )
                return True
            
            # Enviar configuração via API
            # Endpoint pode variar, ajustar conforme documentação JETTAX
            endpoint = f"/api/v1/clients/{client_id}/modules/federal"
            
            self.api._request("PUT", endpoint, json_data=payload)
            
            status = "✓ Ativado" if tem_certificado else "⚠ Desativado (sem certificado)"
            logger.info(f"  {status} Módulo Federal: {cnpj_formatado}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Erro ao configurar Módulo Federal para {cnpj_formatado}: {e}")
            return False
    
    def configurar_modulo_servicos(
        self,
        client_id: str,
        empresa: Empresa,
        eh_empresa_servicos: bool
    ) -> bool:
        """
        Configura módulo Serviços para uma empresa
        
        Args:
            client_id: ID do cliente no JETTAX
            empresa: Dados da empresa
            eh_empresa_servicos: Se a empresa é de serviços
        
        Returns:
            True se configurado com sucesso
        """
        cnpj_formatado = formatar_cnpj(empresa.cnpj)
        
        try:
            # Configuração do módulo Serviços
            payload = {
                "clientId": client_id,
                "module": "services",
                "settings": {
                    # Ativar módulo Serviços apenas para empresas de serviços
                    "enabled": eh_empresa_servicos,
                    
                    # Configurações específicas (ativar se é empresa de serviços)
                    "gerarIss": eh_empresa_servicos,
                    "ativarDctfweb": eh_empresa_servicos
                }
            }
            
            if self.dry_run:
                logger.info(
                    f"  🔍 [DRY-RUN] Configuraria Módulo Serviços para {cnpj_formatado}: "
                    f"enabled={eh_empresa_servicos}"
                )
                return True
            
            # Enviar configuração via API
            endpoint = f"/api/v1/clients/{client_id}/modules/services"
            
            self.api._request("PUT", endpoint, json_data=payload)
            
            status = "✓ Ativado" if eh_empresa_servicos else "⚠ Desativado (não é serviços)"
            logger.info(f"  {status} Módulo Serviços: {cnpj_formatado}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Erro ao configurar Módulo Serviços para {cnpj_formatado}: {e}")
            return False
    
    def configurar_modulos_empresa(
        self,
        empresa: Empresa,
        cliente_jettax: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Configura todos os módulos necessários para uma empresa
        
        Args:
            empresa: Dados da planilha
            cliente_jettax: Dados do cliente no JETTAX
        
        Returns:
            Dict com status de cada módulo configurado
        """
        client_id = cliente_jettax.get("id") or cliente_jettax.get("_id")
        cnpj_formatado = formatar_cnpj(empresa.cnpj)
        
        logger.info(f"[MÓDULOS] Configurando {cnpj_formatado} - {empresa.razao_social}")
        
        resultado = {
            "federal": False,
            "servicos": False
        }
        
        # 1. Verificar se tem certificado digital
        tem_certificado = self.empresa_tem_certificado(empresa, cliente_jettax)
        
        if tem_certificado:
            logger.info(f"  📜 Certificado digital: SIM")
        else:
            logger.info(f"  📜 Certificado digital: NÃO")
        
        # 2. Verificar se é empresa de serviços
        eh_empresa_servicos = empresa.precisa_credenciais_prefeitura()
        
        if eh_empresa_servicos:
            logger.info(f"  🏢 Tipo: SERVIÇOS (regime: {empresa.tributacao})")
        else:
            logger.info(f"  🏢 Tipo: COMÉRCIO/INDÚSTRIA (regime: {empresa.tributacao})")
        
        # 3. Configurar Módulo Federal
        resultado["federal"] = self.configurar_modulo_federal(
            client_id,
            empresa,
            tem_certificado
        )
        
        # 4. Configurar Módulo Serviços
        resultado["servicos"] = self.configurar_modulo_servicos(
            client_id,
            empresa,
            eh_empresa_servicos
        )
        
        return resultado
    
    def configurar_modulos_em_lote(
        self,
        empresas_com_clientes: list
    ) -> Dict[str, Any]:
        """
        Configura módulos para múltiplas empresas em lote
        
        Args:
            empresas_com_clientes: Lista de tuplas (empresa, cliente_jettax)
        
        Returns:
            Estatísticas do processamento
        """
        logger.info(f"Configurando módulos para {len(empresas_com_clientes)} empresas...\n")
        
        stats = {
            "total": len(empresas_com_clientes),
            "federal_ativado": 0,
            "federal_desativado": 0,
            "servicos_ativado": 0,
            "servicos_desativado": 0,
            "erros": 0,
            "detalhes": []
        }
        
        for idx, (empresa, cliente) in enumerate(empresas_com_clientes, 1):
            logger.info(f"\n[{idx}/{len(empresas_com_clientes)}]")
            
            try:
                resultado = self.configurar_modulos_empresa(empresa, cliente)
                
                # Atualizar estatísticas
                tem_certificado = self.empresa_tem_certificado(empresa, cliente)
                eh_servicos = empresa.precisa_credenciais_prefeitura()
                
                if tem_certificado:
                    stats["federal_ativado"] += 1
                else:
                    stats["federal_desativado"] += 1
                
                if eh_servicos:
                    stats["servicos_ativado"] += 1
                else:
                    stats["servicos_desativado"] += 1
                
                stats["detalhes"].append({
                    "cnpj": empresa.cnpj,
                    "razao_social": empresa.razao_social,
                    "federal": "ativado" if tem_certificado else "desativado",
                    "servicos": "ativado" if eh_servicos else "desativado",
                    "sucesso": resultado["federal"] and resultado["servicos"]
                })
                
            except Exception as e:
                logger.error(f"✗ Erro ao processar {formatar_cnpj(empresa.cnpj)}: {e}")
                stats["erros"] += 1
                
                stats["detalhes"].append({
                    "cnpj": empresa.cnpj,
                    "razao_social": empresa.razao_social,
                    "federal": "erro",
                    "servicos": "erro",
                    "sucesso": False
                })
        
        logger.info("\n" + "=" * 60)
        logger.info("RESUMO DA CONFIGURAÇÃO DE MÓDULOS")
        logger.info("=" * 60)
        logger.info(f"Total: {stats['total']}")
        logger.info(f"Módulo Federal:")
        logger.info(f"  ✓ Ativados: {stats['federal_ativado']}")
        logger.info(f"  ⚠ Desativados: {stats['federal_desativado']}")
        logger.info(f"Módulo Serviços:")
        logger.info(f"  ✓ Ativados: {stats['servicos_ativado']}")
        logger.info(f"  ⚠ Desativados: {stats['servicos_desativado']}")
        logger.info(f"✗ Erros: {stats['erros']}")
        logger.info("=" * 60)
        
        return stats
