"""Serviços para sincronizar clientes com a API Jettax 360.

O módulo cobre:
- Autenticação na API via credenciais do .env
- Leitura/normalização da planilha de empresas
- Comparação com clientes já cadastrados
- Criação/atualização conforme diferenças detectadas
- Registro detalhado das ações, com suporte a modo dry-run
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import requests
from dotenv import load_dotenv

from src.utils.cnpj_utils import normalizar_cnpj, somente_digitos
from src.utils.logger import get_logger

logger = get_logger()

# Carrega variáveis de ambiente tanto do diretório raiz quanto de config/
load_dotenv(Path(".env"))
load_dotenv(Path("config/.env"))

API_URL = os.getenv("JETTAX_API_URL", "https://api.jettax360.com.br").rstrip("/")
AUTH_URL = os.getenv("JETTAX_AUTH_URL", "https://api-auth.jettax360.com.br").rstrip("/")
EMAIL = os.getenv("JETTAX_EMAIL")
PASSWORD = os.getenv("JETTAX_PASSWORD")
DEFAULT_SPREADSHEET = os.getenv("JETTAX_SPREADSHEET", "RELAÇÃO DE EMPRESAS.xlsx")


@dataclass
class SyncEntry:
    """Representa uma ação realizada durante a sincronização."""

    cnpj: str
    action: str
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "ok"


@dataclass
class SyncLog:
    """Registra todas as ações executadas."""

    created: List[SyncEntry] = field(default_factory=list)
    updated: List[SyncEntry] = field(default_factory=list)
    skipped: List[SyncEntry] = field(default_factory=list)
    errors: List[SyncEntry] = field(default_factory=list)

    def add(self, entry: SyncEntry) -> None:
        bucket = {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "error": self.errors,
        }.get(entry.action, self.skipped)
        bucket.append(entry)

    @property
    def all_entries(self) -> List[SyncEntry]:
        return self.created + self.updated + self.skipped + self.errors

    def summary_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "CNPJ": e.cnpj,
                    "Ação": e.action,
                    "Mensagem": e.message,
                    "Status": e.status,
                    "Payload": e.payload,
                }
                for e in self.all_entries
            ]
        )


def authenticate(session: Optional[requests.Session] = None) -> Tuple[requests.Session, str]:
    """Autentica na API Jettax e devolve sessão com token Bearer."""

    if not EMAIL or not PASSWORD:
        raise RuntimeError("Defina JETTAX_EMAIL e JETTAX_PASSWORD no .env")

    session = session or requests.Session()
    payload = {"email": EMAIL, "password": PASSWORD, "isCheckMFA": False}
    url = f"{AUTH_URL}/api/jettax360/v1/auth/office/login"

    logger.info("Autenticando no Jettax 360...")
    resp = session.post(url, json=payload, timeout=30)
    resp.raise_for_status()

    token = resp.headers.get("Authorization")
    if token and token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1].strip()
    else:
        token = resp.json().get("access_token")

    if not token:
        raise RuntimeError("Token de autenticação não encontrado na resposta")

    session.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json"})
    logger.info("Autenticação concluída com sucesso.")
    return session, token


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza colunas e valores da planilha."""

    rename_map = {
        "cnpj": "cnpj",
        "cnp": "cnpj",
        "document": "cnpj",
        "razão social": "name",
        "razao social": "name",
        "empresa": "name",
        "nome": "name",
        "cidade": "city",
        "municipio": "city",
        "município": "city",
        "estado": "state",
        "uf": "state",
        "regime": "regime",
        "tributação": "regime",
        "taxation": "regime",
        "inscrição municipal": "municipalRegistration",
        "inscricao municipal": "municipalRegistration",
        "im": "municipalRegistration",
    }

    normalized_columns = {}
    for col in df.columns:
        key = str(col).strip().lower()
        normalized_columns[col] = rename_map.get(key, key)
    df = df.rename(columns=normalized_columns)

    required = ["cnpj", "name", "city", "state", "regime", "municipalRegistration"]
    for col in required:
        if col not in df.columns:
            df[col] = ""

    df["cnpj"] = df["cnpj"].apply(normalizar_cnpj)
    df["name"] = df["name"].apply(_normalize_text)
    df["city"] = df["city"].apply(_normalize_text)
    df["state"] = df["state"].apply(_normalize_text)
    df["regime"] = df["regime"].apply(_normalize_text)
    df["municipalRegistration"] = df["municipalRegistration"].apply(lambda v: somente_digitos(str(v)))

    df = df[df["cnpj"] != ""]
    df = df.drop_duplicates(subset=["cnpj"], keep="first")
    return df


def read_spreadsheet(source: Union[str, Path, bytes]) -> pd.DataFrame:
    """Lê a planilha (caminho ou bytes) e devolve DataFrame normalizado."""

    if isinstance(source, (str, Path)):
        df = pd.read_excel(source)
    else:
        df = pd.read_excel(source)

    return normalize_dataframe(df)


