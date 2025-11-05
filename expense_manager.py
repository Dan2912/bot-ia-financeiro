"""
Sistema de Despesas com UX Guiada e Parcelamento
Interface estruturada para cadastro de despesas
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from typing import Dict, List
from datetime import datetime, date, timedelta
import logging
import calendar

logger = logging.getLogger(__name__)

# Estados da conversa
WAITING_EXPENSE_TYPE = 'waiting_expense_type'
WAITING_EXPENSE_DESCRIPTION = 'waiting_expense_description'
WAITING_EXPENSE_VALUE = 'waiting_expense_value'
WAITING_EXPENSE_DATE = 'waiting_expense_date'
WAITING_EXPENSE_ACCOUNT = 'waiting_expense_account'
WAITING_INSTALLMENT_OPTION = 'waiting_installment_option'
WAITING_INSTALLMENT_COUNT = 'waiting_installment_count'
WAITING_INSTALLMENT_START = 'waiting_installment_start'
WAITING_EXPENSE_CONFIRMATION = 'waiting_expense_confirmation'

class ExpenseManager:
    """Gerenciador de despesas com UX guiada e parcelamento"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        
        # Tipos de despesa predefinidos
        self.expense_types = {
            'food': {
                'name': '🍽️ Alimentação',
                'description': 'Mercado, restaurantes, delivery, cafés',
                'common_accounts': ['c6_pf', 'nubank_pf', 'inter_pf'],
                'allow_installments': False
            },
            'transport': {
                'name': '🚗 Transporte',
                'description': 'Combustível, Uber, transporte público, pedágios',
                'common_accounts': ['c6_pf', 'nubank_pf'],
                'allow_installments': False
            },
            'shopping': {
                'name': '🛒 Compras Pessoais',
                'description': 'Roupas, eletrônicos, casa, presentes',
                'common_accounts': ['c6_pf', 'nubank_pf', 'inter_pf'],
                'allow_installments': True
            },
            'health': {
                'name': '🏥 Saúde',
                'description': 'Médico, dentista, farmácia, planos de saúde',
                'common_accounts': ['c6_pf', 'nubank_pf', 'santander_pf'],
                'allow_installments': True
            },
            'education': {
                'name': '📚 Educação',
                'description': 'Cursos, livros, materiais, mensalidades',
                'common_accounts': ['c6_pf', 'inter_pf'],
                'allow_installments': True
            },
            'bills': {
                'name': '🏠 Contas Fixas',
                'description': 'Luz, água, internet, telefone, streaming',
                'common_accounts': ['c6_pf', 'santander_pf'],
                'allow_installments': False
            },
            'business': {
                'name': '🏢 Empresarial',
                'description': 'Despesas da empresa, fornecedores, equipamentos',
                'common_accounts': ['inter_pj', 'c6_pj', 'santander_pj'],
                'allow_installments': True
            },
            'investment': {
                'name': '📈 Investimentos',
                'description': 'Ações, fundos, criptomoedas, aplicações',
                'common_accounts': ['inter_pf', 'c6_pf'],
                'allow_installments': False
            },
            'entertainment': {
                'name': '🎮 Lazer',
                'description': 'Cinema, shows, jogos, viagens, hobbies',
                'common_accounts': ['nubank_pf', 'c6_pf'],
                'allow_installments': True
            },
            'other': {
                'name': '💡 Outras Despesas',
                'description': 'Outras categorias de gastos',
                'common_accounts': ['c6_pf', 'nubank_pf'],
                'allow_installments': True
            }
        }
    
    async def start_add_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar processo de adição de despesa"""
        user = await self.bot.get_or_create_user(update.effective_user)
        
        # Limpar dados anteriores
        context.user_data.clear()
        context.user_data['user_id'] = user['id']
        
        text = """💳 **Adicionar Nova Despesa**

🎯 **Vamos cadastrar sua despesa passo a passo!**

**Primeiro, escolha a categoria da despesa:**

