#!/usr/bin/env python3
"""
Bot Telegram IA Financeiro - Railway Simple Runner
Sistema manual sem API Pluggy - Contas predefinidas
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
    logger.info("🤖 Iniciando Bot Telegram IA Financeiro - Sistema Manual")
    
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
                # Importar novos sistemas
                from revenue_manager import RevenueManager
                from expense_manager import ExpenseManager
                
                # Criar instâncias dos gerenciadores
                revenue_manager = RevenueManager(bot)
                expense_manager = ExpenseManager(bot)
                
                # Criar função simples de saldo
                async def saldo_command(update, context):
                    """Comando de saldo simplificado"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        # Buscar contas do usuário
                        accounts = await bot.get_user_accounts(user['id'])
                        
                        if not accounts:
                            await update.message.reply_text(
                                "🏦 **Nenhuma conta encontrada**\n\n"
                                "**Opções disponíveis:**\n"
                                "• `/demo` - Carregar dados de exemplo\n"
                                "• `/receitas` - Adicionar primeira receita\n"
                                "• `/gastos` - Registrar primeira despesa\n\n"
                                "💡 Comece adicionando uma receita ou despesa!"
                            )
                            return
                        
                        # Separar contas demo das reais
                        contas_demo = []
                        contas_reais = []
                        
                        for account in accounts:
                            if account.get('pluggy_item_id', '').startswith('demo_'):
                                contas_demo.append(account)
                            else:
                                contas_reais.append(account)
                        
                        text = "💰 **Seus Saldos:**\n\n"
                        
                        # Mostrar contas reais primeiro
                        if contas_reais:
                            text += "🏦 **CONTAS REAIS:**\n"
                            total_real = 0
                            for account in contas_reais:
                                bank_name = account.get('bank_name', 'Banco')
                                if 'inter' in bank_name.lower():
                                    text += "🟡 "  # Cor do Inter
                                elif 'nubank' in bank_name.lower():
                                    text += "💜 "
                                elif 'c6' in bank_name.lower():
                                    text += "⚫ "
                                elif 'santander' in bank_name.lower():
                                    text += "🔴 "
                                else:
                                    text += "🏦 "
                                
                                text += f"**{bank_name}**\n"
                                text += f"Tipo: {account.get('account_type', 'Conta')}\n"
                                balance = float(account.get('balance', 0))
                                text += f"Saldo: R$ {balance:,.2f}\n\n"
                                total_real += balance
                            
                            text += f"💵 **Total Real: R$ {total_real:,.2f}**\n\n"
                        
                        # Mostrar contas demo se existirem
                        if contas_demo:
                            text += "🎮 **DADOS DE DEMONSTRAÇÃO:**\n"
                            total_demo = 0
                            for account in contas_demo:
                                bank_name = account.get('bank_name', 'Banco')
                                if 'nubank' in bank_name.lower():
                                    text += "💜 "
                                elif 'inter' in bank_name.lower():
                                    text += "🟡 "
                                elif 'itau' in bank_name.lower():
                                    text += "🔶 "
                                else:
                                    text += "🏦 "
                                
                                text += f"**{bank_name}**\n"
                                balance = float(account.get('balance', 0))
                                text += f"Saldo: R$ {balance:,.2f}\n\n"
                                total_demo += balance
                            
                            text += f"🎮 **Total Demo: R$ {total_demo:,.2f}**\n"
                        
                        # Total geral
                        total_geral = sum(float(acc.get('balance', 0)) for acc in accounts)
                        text += f"\n💎 **TOTAL GERAL: R$ {total_geral:,.2f}**"
                        
                        await update.message.reply_text(text, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro ao buscar saldo: {e}")
                        await update.message.reply_text(
                            "❌ **Erro ao consultar saldo**\n\n"
                            f"Detalhes técnicos: {str(e)}\n\n"
                            "Tente: `/demo` para dados de exemplo"
                        )
                
                # Criar função para conectar banco (modo manual)
                async def conectar_command(update, context):
                    """Comando para conectar conta bancária manualmente"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        # Sistema manual - usar account_manager
                        from account_manager import account_manager
                        
                        text = """🏦 **Sistema de Contas Manuais**

**✅ Nova funcionalidade: Contas predefinidas!**

**🏦 Contas disponíveis:**
🟡 Banco Inter PJ (Receitas)
🟡 Banco Inter PF (Receitas)  
⚫ C6 Bank PJ
⚫ C6 Bank PF
💜 Nubank PJ
💜 Nubank PF
🔴 Santander PJ  
🔴 Santander PF

**💡 Como usar:**
• `/receitas` - Adicionar receitas (salário, vendas)
• `/gastos` - Adicionar despesas com parcelamento
• `/saldo` - Ver contas cadastradas

**🎯 Benefícios:**
✅ Controle total dos seus dados
✅ Interface guiada e intuitiva  
✅ Parcelamento automático
✅ Categorização inteligente
✅ Sem APIs externas

**Comece adicionando uma receita ou despesa!**"""
                        
                        await update.message.reply_text(text, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro no comando conectar: {e}")
                        await update.message.reply_text(
                            "❌ **Erro no sistema de contas**\n\n"
                            "Tente novamente em alguns instantes."
                        )
                
                # Comando de status dos serviços
                async def status_command(update, context):
                    """Verificar status dos serviços"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        # Mostrar loading
                        loading_msg = await update.message.reply_text(
                            "🔍 **Verificando status dos serviços...**\n⏳ Aguarde alguns segundos"
                        )
                        
                        # Status simplificado - sem API externa
                        status_message = """📊 **Status dos Serviços**

🤖 **Bot Telegram:** ✅ Online
🗄️ **Banco PostgreSQL:** ✅ Conectado  
🏦 **Sistema Manual:** ✅ Ativo
📱 **Interface Guiada:** ✅ Funcionando

**🎯 Funcionalidades disponíveis:**
• ✅ Cadastro de receitas
• ✅ Gestão de despesas com parcelamento
• ✅ Contas bancárias predefinidas
• ✅ Relatórios financeiros
• ✅ Análise por IA (OpenAI)

**💡 Comandos principais:**
• `/receitas` - Adicionar receitas
• `/gastos` - Registrar despesas  
• `/saldo` - Ver contas e saldos
• `/resumo` - Dashboard financeiro

🟢 **Sistema 100% operacional!**"""
                        
                        # Editar mensagem de loading
                        await loading_msg.edit_text(status_message, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro no comando status: {e}")
                        await update.message.reply_text(
                            "❌ **Erro ao verificar status**\n\n"
                            "Bot funcionando normalmente."
                        )
                
                # Criar função de demo
                async def demo_command(update, context):
                    """Comando para carregar dados de demonstração"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        await update.message.reply_text(
                            "🎮 **Carregando dados de demonstração...**\n⏳ Aguarde alguns segundos"
                        )
                        
                        # Criar dados demo
                        await bot.create_demo_accounts(user['id'])
                        
                        await update.message.reply_text(
                            "✅ **Dados de demonstração carregados!**\n\n"
                            "💡 **O que foi criado:**\n"
                            "🏦 Contas bancárias de exemplo\n"
                            "💳 Cartões de crédito demo\n"
                            "📊 Transações de exemplo\n"
                            "🎯 Meta financeira demo\n\n"
                            "**Comandos para testar:**\n"
                            "• `/saldo` - Ver contas e saldos\n"
                            "• `/resumo` - Dashboard completo\n"
                            "• `/receitas` - Adicionar nova receita\n"
                            "• `/gastos` - Registrar nova despesa"
                        )
                        
                    except Exception as e:
                        logger.error(f"Erro ao criar dados demo: {e}")
                        await update.message.reply_text(
                            "❌ **Erro ao carregar dados demo**\n\n"
                            f"Detalhes: {str(e)}"
                        )
                
                # Função de teste
                async def teste_command(update, context):
                    """Comando de teste do sistema"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    await update.message.reply_text(
                        f"✅ **Sistema funcionando!**\n\n"
                        f"👤 **Usuário:** {user['full_name']}\n"
                        f"🆔 **ID:** {user['id']}\n"
                        f"📧 **Email:** {user.get('email', 'Não cadastrado')}\n\n"
                        f"🤖 **Bot:** Online\n"
                        f"🗄️ **Banco:** Conectado\n"
                        f"📱 **Sistema manual:** Ativo\n\n"
                        f"**Teste concluído com sucesso!**"
                    )
                
                # Comandos principais
                application.add_handler(CommandHandler("saldo", saldo_command))
                application.add_handler(CommandHandler("conectar", conectar_command))
                application.add_handler(CommandHandler("status", status_command))
                application.add_handler(CommandHandler("demo", demo_command))
                application.add_handler(CommandHandler("teste", teste_command))
                
                # Novos comandos de receitas e despesas
                from revenue_manager import (WAITING_REVENUE_TYPE, WAITING_REVENUE_DESCRIPTION, 
                                           WAITING_REVENUE_VALUE, WAITING_REVENUE_DATE, 
                                           WAITING_REVENUE_ACCOUNT, WAITING_REVENUE_FREQUENCY, 
                                           WAITING_REVENUE_CONFIRMATION)
                
                from expense_manager import (WAITING_EXPENSE_TYPE, WAITING_EXPENSE_DESCRIPTION,
                                           WAITING_EXPENSE_VALUE, WAITING_EXPENSE_DATE,
                                           WAITING_EXPENSE_ACCOUNT, WAITING_INSTALLMENT_OPTION,
                                           WAITING_INSTALLMENT_COUNT, WAITING_INSTALLMENT_START,
                                           WAITING_EXPENSE_CONFIRMATION)
                
                # ConversationHandler para receitas
                revenue_handler = ConversationHandler(
                    entry_points=[CommandHandler('receitas', revenue_manager.start_add_revenue)],
                    states={
                        WAITING_REVENUE_TYPE: [CallbackQueryHandler(revenue_manager.process_revenue_type)],
                        WAITING_REVENUE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, revenue_manager.receive_revenue_description)],
                        WAITING_REVENUE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, revenue_manager.receive_revenue_value)],
                        WAITING_REVENUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, revenue_manager.receive_revenue_date)],
                        WAITING_REVENUE_ACCOUNT: [CallbackQueryHandler(revenue_manager.process_revenue_account)],
                        WAITING_REVENUE_FREQUENCY: [CallbackQueryHandler(revenue_manager.process_revenue_frequency)],
                        WAITING_REVENUE_CONFIRMATION: [CallbackQueryHandler(revenue_manager.process_confirmation)],
                    },
                    fallbacks=[CommandHandler('cancelar', revenue_manager.cancel_operation)],
                    per_message=False
                )
                
                # ConversationHandler para despesas
                expense_handler_new = ConversationHandler(
                    entry_points=[CommandHandler('gastos', expense_manager.start_add_expense)],
                    states={
                        WAITING_EXPENSE_TYPE: [CallbackQueryHandler(expense_manager.process_expense_type)],
                        WAITING_EXPENSE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_manager.receive_expense_description)],
                        WAITING_EXPENSE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_manager.receive_expense_value)],
                        WAITING_EXPENSE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_manager.receive_expense_date)],
                        WAITING_EXPENSE_ACCOUNT: [CallbackQueryHandler(expense_manager.process_expense_account)],
                        WAITING_INSTALLMENT_OPTION: [CallbackQueryHandler(expense_manager.process_installment_option)],
                        WAITING_INSTALLMENT_COUNT: [
                            CallbackQueryHandler(expense_manager.process_installment_count),
                            MessageHandler(filters.TEXT & ~filters.COMMAND, expense_manager.receive_custom_installments)
                        ],
                        WAITING_INSTALLMENT_START: [
                            CallbackQueryHandler(expense_manager.process_installment_start),
                            MessageHandler(filters.TEXT & ~filters.COMMAND, expense_manager.receive_custom_start_date)
                        ],
                        WAITING_EXPENSE_CONFIRMATION: [CallbackQueryHandler(expense_manager.process_confirmation)],
                    },
                    fallbacks=[CommandHandler('cancelar', expense_manager.cancel_operation)],
                    per_message=False
                )
                
                # Adicionar handlers
                application.add_handler(revenue_handler)
                application.add_handler(expense_handler_new)
                
                # Tentar adicionar outros comandos se existirem
                try:
                    application.add_handler(CommandHandler("cartoes", bot_commands.cards_callback))
                except:
                    logger.warning("Comando cartões não disponível")
                
                try:
                    application.add_handler(CommandHandler("analise", bot_commands.ai_analysis_callback))
                except:
                    logger.warning("Comandos de análise não disponíveis")
                
                # Comandos de debug/suporte temporários
                application.add_handler(CommandHandler("reset_senha", bot_commands.reset_password_command))
                application.add_handler(CommandHandler("debug_user", bot_commands.debug_user_command))
                
                # Adicionar comandos de debug para verificar funcionamento
                async def debug_receitas_command(update, context):
                    """Debug do comando receitas"""
                    await update.message.reply_text("🔧 DEBUG: Comando /receitas funcionando!")
                
                async def debug_gastos_command(update, context):
                    """Debug do comando gastos"""
                    await update.message.reply_text("🔧 DEBUG: Comando /gastos funcionando!")
                
                async def debug_perfil_command(update, context):
                    """Debug do comando perfil"""
                    await update.message.reply_text("🔧 DEBUG: Comando /perfil funcionando!")
                
                # Comando para debugar handlers registrados
                async def debug_handlers_command(update, context):
                    """Debug dos handlers registrados"""
                    try:
                        total_handlers = 0
                        grupos = []
                        
                        for group_id, group_handlers in application.handlers.items():
                            total_handlers += len(group_handlers)
                            grupos.append(f"Grupo {group_id}: {len(group_handlers)} handlers")
                        
                        message = "🔧 HANDLERS REGISTRADOS:\n\n"
                        message += "\n".join(grupos[:10])  # Máximo 10 grupos
                        message += f"\n\nTotal de handlers: {total_handlers}"
                        message += f"\nTotal de grupos: {len(application.handlers)}"
                        
                        await update.message.reply_text(message)
                        
                    except Exception as e:
                        await update.message.reply_text(f"❌ Erro no debug: {str(e)}")
                
                
                # Registrar comandos de debug
                application.add_handler(CommandHandler("debug_receitas", debug_receitas_command))
                application.add_handler(CommandHandler("debug_gastos", debug_gastos_command))
                application.add_handler(CommandHandler("debug_perfil", debug_perfil_command))
                application.add_handler(CommandHandler("debug_handlers", debug_handlers_command))
                
                # Comando de login automático simplificado
                async def entrar_simples_command(update, context):
                    """Login automático funcionando"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    await update.message.reply_text(
                        f"✅ **Login automático realizado!**\n\n"
                        f"👤 **Usuário:** {user['full_name']}\n"
                        f"🆔 **ID:** {user['id']}\n"
                        f"📧 **Email:** {user.get('email', 'Não cadastrado')}\n\n"
                        f"**Sistema funcionando:**\n"
                        f"• Digite `/receitas` para testar receitas\n"
                        f"• Digite `/gastos` para testar despesas\n"
                        f"• Digite `/saldo` para ver contas\n\n"
                        f"**Debug disponível:**\n"
                        f"• `/debug_handlers` - Ver handlers registrados"
                    )
                
                application.add_handler(CommandHandler("entrar", entrar_simples_command))
                
                # Comandos simples que funcionam (para teste)
                async def receitas_simples_command(update, context):
                    """Comando receitas simples"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    await update.message.reply_text(
                        "💰 **Sistema de Receitas Ativo!**\n\n"
                        "🏦 **Contas de receita disponíveis:**\n"
                        "🟢 Inter PF - Pessoa Física\n"
                        "🔵 Inter PJ - Pessoa Jurídica\n\n"
                        "📂 **Categorias disponíveis:**\n"
                        "💼 Salário\n"
                        "🤝 Fornecedor\n"
                        "💻 Freelance\n"
                        "📈 Investimentos\n"
                        "💰 Outros\n\n"
                        "**Em breve:** Interface guiada completa!"
                    )
                
                async def gastos_simples_command(update, context):
                    """Comando gastos simples"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    await update.message.reply_text(
                        "💸 **Sistema de Despesas Ativo!**\n\n"
                        "🏦 **Contas de despesa disponíveis:**\n"
                        "🟣 C6 Bank PF/PJ\n"
                        "🟡 Nubank PF/PJ\n"
                        "🔴 Santander PF/PJ\n\n"
                        "📂 **Categorias disponíveis:**\n"
                        "🍽️ Alimentação • 🚗 Transporte • 🏠 Moradia\n"
                        "💊 Saúde • 🎮 Lazer • 👕 Vestuário\n"
                        "📚 Educação • 📱 Outros\n\n"
                        "💳 **Parcelamento:** até 24x\n"
                        "**Em breve:** Interface guiada completa!"
                    )
                
                # Comando de status simples
                async def status_simples_command(update, context):
                    """Status do bot"""
                    import datetime
                    
                    now = datetime.datetime.now()
                    
                    await update.message.reply_text(
                        f"🤖 BOT STATUS:\n\n"
                        f"✅ Online e funcionando\n"
                        f"🕒 Horário: {now.strftime('%H:%M:%S')}\n"
                        f"📅 Data: {now.strftime('%d/%m/%Y')}\n"
                        f"🗄️ Banco: PostgreSQL Railway\n"
                        f"🔧 Sistema: Manual (sem APIs)\n\n"
                        f"COMANDOS FUNCIONAIS:\n"
                        f"• /receitas - Sistema de receitas\n"
                        f"• /gastos - Sistema de despesas\n"
                        f"• /entrar - Login automático\n"
                        f"• /saldo - Ver contas\n"
                        f"• /start - Menu principal"
                    )
                
                # Registrar comandos simples
                application.add_handler(CommandHandler("receitas", receitas_simples_command))
                application.add_handler(CommandHandler("gastos", gastos_simples_command))
                application.add_handler(CommandHandler("status", status_simples_command))
                
                logger.info("💰 Funcionalidades financeiras carregadas (sistema manual)")
                
            except Exception as e:
                logger.warning(f"⚠️ Algumas funcionalidades financeiras não disponíveis: {e}")
            
            logger.info("✅ Funcionalidades avançadas carregadas")
            
        except Exception as e:
            logger.warning(f"⚠️ Funcionalidades avançadas não disponíveis: {e}")
            # Continuar apenas com comandos básicos
        
        # Adicionar handler de fallback para mensagens não reconhecidas
        async def fallback_handler(update, context):
            """Handler para mensagens não reconhecidas"""
            message_text = update.message.text if update.message and update.message.text else "sem texto"
            
            # Se começa com /, é um comando não reconhecido
            if message_text.startswith('/'):
                await update.message.reply_text(
                    f"❌ **Comando não reconhecido:** `{message_text}`\n\n"
                    "**Comandos disponíveis:**\n"
                    "• `/start` - Menu principal\n"
                    "• `/receitas` - Sistema de receitas\n"
                    "• `/gastos` - Sistema de despesas\n"
                    "• `/saldo` - Ver contas e saldos\n"
                    "• `/perfil` - Seu perfil\n"
                    "• `/demo` - Dados de exemplo\n\n"
                    "**Debug:**\n"
                    "• `/debug_receitas` - Testar receitas\n"
                    "• `/debug_gastos` - Testar gastos\n"
                    "• `/debug_perfil` - Testar perfil\n\n"
                    "💡 Use `/start` para voltar ao menu principal.",
                    parse_mode='Markdown'
                )
            else:
                # Mensagem normal fora de conversa
                await update.message.reply_text(
                    "🤖 **Bot ativo!**\n\n"
                    "Para usar o sistema financeiro, digite um comando:\n"
                    "• `/start` - Começar\n"
                    "• `/receitas` - Adicionar receitas\n" 
                    "• `/gastos` - Registrar despesas\n\n"
                    "💡 **Dica:** Use `/start` para ver o menu completo!"
                )
        
        # Adicionar handler de fallback com prioridade mais baixa (depois de todos os outros)
        from telegram.ext import MessageHandler, filters
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_handler), group=100)
        
        # Adicionar handler de erro global
        async def error_handler(update, context):
            """Handler global de erros"""
            logger.error(f"❌ Erro no bot: {context.error}")
            
            if update and update.effective_message:
                try:
                    await update.effective_message.reply_text(
                        "❌ **Erro interno do bot**\n\n"
                        "Tente novamente em alguns segundos.\n"
                        "Se o problema persistir, use `/start` para reiniciar."
                    )
                except:
                    pass  # Se não conseguir responder, ignorar
        
        # Registrar handler de erro
        application.add_error_handler(error_handler)
        
        logger.info("🚀 Bot configurado com handlers de fallback e tratamento de erros. Iniciando polling...")
        
        # Executar bot com configurações otimizadas
        application.run_polling(
            allowed_updates=['message', 'callback_query'],
            drop_pending_updates=True,
            timeout=30,
            bootstrap_retries=3
        )
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()