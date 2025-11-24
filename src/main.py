import sys
import pandas as pd
from services.atualizacao_service import AtualizacaoService
from models.empresa import Empresa
from core.api_client import JettaxAPI

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
        cadastro_jettax=row.get("Cadastro JETTAX", "")
    )

def automacao_atualizacao():
    print("Iniciando automação de atualização cadastral...")
    df = pd.read_excel(PLANILHA_PATH, dtype=str)
    empresas = [linha_para_empresa(row) for _, row in df.iterrows()]
    api_client = JettaxAPI()  # Configure conforme necessário
    service = AtualizacaoService(api_client, dry_run=True)  # dry_run=True para teste
    resultado = service.atualizar_em_lote(empresas)
    print("Resumo da atualização:")
    print(resultado)

def main():
    print("Escolha o tipo de automação:")
    print("1 - Atualização de dados cadastrais")
    print("2 - Outro tipo de automação (em breve)")
    escolha = input("Digite o número da opção desejada: ")
    if escolha == "1":
        automacao_atualizacao()
    else:
        print("Opção não implementada ou inválida.")

if __name__ == "__main__":
    main()
