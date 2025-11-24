"""
Leitor da planilha RELAÇÃO DE EMPRESAS.xlsx
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..models.empresa import Empresa
from ..utils.logger import get_logger
from ..utils.cnpj_utils import normalizar_cnpj, normalizar_cpf
from ..utils.date_utils import parse_date

logger = get_logger()


class ExcelReaderError(Exception):
    """Erro ao ler planilha Excel"""
    pass


class ExcelReader:
    """Leitor da planilha de empresas"""
    
    def __init__(self, file_path: str):
        """
        Inicializa leitor
        
        Args:
            file_path: Caminho completo da planilha
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            raise ExcelReaderError(f"Planilha não encontrada: {file_path}")
        
        self._df: Optional[pd.DataFrame] = None
    
    def carregar(self) -> pd.DataFrame:
        """
        Carrega planilha em memória
        
        Returns:
            DataFrame com os dados
        """
        logger.info(f"Carregando planilha: {self.file_path.name}")
        
        try:
            # Ler Excel
            df = pd.read_excel(self.file_path, header=0)
            
            # A primeira linha contém os nomes das colunas
            df.columns = df.iloc[0]
            df = df[1:]  # Remover linha de cabeçalho duplicada
            df.reset_index(drop=True, inplace=True)
            
            self._df = df
            
            logger.info(f"✓ Planilha carregada: {len(df)} empresas")
            return df
            
        except Exception as e:
            raise ExcelReaderError(f"Erro ao ler planilha: {e}")
    
    def validar_estrutura(self) -> bool:
        """
        Valida se a planilha tem a estrutura esperada
        
        Returns:
            True se válida
        """
        if self._df is None:
            self.carregar()
        
        colunas_esperadas = [
            "CNPJ",
            "Razao Social",
            "Tributacao",
            "IE",
            "IM",
            "NIRE",
            "Ramo atividade",
            "Responsável",
            "e-mail",
            "Municipio",
            "Data de Cadastro",
            "CPF",
            "Senha",
            "Cadastro JETTAX"
        ]
        
        colunas_faltantes = set(colunas_esperadas) - set(self._df.columns)
        
        if colunas_faltantes:
            logger.error(f"Colunas faltantes na planilha: {', '.join(colunas_faltantes)}")
            return False
        
        logger.debug("✓ Estrutura da planilha validada")
        return True
    
    def converter_para_empresas(self) -> List[Empresa]:
        """
        Converte DataFrame em lista de objetos Empresa
        
        Returns:
            Lista de empresas
        """
        if self._df is None:
            self.carregar()
        
        if not self.validar_estrutura():
            raise ExcelReaderError("Estrutura da planilha inválida")
        
        logger.info("Convertendo dados para objetos Empresa...")
        
        empresas = []
        erros = 0
        
        for idx, row in self._df.iterrows():
            try:
                # Extrair dados da linha
                cnpj = normalizar_cnpj(row.get("CNPJ"))
                razao_social = str(row.get("Razao Social", "")).strip()
                tributacao = str(row.get("Tributacao", "")).strip()
                municipio = str(row.get("Municipio", "")).strip()
                
                # Validar campos obrigatórios
                if not cnpj or not razao_social or not tributacao or not municipio:
                    logger.warning(
                        f"Linha {idx + 2}: Campos obrigatórios faltando "
                        f"(CNPJ={cnpj}, Razão={razao_social[:20]})"
                    )
                    erros += 1
                    continue
                
                # Campos opcionais
                ie = row.get("IE")
                if pd.notna(ie):
                    ie = str(ie).strip()
                else:
                    ie = None
                
                im = row.get("IM")
                if pd.notna(im):
                    im = str(im).strip()
                else:
                    im = None
                
                nire = row.get("NIRE")
                if pd.notna(nire):
                    nire = str(nire).strip()
                else:
                    nire = None
                
                ramo_atividade = row.get("Ramo atividade")
                if pd.notna(ramo_atividade):
                    ramo_atividade = str(ramo_atividade).strip()
                else:
                    ramo_atividade = None
                
                responsavel = row.get("Responsável")
                if pd.notna(responsavel):
                    responsavel = str(responsavel).strip()
                else:
                    responsavel = None
                
                email = row.get("e-mail")
                if pd.notna(email):
                    email = str(email).strip()
                else:
                    email = None
                
                # Datas
                data_cadastro = parse_date(row.get("Data de Cadastro"))
                cadastro_jettax = parse_date(row.get("Cadastro JETTAX"))
                
                # Credenciais prefeitura
                cpf = row.get("CPF")
                if pd.notna(cpf):
                    cpf = normalizar_cpf(cpf)
                else:
                    cpf = None
                
                senha = row.get("Senha")
                if pd.notna(senha):
                    senha = str(senha).strip()
                else:
                    senha = None
                
                # Criar objeto Empresa
                empresa = Empresa(
                    cnpj=cnpj,
                    razao_social=razao_social,
                    tributacao=tributacao,
                    municipio=municipio,
                    ie=ie,
                    im=im,
                    nire=nire,
                    ramo_atividade=ramo_atividade,
                    responsavel=responsavel,
                    email=email,
                    data_cadastro=data_cadastro,
                    cpf_prefeitura=cpf,
                    senha_prefeitura=senha,
                    cadastro_jettax=cadastro_jettax
                )
                
                empresas.append(empresa)
                
            except Exception as e:
                logger.error(f"Erro ao processar linha {idx + 2}: {e}")
                erros += 1
                continue
        
        logger.info(f"✓ {len(empresas)} empresas convertidas com sucesso")
        
        if erros > 0:
            logger.warning(f"⚠ {erros} linhas com erro foram ignoradas")
        
        return empresas
    
    def obter_estatisticas(self) -> dict:
        """
        Retorna estatísticas da planilha
        
        Returns:
            Dict com estatísticas
        """
        if self._df is None:
            self.carregar()
        
        stats = {
            "total_empresas": len(self._df),
            "com_ie": self._df["IE"].notna().sum(),
            "com_im": self._df["IM"].notna().sum(),
            "com_nire": self._df["NIRE"].notna().sum(),
            "com_email": self._df["e-mail"].notna().sum(),
            "com_data_cadastro": self._df["Data de Cadastro"].notna().sum(),
            "com_cadastro_jettax": self._df["Cadastro JETTAX"].notna().sum(),
            "regimes_unicos": self._df["Tributacao"].nunique(),
            "regimes": self._df["Tributacao"].value_counts().to_dict()
        }
        
        return stats
