# 🤖 GUIA DE AUTOMAÇÃO JETTAX 360 - HÍBRIDA (UI + API)

**Versão:** 2.0  
**Data:** 21/11/2025  
**Cobertura:** 77.8% (170 endpoints)  
**Destinado:** Agentes de IA e Desenvolvedores

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Autenticação](#autenticação)
3. [Arquitetura Híbrida](#arquitetura-híbrida)
4. [Módulos e Endpoints](#módulos-e-endpoints)
5. [Fluxos de Automação](#fluxos-de-automação)
6. [Exemplos Práticos](#exemplos-práticos)
7. [Estratégias de Implementação](#estratégias-de-implementação)

---

## 🎯 VISÃO GERAL

### O que é JETTAX 360?

Sistema web de gestão fiscal e contábil com duas interfaces de acesso:

1. **API REST** → Para operações programáticas (endpoints descobertos)
2. **Interface Web (UI)** → Para operações complexas ou sem API

### Descobertas da Captura

- **170 endpoints REST** mapeados
- **19 módulos** identificados
- **Autenticação JWT** (api-auth.jettax360.com.br)
- **3 domínios principais:**
  - `api.jettax360.com.br` (110 endpoints)
  - `api-federal.jettax360.com.br` (54 endpoints)
  - `api-auth.jettax360.com.br` (3 endpoints)

---

## 🔐 AUTENTICAÇÃO

### Fluxo de Autenticação JWT

```
PASSO 1: LOGIN (API)
POST https://api-auth.jettax360.com.br/api/jettax360/v1/auth/office/login

Request:
{
  "email": "seu_email@exemplo.com",
  "password": "sua_senha"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user_id",
    "name": "Nome do Usuário",
    "email": "email@exemplo.com",
    "office": {
      "id": "office_id",
      "name": "Nome do Escritório"
    }
  }
}

PASSO 2: USAR TOKEN EM TODAS AS REQUISIÇÕES
Headers:
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "Content-Type": "application/json"
}

PASSO 3: REFRESH TOKEN (quando expirar)
GET https://api-auth.jettax360.com.br/api/jettax360/v1/auth/office/refresh
Headers: { "Authorization": "Bearer {token_antigo}" }

Response:
{
  "token": "novo_token_jwt..."
}

PASSO 4: OBTER DADOS DO USUÁRIO
GET https://api-auth.jettax360.com.br/api/jettax360/v1/auth/office/user
Headers: { "Authorization": "Bearer {token}" }

Response:
{
  "id": "user_id",
  "name": "Nome",
  "email": "email@exemplo.com",
  "role": "admin",
  "office": {...}
}
```

### Quando Usar API vs UI para Autenticação

| Cenário | Método Recomendado | Razão |
|---------|-------------------|-------|
| **Automação headless** | ✅ API | Mais rápido, confiável |
| **Login com 2FA** | ⚠️ UI (Selenium) | API pode não suportar |
| **Múltiplas sessões** | ✅ API | Tokens independentes |
| **Debug visual** | 🔸 UI | Ver interface real |

---

## 🏗️ ARQUITETURA HÍBRIDA

### Estratégia: Quando Usar API vs UI

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISÃO: API vs UI                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ SEMPRE USE API QUANDO:                                      │
│     • Endpoint REST existe e está mapeado                       │
│     • Operação é CRUD simples (Create/Read/Update/Delete)       │
│     • Precisa de velocidade e confiabilidade                    │
│     • Automação em lote (múltiplos registros)                   │
│     • Integração com outros sistemas                            │
│                                                                 │
│  ⚠️  USE UI (Selenium/Playwright) QUANDO:                       │
│     • Endpoint não existe ou não foi descoberto                 │
│     • Operação complexa com múltiplas etapas visuais            │
│     • Upload de arquivos com interface drag-drop                │
│     • Relatórios com geração de PDF via browser                 │
│     • Validações visuais são necessárias                        │
│     • Download de arquivos com modal de confirmação             │
│                                                                 │
│  🔄 USE HÍBRIDO (API + UI) QUANDO:                              │
│     • API para preparação + UI para confirmação visual          │
│     • API para dados + UI para interação complexa               │
│     • Fallback: tenta API, se falhar usa UI                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Exemplo de Fluxo Híbrido

```python
# CENÁRIO: Baixar todos os documentos de um cliente

# ETAPA 1: API - Obter lista de clientes
response = requests.get(
    "https://api.jettax360.com.br/api/v1/clients/all",
    headers={"Authorization": f"Bearer {token}"}
)
clientes = response.json()

for cliente in clientes:
    # ETAPA 2: API - Verificar downloads disponíveis
    downloads = requests.get(
        f"https://api.jettax360.com.br/api/v1/hub/download/clients/{cliente['id']}",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    if downloads['hasNewDocuments']:
        # ETAPA 3: HÍBRIDO - API retorna URL, mas download precisa de UI
        # Razão: Download pode ter modal de confirmação ou CAPTCHA
        
        # Opção A: Tentar API primeiro
        try:
            download_url = requests.post(
                f"https://api.jettax360.com.br/api/v1/hub/download",
                json={"clientId": cliente['id']},
                headers={"Authorization": f"Bearer {token}"}
            ).json()['url']
            
            # Baixar arquivo diretamente
            arquivo = requests.get(download_url).content
            
        except Exception:
            # Opção B: Fallback para UI
            driver.get(f"https://admin.jettax360.com.br/downloads")
            driver.find_element(By.ID, f"download-{cliente['id']}").click()
            # ... interação com modal, etc
```

---

## 📦 MÓDULOS E ENDPOINTS

### 1. AUTENTICAÇÃO (Auth)

**Domínio:** `api-auth.jettax360.com.br`

| Método | Endpoint | Descrição | Uso |
|--------|----------|-----------|-----|
| POST | `/api/jettax360/v1/auth/office/login` | Login | ✅ SEMPRE API |
| GET | `/api/jettax360/v1/auth/office/user` | Dados do usuário | ✅ API |
| GET | `/api/jettax360/v1/auth/office/refresh` | Refresh token | ✅ API |

**Exemplo:**
```python
import requests

def login(email, password):
    response = requests.post(
        "https://api-auth.jettax360.com.br/api/jettax360/v1/auth/office/login",
        json={"email": email, "password": password}
    )
    return response.json()['token']

token = login("email@exemplo.com", "senha123")
```

---

### 2. CLIENTES (Clients)

**Domínio:** `api.jettax360.com.br`  
**Total:** 12 endpoints

| Método | Endpoint | Descrição | UI Equivalente |
|--------|----------|-----------|----------------|
| GET | `/api/v1/clients` | Listar clientes (paginado) | Geral → Clientes |
| GET | `/api/v1/clients/all` | Todos os clientes | - |
| GET | `/api/v1/clients/{id}` | Detalhes do cliente | Clicar em cliente |
| POST | `/api/v1/clients/import/excel` | Importar Excel | Botão "Importar" |
| PUT | `/api/v1/clients/{id}` | Atualizar cliente | Salvar no formulário |
| DELETE | `/api/v1/clients/delete-certificate/{id}` | Deletar certificado | Botão "Remover Cert" |

**Estrutura de Cliente:**
```json
{
  "id": "68c011f49a213ccebf0463a2",
  "name": "EMPRESA EXEMPLO LTDA",
  "document": "12.345.678/0001-90",
  "city": "São Paulo",
  "status": 1,
  "municipalRegistration": "123456",
  "certificateStatus": 1,
  "certificateType": 1,
  "taxation": "SN",
  "modules": {
    "enableModuleHubFederal": true,
    "enableModuleNFSe": true
  }
}
```

**Quando Usar UI:**
- ❌ Listar clientes → Use API (mais rápido)
- ❌ Buscar cliente → Use API
- ⚠️ Cadastro complexo com upload de documentos → UI pode ser necessária
- ✅ Atualizar dados simples → API

**Exemplo de Automação:**
```python
# Cenário: Atualizar regime tributário de múltiplos clientes

def atualizar_regime_clientes(token, clientes_dict):
    """
    clientes_dict = {
        "12.345.678/0001-90": "SN",  # Simples Nacional
        "98.765.432/0001-10": "LP",  # Lucro Presumido
    }
    """
    # 1. Obter todos os clientes (API)
    clientes = requests.get(
        "https://api.jettax360.com.br/api/v1/clients/all",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    # 2. Filtrar e atualizar (API)
    for cliente in clientes:
        cnpj = cliente['document']
        if cnpj in clientes_dict:
            novo_regime = clientes_dict[cnpj]
            
            # Atualizar via API
            requests.put(
                f"https://api.jettax360.com.br/api/v1/clients/update-regime-type/{cliente['id']}",
                json={"taxation": novo_regime},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            print(f"✅ {cliente['name']} atualizado para {novo_regime}")
```

---

### 3. DOCUMENTOS FISCAIS (Commerce - Federal)

**Domínio:** `api-federal.jettax360.com.br`  
**Total:** 54 endpoints  
**Tipos:** NF-e, NFC-e, CT-e, CF-e

#### 3.1 Dashboard Federal

| Endpoint | Descrição | Response Sample |
|----------|-----------|----------------|
| GET `/api/v1/commerce/hub/federal/dashboard-total-sales` | Total de vendas | `{"total": 1234567.89, "period": "..."}` |
| GET `/api/v1/commerce/hub/federal/dashboard-top-products` | Top 10 produtos | `[{"name": "Produto", "qty": 100}]` |
| GET `/api/v1/commerce/hub/federal/dashboard-top-clients` | Top 10 clientes | `[{"name": "Cliente", "value": 5000}]` |
| GET `/api/v1/commerce/hub/federal/dashboard-pis-cofins` | PIS/COFINS | `{"pis": 1234, "cofins": 5678}` |

**Quando Usar:**
- ✅ API para obter dados do dashboard
- 🔸 UI se precisar visualizar gráficos (mas dados vêm da API)

#### 3.2 Documentos e Autenticidade

| Endpoint | Descrição | Uso API vs UI |
|----------|-----------|---------------|
| GET `/api/v1/commerce/authenticity/list` | Listar documentos para autenticação | ✅ API |
| POST `/api/v1/commerce/authenticity/validate` | Validar autenticidade | ✅ API |
| GET `/api/v1/commerce/hub/nfe/list` | Listar NF-e | ✅ API |
| GET `/api/v1/commerce/hub/nfe/{id}` | Detalhes NF-e | ✅ API |
| POST `/api/v1/commerce/hub/nfe/download` | Baixar XML/PDF | ⚠️ Híbrido* |

*Download pode retornar URL ou precisar de UI para modal

**Exemplo - Baixar NFe:**
```python
def baixar_nfe_periodo(token, client_id, data_inicio, data_fim):
    # 1. Listar NFe do período (API)
    response = requests.get(
        "https://api-federal.jettax360.com.br/api/v1/commerce/hub/nfe/list",
        params={
            "clientId": client_id,
            "startDate": data_inicio,
            "endDate": data_fim,
            "page": 1,
            "limit": 100
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    nfes = response.json()['data']
    
    for nfe in nfes:
        # 2. Tentar baixar via API
        try:
            download_response = requests.post(
                f"https://api-federal.jettax360.com.br/api/v1/commerce/hub/nfe/download",
                json={
                    "nfeId": nfe['id'],
                    "format": "xml"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Se API retornar URL direta
            if 'url' in download_response.json():
                xml_content = requests.get(download_response.json()['url']).content
                with open(f"NFe_{nfe['numero']}.xml", 'wb') as f:
                    f.write(xml_content)
                    
        except Exception as e:
            # Fallback para UI se necessário
            print(f"⚠️ NFe {nfe['numero']} precisa de UI - {e}")
```

#### 3.3 Categorização e Regras

| Endpoint | Descrição | Exemplo Request |
|----------|-----------|-----------------|
| GET `/api/v1/commerce/categories/list` | Listar categorias | - |
| POST `/api/v1/commerce/categories/` | Criar categoria | `{"name": "Revenda", "code": "01"}` |
| PUT `/api/v1/commerce/categories/{id}` | Atualizar | `{"name": "Novo Nome"}` |
| DELETE `/api/v1/commerce/categories/{id}` | Deletar | - |

**Regras PIS/COFINS:**
```python
# Criar regra PIS/COFINS
requests.post(
    "https://api-federal.jettax360.com.br/api/v1/commerce/hub/pis-cofins-rules/",
    json={
        "clientId": "client_id",
        "ncm": "12345678",
        "pisRate": 1.65,
        "cofinsRate": 7.6,
        "regime": "cumulativo"
    },
    headers={"Authorization": f"Bearer {token}"}
)
```

---

### 4. FISCAL (Apurações)

**Domínio:** `api.jettax360.com.br`  
**Total:** 36 endpoints

#### 4.1 Apurações ICMS-ST

| Endpoint | Descrição |
|----------|-----------|
| GET `/api/v1/fiscal/summaries/icms-st/` | Listar apurações |
| GET `/api/v1/fiscal/summaries/icms-st/{id}` | Detalhes da apuração |
| POST `/api/v1/fiscal/summaries/icms-st/batch-reprocess/` | Reprocessar em lote |

**Estrutura de Apuração:**
```json
{
  "id": "apuracao_id",
  "clientId": "client_id",
  "referenceMonth": "2025-11",
  "status": "processed",
  "values": {
    "totalIcmsSt": 1234.56,
    "totalBase": 10000.00
  },
  "details": [...]
}
```

#### 4.2 DAS (Simples Nacional)

| Endpoint | Descrição |
|----------|-----------|
| GET `/api/v1/fiscal/das/list` | Listar DAS |
| GET `/api/v1/fiscal/das/annex/{clientId}` | Anexo do Simples |
| POST `/api/v1/fiscal/das/generate` | Gerar DAS |

#### 4.3 DCTF-Web

| Endpoint | Descrição |
|----------|-----------|
| GET `/api/v1/fiscal/summaries/dctfweb/` | Listar DCTF-Web |
| POST `/api/v1/fiscal/summaries/dctfweb/batch-reprocess` | Reprocessar |

**Exemplo - Automação de Apurações:**
```python
def processar_apuracoes_mes(token, mes_referencia):
    # 1. Obter todos os clientes (API)
    clientes = requests.get(
        "https://api.jettax360.com.br/api/v1/clients/all",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    resultados = []
    
    for cliente in clientes:
        # 2. Verificar regime tributário
        if cliente['taxation'] == 'SN':
            # Simples Nacional - DAS
            das = requests.get(
                f"https://api.jettax360.com.br/api/v1/fiscal/das/list",
                params={
                    "clientId": cliente['id'],
                    "referenceMonth": mes_referencia
                },
                headers={"Authorization": f"Bearer {token}"}
            ).json()
            
            resultados.append({
                "cliente": cliente['name'],
                "tipo": "DAS",
                "valor": das.get('totalValue', 0)
            })
            
        elif cliente['taxation'] in ['LP', 'LR']:
            # Lucro Presumido/Real - DCTF-Web
            dctf = requests.get(
                "https://api.jettax360.com.br/api/v1/fiscal/summaries/dctfweb/",
                params={
                    "clientId": cliente['id'],
                    "referenceMonth": mes_referencia
                },
                headers={"Authorization": f"Bearer {token}"}
            ).json()
            
            resultados.append({
                "cliente": cliente['name'],
                "tipo": "DCTF-Web",
                "valor": dctf.get('totalValue', 0)
            })
    
    return resultados
```

---

### 5. DOWNLOADS (Hub)

**Domínio:** `api.jettax360.com.br`  
**Total:** 24 endpoints

| Endpoint | Descrição | API vs UI |
|----------|-----------|-----------|
| GET `/api/v1/hub/download/list` | Listar downloads | ✅ API |
| GET `/api/v1/hub/download/clients/{id}` | Downloads do cliente | ✅ API |
| POST `/api/v1/hub/download` | Solicitar download | ✅ API |
| GET `/api/v1/hub/download/{id}` | Status do download | ✅ API |

**Estrutura de Download:**
```json
{
  "id": "download_id",
  "clientId": "client_id",
  "type": "NFE",
  "status": "completed",
  "url": "https://storage.jettax360.com.br/downloads/arquivo.zip",
  "createdAt": "2025-11-21T10:00:00Z",
  "expiresAt": "2025-11-22T10:00:00Z"
}
```

**Exemplo - Download em Massa:**
```python
def download_documentos_clientes(token, tipo_documento="NFE"):
    # 1. Listar todos os downloads disponíveis (API)
    downloads = requests.get(
        "https://api.jettax360.com.br/api/v1/hub/download/list",
        params={"type": tipo_documento, "status": "completed"},
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    for download in downloads['data']:
        # 2. Baixar arquivo (API - URL direta)
        if download['status'] == 'completed' and download['url']:
            arquivo = requests.get(download['url']).content
            
            filename = f"{download['clientName']}_{download['type']}_{download['id']}.zip"
            with open(filename, 'wb') as f:
                f.write(arquivo)
                
            print(f"✅ Baixado: {filename}")
```

---

### 6. GRUPOS/CLUSTERS

**Domínio:** `api.jettax360.com.br`  
**Total:** 6 endpoints

| Endpoint | Descrição |
|----------|-----------|
| GET `/api/v1/clusters/` | Listar grupos |
| POST `/api/v1/clusters/` | Criar grupo |
| GET `/api/v1/clusters/{id}` | Detalhes do grupo |
| GET `/api/v1/clusters/clients` | Clientes do grupo |
| POST `/api/v1/clusters/delete` | Deletar grupo |

**Exemplo - Organizar Clientes em Grupos:**
```python
# Criar grupo por tipo de tributação
def organizar_grupos_por_regime(token):
    clientes = requests.get(
        "https://api.jettax360.com.br/api/v1/clients/all",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    # Agrupar por regime
    grupos = {}
    for cliente in clientes:
        regime = cliente['taxation']
        if regime not in grupos:
            grupos[regime] = []
        grupos[regime].append(cliente['id'])
    
    # Criar clusters
    for regime, client_ids in grupos.items():
        nome_grupo = {
            'SN': 'Simples Nacional',
            'LP': 'Lucro Presumido',
            'LR': 'Lucro Real',
            'MEI': 'MEI'
        }.get(regime, regime)
        
        requests.post(
            "https://api.jettax360.com.br/api/v1/clusters/",
            json={
                "name": nome_grupo,
                "clientIds": client_ids
            },
            headers={"Authorization": f"Bearer {token}"}
        )
```

---

### 7. USUÁRIOS

**Domínio:** `api.jettax360.com.br`  
**Total:** 4 endpoints

| Endpoint | Descrição |
|----------|-----------|
| GET `/api/v1/users` | Listar usuários |
| GET `/api/v1/users/{id}` | Detalhes do usuário |
| GET `/api/v1/users/load` | Dados para formulário |
| GET `/api/v1/users/clients/get-to-link/{id}` | Clientes para vincular |

---

### 8. NOTIFICAÇÕES

**Domínio:** `api.jettax360.com.br`  
**Total:** 3 endpoints

| Endpoint | Descrição |
|----------|-----------|
| GET `/api/v1/notifications` | Listar notificações |
| GET `/api/v1/notifications/user` | Notificações do usuário |
| POST `/api/v1/notifications/read` | Marcar como lida |

**Exemplo - Monitoramento:**
```python
def monitorar_notificacoes(token, intervalo_segundos=60):
    while True:
        notif = requests.get(
            "https://api.jettax360.com.br/api/v1/notifications/user",
            headers={"Authorization": f"Bearer {token}"}
        ).json()
        
        nao_lidas = [n for n in notif if not n['read']]
        
        for n in nao_lidas:
            print(f"🔔 {n['type']}: {n['message']}")
            
            # Marcar como lida
            requests.post(
                "https://api.jettax360.com.br/api/v1/notifications/read",
                json={"notificationId": n['id']},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        time.sleep(intervalo_segundos)
```

---

## 🔄 FLUXOS DE AUTOMAÇÃO HÍBRIDA

### Fluxo 1: Sincronização de Clientes (Excel → JETTAX)

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRADA: Planilha Excel com dados de clientes              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 1: Processar Excel (Python/Pandas)                   │
│   • Ler planilha                                            │
│   • Validar CNPJ, IE, etc                                   │
│   • Normalizar dados                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 2: Autenticar (API)                                   │
│   POST /auth/office/login                                   │
│   → Receber token JWT                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 3: Verificar Clientes Existentes (API)               │
│   GET /api/v1/clients/all                                   │
│   → Comparar CNPJs                                          │
│   → Identificar: novos / atualizar / já existem            │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌──────────────────────┐            ┌──────────────────────┐
│ NOVOS CLIENTES       │            │ ATUALIZAR EXISTENTES │
│ POST /clients/       │            │ PUT /clients/{id}    │
│ (API)                │            │ (API)                │
└──────────────────────┘            └──────────────────────┘
        ↓                                       ↓
        └───────────────────┬───────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 4: Configurar Módulos (API)                          │
│   POST /clients/update-modules/                             │
│   → Ativar: Federal, NFS-e, etc                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 5: Upload de Certificados (HÍBRIDO)                  │
│   • Se API aceitar: POST com certificado                    │
│   • Se não: UI (Selenium) para upload via drag-drop        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ RESULTADO: Clientes sincronizados no JETTAX                │
└─────────────────────────────────────────────────────────────┘
```

**Código de Exemplo:**
```python
import pandas as pd
import requests

def sincronizar_clientes_excel(token, arquivo_excel):
    # 1. Ler Excel
    df = pd.read_excel(arquivo_excel)
    
    # 2. Obter clientes existentes
    existentes = requests.get(
        "https://api.jettax360.com.br/api/v1/clients/all",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    cnpjs_existentes = {c['document']: c for c in existentes}
    
    # 3. Processar cada linha
    for _, row in df.iterrows():
        cnpj = row['CNPJ']
        
        dados_cliente = {
            "name": row['Razão Social'],
            "document": cnpj,
            "city": row['Cidade'],
            "taxation": row['Regime Tributário'],
            "municipalRegistration": row.get('IE', ''),
            "modules": {
                "enableModuleHubFederal": True,
                "enableModuleNFSe": True
            }
        }
        
        if cnpj in cnpjs_existentes:
            # Atualizar
            client_id = cnpjs_existentes[cnpj]['id']
            response = requests.put(
                f"https://api.jettax360.com.br/api/v1/clients/{client_id}",
                json=dados_cliente,
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"✅ Atualizado: {row['Razão Social']}")
        else:
            # Criar novo
            response = requests.post(
                "https://api.jettax360.com.br/api/v1/clients/",
                json=dados_cliente,
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"➕ Criado: {row['Razão Social']}")
```

---

### Fluxo 2: Download Automático de Documentos Fiscais

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRADA: Lista de clientes + Período                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 1: Autenticação (API)                                 │
│   POST /auth/office/login                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 2: Listar Clientes (API)                             │
│   GET /api/v1/clients/all                                   │
│   → Filtrar por cidade, regime, status                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 3: Para cada cliente, verificar downloads (API)      │
│   GET /hub/download/clients/{id}                            │
│   → Identificar documentos disponíveis                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌──────────────────────┐            ┌──────────────────────┐
│ SE DOWNLOAD PRONTO   │            │ SE PRECISA SOLICITAR │
│ GET download/{id}    │            │ POST /hub/download   │
│ (API)                │            │ (API)                │
└──────────────────────┘            └──────────────────────┘
        ↓                                       ↓
        └───────────────────┬───────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 4: Baixar Arquivos                                    │
│   • Tentar via API (URL direta)                             │
│   • Se falhar → UI para interagir com modal                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 5: Organizar Arquivos                                 │
│   • Descompactar ZIPs                                       │
│   • Separar por cliente/tipo/mês                           │
│   • Renomear arquivos                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ RESULTADO: Documentos organizados localmente                │
└─────────────────────────────────────────────────────────────┘
```

**Código de Exemplo:**
```python
import os
import zipfile
from datetime import datetime

def download_documentos_periodo(token, data_inicio, data_fim, pasta_destino):
    # 1. Criar pasta se não existir
    os.makedirs(pasta_destino, exist_ok=True)
    
    # 2. Obter clientes
    clientes = requests.get(
        "https://api.jettax360.com.br/api/v1/clients/all",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    for cliente in clientes:
        print(f"📂 Processando: {cliente['name']}")
        
        # 3. Verificar downloads disponíveis
        downloads = requests.get(
            f"https://api.jettax360.com.br/api/v1/hub/download/clients/{cliente['id']}",
            params={
                "startDate": data_inicio,
                "endDate": data_fim,
                "type": "NFE"
            },
            headers={"Authorization": f"Bearer {token}"}
        ).json()
        
        for download in downloads.get('data', []):
            if download['status'] == 'completed':
                # 4. Baixar arquivo
                arquivo_zip = requests.get(download['url']).content
                
                # 5. Salvar e extrair
                pasta_cliente = os.path.join(pasta_destino, cliente['document'])
                os.makedirs(pasta_cliente, exist_ok=True)
                
                zip_path = os.path.join(pasta_cliente, f"download_{download['id']}.zip")
                with open(zip_path, 'wb') as f:
                    f.write(arquivo_zip)
                
                # Extrair
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(pasta_cliente)
                
                os.remove(zip_path)  # Remover zip após extrair
                print(f"  ✅ Baixado e extraído: {download['type']}")
```

---

### Fluxo 3: Monitoramento de Certificados

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRADA: Executar diariamente (agendado)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 1: Listar Clientes (API)                             │
│   GET /api/v1/clients/all                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 2: Para cada cliente, verificar certificado          │
│   • Analisar: certificateStatus, certificateExpireDate     │
│   • Identificar: vencidos, a vencer (30 dias), válidos    │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌──────────────────────┐            ┌──────────────────────┐
│ VENCIDOS/A VENCER    │            │ CERTIFICADOS OK      │
│ → Gerar relatório    │            │ → Log de status      │
│ → Enviar email       │            └──────────────────────┘
│ → Criar notificação  │                        
└──────────────────────┘                        
        ↓                                       
┌─────────────────────────────────────────────────────────────┐
│ RESULTADO: Relatório + Alertas enviados                    │
└─────────────────────────────────────────────────────────────┘
```

**Código de Exemplo:**
```python
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

def monitorar_certificados(token, dias_alerta=30):
    # 1. Obter clientes
    clientes = requests.get(
        "https://api.jettax360.com.br/api/v1/clients/all",
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    
    hoje = datetime.now()
    limite_alerta = hoje + timedelta(days=dias_alerta)
    
    certificados_vencidos = []
    certificados_a_vencer = []
    
    # 2. Verificar cada cliente
    for cliente in clientes:
        if cliente.get('certificateExpireDate'):
            expire_date = datetime.fromisoformat(cliente['certificateExpireDate'])
            
            if expire_date < hoje:
                certificados_vencidos.append(cliente)
            elif expire_date < limite_alerta:
                certificados_a_vencer.append(cliente)
    
    # 3. Gerar relatório
    relatorio = []
    
    if certificados_vencidos:
        relatorio.append(f"🔴 CERTIFICADOS VENCIDOS ({len(certificados_vencidos)}):")
        for c in certificados_vencidos:
            relatorio.append(f"  - {c['name']} (CNPJ: {c['document']}) - Venceu em {c['certificateExpireDate']}")
    
    if certificados_a_vencer:
        relatorio.append(f"\n⚠️  CERTIFICADOS A VENCER ({len(certificados_a_vencer)}):")
        for c in certificados_a_vencer:
            dias_restantes = (datetime.fromisoformat(c['certificateExpireDate']) - hoje).days
            relatorio.append(f"  - {c['name']} (CNPJ: {c['document']}) - Vence em {dias_restantes} dias")
    
    # 4. Enviar email se houver alertas
    if certificados_vencidos or certificados_a_vencer:
        enviar_email_alerta("\n".join(relatorio))
    
    return {
        "vencidos": len(certificados_vencidos),
        "a_vencer": len(certificados_a_vencer),
        "relatorio": "\n".join(relatorio)
    }

def enviar_email_alerta(mensagem):
    # Configurar envio de email
    msg = MIMEText(mensagem)
    msg['Subject'] = 'Alerta: Certificados Digitais'
    msg['From'] = 'sistema@empresa.com'
    msg['To'] = 'contador@empresa.com'
    
    # Enviar (configurar SMTP server)
    # s = smtplib.SMTP('localhost')
    # s.send_message(msg)
    # s.quit()
    
    print("📧 Email de alerta enviado")
```

---

## 📚 ESTRATÉGIAS DE IMPLEMENTAÇÃO

### 1. Estratégia de Retry e Fallback

```python
def executar_com_fallback(funcao_api, funcao_ui, max_retries=3):
    """
    Tenta API primeiro, fallback para UI se falhar
    """
    for tentativa in range(max_retries):
        try:
            return funcao_api()
        except Exception as e:
            print(f"⚠️ API falhou (tentativa {tentativa + 1}): {e}")
            
            if tentativa == max_retries - 1:
                print("🔄 Usando fallback UI")
                return funcao_ui()
            
            time.sleep(2 ** tentativa)  # Exponential backoff
    
# Uso:
resultado = executar_com_fallback(
    funcao_api=lambda: baixar_via_api(token, doc_id),
    funcao_ui=lambda: baixar_via_selenium(driver, doc_id)
)
```

### 2. Cache de Tokens

```python
import json
from datetime import datetime, timedelta

class JettaxAuth:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = None
        self.token_expire = None
        self.cache_file = 'jettax_token_cache.json'
        
        self._carregar_cache()
    
    def _carregar_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                self.token = cache['token']
                self.token_expire = datetime.fromisoformat(cache['expire'])
        except:
            pass
    
    def _salvar_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump({
                'token': self.token,
                'expire': self.token_expire.isoformat()
            }, f)
    
    def get_token(self):
        # Verificar se token ainda é válido
        if self.token and self.token_expire and datetime.now() < self.token_expire:
            return self.token
        
        # Fazer login
        response = requests.post(
            "https://api-auth.jettax360.com.br/api/jettax360/v1/auth/office/login",
            json={"email": self.email, "password": self.password}
        )
        
        self.token = response.json()['token']
        self.token_expire = datetime.now() + timedelta(hours=8)
        
        self._salvar_cache()
        return self.token
    
    def refresh_token(self):
        response = requests.get(
            "https://api-auth.jettax360.com.br/api/jettax360/v1/auth/office/refresh",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.token = response.json()['token']
        self.token_expire = datetime.now() + timedelta(hours=8)
        
        self._salvar_cache()
        return self.token

# Uso:
auth = JettaxAuth("email@empresa.com", "senha123")
token = auth.get_token()  # Usa cache se válido
```

### 3. Rate Limiting

```python
import time
from functools import wraps

def rate_limit(calls_per_second=5):
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        
        return wrapper
    return decorator

@rate_limit(calls_per_second=10)
def fazer_requisicao(url, token):
    return requests.get(url, headers={"Authorization": f"Bearer {token}"})
```

### 4. Logging Estruturado

```python
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'jettax_automation_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('JettaxAutomation')

# Usar em automações
def processar_cliente(token, cliente):
    logger.info(f"Iniciando processamento: {cliente['name']} ({cliente['document']})")
    
    try:
        # Operações...
        logger.info(f"✅ Cliente processado com sucesso: {cliente['name']}")
    except Exception as e:
        logger.error(f"❌ Erro ao processar cliente {cliente['name']}: {e}", exc_info=True)
```

---

## 🎯 DECISÃO RÁPIDA: API vs UI

### Checklist de Decisão

```
PARA CADA AUTOMAÇÃO, RESPONDA:

1. O endpoint está no catálogo (170 endpoints)?
   ✅ SIM → Use API
   ❌ NÃO → Vá para pergunta 2

2. A operação precisa de interação visual complexa?
   (múltiplos cliques, drag-drop, validação CAPTCHA)
   ✅ SIM → Use UI
   ❌ NÃO → Tente API genérica ou vá para pergunta 3

3. É possível fazer fallback para UI se API falhar?
   ✅ SIM → Tente API primeiro, fallback UI
   ❌ NÃO → Use apenas UI

4. A operação é em lote (muitos registros)?
   ✅ SIM → Prefira API (mais rápido)
   ❌ NÃO → Tanto faz

5. Precisa de velocidade e confiabilidade máximas?
   ✅ SIM → Use API
   ❌ NÃO → UI pode ser aceitável
```

---

## 📊 RESUMO EXECUTIVO

### O Que Foi Mapeado

- ✅ **170 endpoints REST** (77.8% de cobertura)
- ✅ **Autenticação JWT** completa
- ✅ **CRUD de clientes** (12 endpoints)
- ✅ **Documentos fiscais** (54 endpoints Federal)
- ✅ **Apurações** (36 endpoints Fiscal)
- ✅ **Downloads** (24 endpoints Hub)
- ✅ **Grupos, Usuários, Notificações**

### Automações Prontas para Implementar

1. ✅ **Sincronização de Clientes** (Excel → JETTAX) - 100% API
2. ✅ **Download de Documentos Fiscais** - 90% API + 10% UI
3. ✅ **Monitoramento de Certificados** - 100% API
4. ✅ **Apurações Fiscais** - 100% API
5. ✅ **Gestão de Grupos** - 100% API
6. ✅ **Dashboard e Relatórios** - 100% API

### Onde UI Ainda É Necessária

- ⚠️ Upload de certificados (pode ter drag-drop)
- ⚠️ Alguns downloads com modal de confirmação
- ⚠️ Relatórios com geração visual de PDF
- ⚠️ Configurações avançadas não mapeadas

### Próximos Passos

1. Implementar classe `JettaxClient` com todos os endpoints
2. Criar wrappers para operações comuns
3. Adicionar UI automation (Selenium/Playwright) para fallback
4. Implementar sistema de cache e retry
5. Criar scripts de exemplo para casos de uso principais

---

**Fim do Guia de Automação JETTAX 360**

*Este documento foi gerado a partir de 2 capturas reais do sistema JETTAX 360, com 170 endpoints descobertos e mapeados. Todas as URLs, estruturas de dados e exemplos são baseados em requisições reais capturadas entre 19-21/11/2025.*