Cada categoria tem contas sugeridas e opções de parcelamento específicas."""
        
        # Criar teclado com tipos de despesa
        keyboard = []
        row = []
        for key, expense_type in self.expense_types.items():
            row.append(InlineKeyboardButton(
                expense_type['name'],
                callback_data=f"expense_type_{key}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        if row:  # Adicionar linha incompleta
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_expense")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return WAITING_EXPENSE_TYPE
    
    async def process_expense_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar seleção do tipo de despesa"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_expense":
            await query.edit_message_text("❌ Cadastro de despesa cancelado.")
            return ConversationHandler.END
        
        expense_type_key = query.data.replace("expense_type_", "")
        expense_type = self.expense_types.get(expense_type_key)
        
        if not expense_type:
            await query.edit_message_text("❌ Tipo de despesa inválido.")
            return ConversationHandler.END
        
        # Salvar dados
        context.user_data['expense_type'] = expense_type_key
        context.user_data['expense_type_info'] = expense_type
        
        installment_info = ""
        if expense_type['allow_installments']:
            installment_info = "\n\n💳 **Esta categoria permite parcelamento!**"
        
        text = f"""✅ **{expense_type['name']} Selecionado**

📝 **{expense_type['description']}**{installment_info}

**Agora, digite uma descrição para esta despesa:**

💡 **Exemplos:**
• "Mercado - Atacadão"
• "Combustível - Posto Shell"  
• "Notebook Dell - Loja XYZ"
• "Plano de saúde - Dezembro"

**Digite a descrição:**"""
        
        await query.edit_message_text(text, parse_mode='Markdown')
        return WAITING_EXPENSE_DESCRIPTION
    
    async def receive_expense_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber descrição da despesa"""
        description = update.message.text.strip()
        
        if len(description) < 3:
            await update.message.reply_text(
                "❌ **Descrição muito curta!**\n\n"
                "Digite uma descrição com pelo menos 3 caracteres:"
            )
            return WAITING_EXPENSE_DESCRIPTION
        
        context.user_data['description'] = description
        
        text = f"""✅ **Descrição salva:** {description}

💵 **Agora digite o valor da despesa:**

💡 **Formatos aceitos:**
• 150 ou 150,00
• 1.350,50 (com pontos e vírgulas)
• 2500.00 (formato americano)

**Qual o valor desta despesa?**"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return WAITING_EXPENSE_VALUE
    
    async def receive_expense_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber valor da despesa"""
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
                "• Exemplo: 150,00\n"
                "• Exemplo: 1.350,50\n\n"
                "**Digite novamente o valor:**"
            )
            return WAITING_EXPENSE_VALUE
        
        context.user_data['value'] = value
        
        text = f"""✅ **Valor salvo:** R$ {value:,.2f}

📅 **Agora digite a data desta despesa:**

💡 **Formatos aceitos:**
• 15/12/2025 (dd/mm/aaaa)
• 15/12 (assumirá ano atual)
• hoje (data de hoje)
• ontem (data de ontem)

**Qual a data desta despesa?**"""
        
        await update.message.reply_text(text, parse_mode='Markdown')
        return WAITING_EXPENSE_DATE
    
    async def receive_expense_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber data da despesa"""
        date_text = update.message.text.strip().lower()
        
        try:
            if date_text == "hoje":
                expense_date = date.today()
            elif date_text == "ontem":
                expense_date = date.today() - timedelta(days=1)
            elif "/" in date_text:
                parts = date_text.split("/")
                if len(parts) == 2:  # dd/mm
                    day, month = int(parts[0]), int(parts[1])
                    year = date.today().year
                elif len(parts) == 3:  # dd/mm/yyyy
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    raise ValueError("Formato inválido")
                
                expense_date = date(year, month, day)
            else:
                raise ValueError("Formato não reconhecido")
                
        except (ValueError, TypeError):
            await update.message.reply_text(
                "❌ **Data inválida!**\n\n"
                "Use um dos formatos:\n"
                "• 15/12/2025\n"
                "• 15/12 (ano atual)\n"
                "• hoje\n"
                "• ontem\n\n"
                "**Digite novamente a data:**"
            )
            return WAITING_EXPENSE_DATE
        
        context.user_data['expense_date'] = expense_date
        
        # Prosseguir para seleção de conta baseada no tipo de despesa
        from account_manager import account_manager
        expense_type_info = context.user_data['expense_type_info']
        
        # Filtrar contas sugeridas
        all_expense_accounts = account_manager.get_expense_accounts()
        suggested_accounts = []
        other_accounts = []
        
        for account in all_expense_accounts:
            if account['key'] in expense_type_info['common_accounts']:
                suggested_accounts.append(account)
            else:
                other_accounts.append(account)
        
        text = f"""✅ **Data salva:** {expense_date.strftime('%d/%m/%Y')}

