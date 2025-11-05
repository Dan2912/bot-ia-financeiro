import aiohttp
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class PluggyClient:
    """Cliente para integração com a API Pluggy"""
    
    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.pluggy.ai" if not sandbox else "https://api.sandbox.pluggy.ai"
        self.api_key = None
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self):
        """Autenticar com a API Pluggy"""
        auth_data = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }
        
        async with self.session.post(
            f"{self.base_url}/auth",
            json=auth_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                self.api_key = data.get("apiKey")
                logger.info("Autenticação Pluggy realizada com sucesso")
            else:
                error_text = await response.text()
                logger.error(f"Erro na autenticação Pluggy: {response.status} - {error_text}")
                raise Exception(f"Falha na autenticação: {response.status}")
    
    async def get_connectors(self) -> List[Dict]:
        """Buscar lista de bancos/conectores disponíveis"""
        headers = {"X-API-KEY": self.api_key}
        
        async with self.session.get(
            f"{self.base_url}/connectors",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("results", [])
            else:
                logger.error(f"Erro ao buscar conectores: {response.status}")
                return []
    
    async def create_connect_token(self, connector_id: str, user_id: str) -> Dict:
        """Criar token para conexão com banco"""
        headers = {"X-API-KEY": self.api_key}
        
        connect_data = {
            "itemId": None,  # Para nova conexão
            "connectorId": connector_id,
            "options": {
                "clientUserId": str(user_id)
            }
        }
        
        async with self.session.post(
            f"{self.base_url}/connect_token",
            headers=headers,
            json=connect_data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                logger.error(f"Erro ao criar connect token: {response.status} - {error_text}")
                return {}

    async def create_connect_token_generic(self, user_id: str) -> Dict:
        """Criar token genérico para conexão (usuário escolhe o banco no Pluggy Connect)"""
        headers = {"X-API-KEY": self.api_key}
        
        connect_data = {
            "itemId": None,  # Para nova conexão
            "options": {
                "clientUserId": str(user_id),
                "webhookUrl": None  # Webhook opcional para notificações
            }
        }
        
        async with self.session.post(
            f"{self.base_url}/connect_token",
            headers=headers,
            json=connect_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"Connect token criado para usuário {user_id}")
                return result
            else:
                error_text = await response.text()
                logger.error(f"Erro ao criar connect token genérico: {response.status} - {error_text}")
                return {}
    
    async def get_items(self, client_user_id: str) -> List[Dict]:
        """Buscar itens (conexões) do usuário"""
        headers = {"X-API-KEY": self.api_key}
        
        params = {"clientUserId": client_user_id}
        
        async with self.session.get(
            f"{self.base_url}/items",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("results", [])
            else:
                logger.error(f"Erro ao buscar items: {response.status}")
                return []
    
    async def get_accounts(self, item_id: str) -> List[Dict]:
        """Buscar contas de um item específico"""
        headers = {"X-API-KEY": self.api_key}
        
        params = {"itemId": item_id}
        
        async with self.session.get(
            f"{self.base_url}/accounts",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("results", [])
            else:
                logger.error(f"Erro ao buscar contas: {response.status}")
                return []
    
    async def get_transactions(self, account_id: str, from_date: str = None, to_date: str = None) -> List[Dict]:
        """Buscar transações de uma conta"""
        headers = {"X-API-KEY": self.api_key}
        
        params = {"accountId": account_id}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        async with self.session.get(
            f"{self.base_url}/transactions",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("results", [])
            else:
                logger.error(f"Erro ao buscar transações: {response.status}")
                return []
    
    async def get_credit_cards(self, item_id: str) -> List[Dict]:
        """Buscar cartões de crédito"""
        headers = {"X-API-KEY": self.api_key}
        
        params = {"itemId": item_id}
        
        async with self.session.get(
            f"{self.base_url}/credit-cards",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("results", [])
            else:
                logger.error(f"Erro ao buscar cartões: {response.status}")
                return []
    
    async def update_item(self, item_id: str) -> Dict:
        """Forçar atualização de um item"""
        headers = {"X-API-KEY": self.api_key}
        
        async with self.session.patch(
            f"{self.base_url}/items/{item_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Erro ao atualizar item: {response.status}")
                return {}


# Exemplo de uso
async def example_usage():
    """Exemplo de como usar o cliente Pluggy"""
    client_id = os.getenv("PLUGGY_CLIENT_ID")
    client_secret = os.getenv("PLUGGY_CLIENT_SECRET")
    sandbox = os.getenv("PLUGGY_SANDBOX", "true").lower() == "true"
    
    async with PluggyClient(client_id, client_secret, sandbox) as pluggy:
        # Listar bancos disponíveis
        connectors = await pluggy.get_connectors()
        print(f"Bancos disponíveis: {len(connectors)}")
        
        # Para um usuário específico
        user_id = "123456"
        
        # Buscar conexões do usuário
        items = await pluggy.get_items(user_id)
        
        for item in items:
            print(f"Conexão: {item['connector']['name']}")
            
            # Buscar contas
            accounts = await pluggy.get_accounts(item['id'])
            
            for account in accounts:
                print(f"  Conta: {account['name']} - R$ {account['balance']}")
                
                # Buscar transações
                transactions = await pluggy.get_transactions(account['id'])
                print(f"    Transações: {len(transactions)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())