#!/usr/bin/env python3
"""
Bot Telegram IA Financeiro - Railway Entry Point
Execução otimizada para ambiente Railway sem health server
"""

import os
import asyncio
import logging
from main import FinancialBot, TELEGRAM_TOKEN
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def run_bot():
    """Executar apenas o bot sem health server para Railway"""
    logger.info("🚀 Iniciando Bot IA Financeiro no Railway")
    
    bot = FinancialBot()
    
    # Inicializar banco de dados
    await bot.init_database()
    
    # Configurar aplicação do Telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers básicos
    application.add_handler(CommandHandler("start", bot.start_command))
    
    try:
        # Configurar bot_commands
        from bot_commands import (BotCommands, WAITING_FULL_NAME, WAITING_EMAIL, WAITING_PASSWORD, 
                                 WAITING_LOGIN_PASSWORD, WAITING_OLD_PASSWORD, WAITING_NEW_PASSWORD,
                                 WAITING_EXPENSE_TITLE, WAITING_EXPENSE_AMOUNT, WAITING_EXPENSE_CATEGORY,
                                 WAITING_GOAL_TITLE, WAITING_GOAL_AMOUNT, WAITING_GOAL_TYPE)
        from telegram.ext import ConversationHandler, MessageHandler, CallbackQueryHandler, filters
        
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
        
        # ConversationHandlers para gestão financeira
        expense_handler = ConversationHandler(
            entry_points=[CommandHandler('despesas', bot_commands.expenses_command)],
            states={
                WAITING_EXPENSE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_expense_title)],
                WAITING_EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_expense_amount)],
                WAITING_EXPENSE_CATEGORY: [CallbackQueryHandler(bot_commands.process_expense_category)],
            },
            fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)],
            per_message=True
        )
        
        goal_handler = ConversationHandler(
            entry_points=[CommandHandler('metas', bot_commands.goals_command)],
            states={
                WAITING_GOAL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_goal_title)],
                WAITING_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_goal_amount)],
                WAITING_GOAL_TYPE: [CallbackQueryHandler(bot_commands.process_goal_type)],
            },
            fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)],
            per_message=True
        )
        
        application.add_handler(expense_handler)
        application.add_handler(goal_handler)
        
        # Comandos financeiros diretos
        application.add_handler(CommandHandler('relatorio', bot_commands.expense_report_command))
        application.add_handler(CommandHandler('resumo', bot_commands.financial_summary_command))
        
        # Comandos de atalho
        application.add_handler(CommandHandler('nova_despesa', bot_commands.start_add_expense))
        application.add_handler(CommandHandler('nova_meta', bot_commands.start_add_goal))
        
        # Handler de callbacks
        application.add_handler(CallbackQueryHandler(bot.callback_handler))
        
    except ImportError as e:
        logger.warning(f"Alguns comandos avançados não disponíveis: {e}")
    
    # Iniciar bot
    logger.info("🤖 Bot Telegram IA Financeiro iniciado no Railway!")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(run_bot())