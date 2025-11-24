"""
Sistema de Automação JETTAX 360
Cadastro e Atualização de Clientes

Autor: Automação Contábil
Data: 2025-11-21
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from src.core.api_client import JettaxAPI
from src.core.excel_reader import ExcelReader
from src.models.empresa import Empresa
from src.services.cadastro_service import CadastroService
from src.services.atualizacao_service import AtualizacaoService
from src.services.comparacao_service import ComparacaoService
from src.services.modulo_service import ModuloService
from src.utils.logger import get_logger, configurar_logger

logger = get_logger()


def configurar_argumentos():
    """Configura parser de argumentos CLI"""
    parser = argparse.ArgumentParser(
        description="Automação JETTAX 360 - Cadastro e Atualização de Clientes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Cadastrar novos clientes da planilha
  python main.py cadastro

  # Atualizar clientes existentes
  python main.py atualizacao

  # Executar cadastro + atualização (modo completo)
  python main.py sync

  # Modo dry-run (apenas simular, sem alterações)
  python main.py cadastro --dry-run

  # Modo debug (log detalhado)
  python main.py sync --debug

  # Especificar planilha customizada
  python main.py cadastro --planilha "C:\\path\\to\\empresas.xlsx"
        """
    )
    
    parser.add_argument(
        "modo",
        choices=["cadastro", "atualizacao", "sync", "comparar", "modulos"],
        help="Modo de operação: cadastro (criar novos), atualizacao (atualizar existentes), sync (cadastro+atualizacao+modulos), comparar (apenas listar diferenças), modulos (configurar módulos Federal e Serviços)"
    )
    
    parser.add_argument(
        "--planilha",
        type=str,
        default=r"G:\- CONTABILIDADE -\Automação\JETTAX\RELAÇÃO DE EMPRESAS.xlsx",
        help="Caminho da planilha Excel com as empresas"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo simulação (não faz alterações reais)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Modo debug (log detalhado)"
    )
    
    parser.add_argument(
        "--intervalo",
        type=float,
        default=1.0,
        help="Intervalo entre requisições em segundos (default: 1.0)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limitar processamento às primeiras N empresas"
    )
    
    return parser


def imprimir_banner():
    """Imprime banner do sistema"""
    print("\n" + "=" * 70)
    print("  SISTEMA DE AUTOMAÇÃO JETTAX 360")
    print("  Cadastro e Atualização de Clientes")
    print("=" * 70 + "\n")


def carregar_empresas(caminho_planilha: str, limit: int = None) -> List[Empresa]:
    """
    Carrega empresas da planilha
    
    Args:
        caminho_planilha: Caminho da planilha
        limit: Limitar número de empresas (para testes)
    
    Returns:
        Lista de empresas
    """
    logger.info(f"Carregando planilha: {caminho_planilha}")
    
    reader = ExcelReader(caminho_planilha)
    empresas = reader.converter_para_empresas()
    
    # Aplicar limite se especificado
    if limit and limit > 0:
        logger.warning(f"⚠ Limitando processamento às primeiras {limit} empresas")
        empresas = empresas[:limit]
    
    logger.info(f"✓ {len(empresas)} empresas carregadas\n")
    
    return empresas


def modo_cadastro(args):
    """Executa modo cadastro"""
    logger.info("MODO: CADASTRO DE NOVOS CLIENTES\n")
    
    # Carregar empresas
    empresas = carregar_empresas(args.planilha, args.limit)
    
    # Criar cliente API
    api = JettaxAPI()
    
    # Criar serviço de cadastro
    cadastro_service = CadastroService(api, dry_run=args.dry_run)
    
    # Executar cadastro em lote
    stats = cadastro_service.cadastrar_em_lote(
        empresas,
        intervalo_segundos=args.intervalo
    )
    
    # Salvar relatório
    salvar_relatorio_cadastro(stats)
    
    return stats


def modo_atualizacao(args):
    """Executa modo atualização"""
    logger.info("MODO: ATUALIZAÇÃO DE CLIENTES EXISTENTES\n")
    
    # Carregar empresas
    empresas = carregar_empresas(args.planilha, args.limit)
    
    # Criar cliente API
    api = JettaxAPI()
    
    # Criar serviço de atualização
    atualizacao_service = AtualizacaoService(api, dry_run=args.dry_run)
    
    # Executar atualização em lote
    stats = atualizacao_service.atualizar_em_lote(
        empresas,
        intervalo_segundos=args.intervalo
    )
    
    # Salvar relatório
    salvar_relatorio_atualizacao(stats)
    
    return stats


