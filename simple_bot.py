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