🏦 **Escolha a conta que será debitada:**

**💡 Contas sugeridas para {expense_type_info['name']}:**"""
        
        keyboard = []
        
        # Contas sugeridas primeiro
        for account in suggested_accounts:
            keyboard.append([InlineKeyboardButton(
                f"⭐ {account['color']} {account['name']}",
                callback_data=f"select_account_{account['key']}"
            )])
        
        # Separador
        if suggested_accounts and other_accounts:
            keyboard.append([InlineKeyboardButton("➖ Outras contas ➖", callback_data="separator")])
        
        # Outras contas
        for account in other_accounts:
            keyboard.append([InlineKeyboardButton(
                f"{account['color']} {account['name']}",
                callback_data=f"select_account_{account['key']}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_expense")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return WAITING_EXPENSE_ACCOUNT
    
    async def process_expense_account(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar seleção da conta de despesa"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_expense":
            await query.edit_message_text("❌ Cadastro de despesa cancelado.")
            return ConversationHandler.END
        elif query.data == "separator":
            await query.answer("Selecione uma conta válida")
            return WAITING_EXPENSE_ACCOUNT
        
        account_key = query.data.replace("select_account_", "")
        from account_manager import account_manager
        account = account_manager.get_account_by_key(account_key)
        
        if not account:
            await query.edit_message_text("❌ Conta inválida.")
            return ConversationHandler.END
        
        context.user_data['account_key'] = account_key
        context.user_data['account'] = account
        
        # Verificar se categoria permite parcelamento
        expense_type_info = context.user_data['expense_type_info']
        
        if expense_type_info['allow_installments'] and context.user_data['value'] >= 100:
            text = f"""✅ **Conta selecionada:** {account['color']} {account['name']}

💳 **Esta despesa pode ser parcelada!**

**Valor:** R$ {context.user_data['value']:,.2f}

**Escolha uma opção:**"""
            
            keyboard = [
                [InlineKeyboardButton("💰 À vista", callback_data="install_once")],
                [InlineKeyboardButton("💳 Parcelar", callback_data="install_multiple")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_expense")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
            return WAITING_INSTALLMENT_OPTION
        else:
            # Não permite parcelamento ou valor muito baixo
            context.user_data['installments'] = 1
            context.user_data['installment_value'] = context.user_data['value']
            return await self.show_confirmation(query, context)
    
    async def process_installment_option(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar opção de parcelamento"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_expense":
            await query.edit_message_text("❌ Cadastro de despesa cancelado.")
            return ConversationHandler.END
        elif query.data == "install_once":
            context.user_data['installments'] = 1
            context.user_data['installment_value'] = context.user_data['value']
            return await self.show_confirmation(query, context)
        elif query.data == "install_multiple":
            # Mostrar opções de parcelamento
            total_value = context.user_data['value']
            
            text = f"""💳 **Parcelamento da despesa**

**Valor total:** R$ {total_value:,.2f}

**Em quantas parcelas?**

💡 **Parcelas sugeridas:**"""
            
            keyboard = []
            # Opções de 2 a 12 parcelas
            suggested_installments = [2, 3, 4, 6, 10, 12]
            
            row = []
            for installments in suggested_installments:
                installment_value = total_value / installments
                if installment_value >= 10:  # Parcela mínima de R$ 10
                    row.append(InlineKeyboardButton(
                        f"{installments}x R$ {installment_value:.2f}",
                        callback_data=f"install_{installments}"
                    ))
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
            
            if row:
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("✏️ Outro valor", callback_data="install_custom")])
            keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_expense")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
            return WAITING_INSTALLMENT_COUNT
        
        return WAITING_INSTALLMENT_OPTION
    
    async def process_installment_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar quantidade de parcelas"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_expense":
            await query.edit_message_text("❌ Cadastro de despesa cancelado.")
            return ConversationHandler.END
        elif query.data == "install_custom":
            text = """✏️ **Parcelas personalizadas**

**Digite o número de parcelas desejado:**

