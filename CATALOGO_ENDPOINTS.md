# 📚 CATÁLOGO DE ENDPOINTS JETTAX 360

**Gerado em:** 21/11/2025  
**Total de Endpoints:** 170  
**Cobertura:** 77.8%  
**Fonte:** 2 capturas (19/11 + 21/11)

---

## 📖 COMO USAR ESTE CATÁLOGO

Este documento lista TODOS os 170 endpoints descobertos, organizados por módulo, com exemplos de request/response reais capturados do sistema.

**Arquivo JSON Completo:** `CATALOGO_COMPLETO_ENDPOINTS.json`

---

## 🔐 AUTENTICAÇÃO (3 endpoints)

**Domínio:** `api-auth.jettax360.com.br`

### 1. Login
```
POST /api/jettax360/v1/auth/office/login

Request:
{
  "email": "email@empresa.com",
  "password": "senha"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { "id": "...", "name": "...", "email": "..." }
}
```

### 2. Dados do Usuário
```
GET /api/jettax360/v1/auth/office/user

Headers:
Authorization: Bearer {token}

Response:
{
  "id": "user_id",
  "name": "Nome",
  "email": "email@empresa.com",
  "office": { "id": "...", "name": "..." }
}
```

### 3. Refresh Token
```
GET /api/jettax360/v1/auth/office/refresh

Headers:
Authorization: Bearer {token}

Response:
{
  "token": "novo_token_jwt..."
}
```

---

## 👥 CLIENTES (12 endpoints)

**Domínio:** `api.jettax360.com.br`

### Listar Clientes (paginado)
```
GET /api/v1/clients?page=1&name=&document=&city=&status=1

Response:
{
  "data": [
    {
      "id": "client_id",
      "name": "EMPRESA LTDA",
      "document": "12.345.678/0001-90",
      "city": "São Paulo",
      "status": 1,
      "taxation": "SN",
      "certificateStatus": 1
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

### Todos os Clientes
```
GET /api/v1/clients/all

Response:
[
  { "id": "...", "name": "...", "document": "..." },
  ...
]
```

### Detalhes do Cliente
```
GET /api/v1/clients/{id}

Response:
{
  "id": "client_id",
  "name": "EMPRESA LTDA",
  "document": "12.345.678/0001-90",
  "city": "São Paulo",
  "state": "SP",
  "taxation": "SN",
  "municipalRegistration": "123456",
  "certificateStatus": 1,
  "certificateExpireDate": "2025-12-31",
  "modules": {
    "enableModuleHubFederal": true,
    "enableModuleNFSe": true
  }
}
```

### Criar Cliente
```
POST /api/v1/clients

Request:
{
  "name": "NOVA EMPRESA LTDA",
  "document": "98.765.432/0001-10",
  "city": "Rio de Janeiro",
  "state": "RJ",
  "taxation": "LP",
  "municipalRegistration": "",
  "modules": {
    "enableModuleHubFederal": true
  }
}

Response:
{
  "id": "novo_client_id",
  "message": "Cliente criado com sucesso"
}
```

### Atualizar Cliente
```
PUT /api/v1/clients/{id}

Request:
{
  "name": "EMPRESA ATUALIZADA LTDA",
  "city": "Belo Horizonte"
}

Response:
{
  "message": "Cliente atualizado com sucesso"
}
```

### Atualizar Regime Tributário
```
PUT /api/v1/clients/update-regime-type/{id}

Request:
{
  "taxation": "LR"
}

Response:
{
  "message": "Regime tributário atualizado"
}
```

### Importar Clientes via Excel
```
POST /api/v1/clients/import/excel

Request:
(FormData com arquivo Excel)

Response:
{
  "imported": 50,
  "errors": []
}
```

### Deletar Certificado
```
DELETE /api/v1/clients/delete-certificate/{id}

Response:
{
  "message": "Certificado removido"
}
```

### Filiais do Cliente
```
GET /api/v1/clients/branches/{id}

Response:
[
  {
    "id": "branch_id",
    "name": "FILIAL 01",
    "document": "12.345.678/0002-71"
  }
]
```

### Buscar Notas via WebService
```
GET /api/v1/clients/search-invoices-ws/{id}

Response:
{
  "found": 150,
  "invoices": [...]
}
```

### Atualizar Módulos
```
POST /api/v1/clients/update-modules/

Request:
{
  "clientId": "client_id",
  "modules": {
    "enableModuleHubFederal": true,
    "enableModuleNFSe": false
  }
}
```

### Carregar Dados do Cliente
```
GET /api/v1/clients/load/

Response:
{
  "cities": [...],
  "regimes": [...],
  "modules": [...]
}
```

---

## 📦 COMMERCE - FEDERAL (54 endpoints)

**Domínio:** `api-federal.jettax360.com.br`

### Dashboard Federal

#### Total de Vendas
```
GET /api/v1/commerce/hub/federal/dashboard-total-sales?clientId={id}&period=month

Response:
{
  "total": 1234567.89,
  "period": "2025-11",
  "growth": 15.5
}
```

#### Top 10 Produtos
```
GET /api/v1/commerce/hub/federal/dashboard-top-products?clientId={id}

Response:
[
  {
    "product": "PRODUTO A",
    "quantity": 1000,
    "total": 50000.00
  },
  ...
]
```

#### Top 10 Clientes
```
GET /api/v1/commerce/hub/federal/dashboard-top-clients?clientId={id}

Response:
[
  {
    "client": "CLIENTE XYZ",
    "total": 100000.00,
    "invoices": 50
  },
  ...
]
```

#### PIS/COFINS
```
GET /api/v1/commerce/hub/federal/dashboard-pis-cofins?clientId={id}

Response:
{
  "pis": 12345.67,
  "cofins": 56789.01,
  "period": "2025-11"
}
```

### Autenticidade

```
GET /api/v1/commerce/authenticity/list?clientId={id}&page=1

Response:
{
  "data": [
    {
      "id": "auth_id",
      "documentKey": "35251112345678000190550010000001234567890123",
      "status": "pending",
      "type": "NFE"
    }
  ]
}
```

### Categorias

#### Listar Categorias
```
GET /api/v1/commerce/categories/list?clientId={id}

Response:
[
  {
    "id": "cat_id",
    "name": "Revenda",
    "code": "01",
    "active": true
  }
]
```

#### Criar Categoria
```
POST /api/v1/commerce/categories/

Request:
{
  "clientId": "client_id",
  "name": "Uso e Consumo",
  "code": "02"
}
```

#### Atualizar Categoria
```
PUT /api/v1/commerce/categories/{id}

Request:
{
  "name": "Revenda de Mercadorias"
}
```

#### Deletar Categoria
```
DELETE /api/v1/commerce/categories/{id}

Response:
{
  "message": "Categoria removida"
}
```

### Regras de Categorização

```
GET /api/v1/commerce/categories/rule/list?clientId={id}

Response:
[
  {
    "id": "rule_id",
    "ncm": "12345678",
    "category": "Revenda",
    "active": true
  }
]
```

### Regras PIS/COFINS

#### Listar Regras
```
GET /api/v1/commerce/hub/pis-cofins-rules/list?clientId={id}

Response:
[
  {
    "id": "rule_id",
    "ncm": "12345678",
    "cst": "01",
    "pisRate": 1.65,
    "cofinsRate": 7.6,
    "regime": "cumulativo"
  }
]
```

#### Criar Regra
```
POST /api/v1/commerce/hub/pis-cofins-rules/

Request:
{
  "clientId": "client_id",
  "ncm": "12345678",
  "pisRate": 1.65,
  "cofinsRate": 7.6,
  "regime": "cumulativo"
}
```

#### Deletar Regra
```
DELETE /api/v1/commerce/hub/pis-cofins-rules/delete/

Request:
{
  "ids": ["rule_id_1", "rule_id_2"]
}
```

### Auditoria e Reprocessamento

```
GET /api/v1/commerce/audit-reprocess/?clientId={id}

Response:
{
  "data": [
    {
      "id": "audit_id",
      "status": "completed",
      "processedInvoices": 1000,
      "errors": 0
    }
  ]
}
```

```
GET /api/v1/commerce/audit-reprocess-details/{id}

Response:
{
  "data": [
    {
      "client": { "name": "...", "document": "..." },
      "status": { "label": "Finalizado", "color": "success" }
    }
  ]
}
```

### Relatórios

```
GET /api/v1/commerce/hub/reports/list?clientId={id}&type=pis_cofins

Response:
[
  {
    "id": "report_id",
    "type": "pis_cofins",
    "period": "2025-11",
    "status": "completed",
    "downloadUrl": "..."
  }
]
```

```
DELETE /api/v1/commerce/hub/reports/delete/{id}
```

---

## 📊 FISCAL (36 endpoints)

**Domínio:** `api.jettax360.com.br`

### Dashboard Fiscal

```
GET /api/v1/fiscal/dashboard?clientId={id}

