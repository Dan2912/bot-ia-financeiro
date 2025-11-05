"""
Sistema de Receitas com UX Guiada
Interface estruturada para cadastro de receitas
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from typing import Dict, List
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

# Estados da conversa
WAITING_REVENUE_TYPE = 'waiting_revenue_type'
WAITING_REVENUE_DESCRIPTION = 'waiting_revenue_description'
WAITING_REVENUE_VALUE = 'waiting_revenue_value'
WAITING_REVENUE_DATE = 'waiting_revenue_date'
WAITING_REVENUE_ACCOUNT = 'waiting_revenue_account'
WAITING_REVENUE_FREQUENCY = 'waiting_revenue_frequency'
WAITING_REVENUE_CONFIRMATION = 'waiting_revenue_confirmation'

class RevenueManager:
    """Gerenciador de receitas com UX guiada"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        
        # Tipos de receita predefinidos
        self.revenue_types = {
            'salary': {
                'name': '💰 Salário',
                'description': 'Salário mensal ou pagamento de trabalho',
                'is_recurring': True,
                'default_frequency': 'monthly'
            },
            'freelance': {
                'name': '💻 Freelance',
                'description': 'Trabalho freelancer ou consultoria',
                'is_recurring': False,
                'default_frequency': 'once'
            },
            'business': {
                'name': '🏢 Faturamento Empresa',
                'description': 'Receita de vendas ou serviços da empresa',
                'is_recurring': False,
                'default_frequency': 'once'
            },
            'investment': {
                'name': '📈 Rendimentos',
                'description': 'Dividendos, juros ou ganhos de investimentos',
                'is_recurring': True,
                'default_frequency': 'monthly'
            },
            'rental': {
                'name': '🏠 Aluguel Recebido',
                'description': 'Receita de aluguel de imóveis',
                'is_recurring': True,
                'default_frequency': 'monthly'
            },
            'other': {
                'name': '💡 Outras Receitas',
                'description': 'Outras formas de receita',
                'is_recurring': False,
                'default_frequency': 'once'
            }
        }
    
    async def start_add_revenue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar processo de adição de receita"""
        user = await self.bot.get_or_create_user(update.effective_user)
        
        # Limpar dados anteriores
        context.user_data.clear()
        context.user_data['user_id'] = user['id']
        
        text = """💰 **Adicionar Nova Receita**

🎯 **Vamos cadastrar sua receita passo a passo!**

**Primeiro, escolha o tipo de receita:**

Cada tipo tem configurações específicas para facilitar o cadastro."""
        
        # Criar teclado com tipos de receita
        keyboard = []
        for key, revenue_type in self.revenue_types.items():
            keyboard.append([InlineKeyboardButton(
                revenue_type['name'],
                callback_data=f"revenue_type_{key}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_revenue")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return WAITING_REVENUE_TYPE
    
    async def process_revenue_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar seleção do tipo de receita"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_revenue":
            await query.edit_message_text("❌ Cadastro de receita cancelado.")
            return ConversationHandler.END
        
        revenue_type_key = query.data.replace("revenue_type_", "")
        revenue_type = self.revenue_types.get(revenue_type_key)
        
        if not revenue_type:
            await query.edit_message_text("❌ Tipo de receita inválido.")
            return ConversationHandler.END
        
        # Salvar dados
        context.user_data['revenue_type'] = revenue_type_key
        context.user_data['revenue_type_info'] = revenue_type
        
        text = f"""✅ **{revenue_type['name']} Selecionado**

📝 **{revenue_type['description']}**

**Agora, digite uma descrição para esta receita:**

💡 **Exemplos:**
• Para salário: "Salário - Empresa XYZ"
• Para freelance: "Projeto website cliente ABC"  
• Para empresa: "Venda de produtos - Novembro"

