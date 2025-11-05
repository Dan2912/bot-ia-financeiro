from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal, InvalidOperation
import json
import bcrypt
import re

logger = logging.getLogger(__name__)

# Estados da conversa para autenticação
WAITING_FULL_NAME, WAITING_EMAIL, WAITING_PASSWORD, WAITING_LOGIN_PASSWORD, WAITING_OLD_PASSWORD, WAITING_NEW_PASSWORD = range(6)

# Estados para gestão financeira (mantidos para compatibilidade)
WAITING_EXPENSE_TITLE, WAITING_EXPENSE_AMOUNT, WAITING_EXPENSE_CATEGORY, WAITING_GOAL_TITLE, WAITING_GOAL_AMOUNT, WAITING_GOAL_TYPE, WAITING_GOAL_DATE = range(6, 13)

class BotCommands:
    """Comandos avançados do bot com autenticação simplificada"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
    
    def validate_email(self, email):
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def hash_password(self, password):
        """Hash da senha com bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password, hashed_password):
        """Verificar senha contra hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    # Comandos de autenticação simplificados
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar processo de cadastro"""
        await update.message.reply_text(
            "👤 **Cadastro de Usuário**\n\n"
            "Para usar todas as funcionalidades do bot, vamos fazer seu cadastro.\n\n"
            "**Digite seu nome completo:**"
        )
        return WAITING_FULL_NAME
    
    async def receive_full_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber nome completo"""
        full_name = update.message.text.strip()
        
        if len(full_name) < 2:
            await update.message.reply_text(
                "❌ Nome muito curto. Digite seu nome completo:"
            )
            return WAITING_FULL_NAME
        
        context.user_data['registration_name'] = full_name
        
        await update.message.reply_text(
            f"✅ Nome: {full_name}\n\n"
            "📧 **Agora digite seu email:**"
        )
        return WAITING_EMAIL
    
    async def receive_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber email"""
        email_text = update.message.text.strip().lower()
        
        if not self.validate_email(email_text):
            await update.message.reply_text(
                "❌ Email inválido. Digite um email válido:\n"
                "Exemplo: seuemail@gmail.com"
            )
            return WAITING_EMAIL
        
        # Verificar se email já existe
        try:
            existing = await self.bot.execute_query_one(
                "SELECT id FROM users WHERE email = $1", (email_text,)
            )
            
            if existing:
                await update.message.reply_text(
                    "❌ **Email já cadastrado!**\n\n"
                    "Use `/login` para entrar ou tente outro email."
                )
                return ConversationHandler.END
        except Exception as e:
            logger.error(f"Erro ao verificar email: {e}")
        
        context.user_data['registration_email'] = email_text
        
        await update.message.reply_text(
            f"✅ Email: {email_text}\n\n"
            "🔒 **Agora crie uma senha:**\n"
            "• Mínimo 6 caracteres\n"
            "• Use letras, números e símbolos"
        )
        return WAITING_PASSWORD
    
    async def receive_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber senha"""
        password = update.message.text.strip()
        
        if len(password) < 6:
            await update.message.reply_text(
                "❌ Senha muito fraca. Use pelo menos 6 caracteres:"
            )
            return WAITING_PASSWORD
        
        # Criar usuário
        try:
            telegram_user = update.effective_user
            full_name = context.user_data['registration_name']
            email = context.user_data['registration_email']
            hashed_password = self.hash_password(password)
            
            query = """
                INSERT INTO users (telegram_id, telegram_username, full_name, email, password_hash, is_active)
                VALUES ($1, $2, $3, $4, $5, true)
                RETURNING id, created_at
            """
            
            result = await self.bot.execute_query_one(
                query, 
                (telegram_user.id, telegram_user.username, full_name, email, hashed_password)
            )
            
            if result:
                await update.message.reply_text(
                    "✅ **Cadastro realizado com sucesso!**\n\n"
                    f"👤 Nome: {full_name}\n"
                    f"📧 Email: {email}\n"
                    f"🆔 ID: {result['id']}\n\n"
                    "**Comandos disponíveis:**\n"
                    "• `/receitas` - Adicionar receitas\n"
                    "• `/gastos` - Registrar despesas\n"
                    "• `/saldo` - Ver contas\n"
                    "• `/perfil` - Seu perfil"
                )
                
                # Limpar dados temporários
                context.user_data.clear()
                return ConversationHandler.END
            else:
                raise Exception("Falha ao criar usuário")
                
        except Exception as e:
            logger.error(f"Erro no cadastro: {e}")
            await update.message.reply_text(
                "❌ **Erro ao criar conta**\n\n"
                "Tente novamente em alguns instantes."
            )
            return ConversationHandler.END
    
    async def login_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando de login"""
        telegram_user = update.effective_user
        
        # Verificar se usuário existe
        try:
            user = await self.bot.execute_query_one(
                "SELECT id, email, full_name FROM users WHERE telegram_id = $1",
                (telegram_user.id,)
            )
            
            if not user:
                await update.message.reply_text(
                    "❌ **Usuário não encontrado**\n\n"
                    "Use `/cadastro` para criar uma conta primeiro."
                )
                return ConversationHandler.END
            
            context.user_data['login_user'] = user
            
            await update.message.reply_text(
                f"🔐 **Login**\n\n"
                f"👤 {user['full_name']}\n"
                f"📧 {user['email']}\n\n"
                f"**Digite sua senha:**"
            )
            return WAITING_LOGIN_PASSWORD
            
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            await update.message.reply_text(
                "❌ **Erro no sistema de login**\n\n"
                "Tente novamente em alguns instantes."
            )
            return ConversationHandler.END
    
    async def receive_login_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber senha do login"""
        password = update.message.text.strip()
        user = context.user_data.get('login_user')
        
        if not user:
            await update.message.reply_text("❌ Sessão expirada. Use `/login` novamente.")
            return ConversationHandler.END
        
        try:
            # Buscar hash da senha
            user_data = await self.bot.execute_query_one(
                "SELECT password_hash FROM users WHERE id = $1",
                (user['id'],)
            )
            
            if user_data and self.verify_password(password, user_data['password_hash']):
                await update.message.reply_text(
                    "✅ **Login realizado com sucesso!**\n\n"
                    f"Bem-vindo de volta, {user['full_name']}!\n\n"
                    "**Comandos disponíveis:**\n"
                    "• `/receitas` - Adicionar receitas\n"
                    "• `/gastos` - Registrar despesas\n"
                    "• `/saldo` - Ver contas\n"
                    "• `/perfil` - Seu perfil"
                )
            else:
                await update.message.reply_text(
                    "❌ **Senha incorreta**\n\n"
                    "Tente novamente ou use `/cadastro` se não tem conta."
                )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            await update.message.reply_text(
                "❌ **Erro na autenticação**\n\n"
                "Tente novamente em alguns instantes."
            )
            return ConversationHandler.END
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostrar perfil do usuário"""
        try:
            user = await self.bot.get_or_create_user(update.effective_user)
            
            # Buscar estatísticas
            stats_query = """
                SELECT 
                    COUNT(CASE WHEN type = 'income' THEN 1 END) as receitas,
                    COUNT(CASE WHEN type = 'expense' THEN 1 END) as despesas,
                    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_receitas,
                    COALESCE(SUM(CASE WHEN type = 'expense' THEN ABS(amount) ELSE 0 END), 0) as total_despesas
                FROM transactions 
                WHERE user_id = $1
            """
            
            stats = await self.bot.execute_query_one(stats_query, (user['id'],))
            
            text = f"""👤 **Seu Perfil**

**Dados pessoais:**
🆔 ID: {user['id']}
👤 Nome: {user['full_name']}
📧 Email: {user.get('email', 'Não cadastrado')}
📅 Membro desde: {user['created_at'].strftime('%d/%m/%Y')}

**Estatísticas:**"""
            
            if stats:
                text += f"""
💰 Receitas: {stats['receitas']} (R$ {float(stats['total_receitas']):,.2f})
💸 Despesas: {stats['despesas']} (R$ {float(stats['total_despesas']):,.2f})
📊 Saldo: R$ {float(stats['total_receitas'] - stats['total_despesas']):,.2f}"""
            else:
                text += """
💰 Receitas: 0
💸 Despesas: 0  
📊 Saldo: R$ 0,00"""
            
            text += """

**Comandos úteis:**
• `/receitas` - Adicionar receita
• `/gastos` - Registrar despesa
• `/saldo` - Ver contas
• `/trocar_senha` - Alterar senha"""
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Erro ao mostrar perfil: {e}")
            await update.message.reply_text(
                "❌ **Erro ao carregar perfil**\n\n"
                "Tente novamente em alguns instantes."
            )
    
    async def change_password_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar alteração de senha"""
        user = await self.bot.get_or_create_user(update.effective_user)
        
        if not user.get('email'):
            await update.message.reply_text(
                "❌ **Sem email cadastrado**\n\n"
                "Use `/cadastro` para criar conta completa."
            )
            return ConversationHandler.END
        
        context.user_data['change_password_user'] = user
        
        await update.message.reply_text(
            "🔐 **Alterar Senha**\n\n"
            "Digite sua senha atual:"
        )
        return WAITING_OLD_PASSWORD
    
    async def receive_old_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber senha atual"""
        old_password = update.message.text.strip()
        user = context.user_data.get('change_password_user')
        
        if not user:
            await update.message.reply_text("❌ Sessão expirada.")
            return ConversationHandler.END
        
        try:
            # Verificar senha atual
            user_data = await self.bot.execute_query_one(
                "SELECT password_hash FROM users WHERE id = $1",
                (user['id'],)
            )
            
            if not user_data or not self.verify_password(old_password, user_data['password_hash']):
                await update.message.reply_text(
                    "❌ **Senha atual incorreta**\n\n"
                    "Tente novamente."
                )
                return WAITING_OLD_PASSWORD
            
            await update.message.reply_text(
                "✅ Senha confirmada!\n\n"
                "🔒 **Digite sua nova senha:**\n"
                "• Mínimo 6 caracteres\n"
                "• Use letras, números e símbolos"
            )
            return WAITING_NEW_PASSWORD
            
        except Exception as e:
            logger.error(f"Erro na verificação de senha: {e}")
            await update.message.reply_text("❌ Erro no sistema.")
            return ConversationHandler.END
    
    async def receive_new_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receber nova senha"""
        new_password = update.message.text.strip()
        user = context.user_data.get('change_password_user')
        
        if not user:
            await update.message.reply_text("❌ Sessão expirada.")
            return ConversationHandler.END
        
        if len(new_password) < 6:
            await update.message.reply_text(
                "❌ Senha muito fraca. Use pelo menos 6 caracteres:"
            )
            return WAITING_NEW_PASSWORD
        
        try:
            # Atualizar senha
            hashed_password = self.hash_password(new_password)
            
            await self.bot.execute_query_one(
                "UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                (hashed_password, user['id'])
            )
            
            await update.message.reply_text(
                "✅ **Senha alterada com sucesso!**\n\n"
                "Sua nova senha já está ativa."
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Erro ao alterar senha: {e}")
            await update.message.reply_text("❌ Erro ao alterar senha.")
            return ConversationHandler.END
    
    async def logout_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Logout do usuário"""
        context.user_data.clear()
        await update.message.reply_text(
            "👋 **Logout realizado**\n\n"
            "Sessão encerrada. Use `/login` para entrar novamente."
        )
    
    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancelar operação em andamento"""
        context.user_data.clear()
        await update.message.reply_text(
            "❌ **Operação cancelada**\n\n"
            "Use `/start` para ver as opções disponíveis."
        )
        return ConversationHandler.END
    
    # Métodos de compatibilidade para funcionalidades financeiras básicas
    async def cards_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para cartões (simplificado)"""
        await update.message.reply_text(
            "💳 **Gestão de Cartões**\n\n"
            "Funcionalidade em desenvolvimento.\n"
            "Use `/gastos` para registrar despesas no cartão."
        )
    
    async def ai_analysis_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para análise IA (simplificado)"""
        await update.message.reply_text(
            "🤖 **Análise por IA**\n\n"
            "Funcionalidade em desenvolvimento.\n"
            "Use `/resumo` para ver relatórios básicos."
        )
    
    # Métodos vazios para compatibilidade com conversation handlers antigos
    async def expenses_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END
    
    async def receive_expense_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END
    
    async def receive_expense_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END
    
    async def process_expense_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END
    
    async def goals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END
    
    async def receive_goal_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END
    
    async def receive_goal_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END
    
    async def process_goal_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END
    
    async def expense_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Relatório em desenvolvimento. Use `/saldo`.")
    
    async def financial_summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Resumo em desenvolvimento. Use `/saldo`.")
    
    async def start_add_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Use `/gastos` para o novo sistema de despesas.")
    
    async def start_add_goal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Sistema de metas em desenvolvimento.")