💡 **Entre 2 e 24 parcelas**
• Mínimo: 2 parcelas
• Máximo: 24 parcelas
• Valor mínimo por parcela: R$ 10,00"""
            
            await query.edit_message_text(text, parse_mode='Markdown')
            context.user_data['waiting_custom_installments'] = True
            return WAITING_INSTALLMENT_COUNT
        elif query.data.startswith("install_"):
            installments = int(query.data.replace("install_", ""))
            context.user_data['installments'] = installments
            context.user_data['installment_value'] = context.user_data['value'] / installments
            
            return await self.ask_installment_start_date(query, context)
        
        return WAITING_INSTALLMENT_COUNT
    
    async def receive_custom_installments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber número customizado de parcelas"""
        if not context.user_data.get('waiting_custom_installments'):
            return WAITING_INSTALLMENT_COUNT
        
        try:
            installments = int(update.message.text.strip())
            
            if installments < 2 or installments > 24:
                raise ValueError("Número de parcelas inválido")
            
            installment_value = context.user_data['value'] / installments
            if installment_value < 10:
                await update.message.reply_text(
                    f"❌ **Parcela muito baixa!**\n\n"
                    f"Com {installments} parcelas, cada parcela seria R$ {installment_value:.2f}\n"
                    f"Valor mínimo por parcela: R$ 10,00\n\n"
                    f"**Digite um número menor de parcelas:**"
                )
                return WAITING_INSTALLMENT_COUNT
            
            context.user_data['installments'] = installments
            context.user_data['installment_value'] = installment_value
            context.user_data['waiting_custom_installments'] = False
            
            # Simular callback query para continuar fluxo
            class FakeQuery:
                async def edit_message_text(self, text, parse_mode=None, reply_markup=None):
                    await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
            
            fake_query = FakeQuery()
            return await self.ask_installment_start_date(fake_query, context)
            
        except (ValueError, TypeError):
            await update.message.reply_text(
                "❌ **Número inválido!**\n\n"
                "Digite um número entre 2 e 24:"
            )
            return WAITING_INSTALLMENT_COUNT
    
    async def ask_installment_start_date(self, query, context):
        """Perguntar data de início das parcelas"""
        installments = context.user_data['installments']
        installment_value = context.user_data['installment_value']
        
        text = f"""📅 **Data das parcelas**

**Parcelamento:** {installments}x R$ {installment_value:.2f}

**Quando será cobrada a primeira parcela?**"""
        
        # Sugerir datas baseadas na data atual
        today = date.today()
        
        keyboard = []
        
        # Hoje, amanhã e próximos dias úteis
        suggestions = [
            (today, "🗓️ Hoje"),
            (today + timedelta(days=1), "📅 Amanhã"),
            (self.next_weekday(today, 0), "📅 Próxima segunda"),  # Segunda-feira
            (self.get_next_month_day(today, 5), "📅 Dia 5 do próximo mês"),
            (self.get_next_month_day(today, 15), "📅 Dia 15 do próximo mês"),
        ]
        
        for date_option, label in suggestions:
            keyboard.append([InlineKeyboardButton(
                f"{label} ({date_option.strftime('%d/%m')})",
                callback_data=f"start_{date_option.strftime('%Y-%m-%d')}"
            )])
        
        keyboard.append([InlineKeyboardButton("✏️ Outra data", callback_data="start_custom")])
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel_expense")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return WAITING_INSTALLMENT_START
    
    def next_weekday(self, d, weekday):
        """Encontrar próximo dia da semana específico"""
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return d + timedelta(days_ahead)
    
    def get_next_month_day(self, current_date, day):
        """Obter data específica do próximo mês"""
        if current_date.month == 12:
            year = current_date.year + 1
            month = 1
        else:
            year = current_date.year
            month = current_date.month + 1
        
        # Verificar se o dia existe no mês
        max_day = calendar.monthrange(year, month)[1]
        if day > max_day:
            day = max_day
        
        return date(year, month, day)
    
    async def process_installment_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar data de início das parcelas"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_expense":
            await query.edit_message_text("❌ Cadastro de despesa cancelado.")
            return ConversationHandler.END
        elif query.data == "start_custom":
            text = """📅 **Data personalizada**

**Digite a data da primeira parcela:**

💡 **Formatos aceitos:**
• 15/01/2025 (dd/mm/aaaa)
• 15/01 (assumirá ano atual)

**Digite a data:**"""
            
            await query.edit_message_text(text, parse_mode='Markdown')
            context.user_data['waiting_custom_start_date'] = True
            return WAITING_INSTALLMENT_START
        elif query.data.startswith("start_"):
            date_str = query.data.replace("start_", "")
            start_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            context.user_data['installment_start_date'] = start_date
            
            return await self.show_confirmation(query, context)
        
        return WAITING_INSTALLMENT_START
    
    async def receive_custom_start_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber data customizada de início"""
        if not context.user_data.get('waiting_custom_start_date'):
            return WAITING_INSTALLMENT_START
        
        date_text = update.message.text.strip()
        
        try:
            if "/" in date_text:
                parts = date_text.split("/")
                if len(parts) == 2:  # dd/mm
                    day, month = int(parts[0]), int(parts[1])
                    year = date.today().year
                elif len(parts) == 3:  # dd/mm/yyyy
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    raise ValueError("Formato inválido")
                
                start_date = date(year, month, day)
                
                # Verificar se não é muito no passado
                if start_date < date.today() - timedelta(days=30):
                    await update.message.reply_text(
                        "❌ **Data muito antiga!**\n\n"
                        "Escolha uma data mais recente."
                    )
                    return WAITING_INSTALLMENT_START
                
            else:
                raise ValueError("Formato não reconhecido")
            
            context.user_data['installment_start_date'] = start_date
            context.user_data['waiting_custom_start_date'] = False
            
            # Simular callback query para continuar fluxo
            class FakeQuery:
                async def edit_message_text(self, text, parse_mode=None, reply_markup=None):
                    await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
            
            fake_query = FakeQuery()
            return await self.show_confirmation(fake_query, context)
                
        except (ValueError, TypeError):
            await update.message.reply_text(
                "❌ **Data inválida!**\n\n"
                "Use o formato:\n"
                "• 15/01/2025\n"
                "• 15/01 (ano atual)\n\n"
                "**Digite novamente:**"
            )
            return WAITING_INSTALLMENT_START
    
    async def show_confirmation(self, query, context):
        """Mostrar confirmação final"""
        data = context.user_data
        expense_type_info = data['expense_type_info']
        account = data['account']
        
        # Texto básico
        text = f"""📋 **Confirme os dados da despesa:**

**Categoria:** {expense_type_info['name']}
**Descrição:** {data['description']}
**Valor total:** R$ {data['value']:,.2f}
**Data:** {data['expense_date'].strftime('%d/%m/%Y')}
**Conta:** {account['color']} {account['name']}"""
        
        # Informações de parcelamento
        installments = data.get('installments', 1)
        if installments > 1:
            installment_value = data['installment_value']
            start_date = data['installment_start_date']
            
            text += f"""
**Parcelamento:** {installments}x R$ {installment_value:.2f}
**Primeira parcela:** {start_date.strftime('%d/%m/%Y')}
**Última parcela:** {self.calculate_last_installment(start_date, installments).strftime('%d/%m/%Y')}"""
        else:
            text += f"\n**Pagamento:** À vista"
        
        text += "\n\n**Tudo correto?**"
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar", callback_data="confirm_expense")],
            [InlineKeyboardButton("✏️ Editar", callback_data="edit_expense")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel_expense")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        return WAITING_EXPENSE_CONFIRMATION
    
    def calculate_last_installment(self, start_date, installments):
        """Calcular data da última parcela"""
        # Adicionar meses (assumindo parcelas mensais)
        months_to_add = installments - 1
        
        year = start_date.year
        month = start_date.month + months_to_add
        
        # Ajustar ano se necessário
        while month > 12:
            year += 1
            month -= 12
        
        # Verificar se o dia existe no mês de destino
        max_day = calendar.monthrange(year, month)[1]
        day = min(start_date.day, max_day)
        
        return date(year, month, day)
    
    async def process_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar confirmação final"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_expense":
            await query.edit_message_text("❌ Cadastro de despesa cancelado.")
            return ConversationHandler.END
        elif query.data == "edit_expense":
            await query.edit_message_text(
                "✏️ **Para editar, inicie novamente com /gastos**\n\n"
                "Em breve teremos opção de edição durante o cadastro!"
            )
            return ConversationHandler.END
        elif query.data == "confirm_expense":
            # Salvar despesa(s) no banco
            success = await self.save_expense(context.user_data)
            
            if success:
                data = context.user_data
                installments = data.get('installments', 1)
                
                if installments > 1:
                    text = f"""✅ **Despesa parcelada cadastrada!**

