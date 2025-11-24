"""Painel Streamlit para automação JETTAX 360.

Interface de teste para disparar comandos do main.py, visualizar logs,
relatórios, payloads e pré-visualizar a planilha de empresas.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PLANILHA = BASE_DIR / "RELAÇÃO DE EMPRESAS.xlsx"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
DEBUG_DIR = BASE_DIR / "debug_payloads"


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def list_files_safe(path: Path, patterns: Iterable[str] = ("*.log", "*.txt", "*.json")) -> List[Path]:
    """Lista arquivos que batem com os padrões, ordenando pelo mtime desc."""
    if not path.exists():
        return []

    files: list[Path] = []
    for pattern in patterns:
        files.extend(path.glob(pattern))

    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def show_file_content(file_path: Path, is_json: bool = False) -> None:
    """Exibe conteúdo do arquivo como texto ou JSON."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:  # pragma: no cover - fallback de leitura
        st.error(f"Erro ao ler arquivo: {exc}")
        return

    if is_json:
        try:
            data = json.loads(text)
            st.json(data)
            return
        except json.JSONDecodeError:
            st.warning("Não foi possível interpretar o JSON, exibindo texto bruto.")

    st.code(text, language="json" if is_json else "text")


def run_command_stream(command: List[str], workdir: Path) -> str:
    """Executa comando mostrando saída em tempo quase real."""
    placeholder = st.empty()
    output_lines: list[str] = []

    process = subprocess.Popen(
        command,
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None  # para type checkers
    for line in process.stdout:
        output_lines.append(line)
        placeholder.code("".join(output_lines))

    process.wait()
    full_output = "".join(output_lines)

    status = "sucesso" if process.returncode == 0 else f"erro (code {process.returncode})"
    st.success(f"Execução finalizada com {status}.") if process.returncode == 0 else st.error(
        f"Execução finalizada com {status}."
    )

    return full_output


def load_planilha(planilha_path: Path) -> pd.DataFrame:
    """Carrega a planilha principal caso exista."""
    if not planilha_path.exists():
        raise FileNotFoundError(f"Planilha não encontrada: {planilha_path}")

    return pd.read_excel(planilha_path, sheet_name="RELAÇÃO DE EMPRESAS")


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def sidebar_controls() -> dict:
    st.sidebar.header("Configurações")
    planilha_input = st.sidebar.text_input(
        "Caminho da planilha",
        value=str(DEFAULT_PLANILHA),
        help="Usada tanto para visualização quanto para execução.",
    )

    modo = st.sidebar.selectbox("Modo de execução", ["cadastro", "atualizacao", "sync", "comparar"])

    dry_run = st.sidebar.checkbox("--dry-run", value=False)
    debug = st.sidebar.checkbox("--debug", value=False)

    limit = st.sidebar.number_input("--limit (opcional)", min_value=0, step=1, value=0, help="0 = não limitar")
    intervalo = st.sidebar.number_input(
        "--intervalo (segundos)", min_value=0.0, step=0.5, value=0.0, help="0 = não enviar parâmetro"
    )

    return {
        "planilha": planilha_input.strip(),
        "modo": modo,
        "dry_run": dry_run,
        "debug": debug,
        "limit": int(limit) if limit else None,
        "intervalo": float(intervalo) if intervalo else None,
    }


def build_command(config: dict) -> List[str]:
    cmd: List[str] = ["python", "main.py", config["modo"], "--planilha", config["planilha"]]

    if config.get("dry_run"):
        cmd.append("--dry-run")
    if config.get("debug"):
        cmd.append("--debug")
    if config.get("limit"):
        cmd.extend(["--limit", str(config["limit"])])
    if config.get("intervalo"):
        cmd.extend(["--intervalo", str(config["intervalo"])])

    return cmd


def render_planilha_tab(planilha_path: Path) -> None:
    st.subheader("Planilha de Empresas")
    try:
        df = load_planilha(planilha_path)
    except Exception as exc:
        st.error(f"Não foi possível carregar a planilha: {exc}")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_cnpj = st.text_input("Filtrar CNPJ")
    with col2:
        filtro_razao = st.text_input("Filtrar Razão Social")
    with col3:
        municipios = sorted(df.get("Municipio", pd.Series(dtype=str)).dropna().unique().tolist())
        municipio_sel = st.selectbox("Municipio", ["(Todos)"] + municipios)

    filtered = df.copy()
    if filtro_cnpj:
        filtered = filtered[filtered["CNPJ"].astype(str).str.contains(filtro_cnpj, case=False, na=False)]
    if filtro_razao:
        filtered = filtered[filtered["Razao Social"].astype(str).str.contains(filtro_razao, case=False, na=False)]
    if municipio_sel and municipio_sel != "(Todos)":
        filtered = filtered[filtered["Municipio"].astype(str) == municipio_sel]

    st.markdown(f"Empresas filtradas: **{len(filtered)}** de **{len(df)}**")
    st.dataframe(filtered.head(500))


def render_execucao_tab(command: List[str]) -> None:
    st.subheader("Execução")
    st.code(" ".join(command), language="bash")

    if st.button("🚀 Executar automação", type="primary"):
        with st.spinner("Executando automação..."):
            output = run_command_stream(command, BASE_DIR)
            st.text_area("Saída completa", value=output, height=300)
    else:
        st.info("Configure os parâmetros na sidebar e clique em Executar.")


def render_logs_tab(path: Path, title: str, patterns: Iterable[str]) -> None:
    st.subheader(title)
    files = list_files_safe(path, patterns=patterns)
    if not files:
        st.info("Nenhum arquivo encontrado.")
        return

    selected = st.selectbox("Selecione um arquivo", files, format_func=lambda p: p.name)
    if selected:
        show_file_content(selected, is_json=False)


def summarize_payload(data: dict) -> str:
    cnpj = data.get("cnpj") or data.get("empresa", {}).get("cnpj")
    status = data.get("status") or data.get("resultado")
    endpoint = data.get("endpoint") or data.get("url") or data.get("operacao")

    parts = []
    if cnpj:
        parts.append(f"**CNPJ:** {cnpj}")
    if status:
        parts.append(f"**Status:** {status}")
    if endpoint:
        parts.append(f"**Endpoint/Op.:** {endpoint}")

    return "\n".join(parts) if parts else "Sem metadados detectados."


def render_debug_tab(path: Path) -> None:
    st.subheader("Debug Payloads")
    files = list_files_safe(path, patterns=("*.json",))
    if not files:
        st.info("Nenhum payload encontrado.")
        return

    selected = st.selectbox("Selecione um payload", files, format_func=lambda p: p.name)
    if not selected:
        return

    try:
        content = selected.read_text(encoding="utf-8", errors="replace")
        data = json.loads(content)
    except Exception:
        data = None

    col_meta, col_json = st.columns([1, 2])
    with col_meta:
        if data is not None:
            st.markdown(summarize_payload(data))
        else:
            st.warning("Não foi possível interpretar o JSON.")
    with col_json:
        if data is not None:
            st.json(data)
        else:
            show_file_content(selected, is_json=False)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="JETTAX Automação", layout="wide")
    st.title("Painel de Testes - JETTAX Automação")
    st.caption("Dispare automações e acompanhe logs/relatórios gerados pelo main.py")

    config = sidebar_controls()
    planilha_path = Path(config["planilha"]) if config["planilha"] else DEFAULT_PLANILHA
    config["planilha"] = str(planilha_path)
    command = build_command(config)

    tabs = st.tabs(["Execução", "Logs", "Relatórios", "Debug Payloads", "Planilha de Empresas"])

    with tabs[0]:
        render_execucao_tab(command)

    with tabs[1]:
        render_logs_tab(LOGS_DIR, "Logs", patterns=("*.log", "*.txt"))

    with tabs[2]:
        render_logs_tab(REPORTS_DIR, "Relatórios", patterns=("*.txt", "*.log"))

    with tabs[3]:
        render_debug_tab(DEBUG_DIR)

    with tabs[4]:
        render_planilha_tab(planilha_path)


if __name__ == "__main__":
    main()
