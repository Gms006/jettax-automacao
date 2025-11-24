"""Aplicação Streamlit para comparar, cadastrar e atualizar clientes no JETTAX 360."""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.core.api_client import JettaxAPI
from src.core.excel_reader import ExcelReader, ExcelReaderError
from src.models.empresa import Empresa
from src.services.atualizacao_service import AtualizacaoService
from src.services.cadastro_service import CadastroService
from src.services.comparacao_service import ComparacaoService
from src.utils.cnpj_utils import formatar_cnpj
from src.utils.logger import configurar_logger, get_logger

# Carregar variáveis de ambiente
load_dotenv(Path("config/.env"))
load_dotenv(Path(".env"))

# Configurar logger base
configurar_logger()
logger = get_logger()

st.set_page_config(page_title="Automação JETTAX 360", layout="wide")
st.title("Automação JETTAX 360 - Cadastro e Atualização")


class StreamlitLogHandler(logging.Handler):
    """Handler de log que escreve em um placeholder do Streamlit."""

    def __init__(self, placeholder: st.delta_generator.DeltaGenerator):
        super().__init__()
        self.placeholder = placeholder

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - integração com streamlit
        msg = self.format(record)
        logs = st.session_state.setdefault("log_lines", [])
        logs.append(msg)
        self.placeholder.text("\n".join(logs[-200:]))


def get_default_planilha_path() -> str:
    """Obtém o caminho padrão da planilha a partir do .env ou usa o arquivo local."""

    return os.getenv(
        "PLANILHA_PATH", os.getenv("PLANILHA_EMPRESAS", "RELAÇÃO DE EMPRESAS.xlsx")
    )


def preparar_planilha(uploaded_file, default_path: str) -> Path:
    """Garante que a planilha esteja salva em disco para leitura pelo ExcelReader."""

    if uploaded_file:
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as temp:
            temp.write(uploaded_file.getbuffer())
            return Path(temp.name)

    return Path(default_path)


def carregar_empresas(planilha_path: Path) -> Tuple[pd.DataFrame, List[Empresa]]:
    """Lê a planilha e retorna dataframe e lista de empresas normalizadas."""

    reader = ExcelReader(str(planilha_path))
    df = reader.carregar()
    empresas = reader.converter_para_empresas()
    return df, empresas


def limitar_empresas(empresas: List[Empresa], limite: int) -> List[Empresa]:
    if limite and limite > 0:
        return empresas[:limite]
    return empresas


def gerar_relatorio_texto(
    operacao: str, stats: Dict[str, Any], log_lines: List[str], detalhes: List[Dict[str, Any]] | None = None
) -> Path:
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"{operacao}_report_{timestamp}.txt"

    with open(report_path, "w", encoding="utf-8") as fp:
        fp.write(f"Operação: {operacao}\n")
        fp.write(f"Data/Hora: {timestamp}\n\n")
        fp.write("Resumo:\n")
        for chave, valor in stats.items():
            if chave == "detalhes":
                continue
            fp.write(f"- {chave}: {valor}\n")

        if detalhes:
            fp.write("\nDetalhes:\n")
            for item in detalhes:
                fp.write(f"CNPJ: {item.get('cnpj')} - {item.get('razao_social', '')}\n")
                fp.write(f"  Sucesso: {item.get('sucesso')}\n")
                if item.get("mensagem"):
                    fp.write(f"  Mensagem: {item.get('mensagem')}\n")
                if item.get("diferencas"):
                    fp.write("  Diferenças:\n")
                    for diff in item.get("diferencas", []):
                        fp.write(f"    - {diff}\n")
                fp.write("\n")

        if log_lines:
            fp.write("Logs:\n")
            fp.write("\n".join(log_lines))

    return report_path


def anexar_logger_streamlit(placeholder: st.delta_generator.DeltaGenerator) -> StreamlitLogHandler:
    handler = StreamlitLogHandler(placeholder)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return handler


