import pandas as pd
from pathlib import Path
from .atualizacao_service import AtualizacaoService
from ..models.empresa import Empresa
from ..core.api_client import JettaxAPI

PLANILHA_PATH = r"G:\- CONTABILIDADE -\Automação\JETTAX\RELAÇÃO DE EMPRESAS.xlsx"

# Função para converter uma linha da planilha em um objeto Empresa
def linha_para_empresa(row):
    return Empresa(
        cnpj=row["CNPJ"],
        razao_social=row["Razão Social"],
        inscricao_estadual=row.get("Inscrição Estadual", ""),
        inscricao_municipal=row.get("Inscrição Municipal", ""),
        email=row.get("Email", ""),
        tributacao=row.get("Tributação", ""),
        # Adicione outros campos conforme necessário
    )

def main():
    # Ler a planilha
    df = pd.read_excel(PLANILHA_PATH, dtype=str)
    empresas = [linha_para_empresa(row) for _, row in df.iterrows()]

    # Inicializar API e serviço de atualização
    api_client = JettaxAPI()  # Configure conforme necessário
    service = AtualizacaoService(api_client, dry_run=True)  # dry_run=True para teste

    # Atualizar empresas
    resultado = service.atualizar_em_lote(empresas)
    print(resultado)

if __name__ == "__main__":
    main()