def fetch_existing_clients(session: requests.Session) -> Dict[str, Dict[str, Any]]:
    """Obtém clientes existentes e indexa por CNPJ normalizado."""

    url = f"{API_URL}/api/v1/clients/all"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, dict):
        clients = data.get("data", data.get("clients", []))
    else:
        clients = data

    indexed: Dict[str, Dict[str, Any]] = {}
    for item in clients or []:
        cnpj = normalizar_cnpj(item.get("document") or item.get("cnpj"))
        if cnpj:
            indexed[cnpj] = item
    return indexed


def _build_create_payload(row: pd.Series) -> Dict[str, Any]:
    return {
        "document": row.get("cnpj"),
        "name": row.get("name"),
        "city": row.get("city"),
        "state": row.get("state"),
        "taxation": row.get("regime"),
        "municipalRegistration": row.get("municipalRegistration", ""),
        "isActive": True,
    }


def _diff_fields(row: pd.Series, existing: Dict[str, Any]) -> Dict[str, Any]:
    fields = {
        "name": row.get("name"),
        "city": row.get("city"),
        "state": row.get("state"),
        "taxation": row.get("regime"),
        "municipalRegistration": row.get("municipalRegistration", ""),
    }

    changes = {}
    for key, value in fields.items():
        existing_value = existing.get(key) or existing.get(key[0].upper() + key[1:])
        if key == "municipalRegistration":
            if somente_digitos(existing_value) != somente_digitos(value):
                changes[key] = value
            continue

        if _normalize_text(existing_value) != _normalize_text(value):
            changes[key] = value
    return changes


def sync_clients(
    df: pd.DataFrame,
    session: requests.Session,
    *,
    dry_run: bool = False,
    progress: Optional[callable] = None,
) -> SyncLog:
    """Compara dados da planilha com a API e cria/atualiza conforme necessário."""

    log = SyncLog()
    existing_clients = fetch_existing_clients(session)

    for _, row in df.iterrows():
        cnpj = row.get("cnpj")
        if not cnpj:
            entry = SyncEntry("", "skipped", "Linha sem CNPJ", status="ignored")
            log.add(entry)
            if progress:
                progress(entry)
            continue

        existing = existing_clients.get(cnpj)
        if not existing:
            payload = _build_create_payload(row)
            message = "[DRY-RUN] Criaria cliente" if dry_run else "Cliente criado"
            entry = SyncEntry(cnpj, "created", message, payload=payload)
            if not dry_run:
                try:
                    resp = session.post(f"{API_URL}/api/v1/clients", json=payload, timeout=30)
                    resp.raise_for_status()
                    entry.message = "Cliente criado com sucesso"
                except requests.HTTPError as exc:
                    entry = SyncEntry(cnpj, "error", f"Erro ao criar: {exc}", status="error", payload=payload)
                    log.add(entry)
                    if progress:
                        progress(entry)
                    continue
            log.add(entry)
            if progress:
                progress(entry)
            continue

        changes = _diff_fields(row, existing)
        if not changes:
            entry = SyncEntry(cnpj, "skipped", "Sem alterações necessárias", status="ok")
            log.add(entry)
            if progress:
                progress(entry)
            continue

        message = "[DRY-RUN] Atualizaria cliente" if dry_run else "Cliente atualizado"
        entry = SyncEntry(cnpj, "updated", message, payload=changes)

        if not dry_run:
            try:
                client_id = existing.get("id") or existing.get("_id")
                resp = session.put(f"{API_URL}/api/v1/clients/{client_id}", json=changes, timeout=30)
                resp.raise_for_status()
                entry.message = "Cliente atualizado com sucesso"
            except requests.HTTPError as exc:
                entry = SyncEntry(cnpj, "error", f"Erro ao atualizar: {exc}", status="error", payload=changes)
                log.add(entry)
                if progress:
                    progress(entry)
                continue

        log.add(entry)
        if progress:
            progress(entry)

    return log


def run_sync_from_source(
    source: Union[str, Path, bytes],
    *,
    dry_run: bool = False,
    session: Optional[requests.Session] = None,
    progress: Optional[callable] = None,
) -> SyncLog:
    """Fluxo completo: autentica, lê planilha e executa sincronização."""

    session, _ = authenticate(session)
    df = read_spreadsheet(source)
    return sync_clients(df, session, dry_run=dry_run, progress=progress)


def save_report(log: SyncLog, reports_dir: Union[str, Path] = "reports") -> Path:
    """Salva relatório CSV com timestamp."""

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_path / f"sync_report_{timestamp}.csv"
    log.summary_dataframe().to_csv(report_path, index=False, encoding="utf-8")
    return report_path


__all__ = [
    "authenticate",
    "fetch_existing_clients",
    "normalize_dataframe",
    "read_spreadsheet",
    "run_sync_from_source",
    "save_report",
    "sync_clients",
    "SyncEntry",
    "SyncLog",
    "DEFAULT_SPREADSHEET",
]
