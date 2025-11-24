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

- Python 3.8 ou superior
- Acesso à planilha `RELAÇÃO DE EMPRESAS.xlsx`
- Credenciais do JETTAX 360

### 2. Instalar Dependências

Use apenas as dependências de runtime para deploys (ex.: Streamlit Cloud):

```bash
cd "G:\- CONTABILIDADE -\Automação\JETTAX"
pip install -r requirements.txt
```

Ferramentas de desenvolvimento (lint/tests) ficam em `requirements-dev.txt` para não
quebrar instalações em ambientes de produção/hosting:

```bash
pip install -r requirements-dev.txt  # opcional, só para quem for desenvolver
```

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

Você verá um menu interativo:

```
========================================
  JETTAX 360 - Sistema de Automacao
========================================

[1] Cadastro de novos clientes
[2] Atualizacao de clientes existentes
[3] Sync completo (cadastro + atualizacao)
[4] Comparar (apenas listar diferencas)
[5] Modo DRY-RUN (cadastro - simulacao)
[6] Modo DRY-RUN (atualizacao - simulacao)
[0] Sair
```

### Modo Linha de Comando

#### Cadastrar novos clientes

```bash
python main.py cadastro
```

#### Atualizar clientes existentes

```bash
python main.py atualizacao
```

#### Sync completo (cadastro + atualização)

```bash
python main.py sync
```

#### Comparar apenas (sem alterações)

```bash
python main.py comparar
```

#### Modo Dry-Run (simulação)

```bash
python main.py cadastro --dry-run
python main.py atualizacao --dry-run
python main.py sync --dry-run
```

#### Modo Debug (log detalhado)

```bash
python main.py sync --debug
```

#### Processar apenas primeiras N empresas (para testes)

```bash
python main.py cadastro --limit 10
```

#### Customizar intervalo entre requisições

```bash
python main.py sync --intervalo 2.0
```

### Painel Streamlit (dashboard web)

Para usar a interface web de testes no Streamlit (localmente ou no Streamlit Cloud), o entrypoint é o arquivo `jettax_dashboard.py` na raiz do repositório. Execute:

```bash
streamlit run jettax_dashboard.py
```

O painel assume a planilha `RELAÇÃO DE EMPRESAS.xlsx` na raiz (pode ser alterada na sidebar) e tenta carregar variáveis do `.env` em `config/.env` ou `./.env` se existirem. Em deployments como Streamlit Cloud, basta subir esses arquivos e rodar o comando acima como o "main" da aplicação.

## 📁 Estrutura do Projeto

```
JETTAX/
├── config/
│   └── .env                          # Configurações
├── data/
│   └── state/                        # Estado da aplicação
├── logs/                             # Logs de execução
├── reports/                          # Relatórios gerados
├── debug_payloads/                   # Payloads de debug
├── src/
│   ├── core/
│   │   ├── api_client.py            # Cliente da API JETTAX
│   │   └── excel_reader.py          # Leitor da planilha
│   ├── models/
│   │   └── empresa.py               # Modelo de dados Empresa
│   ├── services/
│   │   ├── cadastro_service.py      # Serviço de cadastro
│   │   ├── atualizacao_service.py   # Serviço de atualização
│   │   ├── comparacao_service.py    # Serviço de comparação
│   │   └── regime_mapper.py         # Mapeamento de regimes
│   └── utils/
│       ├── cnpj_utils.py            # Utilidades para CNPJ/CPF
│       ├── date_utils.py            # Utilidades para datas
│       └── logger.py                # Sistema de logging
├── main.py                           # Script principal
├── run_automation.bat                # Executor interativo
├── requirements.txt                  # Dependências Python
└── README.md                         # Esta documentação
```

## 🔧 Arquitetura

### Fluxo de Cadastro

1. **Leitura da Planilha**: Carrega empresas do Excel
2. **Validação**: Valida CNPJ, campos obrigatórios
3. **Verificação**: Consulta se já existe no JETTAX
4. **Enriquecimento**: Busca dados na Receita Federal
5. **Mapeamento**: Converte regime tributário para ObjectId
6. **Código IBGE**: Busca código da cidade
7. **Criação**: Envia payload para API JETTAX
8. **Relatório**: Gera relatório de resultados

### Fluxo de Atualização

1. **Leitura da Planilha**: Carrega empresas do Excel
2. **Busca no JETTAX**: Obtém dados atuais do sistema
3. **Comparação**: Detecta divergências campo a campo
4. **Atualização Seletiva**: Atualiza apenas campos diferentes
5. **Relatório**: Gera relatório com diferenças encontradas