def modo_sync(args):
    """Executa modo sync (cadastro + atualização + módulos)"""
    logger.info("MODO: SYNC COMPLETO (CADASTRO + ATUALIZAÇÃO + MÓDULOS)\n")
    
    # Carregar empresas
    empresas = carregar_empresas(args.planilha, args.limit)
    
    # Criar cliente API
    api = JettaxAPI()
    
    # Criar serviços
    cadastro_service = CadastroService(api, dry_run=args.dry_run)
    atualizacao_service = AtualizacaoService(api, dry_run=args.dry_run)
    modulo_service = ModuloService(api, dry_run=args.dry_run)
    
    # 1. Cadastrar novos
    logger.info("\n" + "=" * 60)
    logger.info("FASE 1: CADASTRO DE NOVOS CLIENTES")
    logger.info("=" * 60 + "\n")
    
    stats_cadastro = cadastro_service.cadastrar_em_lote(
        empresas,
        intervalo_segundos=args.intervalo
    )
    
    # 2. Atualizar existentes
    logger.info("\n" + "=" * 60)
    logger.info("FASE 2: ATUALIZAÇÃO DE CLIENTES EXISTENTES")
    logger.info("=" * 60 + "\n")
    
    stats_atualizacao = atualizacao_service.atualizar_em_lote(
        empresas,
        intervalo_segundos=args.intervalo
    )
    
    # 3. Configurar módulos
    logger.info("\n" + "=" * 60)
    logger.info("FASE 3: CONFIGURAÇÃO DE MÓDULOS")
    logger.info("=" * 60 + "\n")
    
    # Carregar clientes do JETTAX
    clientes = api.listar_todos_clientes()
    
    # Criar lista de (empresa, cliente)
    from src.utils.cnpj_utils import somente_digitos
    jettax_por_cnpj = {}
    for cliente in clientes:
        cnpj = somente_digitos(str(cliente.get("document", "")))
        jettax_por_cnpj[cnpj] = cliente
    
    empresas_com_clientes = []
    for empresa in empresas:
        cnpj = somente_digitos(empresa.cnpj)
        if cnpj in jettax_por_cnpj:
            empresas_com_clientes.append((empresa, jettax_por_cnpj[cnpj]))
    
    stats_modulos = modulo_service.configurar_modulos_em_lote(empresas_com_clientes)
    
    # Relatório consolidado
    stats_consolidado = {
        "cadastro": stats_cadastro,
        "atualizacao": stats_atualizacao,
        "modulos": stats_modulos
    }
    
    salvar_relatorio_sync(stats_consolidado)
    
    return stats_consolidado


def modo_comparar(args):
    """Executa modo comparação (apenas lista diferenças)"""
    logger.info("MODO: COMPARAÇÃO (APENAS DIFERENÇAS)\n")
    
    # Carregar empresas
    empresas = carregar_empresas(args.planilha, args.limit)
    
    # Criar cliente API
    api = JettaxAPI()
    
    # Carregar clientes do JETTAX
    logger.info("Carregando clientes do JETTAX...")
    clientes = api.listar_todos_clientes()
    
    # Comparar
    comparador = ComparacaoService()
    divergentes = comparador.detectar_empresas_divergentes(empresas, clientes)
    
    # Imprimir resultado
    logger.info("\n" + "=" * 60)
    logger.info("EMPRESAS COM DIVERGÊNCIAS")
    logger.info("=" * 60 + "\n")
    
    for empresa, cliente, diferencas in divergentes:
        from src.utils.cnpj_utils import formatar_cnpj
        
        logger.info(f"{formatar_cnpj(empresa.cnpj)} - {empresa.razao_social}")
        for diff in diferencas:
            logger.info(f"  - {diff}")
        logger.info("")
    
    logger.info(f"Total de empresas com divergências: {len(divergentes)}")
    
    return {"divergentes": len(divergentes)}


