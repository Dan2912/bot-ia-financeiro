from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal, InvalidOperation
import json
from user_auth import UserAuthSystem
from financial_manager import FinancialManager

logger = logging.getLogger(__name__)

# Estados da conversa para autenticação
WAITING_FULL_NAME, WAITING_EMAIL, WAITING_PASSWORD, WAITING_LOGIN_PASSWORD, WAITING_OLD_PASSWORD, WAITING_NEW_PASSWORD = range(6)

# Estados para gestão financeira
WAITING_EXPENSE_TITLE, WAITING_EXPENSE_AMOUNT, WAITING_EXPENSE_CATEGORY, WAITING_GOAL_TITLE, WAITING_GOAL_AMOUNT, WAITING_GOAL_TYPE, WAITING_GOAL_DATE = range(6, 13)

class BotCommands:
    """Comandos avançados do bot com autenticação e gestão financeira"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.auth_system = UserAuthSystem(bot_instance.db_pool)
        self.financial_manager = FinancialManager(bot_instance.db_pool)
    
    async def connect_bank_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Conectar nova conta bancária"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Buscar bancos disponíveis via Pluggy
            async with self.bot.pluggy as pluggy:
                connectors = await pluggy.get_connectors()
            
            # Filtrar bancos principais brasileiros
            main_banks = [
                "Itaú", "Bradesco", "Banco do Brasil", "Santander", 
                "Caixa", "Nubank", "Inter", "C6 Bank", "BTG Pactual"
            ]
            
            filtered_connectors = [
                conn for conn in connectors 
                if any(bank.lower() in conn['name'].lower() for bank in main_banks)
            ][:10]  # Máximo 10 bancos
            
            if not filtered_connectors:
                await query.edit_message_text(
                    "❌ Nenhum banco disponível no momento. Tente novamente mais tarde.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏠 Menu", callback_data="main_menu")
                    ]])
                )
                return
            
            # Criar teclado com bancos
            keyboard = []
            for connector in filtered_connectors:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🏦 {connector['name']}", 
                        callback_data=f"connect_{connector['id']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="main_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = "🏦 *Conectar Conta Bancária*\n\nSelecione seu banco:"
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro ao buscar bancos: {e}")
            await query.edit_message_text(
                "❌ Erro ao carregar lista de bancos. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Menu", callback_data="main_menu")
                ]])
            )
    
    async def investment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Conselhos de investimento personalizados"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text("💡 Gerando conselhos de investimento personalizados...")
        
        user = await self.bot.get_or_create_user(update.effective_user)
        
        try:
            # Buscar dados financeiros do usuário
            accounts = await self.bot.get_user_accounts(user['id'])
            transactions = await self.bot.get_user_transactions(user['id'], days=90)
            
            # Calcular métricas financeiras
            total_balance = sum(float(acc['balance']) for acc in accounts)
            
            monthly_income = 0
            monthly_expenses = 0
            
            # Calcular renda e gastos mensais baseados nos últimos 30 dias
            last_30_days = datetime.now() - timedelta(days=30)
            
            for tx in transactions:
                if tx['transaction_date'] >= last_30_days:
                    if tx['amount'] > 0:
                        monthly_income += float(tx['amount'])
                    else:
                        monthly_expenses += abs(float(tx['amount']))
            
            available_for_investment = monthly_income - monthly_expenses
            
            # Gerar análise de investimento com IA
            investment_advice = await self.generate_investment_advice(
                total_balance, monthly_income, monthly_expenses, available_for_investment
            )
            
            # Salvar no banco
            await self.bot.save_ai_analysis(user['id'], 'investment_advice', investment_advice)
            
            keyboard = [
                [InlineKeyboardButton("📊 Análise Completa", callback_data="ai_analysis")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"💡 *Conselhos de Investimento:*\n\n{investment_advice}",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar conselhos: {e}")
            await query.edit_message_text(
                "❌ Erro ao gerar conselhos. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Menu", callback_data="main_menu")
                ]])
            )
    
    async def goals_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gerenciar metas financeiras"""
        query = update.callback_query
        await query.answer()
        
        user = await self.bot.get_or_create_user(update.effective_user)
        
        try:
            # Buscar metas do usuário
            goals = await self.get_user_goals(user['id'])
            
            if not goals:
                keyboard = [
                    [InlineKeyboardButton("➕ Criar Meta", callback_data="create_goal")],
                    [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "🎯 *Suas Metas Financeiras*\n\n"
                    "Você ainda não tem metas definidas.\n"
                    "Criar metas ajuda a organizar sua vida financeira!",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return
            
            # Mostrar metas existentes
            text = "🎯 *Suas Metas Financeiras:*\n\n"
            
            for goal in goals:
                progress = (goal['current_amount'] / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
                status_emoji = "✅" if goal['is_completed'] else "🔄"
                
                text += f"{status_emoji} *{goal['name']}*\n"
                text += f"💰 R$ {goal['current_amount']:,.2f} / R$ {goal['target_amount']:,.2f}\n"
                text += f"📊 Progresso: {progress:.1f}%\n"
                
                if goal['target_date']:
                    text += f"📅 Meta: {goal['target_date'].strftime('%d/%m/%Y')}\n"
                
                text += "\n"
            
            keyboard = [
                [InlineKeyboardButton("➕ Nova Meta", callback_data="create_goal")],
                [InlineKeyboardButton("📊 Dicas IA", callback_data="goal_tips")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro ao buscar metas: {e}")
            await query.edit_message_text(
                "❌ Erro ao carregar metas. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Menu", callback_data="main_menu")
                ]])
            )
    
    async def cards_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Informações de cartões de crédito"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text("💳 Consultando cartões de crédito...")
        
        user = await self.bot.get_or_create_user(update.effective_user)
        
        try:
            # Buscar cartões via Pluggy
            async with self.bot.pluggy as pluggy:
                user_items = await pluggy.get_items(str(user['id']))
                
                all_cards = []
                for item in user_items:
                    cards = await pluggy.get_credit_cards(item['id'])
                    all_cards.extend(cards)
            
            if not all_cards:
                await query.edit_message_text(
                    "💳 Nenhum cartão de crédito encontrado.\n\n"
                    "Conecte suas contas bancárias para ver informações dos cartões.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏦 Conectar Banco", callback_data="connect_bank")
                    ], [
                        InlineKeyboardButton("🏠 Menu", callback_data="main_menu")
                    ]])
                )
                return
            
            text = "💳 *Seus Cartões de Crédito:*\n\n"
            
            for card in all_cards:
                available_limit = card.get('creditLimit', 0) - card.get('balance', 0)
                usage_percent = (card.get('balance', 0) / card.get('creditLimit', 1) * 100) if card.get('creditLimit', 0) > 0 else 0
                
                text += f"💳 *{card.get('name', 'Cartão')}*\n"
                text += f"🏦 {card.get('bank', 'N/A')}\n"
                text += f"💰 Limite: R$ {card.get('creditLimit', 0):,.2f}\n"
                text += f"💸 Usado: R$ {card.get('balance', 0):,.2f} ({usage_percent:.1f}%)\n"
                text += f"✅ Disponível: R$ {available_limit:,.2f}\n"
                
                if card.get('dueDate'):
                    text += f"📅 Vencimento: {card['dueDate']}\n"
                
                text += "\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Atualizar", callback_data="cards")],
                [InlineKeyboardButton("📊 Análise IA", callback_data="ai_analysis")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro ao buscar cartões: {e}")
            await query.edit_message_text(
                "❌ Erro ao consultar cartões. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Menu", callback_data="main_menu")
                ]])
            )
    
    async def generate_investment_advice(self, balance: float, income: float, expenses: float, available: float):
        """Gerar conselhos de investimento com IA"""
        
        # Definir perfil de risco baseado nos dados
        risk_profile = "conservador"
        if available > income * 0.3:
            risk_profile = "moderado"
        if available > income * 0.5 and balance > income * 6:
            risk_profile = "arrojado"
        
        prompt = f"""
        Como consultor financeiro brasileiro, analise este perfil:
        
        💰 Patrimônio atual: R$ {balance:,.2f}
        📈 Renda mensal: R$ {income:,.2f}
        📉 Gastos mensais: R$ {expenses:,.2f}
        💵 Disponível para investir: R$ {available:,.2f}
        🎯 Perfil estimado: {risk_profile}
        
        Forneça conselhos específicos sobre:
        1. Alocação de portfólio sugerida para o Brasil
        2. Produtos recomendados (Tesouro, CDB, Ações, Fundos, etc.)
        3. Estratégia de curto (1 ano) e longo prazo (5+ anos)
        4. Valor mensal recomendado para investir
        5. Dicas específicas para o perfil de risco
        
        Seja prático, específico e considere o cenário brasileiro atual.
        Máximo 600 palavras.
        """
        
        try:
            response = self.bot.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um consultor de investimentos especialista no mercado brasileiro. Forneça conselhos práticos e atualizados."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.6
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro OpenAI investimento: {e}")
            return "Conselhos de investimento temporariamente indisponíveis. Tente novamente em alguns instantes."
    
    async def get_user_goals(self, user_id: int):
        """Buscar metas do usuário"""
        async with self.bot.db_pool.acquire() as conn:
            goals = await conn.fetch(
                "SELECT * FROM goals WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            return [dict(goal) for goal in goals]

    # ========================
    # SISTEMA DE AUTENTICAÇÃO
    # ========================

    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar processo de cadastro"""
        telegram_user = update.effective_user
        
        # Verificar se usuário já está cadastrado
        async with self.bot.db_pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id, is_active FROM users WHERE telegram_id = $1",
                telegram_user.id
            )
        
        if existing:
            if existing['is_active']:
                await update.message.reply_text(
                    "✅ Você já possui cadastro ativo!\n"
                    "Use /login para fazer login ou /perfil para ver suas informações."
                )
            else:
                await update.message.reply_text(
                    "⚠️ Sua conta está inativa.\n"
                    "Entre em contato com o suporte para reativar."
                )
            return ConversationHandler.END
        
        await update.message.reply_text(
            f"👋 Olá {telegram_user.first_name}!\n\n"
            "Vou te ajudar a criar sua conta no sistema financeiro.\n"
            "📝 Por favor, digite seu **nome completo**:"
        )
        
        return WAITING_FULL_NAME

    async def receive_full_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber nome completo"""
        full_name = update.message.text.strip()
        
        if len(full_name) < 3:
            await update.message.reply_text(
                "❌ Nome muito curto. Digite seu nome completo (mínimo 3 caracteres):"
            )
            return WAITING_FULL_NAME
        
        if len(full_name) > 500:
            await update.message.reply_text(
                "❌ Nome muito longo. Digite um nome com até 500 caracteres:"
            )
            return WAITING_FULL_NAME
        
        # Salvar nome temporariamente
        context.user_data['full_name'] = full_name
        
        await update.message.reply_text(
            f"✅ Nome: {full_name}\n\n"
            "📧 Agora digite seu **email** (opcional - digite 'pular' para pular):"
        )
        
        return WAITING_EMAIL

    async def receive_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber email"""
        email_text = update.message.text.strip().lower()
        
        if email_text == 'pular':
            email = None
        else:
            if not self.auth_system.validate_email(email_text):
                await update.message.reply_text(
                    "❌ Email inválido. Digite um email válido ou 'pular' para pular:"
                )
                return WAITING_EMAIL
            email = email_text
        
        # Salvar email temporariamente
        context.user_data['email'] = email
        
        email_msg = f"📧 Email: {email}" if email else "📧 Email: não informado"
        
        await update.message.reply_text(
            f"✅ {email_msg}\n\n"
            "🔐 Agora crie uma **senha segura**:\n"
            "• Pelo menos 8 caracteres\n"
            "• Letras maiúsculas e minúsculas\n" 
            "• Números e símbolos\n"
            "• Não use senhas comuns"
        )
        
        return WAITING_PASSWORD

    async def receive_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber e processar senha"""
        password = update.message.text
        telegram_user = update.effective_user
        
        # Deletar mensagem da senha por segurança
        try:
            await update.message.delete()
        except:
            pass
        
        # Registrar usuário
        result = await self.auth_system.register_user(
            telegram_user=telegram_user,
            full_name=context.user_data['full_name'],
            password=password,
            email=context.user_data.get('email'),
            registration_ip=None  # Telegram não fornece IP
        )
        
        if result['success']:
            await update.effective_chat.send_message(
                f"🎉 **Cadastro realizado com sucesso!**\n\n"
                f"👤 Nome: {context.user_data['full_name']}\n"
                f"🔐 Força da senha: {result['password_strength']}\n"
                f"🆔 ID: {result['user_id']}\n\n"
                "Agora você pode usar /login para acessar o sistema!"
            )
        else:
            if result['error'] == 'password_weak':
                message = "❌ **Senha muito fraca!**\n\n"
                for msg in result['messages']:
                    message += f"• {msg}\n"
                message += "\nDigite uma senha mais segura:"
                
                await update.effective_chat.send_message(message)
                return WAITING_PASSWORD
            else:
                await update.effective_chat.send_message(
                    f"❌ Erro no cadastro: {result['message']}\n"
                    "Tente novamente com /cadastro"
                )
        
        # Limpar dados temporários
        context.user_data.clear()
        return ConversationHandler.END

    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando de login"""
        await update.message.reply_text(
            "🔐 **Login no Sistema**\n\n"
            "Digite sua senha de acesso:"
        )
        
        return WAITING_LOGIN_PASSWORD

    async def receive_login_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar login"""
        password = update.message.text
        telegram_user = update.effective_user
        
        # Deletar mensagem da senha
        try:
            await update.message.delete()
        except:
            pass
        
        # Autenticar
        result = await self.auth_system.authenticate_user(
            telegram_id=telegram_user.id,
            password=password,
            login_ip=None
        )
        
        if result['success']:
            # Salvar sessão do usuário
            context.user_data['user_id'] = result['user_id']
            context.user_data['authenticated'] = True
            context.user_data['login_time'] = datetime.now()
            
            await update.effective_chat.send_message(
                f"✅ **Login realizado com sucesso!**\n\n"
                f"👋 Bem-vindo(a), {result['full_name']}!\n\n"
                "Comandos disponíveis:\n"
                "💰 /saldo - Ver saldo das contas\n"
                "💳 /cartoes - Informações dos cartões\n"
                "📊 /extrato - Extrato detalhado\n"
                "🎯 /metas - Gerenciar metas\n"
                "🔧 /perfil - Ver perfil\n"
                "🔒 /trocar_senha - Alterar senha"
            )
        else:
            error_messages = {
                'user_not_found': '❌ Usuário não cadastrado. Use /cadastro primeiro.',
                'account_inactive': '⚠️ Conta inativa. Contate o suporte.',
                'account_locked': f'🔒 {result["message"]}',
                'invalid_password': f'❌ {result["message"]}'
            }
            
            message = error_messages.get(result['error'], f"❌ {result['message']}")
            await update.effective_chat.send_message(message)
        
        return ConversationHandler.END

    async def change_password_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar alteração de senha"""
        # Verificar se está logado
        if not context.user_data.get('authenticated'):
            await update.message.reply_text(
                "❌ Você precisa fazer login primeiro. Use /login"
            )
            return ConversationHandler.END
        
        await update.message.reply_text(
            "🔐 **Alterar Senha**\n\n"
            "Digite sua senha atual:"
        )
        
        return WAITING_OLD_PASSWORD

    async def receive_old_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber senha atual"""
        old_password = update.message.text
        
        # Deletar mensagem
        try:
            await update.message.delete()
        except:
            pass
        
        # Salvar temporariamente
        context.user_data['old_password'] = old_password
        
        await update.effective_chat.send_message(
            "🔐 Agora digite sua **nova senha**:\n"
            "• Pelo menos 8 caracteres\n"
            "• Letras maiúsculas e minúsculas\n"
            "• Números e símbolos\n"
            "• Não use senhas comuns"
        )
        
        return WAITING_NEW_PASSWORD

    async def receive_new_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar nova senha"""
        new_password = update.message.text
        old_password = context.user_data.get('old_password')
        user_id = context.user_data.get('user_id')
        
        # Deletar mensagem
        try:
            await update.message.delete()
        except:
            pass
        
        # Alterar senha
        result = await self.auth_system.change_password(
            user_id=user_id,
            old_password=old_password,
            new_password=new_password
        )
        
        # Limpar dados temporários
        context.user_data.pop('old_password', None)
        
        if result['success']:
            await update.effective_chat.send_message(
                f"✅ **Senha alterada com sucesso!**\n\n"
                f"🔐 Força da nova senha: {result['password_strength']}\n\n"
                "Sua sessão continuará ativa."
            )
        else:
            if result['error'] == 'password_weak':
                message = "❌ **Nova senha muito fraca!**\n\n"
                for msg in result['messages']:
                    message += f"• {msg}\n"
                message += "\nDigite uma nova senha mais segura:"
                
                await update.effective_chat.send_message(message)
                return WAITING_NEW_PASSWORD
            else:
                await update.effective_chat.send_message(
                    f"❌ {result['message']}\n"
                    "Tente novamente com /trocar_senha"
                )
        
        return ConversationHandler.END

    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostrar perfil do usuário"""
        # Verificar se está logado
        if not context.user_data.get('authenticated'):
            await update.message.reply_text(
                "❌ Você precisa fazer login primeiro. Use /login"
            )
            return
        
        user_id = context.user_data.get('user_id')
        profile = await self.auth_system.get_user_profile(user_id)
        
        if not profile:
            await update.message.reply_text("❌ Erro ao carregar perfil.")
            return
        
        # Formatar datas
        created_date = profile['created_at'].strftime("%d/%m/%Y %H:%M") if profile['created_at'] else "N/A"
        last_login = profile['last_login'].strftime("%d/%m/%Y %H:%M") if profile['last_login'] else "Nunca"
        
        # Status
        status_emoji = "✅" if profile['is_active'] else "❌"
        verified_emoji = "✅" if profile['is_verified'] else "❌"
        premium_emoji = "👑" if profile['is_premium'] else "👤"
        
        message = f"""
👤 **Seu Perfil**

{premium_emoji} **{profile['full_name']}**
📱 Telegram: @{profile['telegram_username'] or 'N/A'}
📧 Email: {profile['email'] or 'Não informado'}
📞 Telefone: {profile['phone'] or 'Não informado'}

📊 **Status da Conta:**
{status_emoji} Ativa: {'Sim' if profile['is_active'] else 'Não'}
{verified_emoji} Verificada: {'Sim' if profile['is_verified'] else 'Não'}
{premium_emoji} Premium: {'Sim' if profile['is_premium'] else 'Não'}

📅 **Datas:**
🆕 Cadastro: {created_date}
🔓 Último login: {last_login}
🔐 Senha alterada: {profile['password_changed_at'].strftime("%d/%m/%Y") if profile['password_changed_at'] else 'Nunca'}

🔐 **Segurança:**
❌ Tentativas falhadas: {profile['failed_login_attempts']}
        """
        
        # Botões de ação
        keyboard = [
            [InlineKeyboardButton("🔐 Trocar Senha", callback_data="change_password")],
            [InlineKeyboardButton("📧 Alterar Email", callback_data="change_email")],
            [InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_profile")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def logout_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fazer logout"""
        if context.user_data.get('authenticated'):
            context.user_data.clear()
            await update.message.reply_text(
                "👋 **Logout realizado com sucesso!**\n\n"
                "Para acessar novamente, use /login"
            )
        else:
            await update.message.reply_text(
                "❌ Você não estava logado."
            )

    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancelar operação atual"""
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Operação cancelada."
        )
        return ConversationHandler.END

    def is_authenticated(self, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Verificar se usuário está autenticado"""
        return context.user_data.get('authenticated', False)

    # ========================
    # COMANDOS FINANCEIROS
    # ========================

    async def expenses_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando principal de gestão de despesas"""
        if not self.is_authenticated(context):
            await update.message.reply_text(
                "❌ Você precisa fazer login primeiro. Use /login"
            )
            return

        user_id = context.user_data.get('user_id')
        
        # Criar categorias padrão se necessário
        categories = await self.financial_manager.get_user_categories(user_id, 'expense')
        if not categories:
            await self.financial_manager.create_default_categories(user_id)
            categories = await self.financial_manager.get_user_categories(user_id, 'expense')

        # Resumo das despesas do mês
        month_start = date.today().replace(day=1)
        summary = await self.financial_manager.get_monthly_summary(user_id, month_start)
        
        message = f"""💸 **Gestão de Despesas**

📊 **Resumo do Mês:**
• Total gasto: {self.financial_manager.format_currency(summary.get('total_expenses', 0))}
• Número de gastos: {summary.get('expense_count', 0)}
• Saldo do mês: {self.financial_manager.format_currency(summary.get('balance', 0))}

📂 **Suas Categorias:**"""

        for cat in categories[:5]:  # Mostrar top 5
            message += f"\n{cat['icon']} {cat['name']}"

        keyboard = [
            [InlineKeyboardButton("💸 Nova Despesa", callback_data="add_expense")],
            [InlineKeyboardButton("📊 Relatório", callback_data="expense_report")],
            [InlineKeyboardButton("📂 Categorias", callback_data="manage_categories")],
            [InlineKeyboardButton("🔄 Parcelamentos", callback_data="installments")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def goals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando principal de gestão de metas"""
        if not self.is_authenticated(context):
            await update.message.reply_text(
                "❌ Você precisa fazer login primeiro. Use /login"
            )
            return

        user_id = context.user_data.get('user_id')
        goals = await self.financial_manager.get_user_goals(user_id)

        if not goals:
            message = """🎯 **Suas Metas Financeiras**

📝 Você ainda não tem metas cadastradas.

✨ **Comece definindo suas metas:**
• 💰 Reserva de emergência
• 🏖️ Viagem dos sonhos  
• 🏠 Compra da casa própria
• 📈 Investimentos
• 💳 Quitação de dívidas"""

            keyboard = [
                [InlineKeyboardButton("🎯 Criar Primeira Meta", callback_data="add_goal")],
                [InlineKeyboardButton("💡 Dicas de Metas", callback_data="goal_tips")]
            ]
        else:
            message = "🎯 **Suas Metas Financeiras**\n\n"
            
            for goal in goals[:5]:  # Top 5 metas
                percentage = self.financial_manager.calculate_percentage(
                    goal['current_amount'], goal['target_amount']
                )
                emoji = self.financial_manager.get_goal_type_emoji(goal['goal_type'])
                status_emoji = "✅" if goal['is_completed'] else "🔄"
                
                message += f"""{emoji} **{goal['title']}** {status_emoji}
💰 {self.financial_manager.format_currency(goal['current_amount'])} de {self.financial_manager.format_currency(goal['target_amount'])}
📈 Progresso: {percentage:.1f}%
{'📅 Prazo: ' + goal['target_date'].strftime('%d/%m/%Y') if goal['target_date'] else ''}

"""

            keyboard = [
                [InlineKeyboardButton("🎯 Nova Meta", callback_data="add_goal")],
                [InlineKeyboardButton("📊 Progresso", callback_data="goals_progress")],
                [InlineKeyboardButton("💰 Depositar", callback_data="deposit_goal")],
                [InlineKeyboardButton("📋 Todas as Metas", callback_data="all_goals")]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def start_add_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar processo de adicionar despesa"""
        await update.message.reply_text(
            "💸 **Nova Despesa**\n\n"
            "📝 Digite o título/descrição da despesa:"
        )
        return WAITING_EXPENSE_TITLE

    async def receive_expense_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber título da despesa"""
        title = update.message.text.strip()
        
        if len(title) < 2:
            await update.message.reply_text(
                "❌ Título muito curto. Digite um título descritivo:"
            )
            return WAITING_EXPENSE_TITLE
        
        context.user_data['expense_title'] = title
        
        await update.message.reply_text(
            f"✅ Título: {title}\n\n"
            "💰 Digite o valor da despesa (ex: 15.50):"
        )
        return WAITING_EXPENSE_AMOUNT

    async def receive_expense_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber valor da despesa"""
        try:
            # Limpar e converter valor
            amount_text = update.message.text.replace(',', '.').replace('R$', '').strip()
            amount = Decimal(amount_text)
            
            if amount <= 0:
                await update.message.reply_text(
                    "❌ O valor deve ser maior que zero. Digite novamente:"
                )
                return WAITING_EXPENSE_AMOUNT
            
            context.user_data['expense_amount'] = amount
            
            # Buscar categorias do usuário
            user_id = context.user_data.get('user_id')
            categories = await self.financial_manager.get_user_categories(user_id, 'expense')
            
            if not categories:
                await self.financial_manager.create_default_categories(user_id)
                categories = await self.financial_manager.get_user_categories(user_id, 'expense')
            
            # Criar teclado com categorias
            keyboard = []
            for i in range(0, len(categories), 2):
                row = []
                for j in range(2):
                    if i + j < len(categories):
                        cat = categories[i + j]
                        row.append(InlineKeyboardButton(
                            f"{cat['icon']} {cat['name']}", 
                            callback_data=f"expense_cat_{cat['id']}"
                        ))
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("➕ Nova Categoria", callback_data="new_expense_category")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Valor: {self.financial_manager.format_currency(amount)}\n\n"
                "📂 Selecione a categoria:",
                reply_markup=reply_markup
            )
            return WAITING_EXPENSE_CATEGORY
            
        except (ValueError, InvalidOperation):
            await update.message.reply_text(
                "❌ Valor inválido. Use apenas números (ex: 15.50):"
            )
            return WAITING_EXPENSE_AMOUNT

    async def process_expense_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar seleção de categoria e criar despesa"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("expense_cat_"):
            category_id = int(query.data.split("_")[2])
            
            # Criar transação
            user_id = context.user_data.get('user_id')
            title = context.user_data.get('expense_title')
            amount = context.user_data.get('expense_amount')
            
            result = await self.financial_manager.create_transaction(
                user_id=user_id,
                title=title,
                amount=amount,
                transaction_type='expense',
                category_id=category_id
            )
            
            if result['success']:
                # Buscar nome da categoria
                categories = await self.financial_manager.get_user_categories(user_id, 'expense')
                category_name = next((cat['name'] for cat in categories if cat['id'] == category_id), 'N/A')
                
                await query.edit_message_text(
                    f"✅ **Despesa cadastrada com sucesso!**\n\n"
                    f"📝 {title}\n"
                    f"💰 {self.financial_manager.format_currency(amount)}\n"
                    f"📂 {category_name}\n"
                    f"📅 {date.today().strftime('%d/%m/%Y')}\n\n"
                    "Use /despesas para ver mais opções.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    f"❌ Erro ao cadastrar despesa: {result['message']}"
                )
            
            # Limpar dados temporários
            context.user_data.pop('expense_title', None)
            context.user_data.pop('expense_amount', None)
            
            return ConversationHandler.END

    async def start_add_goal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar processo de adicionar meta"""
        await update.message.reply_text(
            "🎯 **Nova Meta Financeira**\n\n"
            "📝 Digite o nome/título da sua meta:"
        )
        return WAITING_GOAL_TITLE

    async def receive_goal_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber título da meta"""
        title = update.message.text.strip()
        
        if len(title) < 3:
            await update.message.reply_text(
                "❌ Título muito curto. Digite um título descritivo:"
            )
            return WAITING_GOAL_TITLE
        
        context.user_data['goal_title'] = title
        
        await update.message.reply_text(
            f"✅ Meta: {title}\n\n"
            "💰 Digite o valor objetivo (ex: 5000.00):"
        )
        return WAITING_GOAL_AMOUNT

    async def receive_goal_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber valor da meta"""
        try:
            amount_text = update.message.text.replace(',', '.').replace('R$', '').strip()
            amount = Decimal(amount_text)
            
            if amount <= 0:
                await update.message.reply_text(
                    "❌ O valor deve ser maior que zero. Digite novamente:"
                )
                return WAITING_GOAL_AMOUNT
            
            context.user_data['goal_amount'] = amount
            
            # Teclado com tipos de meta
            keyboard = [
                [InlineKeyboardButton("💰 Poupança", callback_data="goal_type_saving")],
                [InlineKeyboardButton("📈 Investimento", callback_data="goal_type_investment")],
                [InlineKeyboardButton("🏖️ Viagem", callback_data="goal_type_vacation")],
                [InlineKeyboardButton("🏠 Compra", callback_data="goal_type_purchase")],
                [InlineKeyboardButton("🆘 Emergência", callback_data="goal_type_emergency_fund")],
                [InlineKeyboardButton("💳 Quitação", callback_data="goal_type_debt_payment")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ Valor: {self.financial_manager.format_currency(amount)}\n\n"
                "🎯 Qual o tipo da sua meta?",
                reply_markup=reply_markup
            )
            return WAITING_GOAL_TYPE
            
        except (ValueError, InvalidOperation):
            await update.message.reply_text(
                "❌ Valor inválido. Use apenas números (ex: 5000.00):"
            )
            return WAITING_GOAL_AMOUNT

    async def process_goal_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar tipo de meta e criar"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("goal_type_"):
            goal_type = query.data.split("goal_type_")[1]
            
            # Criar meta
            user_id = context.user_data.get('user_id')
            title = context.user_data.get('goal_title')
            amount = context.user_data.get('goal_amount')
            
            result = await self.financial_manager.create_goal(
                user_id=user_id,
                title=title,
                goal_type=goal_type,
                target_amount=amount
            )
            
            if result['success']:
                emoji = self.financial_manager.get_goal_type_emoji(goal_type)
                type_names = {
                    'saving': 'Poupança',
                    'investment': 'Investimento', 
                    'vacation': 'Viagem',
                    'purchase': 'Compra',
                    'emergency_fund': 'Emergência',
                    'debt_payment': 'Quitação'
                }
                
                await query.edit_message_text(
                    f"🎉 **Meta criada com sucesso!**\n\n"
                    f"{emoji} **{title}**\n"
                    f"💰 Objetivo: {self.financial_manager.format_currency(amount)}\n"
                    f"🎯 Tipo: {type_names.get(goal_type, goal_type)}\n"
                    f"📈 Progresso: 0%\n\n"
                    "Use /metas para acompanhar o progresso!",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    f"❌ Erro ao criar meta: {result['message']}"
                )
            
            # Limpar dados temporários
            context.user_data.pop('goal_title', None)
            context.user_data.pop('goal_amount', None)
            
            return ConversationHandler.END

    async def expense_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Relatório detalhado de despesas"""
        if not self.is_authenticated(context):
            await update.message.reply_text(
                "❌ Você precisa fazer login primeiro. Use /login"
            )
            return

        user_id = context.user_data.get('user_id')
        
        # Análise dos últimos 30 dias
        analysis = await self.financial_manager.get_spending_analysis(user_id, 30)
        
        if not analysis or analysis.get('expense_count', 0) == 0:
            await update.message.reply_text(
                "📊 **Relatório de Gastos**\n\n"
                "😴 Você ainda não possui gastos registrados nos últimos 30 dias.\n\n"
                "Use /despesas para começar a registrar seus gastos!"
            )
            return
        
        message = f"""📊 **Relatório de Gastos - 30 dias**

💰 **Resumo:**
• Total gasto: {self.financial_manager.format_currency(analysis['total_spent'])}
• Média por gasto: {self.financial_manager.format_currency(analysis['avg_expense'])}
• Média diária: {self.financial_manager.format_currency(analysis['daily_average'])}
• Número de gastos: {analysis['expense_count']}
• Maior gasto: {self.financial_manager.format_currency(analysis['max_expense'])}

📈 **Tendência:** {analysis['trend_percent']:+.1f}% vs período anterior

🏆 **Top Categorias:**"""

        for i, cat in enumerate(analysis['top_categories'][:5], 1):
            percentage = (cat['total'] / analysis['total_spent'] * 100) if analysis['total_spent'] > 0 else 0
            message += f"\n{i}. {cat['icon']} {cat['name']}: {self.financial_manager.format_currency(cat['total'])} ({percentage:.1f}%)"

        keyboard = [
            [InlineKeyboardButton("💸 Nova Despesa", callback_data="add_expense")],
            [InlineKeyboardButton("📊 Análise IA", callback_data="ai_expense_analysis")],
            [InlineKeyboardButton("🎯 Criar Meta de Economia", callback_data="saving_goal")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def financial_summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resumo financeiro completo"""
        if not self.is_authenticated(context):
            await update.message.reply_text(
                "❌ Você precisa fazer login primeiro. Use /login"
            )
            return

        user_id = context.user_data.get('user_id')
        
        # Resumo do mês atual
        month_start = date.today().replace(day=1)
        summary = await self.financial_manager.get_monthly_summary(user_id, month_start)
        
        # Metas ativas
        goals = await self.financial_manager.get_user_goals(user_id)
        
        # Alertas não lidos
        alerts = await self.financial_manager.get_user_alerts(user_id, unread_only=True)

        balance = summary.get('balance', 0)
        balance_emoji = "📈" if balance >= 0 else "📉"
        
        message = f"""📋 **Resumo Financeiro - {date.today().strftime('%B %Y')}**

{balance_emoji} **Saldo do Mês:**
• Receitas: {self.financial_manager.format_currency(summary.get('total_income', 0))}
• Despesas: {self.financial_manager.format_currency(summary.get('total_expenses', 0))}
• Saldo: {self.financial_manager.format_currency(balance)}

🎯 **Metas Ativas:** {len(goals)}"""

        if goals:
            message += "\n"
            for goal in goals[:3]:  # Top 3 metas
                percentage = self.financial_manager.calculate_percentage(
                    goal['current_amount'], goal['target_amount']
                )
                emoji = self.financial_manager.get_goal_type_emoji(goal['goal_type'])
                message += f"\n{emoji} {goal['title']}: {percentage:.1f}%"

        if alerts:
            message += f"\n\n🔔 **Alertas:** {len(alerts)} não lidos"

        keyboard = [
            [InlineKeyboardButton("💸 Despesas", callback_data="manage_expenses"),
             InlineKeyboardButton("💰 Receitas", callback_data="manage_income")],
            [InlineKeyboardButton("🎯 Metas", callback_data="manage_goals"),
             InlineKeyboardButton("📊 Relatórios", callback_data="reports")],
            [InlineKeyboardButton("🔔 Alertas", callback_data="view_alerts"),
             InlineKeyboardButton("⚙️ Configurações", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )