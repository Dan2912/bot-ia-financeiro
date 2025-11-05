#!/usr/bin/env python3
"""
Bot Telegram IA Financeiro - Railway Simple Runner
Versão minimalista sem conflitos de event loop
"""

import os
import sys
import logging
from telegram.ext import Application

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Verificar se temos o token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN não configurado!")
    sys.exit(1)

def main():
    """Execução simples do bot"""
    logger.info("🤖 Iniciando Bot Telegram IA Financeiro")
    
    try:
        # Importar dependências locais
        from main import FinancialBot
        
        # Criar instância do bot
        bot = FinancialBot()
        
        # Inicializar banco de dados de forma síncrona
        import asyncio
        
        # Verificar se há um loop rodando
        try:
            loop = asyncio.get_running_loop()
            logger.info("Loop detectado, usando existente")
        except RuntimeError:
            # Criar novo loop
            logger.info("Criando novo loop")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Inicializar banco
        loop.run_until_complete(bot.init_database())
        
        # Configurar aplicação completa
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Comandos básicos
        from telegram.ext import CommandHandler, CallbackQueryHandler
        application.add_handler(CommandHandler("start", bot.start_command))
        
        # Handler para callbacks dos botões
        application.add_handler(CallbackQueryHandler(bot.callback_handler))
        
        # Tentar adicionar funcionalidades avançadas
        try:
            # Importar bot_commands apenas se disponível
            from bot_commands import (BotCommands, WAITING_FULL_NAME, WAITING_EMAIL, WAITING_PASSWORD, 
                                     WAITING_LOGIN_PASSWORD, WAITING_OLD_PASSWORD, WAITING_NEW_PASSWORD)
            from telegram.ext import ConversationHandler, MessageHandler, filters
            
            bot_commands = BotCommands(bot)
            
            # ConversationHandler para cadastro
            registration_handler = ConversationHandler(
                entry_points=[CommandHandler('cadastro', bot_commands.start_registration)],
                states={
                    WAITING_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_full_name)],
                    WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_email)],
                    WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_password)],
                },
                fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)],
            )
            
            # ConversationHandler para login
            login_handler = ConversationHandler(
                entry_points=[CommandHandler('login', bot_commands.login_command)],
                states={
                    WAITING_LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_login_password)],
                },
                fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)],
            )
            
            # ConversationHandler para alteração de senha
            change_password_handler = ConversationHandler(
                entry_points=[CommandHandler('trocar_senha', bot_commands.change_password_command)],
                states={
                    WAITING_OLD_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_old_password)],
                    WAITING_NEW_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_new_password)],
                },
                fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)],
            )
            
            # Adicionar conversation handlers
            application.add_handler(registration_handler)
            application.add_handler(login_handler)
            application.add_handler(change_password_handler)
            
            # Comandos de autenticação
            application.add_handler(CommandHandler('perfil', bot_commands.profile_command))
            application.add_handler(CommandHandler('logout', bot_commands.logout_command))
            
            # Adicionar funcionalidades financeiras
            try:
                # Criar função simples de saldo
                async def saldo_command(update, context):
                    """Comando de saldo simplificado"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        # Buscar contas do usuário
                        accounts = await bot.get_user_accounts(user['id'])
                        
                        if not accounts:
                            await update.message.reply_text(
                                "🏦 Você ainda não conectou nenhuma conta bancária.\n\n"
                                "Use o menu principal → 🏦 Conectar Banco para vincular seus bancos via Pluggy."
                            )
                            return
                        
                        text = "💰 *Seus Saldos:*\n\n"
                        total_balance = 0
                        
                        for account in accounts:
                            text += f"🏦 *{account.get('bank_name', 'Banco')}*\n"
                            text += f"Tipo: {account.get('account_type', 'Conta')}\n" 
                            balance = float(account.get('balance', 0))
                            text += f"Saldo: R$ {balance:,.2f}\n\n"
                            total_balance += balance
                        
                        text += f"💵 *Total Geral: R$ {total_balance:,.2f}*"
                        
                        await update.message.reply_text(text, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro ao buscar saldo: {e}")
                        await update.message.reply_text(
                            "❌ Erro ao consultar saldo. Tente conectar suas contas bancárias primeiro.\n\n"
                            "Use /start → 🏦 Conectar Banco"
                        )
                
                # Criar função para conectar banco
                async def conectar_command(update, context):
                    """Comando para conectar conta bancária via Pluggy"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        # Verificar credenciais Pluggy
                        client_id = os.getenv('PLUGGY_CLIENT_ID')
                        client_secret = os.getenv('PLUGGY_CLIENT_SECRET')
                        
                        if not client_id or not client_secret:
                            await update.message.reply_text(
                                "❌ **Serviço temporariamente indisponível**\n\n"
                                "A integração bancária está sendo configurada.\n"
                                "Tente novamente em alguns minutos.\n\n"
                                "💡 Use /saldo para ver se já tem contas conectadas."
                            )
                            return
                        
                        # Gerar Connect Token
                        connect_url = await bot.generate_connect_url(user['id'])
                        
                        if connect_url:
                            text = f"""🏦 **Conectar Conta Bancária**

🔗 **Link personalizado gerado com sucesso!**

**Bancos disponíveis:**
🏦 Banco Inter • 💜 Nubank • 🔴 Bradesco
🔶 Itaú • 🔴 Santander • 🟡 Banco do Brasil
⚫ C6 Bank • 🟢 BTG Pactual • 📱 PicPay
💰 XP • 🟣 Will Bank • **+190 outros!**

🔒 **Processo 100% seguro:**
1️⃣ Clique no seu link personalizado abaixo
2️⃣ Escolha seu banco na lista
3️⃣ Faça login (suas credenciais ficam só no Pluggy)
4️⃣ Autorize o acesso aos dados financeiros
5️⃣ Pronto! Dados sincronizados automaticamente

**🔗 SEU LINK PERSONALIZADO:**
{connect_url}

⚠️ **Segurança garantida:**
• Certificado pelo Banco Central
• Conformidade LGPD
• Criptografia end-to-end
• Revogação a qualquer momento

� **Após conectar, use /saldo para ver seus dados!**"""
                        else:
                            # Modo offline - instruções manuais
                            text = """🏦 **Conectar Conta Bancária**

🔧 **Serviço temporariamente em manutenção**

**Enquanto isso, você pode:**

📱 **Via App do seu banco:**
1️⃣ Acesse o Open Banking no app
2️⃣ Procure por "Pluggy" ou nosso serviço  
3️⃣ Autorize o compartilhamento de dados

💻 **Via Web:**
• Acesse: https://pluggy.ai
• Escolha seu banco e conecte

**Bancos principais:**
🏦 Banco Inter • 💜 Nubank • 🔴 Bradesco
🔶 Itaú • 🔴 Santander • 🟡 Banco do Brasil
⚫ C6 Bank • 🟢 BTG Pactual • 📱 PicPay
💰 XP Investimentos • 🏛️ Caixa

⚠️ **O serviço será normalizado em breve!**
Tente novamente em alguns minutos.

💡 Use /saldo para verificar contas já conectadas."""
                        
                        await update.message.reply_text(text, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro no comando conectar: {e}")
                        await update.message.reply_text(
                            "❌ **Erro no serviço de conexão bancária**\n\n"
                            "Tente novamente em alguns instantes.\n\n"
                            "💡 Use /saldo para ver contas já conectadas."
                        )
                
                # Comandos principais
                application.add_handler(CommandHandler("saldo", saldo_command))
                application.add_handler(CommandHandler("conectar", conectar_command))
                
                # Tentar adicionar outros comandos se existirem
                try:
                    application.add_handler(CommandHandler("cartoes", bot_commands.cards_callback))
                except:
                    logger.warning("Comando cartões não disponível")
                
                try:
                    application.add_handler(CommandHandler("gastos", bot_commands.ai_analysis_callback))
                    application.add_handler(CommandHandler("analise", bot_commands.ai_analysis_callback))
                except:
                    logger.warning("Comandos de análise não disponíveis")
                
                # Funcionalidades de despesas e metas
                from bot_commands import WAITING_EXPENSE_TITLE, WAITING_EXPENSE_AMOUNT, WAITING_EXPENSE_CATEGORY
                from bot_commands import WAITING_GOAL_TITLE, WAITING_GOAL_AMOUNT, WAITING_GOAL_TYPE
                
                # ConversationHandlers financeiros
                expense_handler = ConversationHandler(
                    entry_points=[CommandHandler('despesas', bot_commands.expenses_command)],
                    states={
                        WAITING_EXPENSE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_expense_title)],
                        WAITING_EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_expense_amount)],
                        WAITING_EXPENSE_CATEGORY: [CallbackQueryHandler(bot_commands.process_expense_category)],
                    },
                    fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)]
                )
                
                goal_handler = ConversationHandler(
                    entry_points=[CommandHandler('metas', bot_commands.goals_command)],
                    states={
                        WAITING_GOAL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_goal_title)],
                        WAITING_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_goal_amount)],
                        WAITING_GOAL_TYPE: [CallbackQueryHandler(bot_commands.process_goal_type)],
                    },
                    fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)]
                )
                
                application.add_handler(expense_handler)
                application.add_handler(goal_handler)
                
                # Comandos financeiros diretos
                application.add_handler(CommandHandler('relatorio', bot_commands.expense_report_command))
                application.add_handler(CommandHandler('resumo', bot_commands.financial_summary_command))
                
                # Comandos de atalho
                application.add_handler(CommandHandler('nova_despesa', bot_commands.start_add_expense))
                application.add_handler(CommandHandler('nova_meta', bot_commands.start_add_goal))
                
                logger.info("💰 Funcionalidades financeiras carregadas (saldo, cartões, IA)")
                
            except Exception as e:
                logger.warning(f"⚠️ Algumas funcionalidades financeiras não disponíveis: {e}")
            
            logger.info("✅ Funcionalidades avançadas carregadas")
            
        except ImportError as e:
            logger.warning(f"⚠️ Funcionalidades avançadas não disponíveis: {e}")
            logger.info("ℹ️ Bot funcionará apenas com comandos básicos")
        
        logger.info("✅ Bot configurado, iniciando polling")
        
        # Executar bot de forma simples
        application.run_polling()
        
    except Exception as e:
        logger.error(f"💥 Erro fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()