"""
Cliente da API JETTAX 360
"""
import os
import time
from typing import Optional, Dict, Any, List
import requests
from pathlib import Path
from dotenv import load_dotenv

from ..utils.logger import get_logger
from ..utils.cnpj_utils import somente_digitos, formatar_cnpj

logger = get_logger()


class JettaxAPIError(Exception):
    """Erro específico da API JETTAX"""
    pass


class JettaxAPI:
    """Cliente para comunicação com a API JETTAX 360"""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        auth_url: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Inicializa cliente da API
        
        Args:
            api_url: URL base da API (usa .env se não fornecido)
            auth_url: URL de autenticação (usa .env se não fornecido)
            email: E-mail do escritório (usa .env se não fornecido)
            password: Senha do escritório (usa .env se não fornecido)
            timeout: Timeout para requisições em segundos
            max_retries: Número máximo de tentativas em caso de erro
        """
        # Carregar variáveis de ambiente
        load_dotenv(Path(__file__).parent.parent.parent / "config" / ".env")
        
        self.api_url = (api_url or os.getenv("JETTAX_API_URL", "https://api.jettax360.com.br")).rstrip("/")
        self.auth_url = (auth_url or os.getenv("JETTAX_AUTH_URL", "https://api-auth.jettax360.com.br")).rstrip("/")
        self.email = email or os.getenv("JETTAX_EMAIL")
        self.password = password or os.getenv("JETTAX_PASSWORD")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Session HTTP
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "JettaxAutomation/1.0"
        })
        
        # Token de autenticação (será preenchido no login)
        self._token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
    
    def _ensure_auth(self) -> None:
        """Garante que há um token válido de autenticação"""
        # Se já tem token válido, não faz nada
        if self._token and self._token_expires_at and time.time() < self._token_expires_at:
            return
        
        # Fazer login
        self._login()
    
    def _login(self) -> None:
        """Realiza login na API JETTAX"""
        if not self.email or not self.password:
            raise JettaxAPIError(
                "Credenciais não configuradas. Defina JETTAX_EMAIL e JETTAX_PASSWORD no .env"
            )
        
        url = f"{self.auth_url}/api/jettax360/v1/auth/office/login"
        payload = {
            "email": self.email,
            "password": self.password,
            "isCheckMFA": False
        }
        
        logger.info(f"Autenticando no JETTAX como {self.email}...")
        
        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise JettaxAPIError(f"Erro ao fazer login: {e}")
        
        # Extrair token do header Authorization
        token = resp.headers.get("Authorization")
        if token and token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1].strip()
        else:
            # Tentar extrair do corpo da resposta
            data = resp.json()
            token = data.get("access_token")
        
        if not token:
            raise JettaxAPIError("Token não encontrado na resposta de login")
        
        self._token = token
        self.session.headers["Authorization"] = f"Bearer {token}"
        
        # Definir expiração (1 hora)
        self._token_expires_at = time.time() + 3600
        
        logger.info("✓ Autenticação realizada com sucesso")
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> requests.Response:
        """
        Faz requisição HTTP com retry automático
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API (ex: /api/v1/clients)
            params: Parâmetros de query string
            json_data: Dados JSON para enviar no body
            retry_count: Contador interno de tentativas
        
        Returns:
            Objeto Response
        """
        self._ensure_auth()
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            resp = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout
            )
            
            # Se 401/403, tentar reautenticar
            if resp.status_code in (401, 403) and retry_count < self.max_retries:
                logger.warning("Token expirado, reautenticando...")
                self._token = None
                self._login()
                return self._request(method, endpoint, params, json_data, retry_count + 1)
            
            resp.raise_for_status()
            return resp
            
        except requests.exceptions.RequestException as e:
            if retry_count < self.max_retries:
                logger.warning(f"Erro na requisição, tentando novamente ({retry_count + 1}/{self.max_retries})...")
                time.sleep(2 ** retry_count)  # Backoff exponencial
                return self._request(method, endpoint, params, json_data, retry_count + 1)
            
            raise JettaxAPIError(f"Erro na requisição: {e}")
    
    # ============================================================================
    # CLIENTES
    # ============================================================================
    
    def listar_clientes(self, limit: int = 50, page: int = 1) -> Dict[str, Any]:
        """
        Lista clientes do escritório (paginado)
        
        Args:
            limit: Número de resultados por página
            page: Número da página
        
        Returns:
            Dict com 'data' (lista de clientes) e 'meta' (paginação)
        """
        params = {
            "page": page,
            "limit": limit,
            "status": "",  # Todas (ativas e inativas)
            "name": "",
            "document": "",
            "city": "",
            "municipalRegistration": "",
            "excel": "",
            "validCertificate": "",
            "simpleOptionInfo": "",
            "certificateStatus": "",
            "certificateType": "",
            "taxation": ""
        }
        
        resp = self._request("GET", "/api/v1/clients", params=params)
        return resp.json()
    
    def listar_todos_clientes(self) -> List[Dict[str, Any]]:
        """
        Lista TODOS os clientes (faz paginação automática)
        
        Returns:
            Lista completa de clientes
        """
        logger.info("Carregando todos os clientes do JETTAX...")
        
        all_clients = []
        page = 1
        
        while True:
            try:
                result = self.listar_clientes(limit=50, page=page)
                clients = result.get("data", [])
                
                if not clients:
                    break
                
                all_clients.extend(clients)
                
                # Verificar se há mais páginas
                meta = result.get("meta", {})
                pagination = meta.get("pagination", {})
                total_pages = pagination.get("total_pages", 1)
                
                logger.debug(f"Página {page}/{total_pages} carregada ({len(clients)} empresas)")
                
                if page >= total_pages:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Erro ao carregar página {page}: {e}")
                break
        
        logger.info(f"✓ {len(all_clients)} clientes carregados")
        return all_clients
    
    def buscar_cliente_por_cnpj(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """
        Busca um cliente específico por CNPJ
        
        Args:
            cnpj: CNPJ com ou sem máscara
        
        Returns:
            Dados do cliente ou None se não encontrado
        """
        cnpj_digitos = somente_digitos(cnpj)
        
        # Buscar em todas as empresas
        clientes = self.listar_todos_clientes()
        
        for cliente in clientes:
            doc = somente_digitos(str(cliente.get("document", "")))
            if doc == cnpj_digitos:
                return cliente
        
        return None
    
    def obter_cliente(self, client_id: str) -> Dict[str, Any]:
        """
        Obtém dados completos de um cliente por ID
        
        IMPORTANTE: Retorna o objeto COMPLETO do cliente (59 campos).
        Este objeto deve ser usado para fazer PUT /api/v1/clients/{id}
        
        Args:
            client_id: ID do cliente no JETTAX
        
        Returns:
            Dados completos do cliente (objeto com 59 campos)
        """
        resp = self._request("GET", f"/api/v1/clients/{client_id}")
        result = resp.json()
        
        # API retorna {data: {...}} - extrair o objeto data
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        
        return result
    
    def criar_cliente(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo cliente no JETTAX
        
        Args:
            payload: Dados do cliente no formato da API
        
        Returns:
            Resposta da API (com ID do cliente criado)
        """
        logger.info(f"Criando cliente {payload.get('document')} - {payload.get('name')}")
        
        resp = self._request("POST", "/api/v1/clients", json_data=payload)
        result = resp.json()
        
        logger.info(f"✓ Cliente criado com sucesso (ID: {result.get('id', 'N/A')})")
        return result
    
    def atualizar_cliente(self, client_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza um cliente existente
        
        Args:
            client_id: ID do cliente no JETTAX
            payload: Dados atualizados do cliente
        
        Returns:
            Resposta da API
        """
        logger.info(f"Atualizando cliente {client_id}")
        
        resp = self._request("PUT", f"/api/v1/clients/{client_id}", json_data=payload)
        result = resp.json()
        
        logger.info(f"✓ Cliente atualizado com sucesso")
        return result
    
    # ============================================================================
    # UTILITÁRIOS
    # ============================================================================
    
    def consultar_cnpj_receita(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """
        Consulta dados de um CNPJ na Receita Federal (via API JETTAX)
        
        Args:
            cnpj: CNPJ apenas com dígitos
        
        Returns:
            Dados do CNPJ ou None se não encontrado
        """
        logger.debug(f"Consultando CNPJ {formatar_cnpj(cnpj)} na Receita Federal...")
        
        try:
            resp = self._request("GET", f"/api/v1/utils/search-document/{cnpj}")
            data = resp.json()
            
            # Normalizar resposta
            if isinstance(data, dict) and "item" in data:
                return data["item"]
            
            return data
            
        except Exception as e:
            logger.warning(f"Erro ao consultar CNPJ {formatar_cnpj(cnpj)}: {e}")
            return None
    
    def buscar_codigo_ibge(self, cidade: str, uf: str) -> Optional[int]:
        """
        Busca código IBGE de uma cidade
        
        Args:
            cidade: Nome da cidade
            uf: UF (2 letras)
        
        Returns:
            Código IBGE ou None se não encontrado
        """
        try:
            params = {"name": cidade, "state": uf}
            resp = self._request("GET", "/api/v1/ibge/cities", params=params)
            
            cidades = resp.json()
            
            if isinstance(cidades, list) and len(cidades) > 0:
                first = cidades[0]
                code = first.get("ibgeCode") or first.get("code")
                return int(code) if code else None
            
            return None
            
        except Exception as e:
            logger.warning(f"Erro ao buscar código IBGE para {cidade}/{uf}: {e}")
            return None
    
    def listar_regimes_tributarios(self) -> List[Dict[str, Any]]:
        """
        Lista todos os regimes tributários disponíveis no JETTAX
        
        Returns:
            Lista de regimes com id e nome
        """
        try:
            resp = self._request("GET", "/api/v1/tax-regimes")
            return resp.json()
        except Exception as e:
            logger.error(f"Erro ao listar regimes tributários: {e}")
            return []
    
    def buscar_regime_por_nome(self, nome: str) -> Optional[str]:
        """
        Busca ObjectId de um regime tributário pelo nome
        
        Args:
            nome: Nome do regime (ex: "Simples Nacional - Serviços")
        
        Returns:
            ObjectId do regime ou None se não encontrado
        """
        regimes = self.listar_regimes_tributarios()
        
        nome_normalizado = nome.lower().strip()
        
        for regime in regimes:
            regime_nome = str(regime.get("name") or regime.get("description") or "").lower().strip()
            
            # Busca exata
            if regime_nome == nome_normalizado:
                return regime.get("id") or regime.get("_id")
            
            # Busca parcial
            if nome_normalizado in regime_nome or regime_nome in nome_normalizado:
                return regime.get("id") or regime.get("_id")
        
        return None