**Digite a descrição:**"""
        
        await query.edit_message_text(text, parse_mode='Markdown')
        return WAITING_REVENUE_DESCRIPTION
    
    async def receive_revenue_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber descrição da receita"""
        description = update.message.text.strip()
        
        if len(description) < 3:
            await update.message.reply_text(
                "❌ **Descrição muito curta!**\n\n"
                "Digite uma descrição com pelo menos 3 caracteres:"
            )
            return WAITING_REVENUE_DESCRIPTION
        
        context.user_data['description'] = description
        revenue_type = context.user_data['revenue_type_info']
        
        text = f"""✅ **Descrição salva:** {description}

💵 **Agora digite o valor da receita:**

💡 **Formatos aceitos:**
• 1500 ou 1500,00
• 2.350,50 (com pontos e vírgulas)
• 5000.00 (formato americano)

**Qual o valor desta receita?**"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return WAITING_REVENUE_VALUE
    
    async def receive_revenue_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber valor da receita"""
        value_text = update.message.text.strip()
        
        try:
            # Limpar e converter valor
            value_clean = value_text.replace('R$', '').replace(' ', '')
            value_clean = value_clean.replace('.', '').replace(',', '.')
            value = float(value_clean)
            
            if value <= 0:
                raise ValueError("Valor deve ser positivo")
                
        except (ValueError, TypeError):
            await update.message.reply_text(
                "❌ **Valor inválido!**\n\n"
                "Digite um valor numérico válido:\n"
                "• Exemplo: 1500,00\n"
                "• Exemplo: 2.350,50\n\n"
                "**Digite novamente o valor:**"
            )
            return WAITING_REVENUE_VALUE
        
        context.user_data['value'] = value
        
        text = f"""✅ **Valor salvo:** R$ {value:,.2f}

📅 **Agora digite a data desta receita:**

💡 **Formatos aceitos:**
• 15/11/2025 (dd/mm/aaaa)
• 15/11 (assumirá ano atual)
• hoje (data de hoje)
• ontem (data de ontem)

**Qual a data desta receita?**"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return WAITING_REVENUE_DATE
    
    async def receive_revenue_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber data da receita"""
        date_text = update.message.text.strip().lower()
        
        try:
            if date_text == "hoje":
                revenue_date = date.today()
            elif date_text == "ontem":
                from datetime import timedelta
                revenue_date = date.today() - timedelta(days=1)
            elif "/" in date_text:
                parts = date_text.split("/")
                if len(parts) == 2:  # dd/mm
                    day, month = int(parts[0]), int(parts[1])
                    year = date.today().year
                elif len(parts) == 3:  # dd/mm/yyyy
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    raise ValueError("Formato inválido")
                
                revenue_date = date(year, month, day)
            else:
                raise ValueError("Formato não reconhecido")
                
        except (ValueError, TypeError):
            await update.message.reply_text(
                "❌ **Data inválida!**\n\n"
                "Use um dos formatos:\n"
                "• 15/11/2025\n"
                "• 15/11 (ano atual)\n"
                "• hoje\n"
                "• ontem\n\n"
                "**Digite novamente a data:**"
            )
            return WAITING_REVENUE_DATE
        
        context.user_data['revenue_date'] = revenue_date
        
        # Prosseguir para seleção de conta (sempre Inter PF ou PJ)
        from account_manager import account_manager
        revenue_accounts = account_manager.get_revenue_accounts()
        
        text = f"""✅ **Data salva:** {revenue_date.strftime('%d/%m/%Y')}

🏦 **Escolha a conta que receberá o dinheiro:**

**💡 Contas de receita disponíveis:**
(Como definido, receitas sempre vão para contas Inter)"""
        
        keyboard = account_manager.get_account_keyboard(revenue_accounts)
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_revenue")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return WAITING_REVENUE_ACCOUNT
    
    async def process_revenue_account(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar seleção da conta de receita"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_revenue":
            await query.edit_message_text("❌ Cadastro de receita cancelado.")
            return ConversationHandler.END
        
        account_key = query.data.replace("select_account_", "")
        from account_manager import account_manager
        account = account_manager.get_account_by_key(account_key)
        
        if not account:
            await query.edit_message_text("❌ Conta inválida.")
            return ConversationHandler.END
        
        context.user_data['account_key'] = account_key
        context.user_data['account'] = account
        
        # Verificar se é receita recorrente
        revenue_type_info = context.user_data['revenue_type_info']
        
        if revenue_type_info['is_recurring']:
            text = f"""✅ **Conta selecionada:** {account['color']} {account['name']}

🔄 **Esta receita é recorrente?**

Como você selecionou "{revenue_type_info['name']}", geralmente é uma receita que se repete.

**Escolha a frequência:**"""
            
            keyboard = [
                [InlineKeyboardButton("📅 Mensal", callback_data="freq_monthly")],
                [InlineKeyboardButton("📆 Semanal", callback_data="freq_weekly")],
                [InlineKeyboardButton("🔄 Apenas uma vez", callback_data="freq_once")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_revenue")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
            return WAITING_REVENUE_FREQUENCY
        else:
            # Receita não recorrente, pular para confirmação
            context.user_data['frequency'] = 'once'
            return await self.show_confirmation(query, context)
    
    async def process_revenue_frequency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar frequência da receita"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_revenue":
            await query.edit_message_text("❌ Cadastro de receita cancelado.")
            return ConversationHandler.END
        
        frequency = query.data.replace("freq_", "")
        context.user_data['frequency'] = frequency
        
        return await self.show_confirmation(query, context)
    
    async def show_confirmation(self, query, context):
        """Mostrar confirmação final"""
        data = context.user_data
        revenue_type_info = data['revenue_type_info']
        account = data['account']
        
        frequency_text = {
            'once': '🔄 Apenas uma vez',
            'monthly': '📅 Mensal',
            'weekly': '📆 Semanal'
        }.get(data['frequency'], 'Uma vez')
        
        text = f"""📋 **Confirme os dados da receita:**

**Tipo:** {revenue_type_info['name']}
**Descrição:** {data['description']}
**Valor:** R$ {data['value']:,.2f}
**Data:** {data['revenue_date'].strftime('%d/%m/%Y')}
**Conta:** {account['color']} {account['name']}
**Frequência:** {frequency_text}

**Tudo correto?**"""
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data="confirm_revenue")],
            [InlineKeyboardButton("✏️ Editar", callback_data="edit_revenue")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_revenue")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return WAITING_REVENUE_CONFIRMATION
    
    async def process_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar confirmação final"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_revenue":
            await query.edit_message_text("❌ Cadastro de receita cancelado.")
            return ConversationHandler.END
        elif query.data == "edit_revenue":
            await query.edit_message_text(
                "✏️ **Para editar, inicie novamente com /receitas**\n\n"
                "Em breve teremos opção de edição durante o cadastro!"
            )
            return ConversationHandler.END
        elif query.data == "confirm_revenue":
            # Salvar receita no banco
            success = await self.save_revenue(context.user_data)
            
            if success:
                data = context.user_data
                text = f"""✅ **Receita cadastrada com sucesso!**

💰 **{data['description']}**
💵 **R$ {data['value']:,.2f}**
📅 **{data['revenue_date'].strftime('%d/%m/%Y')}**

**Comandos úteis:**
• /saldo - Ver saldos atualizados
• /receitas - Adicionar nova receita  
• /resumo - Dashboard financeiro"""
                
                await query.edit_message_text(text, parse_mode='Markdown')
            else:
                await query.edit_message_text(
                    "❌ **Erro ao salvar receita**\n\n"
                    "Tente novamente em alguns instantes."
                )
            
            return ConversationHandler.END
        
        return WAITING_REVENUE_CONFIRMATION
    
    async def save_revenue(self, data: Dict) -> bool:
        """Salvar receita no banco de dados"""
        try:
            # Buscar ou criar categoria de receita
            category = await self.bot.get_or_create_category(
                data['user_id'], 
                data['revenue_type_info']['name'], 
                'income'
            )
            
            # Salvar transação
            query = """
                INSERT INTO transactions (
                    user_id, title, description, amount, type, category_id,
                    transaction_date, status, notes, tags
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """
            
            transaction_data = (
                data['user_id'],
                data['description'],
                f"Receita: {data['revenue_type_info']['description']}",
                data['value'],
                'income',
                category['id'] if category else None,
                data['revenue_date'],
                'paid',
                f"Conta: {data['account']['name']}, Frequência: {data['frequency']}",
                [data['revenue_type'], data['account_key']]
            )
            
            result = await self.bot.execute_query_one(query, transaction_data)
            
            if result:
                # Se é recorrente, criar lembretes futuros (implementar depois)
                logger.info(f"Receita salva: {data['description']} - R$ {data['value']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao salvar receita: {e}")
            return False
    
    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancelar operação"""
        await update.message.reply_text("❌ Operação cancelada.")
        return ConversationHandler.END