def executar_operacao(
    operacao: str,
    empresas: List[Empresa],
    api_client: JettaxAPI,
    intervalo: float,
    dry_run: bool,
    log_placeholder: st.delta_generator.DeltaGenerator,
):
    detalhes: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {}
    st.session_state["log_lines"] = []
    handler = anexar_logger_streamlit(log_placeholder)

    try:
        if operacao == "comparar":
            comparador = ComparacaoService()
            clientes = api_client.listar_todos_clientes()
            divergentes = comparador.detectar_empresas_divergentes(empresas, clientes)

            st.success(f"Comparação concluída: {len(divergentes)} divergências encontradas.")

            dados = [
                {
                    "CNPJ": formatar_cnpj(empresa.cnpj),
                    "Razão Social": empresa.razao_social,
                    "Diferenças": "\n".join(diferencas),
                }
                for empresa, _, diferencas in divergentes
            ]

            if dados:
                st.dataframe(pd.DataFrame(dados))

            stats = {
                "total_processado": len(empresas),
                "divergentes": len(dados),
                "sem_diferencas": len(empresas) - len(dados),
            }
            detalhes = [
                {
                    "cnpj": item[0].cnpj,
                    "razao_social": item[0].razao_social,
                    "sucesso": True,
                    "mensagem": "Divergências identificadas",
                    "diferencas": item[2],
                }
                for item in divergentes
            ]
        elif operacao == "cadastrar":
            cadastro = CadastroService(api_client, dry_run=dry_run)
            stats = cadastro.cadastrar_em_lote(empresas, intervalo_segundos=intervalo)
            detalhes = stats.get("detalhes", [])

            st.success(
                f"Cadastro finalizado. Sucesso: {stats['sucesso']}, "
                f"já existentes: {stats['ja_cadastrados']}, erros: {stats['erros']}"
            )

            if detalhes:
                st.dataframe(pd.DataFrame(detalhes))
        elif operacao == "atualizar":
            atualizacao = AtualizacaoService(api_client, dry_run=dry_run)
            stats = atualizacao.atualizar_em_lote(empresas, intervalo_segundos=intervalo)
            detalhes = stats.get("detalhes", [])

            st.success(
                f"Atualização finalizada. Atualizados: {stats['atualizados']}, "
                f"sem alteração: {stats['sem_alteracao']}, não cadastrados: {stats['nao_cadastrados']}, "
                f"erros: {stats['erros']}"
            )

            if detalhes:
                st.dataframe(pd.DataFrame(detalhes))
        else:  # pragma: no cover - guarda para futuras operações
            st.error("Operação não suportada")
            return

        log_lines = list(st.session_state.get("log_lines", []))
        relatorio = gerar_relatorio_texto(operacao, stats, log_lines, detalhes)
        with open(relatorio, "rb") as fp:
            st.download_button(
                label=f"Baixar relatório ({operacao})", data=fp.read(), file_name=relatorio.name, mime="text/plain"
            )

    except Exception as exc:  # pragma: no cover - feedback ao usuário final
        logger.exception("Erro durante a execução da operação")
        st.error(f"Erro durante a operação de {operacao}: {exc}")
        return
    finally:
        logger.removeHandler(handler)


# Sidebar
with st.sidebar:
    st.header("Configurações")
    caminho_padrao = st.text_input("Caminho da planilha", value=get_default_planilha_path())
    dry_run = st.checkbox("Dry-run (não envia para API)", value=True)
    intervalo = st.number_input(
        "Intervalo entre requisições (segundos)", min_value=0.0, max_value=30.0, value=1.0, step=0.5
    )
    limite_empresas = st.number_input("Limitar número de empresas", min_value=0, value=0, step=1)

st.caption(
    "Faça upload de uma planilha XLSX ou informe o caminho configurado. As operações respeitam o modo "
    "dry-run e não alteram certificados digitais."
)

uploaded_file = st.file_uploader("Planilha de empresas (.xlsx)", type=["xlsx"])

log_placeholder = st.empty()

col1, col2, col3 = st.columns(3)

if "empresas_cache" not in st.session_state:
    st.session_state.empresas_cache = None
    st.session_state.planilha_usada = None


def obter_empresas_para_execucao() -> Tuple[pd.DataFrame, List[Empresa], Path]:
    planilha_path = preparar_planilha(uploaded_file, caminho_padrao)
    st.session_state.planilha_usada = planilha_path

    df, empresas = carregar_empresas(planilha_path)
    empresas = limitar_empresas(empresas, int(limite_empresas))
    return df, empresas, planilha_path


with st.spinner("Carregando planilha..."):
    try:
        dataframe, empresas_lidas, planilha_path = obter_empresas_para_execucao()
        st.session_state.empresas_cache = (dataframe, empresas_lidas)
        st.write(f"Planilha carregada: {planilha_path}")
        st.dataframe(dataframe.head())
    except ExcelReaderError as exc:
        st.error(f"Erro ao ler a planilha: {exc}")
    except FileNotFoundError:
        st.warning("Informe um caminho válido para a planilha ou faça upload do arquivo.")


api_client = JettaxAPI()

if col1.button("Comparar"):
    if not st.session_state.empresas_cache:
        st.error("Nenhuma planilha carregada.")
    else:
        executar_operacao(
            "comparar",
            st.session_state.empresas_cache[1],
            api_client,
            intervalo,
            dry_run,
            log_placeholder,
        )

if col2.button("Cadastrar novos clientes"):
    if not st.session_state.empresas_cache:
        st.error("Nenhuma planilha carregada.")
    else:
        executar_operacao(
            "cadastrar",
            st.session_state.empresas_cache[1],
            api_client,
            intervalo,
            dry_run,
            log_placeholder,
        )

if col3.button("Atualizar clientes existentes"):
    if not st.session_state.empresas_cache:
        st.error("Nenhuma planilha carregada.")
    else:
        executar_operacao(
            "atualizar",
            st.session_state.empresas_cache[1],
            api_client,
            intervalo,
            dry_run,
            log_placeholder,
        )