def modo_modulos(args):
    """Executa modo configuração de módulos"""
    logger.info("MODO: CONFIGURAÇÃO DE MÓDULOS\n")
    
    # Carregar empresas
    empresas = carregar_empresas(args.planilha, args.limit)
    
    # Criar cliente API
    api = JettaxAPI()
    
    # Carregar clientes do JETTAX
    logger.info("Carregando clientes do JETTAX...")
    clientes = api.listar_todos_clientes()
    
    # Criar lista de (empresa, cliente)
    from src.utils.cnpj_utils import somente_digitos
    jettax_por_cnpj = {}
    for cliente in clientes:
        cnpj = somente_digitos(str(cliente.get("document", "")))
        jettax_por_cnpj[cnpj] = cliente
    
    empresas_com_clientes = []
    for empresa in empresas:
        cnpj = somente_digitos(empresa.cnpj)
        if cnpj in jettax_por_cnpj:
            empresas_com_clientes.append((empresa, jettax_por_cnpj[cnpj]))
    
    logger.info(f"✓ {len(empresas_com_clientes)} empresas encontradas no JETTAX\n")
    
    # Configurar módulos
    modulo_service = ModuloService(api, dry_run=args.dry_run)
    stats = modulo_service.configurar_modulos_em_lote(empresas_com_clientes)
    
    # Salvar relatório
    salvar_relatorio_modulos(stats)
    
    return stats


def salvar_relatorio_cadastro(stats: dict):
    """Salva relatório de cadastro"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = ROOT_DIR / "reports" / f"cadastro_{timestamp}.txt"
    
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE CADASTRO\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write(f"Total: {stats['total']}\n")
        f.write(f"✓ Cadastrados: {stats['sucesso']}\n")
        f.write(f"⚠ Já existiam: {stats['ja_cadastrados']}\n")
        f.write(f"✗ Erros: {stats['erros']}\n\n")
        f.write("=" * 60 + "\n")
        f.write("DETALHES\n")
        f.write("=" * 60 + "\n\n")
        
        for detalhe in stats['detalhes']:
            f.write(f"{detalhe['cnpj']} - {detalhe['razao_social']}\n")
            f.write(f"  Status: {'✓ OK' if detalhe['sucesso'] else '✗ ERRO'}\n")
            f.write(f"  Mensagem: {detalhe['mensagem']}\n\n")
    
    logger.info(f"\n✓ Relatório salvo em: {arquivo}")


def salvar_relatorio_atualizacao(stats: dict):
    """Salva relatório de atualização"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = ROOT_DIR / "reports" / f"atualizacao_{timestamp}.txt"
    
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE ATUALIZAÇÃO\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write(f"Total: {stats['total']}\n")
        f.write(f"✓ Atualizados: {stats['atualizados']}\n")
        f.write(f"= Sem alteração: {stats['sem_alteracao']}\n")
        f.write(f"⚠ Não cadastrados: {stats['nao_cadastrados']}\n")
        f.write(f"✗ Erros: {stats['erros']}\n\n")
        f.write("=" * 60 + "\n")
        f.write("DETALHES\n")
        f.write("=" * 60 + "\n\n")
        
        for detalhe in stats['detalhes']:
            f.write(f"{detalhe['cnpj']} - {detalhe['razao_social']}\n")
            f.write(f"  Status: {'✓ OK' if detalhe['sucesso'] else '✗ ERRO'}\n")
            f.write(f"  Mensagem: {detalhe['mensagem']}\n")
            
            if detalhe.get('diferencas'):
                f.write(f"  Diferenças:\n")
                for diff in detalhe['diferencas']:
                    f.write(f"    - {diff}\n")
            
            f.write("\n")
    
    logger.info(f"\n✓ Relatório salvo em: {arquivo}")


