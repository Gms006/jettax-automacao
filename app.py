"""Interface Streamlit para sincronização de clientes no Jettax 360."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import List

import requests
import streamlit as st
from dotenv import load_dotenv

from src.services.client_sync import (
    DEFAULT_SPREADSHEET,
    SyncEntry,
    authenticate,
    read_spreadsheet,
    save_report,
    sync_clients,
)

# Carrega variáveis de ambiente locais
load_dotenv(Path(".env"))
load_dotenv(Path("config/.env"))

st.set_page_config(page_title="Automação Jettax 360", layout="wide")
st.title("Automação de cadastro e atualização de clientes - Jettax 360")
st.write(
    "Envie a planilha de empresas, compare com o Jettax 360 e cadastre ou atualize"
    " somente os campos divergentes (nome, cidade, estado, regime e inscrição municipal)."
)


def render_logs(entries: List[SyncEntry]) -> str:
    lines = []
    for entry in entries:
        prefix = {
            "created": "🟢 Criado",
            "updated": "🟡 Atualizado",
            "skipped": "⚪ Ignorado",
            "error": "🔴 Erro",
        }.get(entry.action, "⚪")
        lines.append(f"{prefix} {entry.cnpj} - {entry.message}")
    return "\n".join(lines)


with st.sidebar:
    st.header("Configurações")
    default_path = st.text_input("Caminho da planilha", value=DEFAULT_SPREADSHEET)
    dry_run = st.checkbox("Modo dry-run (não envia para API)", value=True)
    st.caption(
        "O modo dry-run registra tudo que seria feito sem alterar os clientes ou"
        " certificados."
    )

uploaded_file = st.file_uploader("Planilha Excel (.xlsx)", type=["xlsx"])

log_placeholder = st.empty()
summary_placeholder = st.empty()
report_placeholder = st.empty()

if st.button("Executar", type="primary"):
    source = BytesIO(uploaded_file.read()) if uploaded_file else default_path

    try:
        df = read_spreadsheet(source)
    except Exception as exc:  # pragma: no cover - trata erro de entrada
        st.error(f"Não foi possível ler a planilha: {exc}")
        st.stop()

    # pré-visualização
    st.subheader("Pré-visualização da planilha normalizada")
    st.dataframe(df.head())

    progress_entries: List[SyncEntry] = []

    def on_progress(entry: SyncEntry) -> None:
        progress_entries.append(entry)
        log_placeholder.text(render_logs(progress_entries))

    with st.spinner("Executando sincronização..."):
        try:
            session, _ = authenticate(requests.Session())
            log = sync_clients(df, session, dry_run=dry_run, progress=on_progress)
        except Exception as exc:  # pragma: no cover - feedback ao usuário
            st.error(f"Erro durante a sincronização: {exc}")
            st.stop()

    st.success("Processo concluído.")

    summary_placeholder.subheader("Relatório de ações")
    summary_placeholder.dataframe(log.summary_dataframe())

    report_path = save_report(log)
    report_placeholder.download_button(
        label="Baixar relatório CSV",
        data=report_path.read_bytes(),
        file_name=report_path.name,
        mime="text/csv",
    )
else:
    st.info(
        "Envie a planilha ou indique o caminho padrão e clique em Executar para"
        " sincronizar os clientes."
    )