Response:
{
  "icmsSt": 12345.67,
  "das": 5678.90,
  "dctfWeb": 9876.54
}
```

### Apurações ICMS-ST

```
GET /api/v1/fiscal/summaries/icms-st/?clientId={id}&referenceMonth=2025-11

Response:
{
  "data": [
    {
      "id": "apuracao_id",
      "clientId": "client_id",
      "referenceMonth": "2025-11",
      "status": "processed",
      "totalIcmsSt": 12345.67,
      "totalBase": 100000.00
    }
  ]
}
```

```
POST /api/v1/fiscal/summaries/icms-st/batch-reprocess/

Request:
{
  "clientIds": ["client_id_1", "client_id_2"],
  "referenceMonth": "2025-11"
}
```

### DAS (Simples Nacional)

```
GET /api/v1/fiscal/das/list?clientId={id}&referenceMonth=2025-11

Response:
[
  {
    "id": "das_id",
    "clientId": "client_id",
    "referenceMonth": "2025-11",
    "totalValue": 5678.90,
    "dueDate": "2025-12-20",
    "status": "pending"
  }
]
```

```
GET /api/v1/fiscal/das/annex/{clientId}

Response:
{
  "annex": "I",
  "description": "Comércio"
}
```

### DCTF-Web

```
GET /api/v1/fiscal/summaries/dctfweb/?clientId={id}&referenceMonth=2025-11

Response:
{
  "data": [
    {
      "id": "dctf_id",
      "totalValue": 9876.54,
      "status": "pending"
    }
  ]
}
```

```
POST /api/v1/fiscal/summaries/dctfweb/batch-reprocess

Request:
{
  "clientIds": ["..."],
  "referenceMonth": "2025-11"
}
```

### Auditorias

```
GET /api/v1/fiscal/audits?clientId={id}

Response:
[
  {
    "id": "audit_id",
    "type": "ICMS-ST",
    "status": "completed",
    "issues": 0
  }
]
```

---

## 📥 HUB - DOWNLOADS (24 endpoints)

**Domínio:** `api.jettax360.com.br`

### Listar Downloads

```
GET /api/v1/hub/download/list?type=NFE&status=completed

Response:
{
  "data": [
    {
      "id": "download_id",
      "clientId": "client_id",
      "type": "NFE",
      "status": "completed",
      "url": "https://storage.jettax360.com.br/downloads/arquivo.zip",
      "createdAt": "2025-11-21T10:00:00Z",
      "expiresAt": "2025-11-22T10:00:00Z"
    }
  ]
}
```

### Downloads do Cliente

```
GET /api/v1/hub/download/clients/{id}?startDate=2025-11-01&endDate=2025-11-30

Response:
{
  "hasNewDocuments": true,
  "downloads": [...]
}
```

### Solicitar Download

```
POST /api/v1/hub/download

Request:
{
  "clientId": "client_id",
  "type": "NFE",
  "startDate": "2025-11-01",
  "endDate": "2025-11-30"
}

Response:
{
  "id": "download_id",
  "status": "processing"
}
```

### Status do Download

```
GET /api/v1/hub/download/{id}

Response:
{
  "id": "download_id",
  "status": "completed",
  "url": "https://...",
  "progress": 100
}
```

### Pendências

```
GET /api/v1/hub/pendencies/list/?clientId={id}

Response:
[
  {
    "id": "pend_id",
    "type": "missing_certificate",
    "description": "Certificado vencido",
    "priority": "high"
  }
]
```

---

## 👥 GRUPOS/CLUSTERS (6 endpoints)

**Domínio:** `api.jettax360.com.br`

```
GET /api/v1/clusters/

Response:
[
  {
    "id": "cluster_id",
    "name": "Simples Nacional",
    "clientCount": 50
  }
]
```

```
POST /api/v1/clusters/

Request:
{
  "name": "Lucro Presumido",
  "clientIds": ["client_id_1", "client_id_2"]
}
```

```
GET /api/v1/clusters/{id}

Response:
{
  "id": "cluster_id",
  "name": "Simples Nacional",
  "clients": [...]
}
```

```
POST /api/v1/clusters/delete

Request:
{
  "id": "cluster_id"
}
```

---

## 👤 USUÁRIOS (4 endpoints)

```
GET /api/v1/users?page=1&name=&email=&status=&client=&role=

Response:
{
  "data": [
    {
      "id": "user_id",
      "name": "João Silva",
      "email": "joao@empresa.com",
      "role": "admin",
      "status": "active"
    }
  ]
}
```

```
GET /api/v1/users/{id}