## 📊 Campos Processados

### Dados Obrigatórios
- CNPJ (validado com dígitos verificadores)
- Razão Social
- Tributação (mapeado para ObjectId)
- Município (convertido para código IBGE)

### Dados Opcionais
- IE (Inscrição Estadual)
- IM (Inscrição Municipal)
- NIRE
- E-mail
- Ramo de atividade
- Responsável
- Data de cadastro
- CPF/Senha Prefeitura (para regimes de serviços)

## 🔍 Validações

### CNPJ
- Normalização (apenas dígitos)
- Validação com dígitos verificadores
- Formatação (00.000.000/0000-00)

### IE
- Conversão "FALSE" → 0 ou vazio
- Preservação de valores numéricos

### E-mail
- Validação básica de formato
- Normalização (lowercase)

### Datas
- Suporte a múltiplos formatos:
  - YYYY-MM-DD
  - DD/MM/YYYY
  - Datetime objects

## 📈 Relatórios

Os relatórios são salvos na pasta `reports/` com timestamp:

- `cadastro_YYYYMMDD_HHMMSS.txt`: Resultado de cadastro
- `atualizacao_YYYYMMDD_HHMMSS.txt`: Resultado de atualização
- `sync_YYYYMMDD_HHMMSS.txt`: Resultado de sync completo

Exemplo de relatório:

```
RELATÓRIO DE SYNC COMPLETO
============================================================

Data: 21/11/2025 14:30:00

FASE 1: CADASTRO
------------------------------------------------------------
Total: 219
✓ Cadastrados: 15
⚠ Já existiam: 204
✗ Erros: 0

FASE 2: ATUALIZAÇÃO
------------------------------------------------------------
Total: 219
✓ Atualizados: 42
= Sem alteração: 177
⚠ Não cadastrados: 0
✗ Erros: 0

============================================================
RESUMO GERAL
============================================================
Empresas processadas: 219
Novos cadastros: 15
Atualizações: 42
Sem alteração: 177
Erros: 0
```

## 🛡️ Segurança

- Credenciais armazenadas em `.env` (não versionado)
- Validação de CNPJ com dígitos verificadores
- Tratamento seguro de exceções
- Logs não expõem senhas

## ⚙️ Parâmetros de Linha de Comando

```
usage: main.py [-h] [--planilha PLANILHA] [--dry-run] [--debug]
               [--intervalo INTERVALO] [--limit LIMIT]
               {cadastro,atualizacao,sync,comparar}

positional arguments:
  {cadastro,atualizacao,sync,comparar}
                        Modo de operação

optional arguments:
  -h, --help            Mostrar ajuda
  --planilha PLANILHA   Caminho da planilha Excel
  --dry-run             Modo simulação (sem alterações)
  --debug               Modo debug (log detalhado)
  --intervalo INTERVALO Intervalo entre requisições (segundos)
  --limit LIMIT         Limitar a N empresas
```

## 🐛 Troubleshooting

### Erro ao ler planilha

Verifique:
- Arquivo existe no caminho especificado
- Planilha tem a estrutura esperada (14 colunas)
- Arquivo não está aberto em outro programa

### Erro de autenticação

Verifique:
- Credenciais corretas no `.env`
- URLs da API estão acessíveis
- Conexão com internet

### Regime não encontrado

O sistema mapeia automaticamente regimes da planilha para o JETTAX:
- Simples Nacional - Serviços
- Simples Nacional - Comércio
- Lucro Presumido - Serviços
- etc.

Verifique se o regime está no mapeamento (`src/services/regime_mapper.py`).

## 📝 Logs

Os logs são salvos em:
- **Console**: Log colorido em tempo real
- **Arquivo**: `logs/jettax_automation_YYYY-MM-DD.log`

Níveis de log:
- 🔵 DEBUG: Informações detalhadas (apenas com --debug)
- ⚪ INFO: Informações gerais
- 🟡 WARNING: Avisos
- 🔴 ERROR: Erros

## 🎯 Boas Práticas

1. **Sempre use --dry-run primeiro** para validar operações
2. **Comece com --limit 10** para testar com poucas empresas
3. **Verifique os relatórios** após cada execução
4. **Use --debug** para investigar erros específicos
5. **Faça backup da planilha** antes de alterações manuais

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `logs/`
2. Execute com `--debug` para mais detalhes
3. Consulte a documentação da API JETTAX

---

**Versão**: 1.0.0  
**Data**: 21/11/2025  
**Autor**: Automação Contábil
>>>>>>> ae4405a (Primeiro commit do projeto Jettax Automação)
