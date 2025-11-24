"""
Modelo de dados: Empresa
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date
import re


class Empresa(BaseModel):
    """Modelo de dados de uma empresa"""
    
    # Dados obrigatórios da planilha
    cnpj: str = Field(..., min_length=14, max_length=14, description="CNPJ sem máscara (14 dígitos)")
    razao_social: str = Field(..., min_length=1, description="Razão social da empresa")
    tributacao: str = Field(..., description="Regime tributário completo")
    municipio: str = Field(..., description="Município da empresa")
    
    # Dados opcionais da planilha
    ie: Optional[str] = Field(None, description="Inscrição Estadual (FALSE se não tiver)")
    im: Optional[str] = Field(None, description="Inscrição Municipal")
    nire: Optional[str] = Field(None, description="NIRE (JUCEG)")
    ramo_atividade: Optional[str] = Field(None, description="Descrição da atividade")
    responsavel: Optional[str] = Field(None, description="Nome do responsável")
    email: Optional[str] = Field(None, description="E-mail da empresa")
    data_cadastro: Optional[date] = Field(None, description="Data de abertura/cadastro")
    
    # Credenciais de prefeitura
    cpf_prefeitura: Optional[str] = Field(None, description="CPF para login prefeitura")
    senha_prefeitura: Optional[str] = Field(None, description="Senha para login prefeitura")
    
    # Controle JETTAX
    cadastro_jettax: Optional[date] = Field(None, description="Data de cadastro no JETTAX")
    id_jettax: Optional[str] = Field(None, description="ID no sistema JETTAX")
    
    # Dados enriquecidos (consulta Receita Federal)
    endereco_completo: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cep: Optional[str] = None
    uf: Optional[str] = None
    codigo_ibge: Optional[int] = None
    cnaes: Optional[List[dict]] = None
    natureza_juridica: Optional[str] = None
    
    # Mapeamento JETTAX
    regime_object_id: Optional[str] = Field(None, description="ObjectId do regime no JETTAX")
    
    class Config:
        json_schema_extra = {
            "example": {
                "cnpj": "46149398000123",
                "razao_social": "EMPRESA EXEMPLO LTDA",
                "tributacao": "Simples Nacional - Serviços",
                "municipio": "ANAPOLIS",
                "ie": "FALSE",
                "im": "103416",
                "cpf_prefeitura": "87298244604",
                "senha_prefeitura": "872982"
            }
        }
    
    @validator('cnpj')
    def validar_cnpj(cls, v):
        """Valida formato do CNPJ"""
        if not v:
            raise ValueError('CNPJ é obrigatório')
        
        # Remover máscara se houver
        digitos = re.sub(r'\D', '', v)
        
        if len(digitos) != 14:
            raise ValueError(f'CNPJ deve ter 14 dígitos, recebeu {len(digitos)}')
        
        return digitos
    
    @validator('ie')
    def tratar_ie(cls, v):
        """Trata IE FALSE ou vazio"""
        if not v or str(v).upper() == 'FALSE':
            return None
        return str(v).strip()
    
    @validator('email')
    def validar_email(cls, v):
        """Valida formato de e-mail básico"""
        if not v:
            return None
        
        v = str(v).strip()
        
        # Regex básico para e-mail
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            # Apenas warning, não bloqueia
            return v
        
        return v
    
    def precisa_credenciais_prefeitura(self) -> bool:
        """
        Verifica se empresa precisa de credenciais de prefeitura
        (regimes com "Serviços" no nome)
        """
        if not self.tributacao:
            return False
        
        keywords = ['serviço', 'servico']
        tributacao_lower = self.tributacao.lower()
        
        return any(kw in tributacao_lower for kw in keywords)
    
    def tem_credenciais_completas(self) -> bool:
        """Verifica se tem CPF e Senha preenchidos"""
        return bool(self.cpf_prefeitura and self.senha_prefeitura)
    
    def get_ie_numerico(self) -> int:
        """Retorna IE como número ou 0 se vazio/FALSE"""
        if not self.ie:
            return 0
        
        try:
            # Tentar extrair apenas dígitos
            digitos = re.sub(r'\D', '', self.ie)
            return int(digitos) if digitos else 0
        except (ValueError, TypeError):
            return 0
    
    def __str__(self) -> str:
        return f"{self.cnpj} - {self.razao_social}"
    
    def __repr__(self) -> str:
        return f"Empresa(cnpj='{self.cnpj}', razao='{self.razao_social[:30]}...')"
