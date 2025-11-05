"""
Sistema de Contas Bancárias Predefinidas
Substitui a integração Pluggy por sistema manual
"""
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class AccountManager:
    """Gerenciador de contas bancárias predefinidas"""
    
    def __init__(self):
        self.predefined_accounts = {
            # Inter
            'inter_pf': {
                'name': 'Banco Inter PF',
                'type': 'Pessoa Física',
                'bank_code': 'INTER',
                'color': '🟡',
                'is_revenue_account': True,  # Conta de receita
                'account_types': ['Conta Corrente', 'Conta Poupança']
            },
            'inter_pj': {
                'name': 'Banco Inter PJ',
                'type': 'Pessoa Jurídica', 
                'bank_code': 'INTER',
                'color': '🟡',
                'is_revenue_account': True,  # Conta de receita
                'account_types': ['Conta Corrente', 'Conta Poupança']
            },
            
            # C6 Bank
            'c6_pf': {
                'name': 'C6 Bank PF',
                'type': 'Pessoa Física',
                'bank_code': 'C6',
                'color': '⚫',
                'is_revenue_account': False,
                'account_types': ['Conta Corrente', 'Conta Poupança']
            },
            'c6_pj': {
                'name': 'C6 Bank PJ', 
                'type': 'Pessoa Jurídica',
                'bank_code': 'C6',
                'color': '⚫',
                'is_revenue_account': False,
                'account_types': ['Conta Corrente', 'Conta Poupança']
            },
            
            # Nubank
            'nubank_pf': {
                'name': 'Nubank PF',
                'type': 'Pessoa Física',
                'bank_code': 'NUBANK',
                'color': '💜',
                'is_revenue_account': False,
                'account_types': ['Conta Corrente', 'Conta Poupança']
            },
            'nubank_pj': {
                'name': 'Nubank PJ',
                'type': 'Pessoa Jurídica', 
                'bank_code': 'NUBANK',
                'color': '💜',
                'is_revenue_account': False,
                'account_types': ['Conta Corrente', 'Conta Poupança']
            },
            
            # Santander
            'santander_pf': {
                'name': 'Santander PF',
                'type': 'Pessoa Física',
                'bank_code': 'SANTANDER',
                'color': '🔴',
                'is_revenue_account': False,
                'account_types': ['Conta Corrente', 'Conta Poupança']
            },
            'santander_pj': {
                'name': 'Santander PJ',
                'type': 'Pessoa Jurídica',
                'bank_code': 'SANTANDER', 
                'color': '🔴',
                'is_revenue_account': False,
                'account_types': ['Conta Corrente', 'Conta Poupança']
            }
        }
    
    def get_all_accounts(self) -> Dict:
        """Retornar todas as contas predefinidas"""
        return self.predefined_accounts
    
    def get_revenue_accounts(self) -> Dict:
        """Retornar apenas contas de receita (Inter PF e PJ)"""
        return {
            key: account for key, account in self.predefined_accounts.items()
            if account['is_revenue_account']
        }
    
    def get_expense_accounts(self) -> Dict:
        """Retornar contas para despesas (todas exceto receita)"""
        return {
            key: account for key, account in self.predefined_accounts.items()
            if not account['is_revenue_account']
        }
    
    def get_account_by_key(self, key: str) -> Optional[Dict]:
        """Buscar conta específica por chave"""
        return self.predefined_accounts.get(key)
    
    def format_account_list(self, accounts: Dict, for_selection: bool = True) -> str:
        """Formatar lista de contas para exibição"""
        if not accounts:
            return "Nenhuma conta disponível"
        
        text = ""
        for key, account in accounts.items():
            icon = account['color']
            name = account['name']
            type_text = account['type']
            
            if for_selection:
                text += f"{icon} {name} ({type_text})\n"
            else:
                text += f"{icon} **{name}**\n"
                text += f"   Tipo: {type_text}\n"
                text += f"   Banco: {account['bank_code']}\n\n"
        
        return text
    
    def get_account_keyboard(self, accounts: Dict) -> List[List]:
        """Gerar teclado inline para seleção de contas"""
        from telegram import InlineKeyboardButton
        
        keyboard = []
        for key, account in accounts.items():
            icon = account['color']
            name = account['name']
            button = InlineKeyboardButton(
                f"{icon} {name}",
                callback_data=f"select_account_{key}"
            )
            keyboard.append([button])
        
        return keyboard

# Instância global do gerenciador
account_manager = AccountManager()