Response:
{
  "id": "user_id",
  "name": "João Silva",
  "email": "joao@empresa.com",
  "clients": [...]
}
```

---

## 🔔 NOTIFICAÇÕES (3 endpoints)

```
GET /api/v1/notifications?page=1

Response:
{
  "data": [
    {
      "id": "notif_id",
      "type": "certificate_expiring",
      "message": "Certificado de EMPRESA XYZ vence em 15 dias",
      "read": false,
      "createdAt": "2025-11-21T10:00:00Z"
    }
  ]
}
```

```
POST /api/v1/notifications/read

Request:
{
  "notificationId": "notif_id"
}
```

---

## 🏢 ESCRITÓRIO/OFFICE (8 endpoints)

```
GET /api/v1/offices/load

Response:
{
  "id": "office_id",
  "name": "Escritório Contábil XYZ",
  "document": "12.345.678/0001-90"
}
```

```
GET /api/v1/offices/credentials

Response:
[
  {
    "id": "cred_id",
    "client": "EMPRESA ABC",
    "type": "certificate",
    "status": "valid",
    "expiresAt": "2025-12-31"
  }
]
```

```
GET /api/v1/offices/has-certificate

Response:
{
  "hasCertificate": true,
  "expiresAt": "2025-12-31"
}
```

---

## 🛠️ UTILIDADES (4 endpoints)

```
GET /api/v1/utils/load-global-data

Response:
{
  "cities": [...],
  "states": [...],
  "regimes": [...]
}
```

```
GET /api/v1/utils/search-document/{cnpj}

Response:
{
  "document": "12.345.678/0001-90",
  "name": "EMPRESA LTDA",
  "address": "..."
}
```

```
GET /api/v1/utils/search-address/{cep}

Response:
{
  "cep": "01234-567",
  "street": "Rua Exemplo",
  "city": "São Paulo",
  "state": "SP"
}
```

---

## 📋 AGENDAMENTOS (1 endpoint)

```
GET /api/v1/schedules/load

Response:
[
  {
    "id": "schedule_id",
    "type": "download_nfe",
    "frequency": "daily",
    "time": "08:00",
    "active": true
  }
]
```

---

## 📢 OUTROS ENDPOINTS

### Bulletins
```
GET /api/v1/bulletins/notify

Response:
{
  "hasNewBulletins": true,
  "count": 5
}
```

### Email
```
GET /api/v1/email/getAll

Response:
[
  {
    "id": "email_id",
    "subject": "Notificação Fiscal",
    "from": "sistema@jettax360.com.br"
  }
]
```

### Calls
```
GET /api/v1/calls/notification

Response:
{
  "hasNewCalls": false
}
```

---

## 🌐 DOMÍNIOS E DISTRIBUIÇÃO

### Distribuição de Endpoints por Domínio

- **api.jettax360.com.br**: 110 endpoints (65%)
- **api-federal.jettax360.com.br**: 54 endpoints (32%)
- **api-auth.jettax360.com.br**: 3 endpoints (2%)
- **admin.jettax360.com.br**: 2 endpoints (1%)
- **Outros**: 1 endpoint (<1%)

### Distribuição por Método HTTP

- **GET**: 122 endpoints (72%)
- **POST**: 34 endpoints (20%)
- **PUT**: 8 endpoints (5%)
- **DELETE**: 6 endpoints (3%)

---

## 📝 NOTAS DE USO

### Headers Obrigatórios

Todas as requisições (exceto login) requerem:

```
Authorization: Bearer {token}
Content-Type: application/json
```

### Paginação Padrão

Endpoints paginados usam:
```
?page=1&limit=20
```

Response:
```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

### IDs e Normalização

- **{id}**: IDs são strings (MongoDB ObjectId ou UUID)
- **URLs normalizadas**: `/api/v1/resource/{id}` (IDs substituídos por `{id}` no catálogo)

### Status Codes

- **200**: Sucesso
- **201**: Criado
- **202**: Aceito (processamento assíncrono)
- **204**: Sem conteúdo (deletado com sucesso)
- **400**: Requisição inválida
- **401**: Não autenticado
- **403**: Sem permissão
- **404**: Não encontrado
- **422**: Erro de validação
- **500**: Erro do servidor

---

**Arquivo JSON Completo:** `CATALOGO_COMPLETO_ENDPOINTS.json` (2631 linhas)

**Última Atualização:** 21/11/2025