def salvar_relatorio_sync(stats: dict):
    """Salva relatório consolidado de sync"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = ROOT_DIR / "reports" / f"sync_{timestamp}.txt"
    
    stats_cadastro = stats['cadastro']
    stats_atualizacao = stats['atualizacao']
    stats_modulos = stats.get('modulos')
    
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE SYNC COMPLETO\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        
        f.write("FASE 1: CADASTRO\n")
        f.write("-" * 60 + "\n")
        f.write(f"Total: {stats_cadastro['total']}\n")
        f.write(f"✓ Cadastrados: {stats_cadastro['sucesso']}\n")
        f.write(f"⚠ Já existiam: {stats_cadastro['ja_cadastrados']}\n")
        f.write(f"✗ Erros: {stats_cadastro['erros']}\n\n")
        
        f.write("FASE 2: ATUALIZAÇÃO\n")
        f.write("-" * 60 + "\n")
        f.write(f"Total: {stats_atualizacao['total']}\n")
        f.write(f"✓ Atualizados: {stats_atualizacao['atualizados']}\n")
        f.write(f"= Sem alteração: {stats_atualizacao['sem_alteracao']}\n")
        f.write(f"⚠ Não cadastrados: {stats_atualizacao['nao_cadastrados']}\n")
        f.write(f"✗ Erros: {stats_atualizacao['erros']}\n\n")
        
        if stats_modulos:
            f.write("FASE 3: CONFIGURAÇÃO DE MÓDULOS\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total: {stats_modulos['total']}\n")
            f.write(f"Módulo Federal:\n")
            f.write(f"  ✓ Ativados: {stats_modulos['federal_ativado']}\n")
            f.write(f"  ⚠ Desativados: {stats_modulos['federal_desativado']}\n")
            f.write(f"Módulo Serviços:\n")
            f.write(f"  ✓ Ativados: {stats_modulos['servicos_ativado']}\n")
            f.write(f"  ⚠ Desativados: {stats_modulos['servicos_desativado']}\n")
            f.write(f"✗ Erros: {stats_modulos['erros']}\n\n")
        
        f.write("=" * 60 + "\n")
        f.write("RESUMO GERAL\n")
        f.write("=" * 60 + "\n")
        f.write(f"Empresas processadas: {stats_cadastro['total']}\n")
        f.write(f"Novos cadastros: {stats_cadastro['sucesso']}\n")
        f.write(f"Atualizações: {stats_atualizacao['atualizados']}\n")
        f.write(f"Sem alteração: {stats_atualizacao['sem_alteracao']}\n")
        
        if stats_modulos:
            f.write(f"Módulos Federal ativados: {stats_modulos['federal_ativado']}\n")
            f.write(f"Módulos Serviços ativados: {stats_modulos['servicos_ativado']}\n")
        
        total_erros = stats_cadastro['erros'] + stats_atualizacao['erros']
        if stats_modulos:
            total_erros += stats_modulos['erros']
        
        f.write(f"Erros: {total_erros}\n")
    
    logger.info(f"\n✓ Relatório salvo em: {arquivo}")


def salvar_relatorio_modulos(stats: dict):
    """Salva relatório de configuração de módulos"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = ROOT_DIR / "reports" / f"modulos_{timestamp}.txt"
    
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE CONFIGURAÇÃO DE MÓDULOS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write(f"Total: {stats['total']}\n")
        f.write(f"Módulo Federal:\n")
        f.write(f"  ✓ Ativados: {stats['federal_ativado']}\n")
        f.write(f"  ⚠ Desativados: {stats['federal_desativado']}\n")
        f.write(f"Módulo Serviços:\n")
        f.write(f"  ✓ Ativados: {stats['servicos_ativado']}\n")
        f.write(f"  ⚠ Desativados: {stats['servicos_desativado']}\n")
        f.write(f"✗ Erros: {stats['erros']}\n\n")
        f.write("=" * 60 + "\n")
        f.write("DETALHES\n")
        f.write("=" * 60 + "\n\n")
        
        for detalhe in stats['detalhes']:
            f.write(f"{detalhe['cnpj']} - {detalhe['razao_social']}\n")
            f.write(f"  Módulo Federal: {detalhe['federal']}\n")
            f.write(f"  Módulo Serviços: {detalhe['servicos']}\n")
            f.write(f"  Status: {'✓ OK' if detalhe['sucesso'] else '✗ ERRO'}\n\n")
    
    logger.info(f"\n✓ Relatório salvo em: {arquivo}")


def main():
    """Função principal"""
    try:
        # Configurar argumentos
        parser = configurar_argumentos()
        args = parser.parse_args()
        
        # Configurar logger
        configurar_logger(debug=args.debug)
        
        # Imprimir banner
        imprimir_banner()
        
        # Log do modo
        if args.dry_run:
            logger.warning("⚠ MODO DRY-RUN: Nenhuma alteração será feita\n")
        
        # Executar modo selecionado
        if args.modo == "cadastro":
            modo_cadastro(args)
        elif args.modo == "atualizacao":
            modo_atualizacao(args)
        elif args.modo == "sync":
            modo_sync(args)
        elif args.modo == "comparar":
            modo_comparar(args)
        elif args.modo == "modulos":
            modo_modulos(args)
        
        logger.info("\n✓ Processamento concluído com sucesso!\n")
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠ Processamento interrompido pelo usuário")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"\n✗ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
