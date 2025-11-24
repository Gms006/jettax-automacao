# Sistema de Automação JETTAX 360
Sistema profissional de automação para cadastro e atualização de clientes no JETTAX 360.

## 📋 Funcionalidades

- ✅ **Cadastro Automático**: Registra novos clientes da planilha no JETTAX
- ✅ **Atualização Inteligente**: Detecta e atualiza divergências entre planilha e sistema
- ✅ **Enriquecimento de Dados**: Consulta automática à Receita Federal (CNPJ)
- ✅ **Validação Completa**: Valida CNPJ, IE, e-mail, datas e credenciais
- ✅ **Modo Dry-Run**: Simula operações sem fazer alterações reais
- ✅ **Relatórios Detalhados**: Gera relatórios completos de todas as operações
- ✅ **Logs Coloridos**: Sistema de logging com níveis e cores para fácil monitoramento

## 🚀 Instalação

### 1. Pré-requisitos

- Python **3.12.x** (evite 3.13: o `pydantic-core` ainda não fornece wheel estável e tenta compilar)
- Acesso à planilha `RELAÇÃO DE EMPRESAS.xlsx`
- Credenciais do JETTAX 360

### 2. Instalar Dependências

Use apenas as dependências de runtime para deploys (ex.: Streamlit Cloud) e garanta o Python 3.12.

```bash
cd "G:\- CONTABILIDADE -\Automação\JETTAX"
pip install -r requirements.txt
```

> Nota: o `pydantic` está fixado em uma versão que tem wheel pronto para Python 3.12. Em Python 3.13 a lib tenta compilar o `pydantic-core` e falha, então force 3.12 em produção/Streamlit Cloud.

Ferramentas de desenvolvimento (lint/tests) ficam em `requirements-dev.txt` para não
quebrar instalações em ambientes de produção/hosting:

```bash
pip install -r requirements-dev.txt  # opcional, só para quem for desenvolver
```

### Teste rápido das dependências

```bash
pip install -r requirements.txt
python -c "import requests, pandas; print('Dependências OK')"
```

Se o comando acima rodar sem erros, `requests` e `pandas` foram instalados corretamente.

### 3. Configuração

As configurações já estão prontas no arquivo `config/.env`:

```env
# API URLs
JETTAX_API_URL=https://api.jettax360.com.br
JETTAX_AUTH_URL=https://api-auth.jettax360.com.br

# Credenciais do escritório
JETTAX_EMAIL=contabil2@netocontabilidade.com.br
JETTAX_PASSWORD=2905Macn*

# Caminhos
PLANILHA_EMPRESAS=G:\- CONTABILIDADE -\Automação\JETTAX\RELAÇÃO DE EMPRESAS.xlsx
CERTIFICADOS_DIR=G:\CERTIFICADOS DIGITAIS

# Configurações de execução
DEBUG=false
DRY_RUN=false
```

## 📖 Uso

### Modo Interativo (Recomendado)

Execute o script `run_automation.bat`:

```bash
run_automation.bat
```

Um menu interativo será exibido no terminal; escolha as opções desejadas para comparar, cadastrar ou atualizar empresas conforme a necessidade.