💳 **{data['description']}**
💵 **{installments}x R$ {data['installment_value']:.2f} = R$ {data['value']:,.2f}**
📅 **Primeira parcela: {data['installment_start_date'].strftime('%d/%m/%Y')}**

**Todas as {installments} parcelas foram agendadas automaticamente!**"""
                else:
                    text = f"""✅ **Despesa cadastrada com sucesso!**

💳 **{data['description']}**
💵 **R$ {data['value']:,.2f}**
📅 **{data['expense_date'].strftime('%d/%m/%Y')}**"""
                
                text += f"""

**Comandos úteis:**
• /saldo - Ver saldos atualizados
• /gastos - Adicionar nova despesa
• /resumo - Dashboard financeiro"""
                
                await query.edit_message_text(text, parse_mode='Markdown')
            else:
                await query.edit_message_text(
                    "❌ **Erro ao salvar despesa**\n\n"
                    "Tente novamente em alguns instantes."
                )
            
            return ConversationHandler.END
        
        return WAITING_EXPENSE_CONFIRMATION
    
    async def save_expense(self, data: Dict) -> bool:
        """Salvar despesa(s) no banco de dados"""
        try:
            # Buscar ou criar categoria
            category = await self.bot.get_or_create_category(
                data['user_id'], 
                data['expense_type_info']['name'], 
                'expense'
            )
            
            installments = data.get('installments', 1)
            
            if installments == 1:
                # Despesa única
                return await self.save_single_expense(data, category)
            else:
                # Despesa parcelada
                return await self.save_installment_expenses(data, category)
                
        except Exception as e:
            logger.error(f"Erro ao salvar despesa: {e}")
            return False
    
    async def save_single_expense(self, data: Dict, category: Dict) -> bool:
        """Salvar despesa única"""
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
            f"Despesa: {data['expense_type_info']['description']}",
            -abs(data['value']),  # Negativo para despesa
            'expense',
            category['id'] if category else None,
            data['expense_date'],
            'paid',
            f"Conta: {data['account']['name']}",
            [data['expense_type'], data['account_key']]
        )
        
        result = await self.bot.execute_query_one(query, transaction_data)
        return result is not None
    
    async def save_installment_expenses(self, data: Dict, category: Dict) -> bool:
        """Salvar despesas parceladas"""
        installments = data['installments']
        installment_value = data['installment_value']
        start_date = data['installment_start_date']
        
        success_count = 0
        
        for i in range(installments):
            # Calcular data da parcela
            installment_date = self.calculate_installment_date(start_date, i)
            
            # Determinar status baseado na data
            today = date.today()
            if installment_date <= today:
                status = 'paid'
            elif installment_date <= today + timedelta(days=7):
                status = 'pending'
            else:
                status = 'scheduled'
            
            query = """
                INSERT INTO transactions (
                    user_id, title, description, amount, type, category_id,
                    transaction_date, status, notes, tags, installment_info
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
            """
            
            installment_info = {
                'current_installment': i + 1,
                'total_installments': installments,
                'total_value': data['value']
            }
            
            transaction_data = (
                data['user_id'],
                f"{data['description']} ({i+1}/{installments})",
                f"Parcela {i+1} de {installments} - {data['expense_type_info']['description']}",
                -abs(installment_value),  # Negativo para despesa
                'expense',
                category['id'] if category else None,
                installment_date,
                status,
                f"Conta: {data['account']['name']}, Parcela {i+1}/{installments}",
                [data['expense_type'], data['account_key'], 'installment'],
                installment_info
            )
            
            result = await self.bot.execute_query_one(query, transaction_data)
            if result:
                success_count += 1
        
        # Considerar sucesso se pelo menos 80% das parcelas foram salvas
        return success_count >= (installments * 0.8)
    
    def calculate_installment_date(self, start_date, installment_number):
        """Calcular data de uma parcela específica"""
        months_to_add = installment_number
        
        year = start_date.year
        month = start_date.month + months_to_add
        
        # Ajustar ano se necessário
        while month > 12:
            year += 1
            month -= 12
        
        # Verificar se o dia existe no mês de destino
        max_day = calendar.monthrange(year, month)[1]
        day = min(start_date.day, max_day)
        
        return date(year, month, day)
    
    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancelar operação"""
        await update.message.reply_text("❌ Operação cancelada.")
        return ConversationHandler.END