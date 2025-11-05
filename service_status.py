import asyncio
import aiohttp
import ssl
import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)

class ServiceStatus:
    """Classe para verificar status dos serviços externos"""
    
    def __init__(self):
        self.services = {
            'pluggy_api': 'https://api.sandbox.pluggy.ai/health',
            'pluggy_connect': 'https://connect.sandbox.pluggy.ai',
            'openai_api': 'https://api.openai.com/v1/models'
        }
    
    async def check_service_health(self, service_name: str, url: str) -> Dict:
        """Verificar saúde de um serviço específico"""
        try:
            # Configurar SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            
            async with aiohttp.ClientSession(
                connector=connector, 
                timeout=timeout
            ) as session:
                
                start_time = asyncio.get_event_loop().time()
                
                async with session.get(url) as response:
                    response_time = round(
                        (asyncio.get_event_loop().time() - start_time) * 1000, 2
                    )
                    
                    status = {
                        'service': service_name,
                        'status': 'online' if response.status < 500 else 'degraded',
                        'status_code': response.status,
                        'response_time_ms': response_time,
                        'error': None
                    }
                    
                    if response.status >= 400:
                        status['status'] = 'error'
                        status['error'] = f"HTTP {response.status}"
                    
                    return status
                    
        except asyncio.TimeoutError:
            return {
                'service': service_name,
                'status': 'timeout',
                'status_code': None,
                'response_time_ms': None,
                'error': 'Timeout de conexão'
            }
        except Exception as e:
            return {
                'service': service_name,
                'status': 'offline',
                'status_code': None,
                'response_time_ms': None,
                'error': str(e)
            }
    
    async def check_all_services(self) -> Dict:
        """Verificar status de todos os serviços"""
        results = {}
        
        for service_name, url in self.services.items():
            results[service_name] = await self.check_service_health(service_name, url)
        
        return results
    
    async def check_pluggy_credentials(self) -> Dict:
        """Verificar se as credenciais Pluggy estão configuradas"""
        client_id = os.getenv('PLUGGY_CLIENT_ID')
        client_secret = os.getenv('PLUGGY_CLIENT_SECRET')
        
        return {
            'pluggy_credentials': {
                'client_id_configured': bool(client_id),
                'client_secret_configured': bool(client_secret),
                'status': 'configured' if (client_id and client_secret) else 'missing'
            }
        }
    
    def format_status_message(self, status_results: Dict) -> str:
        """Formatar mensagem de status para o usuário"""
        message = "🔍 **Status dos Serviços**\n\n"
        
        # Pluggy API
        pluggy_status = status_results.get('pluggy_api', {})
        pluggy_icon = self._get_status_icon(pluggy_status.get('status'))
        message += f"{pluggy_icon} **Pluggy API**: {pluggy_status.get('status', 'unknown').title()}\n"
        
        if pluggy_status.get('error'):
            message += f"   ❌ {pluggy_status['error']}\n"
        elif pluggy_status.get('response_time_ms'):
            message += f"   ⚡ {pluggy_status['response_time_ms']}ms\n"
        
        # Pluggy Connect
        connect_status = status_results.get('pluggy_connect', {})
        connect_icon = self._get_status_icon(connect_status.get('status'))
        message += f"{connect_icon} **Pluggy Connect**: {connect_status.get('status', 'unknown').title()}\n"
        
        # OpenAI
        openai_status = status_results.get('openai_api', {})
        openai_icon = self._get_status_icon(openai_status.get('status'))
        message += f"{openai_icon} **OpenAI API**: {openai_status.get('status', 'unknown').title()}\n"
        
        # Credenciais
        creds = status_results.get('pluggy_credentials', {})
        if creds.get('status') == 'configured':
            message += "🔑 **Credenciais**: ✅ Configuradas\n"
        else:
            message += "🔑 **Credenciais**: ❌ Não configuradas\n"
        
        # Status geral
        message += "\n📊 **Status Geral:**\n"
        
        if self._all_services_ok(status_results):
            message += "✅ Todos os serviços funcionando normalmente\n"
            message += "🏦 Conexão bancária disponível"
        elif self._pluggy_available(status_results):
            message += "⚠️ Alguns serviços com problemas\n"
            message += "🏦 Conexão bancária limitada"
        else:
            message += "❌ Serviços principais indisponíveis\n"
            message += "🏦 Conexão bancária em manutenção\n"
            message += "\n💡 **Use funcionalidades offline:**\n"
            message += "• /despesas - Cadastrar gastos manualmente\n"
            message += "• /metas - Definir objetivos financeiros\n"
            message += "• /resumo - Ver análises locais"
        
        return message
    
    def _get_status_icon(self, status: str) -> str:
        """Obter ícone baseado no status"""
        icons = {
            'online': '🟢',
            'degraded': '🟡',
            'error': '🔴',
            'offline': '⚫',
            'timeout': '⏱️'
        }
        return icons.get(status, '❓')
    
    def _all_services_ok(self, status_results: Dict) -> bool:
        """Verificar se todos os serviços estão OK"""
        for service_name, result in status_results.items():
            if service_name == 'pluggy_credentials':
                continue
            if result.get('status') not in ['online', 'degraded']:
                return False
        return True
    
    def _pluggy_available(self, status_results: Dict) -> bool:
        """Verificar se pelo menos o Pluggy está disponível"""
        pluggy_api = status_results.get('pluggy_api', {})
        return pluggy_api.get('status') in ['online', 'degraded']

# Instância global
service_status = ServiceStatus()