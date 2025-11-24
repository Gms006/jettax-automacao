"""
Serviço de atualização de clientes existentes
"""
import time
from typing import Dict, Any, List, Tuple

import pandas as pd
from pathlib import Path


from models.empresa import Empresa
from core.api_client import JettaxAPI
from services.regime_mapper import obter_regime_object_id
from services.comparacao_service import ComparacaoService
from utils.logger import get_logger
from utils.cnpj_utils import formatar_cnpj, somente_digitos

logger = get_logger()

PLANILHA_PATH = r"G:\- CONTABILIDADE -\Automação\JETTAX\RELAÇÃO DE EMPRESAS.xlsx"


def linha_para_empresa(row):
    return Empresa(
        cnpj=row["CNPJ"],
        razao_social=row["Razao Social"],
        regime=row.get("Regime", ""),
        tributacao=row.get("Tributacao", ""),
        inscricao_estadual=row.get("IE", ""),
        inscricao_municipal=row.get("IM", ""),
        nire=row.get("NIRE", ""),
        ramo_atividade=row.get("Ramo atividade", ""),
        responsavel=row.get("Responsável", ""),
        email=row.get("e-mail", ""),
        municipio=row.get("Municipio", ""),
        data_cadastro=row.get("Data de Cadastro", ""),
        cpf=row.get("CPF", ""),
        senha=row.get("Senha", ""),
        cadastro_jettax=row.get("Cadastro JETTAX", ""),
        # Adicione outros campos conforme necessário no modelo Empresa
    )


