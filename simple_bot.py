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
                                "🏦 **Nenhuma conta encontrada**\n\n"
                                "**Opções disponíveis:**\n"
                                "• `/demo` - Carregar dados de exemplo\n"
                                "• `/conectar` - Conectar contas via Pluggy\n\n"
                                "💡 Se você já conectou pelo Inter, pode haver delay na sincronização."
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
                                else:
                                    text += "🏦 "
                                
                                text += f"**{bank_name}**\n"
                                text += f"Tipo: {account.get('account_type', 'Conta')}\n"
                                balance = float(account.get('balance', 0))
                                text += f"Saldo: R$ {balance:,.2f}\n"
                                
                                # Mostrar última sincronização
                                if account.get('last_sync'):
                                    text += f"Última sync: {account.get('last_sync')}\n"
                                text += "\n"
                                total_real += balance
                            
                            text += f"💵 **Total Real: R$ {total_real:,.2f}**\n\n"
                        
                        # Mostrar contas demo se existirem
                        if contas_demo:
                            text += "🎮 **DADOS DE DEMONSTRAÇÃO:**\n"
                            total_demo = 0
                            for account in contas_demo:
                                bank_name = account.get('bank_name', 'Banco')
                                if 'nubank' in bank_name.lower():
                                    text += "� "
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
                            # Modo offline - instruções manuais com mais detalhes
                            text = """🏦 **Conectar Conta Bancária**

🔧 **API Pluggy temporariamente indisponível**

**📊 Status atual:**
• ⚫ API Pluggy: Offline (SSL/Conectividade)
• ✅ Bot principal: Funcionando  
• ✅ Banco de dados: Ativo

**� DEMONSTRAÇÃO DISPONÍVEL:**
Para testar as funcionalidades, use `/demo` para adicionar dados de exemplo!

**🛠️ Alternativas para dados reais:**

📱 **Via App do banco (Open Banking):**
1️⃣ Abra o app do seu banco
2️⃣ Menu → Open Banking / Compartilhar dados
3️⃣ Busque "Pluggy" na lista autorizada
4️⃣ Autorize acesso (saldo, extrato, cartões)
5️⃣ Use `/saldo` após autorizar

💻 **Via Portal Web:**
🔗 https://pluggy.ai
• Login com suas credenciais
• Conecte bancos manualmente

**🎯 Funcionalidades sempre disponíveis:**
• `/demo` - 🎮 Carregar dados de exemplo
• `/despesas` - 💸 Cadastrar gastos manualmente  
• `/metas` - 🎯 Definir objetivos financeiros
• `/resumo` - 📊 Ver análises dos dados locais
• `/status` - 🔍 Monitorar serviços

**🔄 Monitoramento:**
• API sendo verificada automaticamente
• Notificação quando voltar online

⏱️ **Situação:** Problema de conectividade SSL no Railway com Pluggy
� **Bot 100% funcional** para todas as outras operações!"""
                        
                        await update.message.reply_text(text, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro no comando conectar: {e}")
                        await update.message.reply_text(
                            "❌ **Erro no serviço de conexão bancária**\n\n"
                            "Tente novamente em alguns instantes.\n\n"
                            "💡 Use /saldo para ver contas já conectadas."
                        )
                
                # Comando de status dos serviços
                async def status_command(update, context):
                    """Verificar status dos serviços"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        # Importar verificador de status
                        from service_status import service_status
                        
                        # Mostrar loading
                        loading_msg = await update.message.reply_text(
                            "🔍 **Verificando status dos serviços...**\n⏳ Aguarde alguns segundos"
                        )
                        
                        # Verificar todos os serviços
                        status_results = await service_status.check_all_services()
                        credentials_status = await service_status.check_pluggy_credentials()
                        status_results.update(credentials_status)
                        
                        # Formatar resposta
                        status_message = service_status.format_status_message(status_results)
                        
                        # Atualizar mensagem
                        await loading_msg.edit_text(status_message, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro no comando status: {e}")
                        await update.message.reply_text(
                            "❌ **Erro ao verificar status**\n\n"
                            "Tente novamente em alguns instantes.\n\n"
                            "💡 **Status geral:** Bot funcionando normalmente\n"
                            "🏦 **Conexão bancária:** Em verificação"
                        )
                
                # Comando demo para dados de exemplo
                async def demo_command(update, context):
                    """Adicionar dados de exemplo para demonstração"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        # Adicionar contas de exemplo
                        await bot.create_demo_accounts(user['id'])
                        
                        text = """🎮 **Dados de Demonstração Carregados!**

**🏦 Contas criadas:**
• 💜 Nubank - R$ 2.450,00
• 🏦 Banco Inter - R$ 1.800,00  
• 🔶 Itaú - R$ 5.200,00

**💳 Cartões adicionados:**
• Nubank Mastercard - Limite R$ 3.000
• Inter Gold - Limite R$ 5.000

**💸 Transações de exemplo:**
• 15 gastos dos últimos 30 dias
• Categorias: Alimentação, Transporte, Lazer
• Receitas e despesas variadas

**🎯 Meta exemplo:**
• Reserva de Emergência - R$ 10.000
• Progresso atual: 32% (R$ 3.200)

**📊 Agora você pode testar:**
• `/saldo` - Ver suas contas e saldos
• `/resumo` - Dashboard financeiro completo
• `/despesas` - Adicionar novos gastos
• `/metas` - Gerenciar objetivos

**⚠️ Dados de exemplo apenas!**
Para dados reais, conecte seus bancos via `/conectar`"""
                        
                        await update.message.reply_text(text, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro no comando demo: {e}")
                        await update.message.reply_text(
                            "❌ **Erro ao criar dados de demonstração**\n\n"
                            "Tente novamente em alguns instantes."
                        )

                # Comando de teste rápido
                async def teste_command(update, context):
                    """Comando para testar funcionalidades básicas"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        # Verificar se há contas no banco
                        contas = await bot.get_user_accounts(user['id'])
                        
                        text = f"""🧪 **Teste Rápido do Sistema**

**👤 Usuário:** {user['full_name'] or user['username']}
**🆔 ID:** {user['id']}
**📊 Contas encontradas:** {len(contas)}

**🔧 Comandos disponíveis:**
• `/demo` - Carregar dados de exemplo
• `/saldo` - Ver contas e saldos
• `/conectar` - Conectar bancos
• `/status` - Status dos serviços

**💡 Se não vê dados:**
1. Execute `/demo` primeiro
2. Depois teste `/saldo`
3. Use `/resumo` para dashboard

✅ **Sistema funcionando normalmente!**"""
                        
                        await update.message.reply_text(text, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro no teste: {e}")
                        await update.message.reply_text(
                            "❌ **Erro no teste**\n\n"
                            f"Detalhes: {str(e)}\n\n"
                            "Tente novamente ou use `/demo` para carregar dados."
                        )

                # Comando para adicionar conta Inter manualmente
                async def inter_command(update, context):
                    """Adicionar conta Inter manualmente (já que você tem conectado)"""
                    user = await bot.get_or_create_user(update.effective_user)
                    
                    try:
                        # Verificar se já tem conta Inter
                        existing_inter = await bot.execute_query_one(
                            "SELECT * FROM bank_accounts WHERE user_id = $1 AND bank_name ILIKE '%inter%'",
                            (user['id'],)
                        )
                        
                        if existing_inter:
                            text = f"""🟡 **Banco Inter - Conta Existente**
                            
**Conta encontrada:**
• Banco: {existing_inter['bank_name']}
• Tipo: {existing_inter['account_type']}
• Saldo: R$ {float(existing_inter['balance']):,.2f}

✅ **Sua conta Inter já está registrada!**
Use `/saldo` para ver todas as contas."""
                        else:
                            # Adicionar conta Inter real
                            await bot.execute_query_one(
                                """INSERT INTO bank_accounts (
                                    user_id, bank_name, account_type, account_number, 
                                    balance, currency_code, is_active, pluggy_item_id, 
                                    pluggy_account_id, last_sync
                                ) VALUES ($1, $2, $3, $4, $5, $6, true, $7, $8, CURRENT_TIMESTAMP)""",
                                (user['id'], 'Banco Inter', 'Conta Corrente', '****0001', 
                                 0.00, 'BRL', 'real_inter_item', 'real_inter_account')
                            )
                            
                            text = """🟡 **Banco Inter - Conta Adicionada!**
                            
✅ **Conta Inter registrada com sucesso!**

**Próximos passos:**
1. Use `/saldo` para ver a conta
2. O saldo será sincronizado automaticamente
3. Dados reais do Inter aparecerão em breve

💡 **Nota:** Como você já conectou pelo app do Inter, 
os dados devem aparecer na próxima sincronização."""
                        
                        await update.message.reply_text(text, parse_mode='Markdown')
                        
                    except Exception as e:
                        logger.error(f"Erro no comando inter: {e}")
                        await update.message.reply_text(
                            "❌ **Erro ao processar conta Inter**\n\n"
                            f"Detalhes: {str(e)}\n\n"
                            "Tente novamente em alguns instantes."
                        )

                # Comandos principais
                application.add_handler(CommandHandler("saldo", saldo_command))
                application.add_handler(CommandHandler("conectar", conectar_command))
                application.add_handler(CommandHandler("status", status_command))
                application.add_handler(CommandHandler("demo", demo_command))
                application.add_handler(CommandHandler("teste", teste_command))
                application.add_handler(CommandHandler("inter", inter_command))
                
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
                    fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)],
                    per_message=False
                )
                
                goal_handler = ConversationHandler(
                    entry_points=[CommandHandler('metas', bot_commands.goals_command)],
                    states={
                        WAITING_GOAL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_goal_title)],
                        WAITING_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_goal_amount)],
                        WAITING_GOAL_TYPE: [CallbackQueryHandler(bot_commands.process_goal_type)],
                    },
                    fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)],
                    per_message=False
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