class AtualizacaoService:
    """Serviço para atualização de clientes existentes"""

    def __init__(self, api_client: JettaxAPI, dry_run: bool = False):
        """
        Inicializa o serviço

        Args:
            api_client: Cliente da API JETTAX
            dry_run: Se True, não faz alterações reais
        """
        self.api = api_client
        self.dry_run = dry_run
        self.comparador = ComparacaoService()

    def atualizar_empresa(
        self, empresa: Empresa, cliente_jettax: Dict[str, Any]
    ) -> Tuple[bool, str, List[str]]:
        """
        Atualiza uma empresa no JETTAX

        Args:
            empresa: Dados da planilha
            cliente_jettax: Dados atuais no JETTAX

        Returns:
            Tupla (sucesso, mensagem, diferenças)
        """
        cnpj_formatado = formatar_cnpj(empresa.cnpj)
        client_id = cliente_jettax.get("id") or cliente_jettax.get("_id")

        try:
            # 1. Comparar dados
            tem_diferencas, diferencas = self.comparador.comparar_empresa(
                empresa, cliente_jettax
            )

            if not tem_diferencas:
                msg = "Dados iguais, nada a atualizar"
                logger.info(f"[ATUALIZAÇÃO] {cnpj_formatado}: {msg}")
                return True, msg, []

            logger.info(f"[ATUALIZAÇÃO] {cnpj_formatado} - {empresa.razao_social}")
            logger.info(f"  Diferenças encontradas: {len(diferencas)}")

            for diff in diferencas:
                logger.info(f"    - {diff}")

            # 2. Obter regime tributário
            regime_object_id = obter_regime_object_id(empresa.tributacao, self.api)

            if not regime_object_id:
                msg = f"Regime '{empresa.tributacao}' não encontrado no JETTAX"
                logger.error(f"  ✗ {msg}")
                return False, msg, diferencas

            # 3. Buscar cliente COMPLETO (59 campos) para fazer PUT
            logger.debug(f"  Buscando dados completos do cliente {client_id}...")
            cliente_completo = self.api.obter_cliente(client_id)

            # 4. Aplicar atualizações no objeto completo
            cliente_atualizado = self.comparador.aplicar_atualizacoes_no_cliente(
                empresa, cliente_completo, regime_object_id
            )

            cliente_atualizado["stateRegistration"] = (
                empresa.inscricao_estadual if empresa.inscricao_estadual else "0"
            )

            if empresa.email:
                cliente_atualizado["emails"] = [
                    {
                        "email": empresa.email,
                        "type": [{"text": "Fiscal", "value": "fiscal"}],
                    }
                ]
            else:
                cliente_atualizado["emails"] = []

            # 5. Atualizar cliente (PUT com objeto completo)
            if self.dry_run:
                logger.info(f"  🔍 [DRY-RUN] Atualizaria cliente {client_id}")
                for diff in diferencas:
                    logger.info(f"    - {diff}")
                return True, "Sucesso (dry-run)", diferencas

            # DEBUG: Salvar payload antes de enviar
            import json
            from pathlib import Path
            debug_dir = Path(__file__).parent.parent.parent / "debug_payloads"
            debug_dir.mkdir(exist_ok=True)

            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = debug_dir / f"update_{empresa.cnpj}_{timestamp}.json"

            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "client_id": client_id,
                        "cnpj": empresa.cnpj,
                        "razao_social": empresa.razao_social,
                        "payload": cliente_atualizado,
                        "diferencas": diferencas,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            logger.debug(f"  📝 Payload salvo em: {debug_file}")

            self.api.atualizar_cliente(client_id, cliente_atualizado)

            msg = f"Atualizado com sucesso ({len(diferencas)} campos alterados)"
            logger.info(f"  ✓ {msg}")

            return True, msg, diferencas

        except Exception as e:
            msg = f"Erro: {str(e)}"
            logger.error(f"  ✗ {msg}")
            return False, msg, []

    def atualizar_em_lote(
        self, empresas: List[Empresa], intervalo_segundos: float = 1.0
    ) -> Dict[str, Any]:
        """
        Atualiza múltiplas empresas em lote

        Args:
            empresas: Lista de empresas a atualizar
            intervalo_segundos: Intervalo entre requisições

        Returns:
            Estatísticas do processamento
        """
        logger.info(f"Iniciando atualização em lote de {len(empresas)} empresas...")

        # Carregar todos os clientes do JETTAX
        logger.info("Carregando clientes do JETTAX...")
        clientes_jettax = self.api.listar_todos_clientes()

        # Criar índice por CNPJ
        jettax_por_cnpj = {}
        for cliente in clientes_jettax:
            cnpj = somente_digitos(str(cliente.get("document", "")))
            jettax_por_cnpj[cnpj] = cliente

        stats = {
            "total": len(empresas),
            "atualizados": 0,
            "sem_alteracao": 0,
            "nao_cadastrados": 0,
            "erros": 0,
            "detalhes": [],
        }

        for idx, empresa in enumerate(empresas, 1):
            logger.info(f"\n[{idx}/{len(empresas)}]")

            cnpj = somente_digitos(empresa.cnpj)

            # Verificar se existe no JETTAX
            if cnpj not in jettax_por_cnpj:
                msg = "Não cadastrado no JETTAX"
                logger.warning(f"[ATUALIZAÇÃO] {formatar_cnpj(empresa.cnpj)}: {msg}")
                stats["nao_cadastrados"] += 1

                stats["detalhes"].append(
                    {
                        "cnpj": empresa.cnpj,
                        "razao_social": empresa.razao_social,
                        "sucesso": False,
                        "mensagem": msg,
                        "diferencas": [],
                    }
                )

                continue

            cliente = jettax_por_cnpj[cnpj]

            # Atualizar
            sucesso, mensagem, diferencas = self.atualizar_empresa(empresa, cliente)

            if sucesso and diferencas:
                stats["atualizados"] += 1
            elif sucesso and not diferencas:
                stats["sem_alteracao"] += 1
            else:
                stats["erros"] += 1

            stats["detalhes"].append(
                {
                    "cnpj": empresa.cnpj,
                    "razao_social": empresa.razao_social,
                    "sucesso": sucesso,
                    "mensagem": mensagem,
                    "diferencas": diferencas,
                }
            )

            # Intervalo entre requisições
            if idx < len(empresas):
                time.sleep(intervalo_segundos)

        logger.info("\n" + "=" * 60)
        logger.info("RESUMO DA ATUALIZAÇÃO")
        logger.info("=" * 60)
        logger.info(f"Total: {stats['total']}")
        logger.info(f"✓ Atualizados: {stats['atualizados']}")
        logger.info(f"= Sem alteração: {stats['sem_alteracao']}")
        logger.info(f"⚠ Não cadastrados: {stats['nao_cadastrados']}")
        logger.info(f"✗ Erros: {stats['erros']}")
        logger.info("=" * 60)

        return stats


def main():
    df = pd.read_excel(PLANILHA_PATH, dtype=str)
    empresas = [linha_para_empresa(row) for _, row in df.iterrows()]

    api_client = JettaxAPI()  # Configure conforme necessário
    service = AtualizacaoService(api_client, dry_run=True)  # dry_run=True para teste

    resultado = service.atualizar_em_lote(empresas)
    print(resultado)


if __name__ == "__main__":
    main()
