import os
import asyncio
import logging
import threading
from datetime import datetime

import asyncpg
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import openai
from pluggy_client import PluggyClient
from health_server import start_health_server

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurações (todas vêm das variáveis de ambiente do Railway)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
PLUGGY_CLIENT_ID = os.getenv('PLUGGY_CLIENT_ID')
PLUGGY_CLIENT_SECRET = os.getenv('PLUGGY_CLIENT_SECRET')
PLUGGY_SANDBOX = os.getenv('PLUGGY_SANDBOX', 'true').lower() == 'true'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class FinancialBot:
    def __init__(self):
        self.pluggy = PluggyClient(
            client_id=PLUGGY_CLIENT_ID,
            client_secret=PLUGGY_CLIENT_SECRET,
            sandbox=PLUGGY_SANDBOX
        )
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.db_pool = None
    
    async def init_database(self):
        """Inicializar pool de conexões do banco PostgreSQL do Railway"""
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL não configurada! Configure no Railway.")
            
        self.db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        
        logger.info("🗄️ Conectado ao PostgreSQL do Railway")
        
        # Executar migrações automaticamente - Schema limpo e corrigido
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                -- Tabela de usuários
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    telegram_username VARCHAR(255),
                    full_name VARCHAR(500) NOT NULL,
                    first_name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255),
                    email VARCHAR(320),
                    phone VARCHAR(20),
                    password_hash VARCHAR(255),
                    password_salt VARCHAR(255),
                    is_active BOOLEAN DEFAULT true,
                    is_verified BOOLEAN DEFAULT false,
                    is_premium BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0,
                    account_locked_until TIMESTAMP,
                    two_factor_enabled BOOLEAN DEFAULT false,
                    two_factor_secret VARCHAR(32),
                    registration_ip INET,
                    last_login_ip INET,
                    preferred_language VARCHAR(10) DEFAULT 'pt-BR',
                    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo'
                );
                
                -- Função para atualizar updated_at automaticamente
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                -- Trigger para updated_at automático
                DROP TRIGGER IF EXISTS update_users_updated_at ON users;
                CREATE TRIGGER update_users_updated_at
                    BEFORE UPDATE ON users
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
                
                -- Tabela de categorias (DEVE vir ANTES de transactions)
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('expense', 'income')),
                    color VARCHAR(7),
                    icon VARCHAR(50),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name, type)
                );

                -- Tabela de metas financeiras (DEVE vir ANTES de transactions)
                CREATE TABLE IF NOT EXISTS goals (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    goal_type VARCHAR(30) NOT NULL CHECK (goal_type IN ('saving', 'spending_limit', 'investment', 'debt_payment', 'emergency_fund', 'vacation', 'purchase')),
                    target_amount DECIMAL(15,2) NOT NULL,
                    current_amount DECIMAL(15,2) DEFAULT 0,
                    target_date DATE,
                    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
                    is_active BOOLEAN DEFAULT true,
                    is_completed BOOLEAN DEFAULT false,
                    completed_at TIMESTAMP,
                    category_id INTEGER REFERENCES categories(id),
                    auto_calculate BOOLEAN DEFAULT false,
                    notification_enabled BOOLEAN DEFAULT true,
                    notification_threshold INTEGER DEFAULT 80,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Tabela de transações (agora categories e goals já existem)
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    amount DECIMAL(15,2) NOT NULL,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('expense', 'income')),
                    category_id INTEGER REFERENCES categories(id),
                    goal_id INTEGER REFERENCES goals(id),
                    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    due_date DATE,
                    is_installment BOOLEAN DEFAULT false,
                    installment_number INTEGER,
                    total_installments INTEGER,
                    parent_transaction_id INTEGER REFERENCES transactions(id),
                    is_recurring BOOLEAN DEFAULT false,
                    recurrence_type VARCHAR(20) CHECK (recurrence_type IN ('daily', 'weekly', 'monthly', 'yearly')),
                    recurrence_interval INTEGER DEFAULT 1,
                    recurrence_end_date DATE,
                    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled')),
                    paid_at TIMESTAMP,
                    bank_account_id VARCHAR(100),
                    bank_transaction_id VARCHAR(100),
                    tags TEXT[],
                    location VARCHAR(200),
                    receipt_url VARCHAR(500),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Tabela de orçamentos
                CREATE TABLE IF NOT EXISTS budgets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
                    month_year DATE NOT NULL,
                    budget_limit DECIMAL(15,2) NOT NULL,
                    spent_amount DECIMAL(15,2) DEFAULT 0,
                    is_active BOOLEAN DEFAULT true,
                    alert_at_percent INTEGER DEFAULT 80,
                    alert_sent BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, category_id, month_year)
                );

                -- Tabela de alertas
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    alert_type VARCHAR(30) NOT NULL CHECK (alert_type IN ('goal_progress', 'budget_exceeded', 'bill_due', 'goal_completed', 'overspending')),
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    related_id INTEGER,
                    related_type VARCHAR(20),
                    is_read BOOLEAN DEFAULT false,
                    is_sent BOOLEAN DEFAULT false,
                    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                );

                -- Tabela de contas bancárias (Pluggy)
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    bank_name VARCHAR(100) NOT NULL,
                    account_type VARCHAR(50) NOT NULL,
                    account_number VARCHAR(50),
                    balance DECIMAL(15,2) DEFAULT 0,
                    currency_code VARCHAR(10) DEFAULT 'BRL',
                    is_active BOOLEAN DEFAULT true,
                    pluggy_item_id VARCHAR(100),
                    pluggy_account_id VARCHAR(100),
                    last_sync TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, pluggy_account_id)
                );

                -- Tabela de cartões de crédito
                CREATE TABLE IF NOT EXISTS credit_cards (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    bank_name VARCHAR(100) NOT NULL,
                    card_name VARCHAR(100) NOT NULL,
                    card_number_last4 VARCHAR(4),
                    credit_limit DECIMAL(15,2),
                    available_limit DECIMAL(15,2),
                    current_balance DECIMAL(15,2) DEFAULT 0,
                    due_date INTEGER, -- dia do mês
                    closing_date INTEGER, -- dia do mês
                    is_active BOOLEAN DEFAULT true,
                    pluggy_item_id VARCHAR(100),
                    pluggy_account_id VARCHAR(100),
                    last_sync TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, pluggy_account_id)
                );
                
                -- Índices para performance
                CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
                CREATE INDEX IF NOT EXISTS idx_categories_user_type ON categories(user_id, type);
                CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id);
                CREATE INDEX IF NOT EXISTS idx_goals_active ON goals(user_id, is_active, is_completed);
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, transaction_date DESC);
                CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_goal ON transactions(goal_id);
                CREATE INDEX IF NOT EXISTS idx_budgets_user_month ON budgets(user_id, month_year);
                CREATE INDEX IF NOT EXISTS idx_alerts_user_unread ON alerts(user_id, is_read, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_bank_accounts_user ON bank_accounts(user_id, is_active);
                CREATE INDEX IF NOT EXISTS idx_bank_accounts_pluggy ON bank_accounts(pluggy_item_id, pluggy_account_id);
                CREATE INDEX IF NOT EXISTS idx_credit_cards_user ON credit_cards(user_id, is_active);
                CREATE INDEX IF NOT EXISTS idx_credit_cards_pluggy ON credit_cards(pluggy_item_id, pluggy_account_id);

                -- Triggers para updated_at
                DROP TRIGGER IF EXISTS update_goals_updated_at ON goals;
                CREATE TRIGGER update_goals_updated_at BEFORE UPDATE ON goals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                
                DROP TRIGGER IF EXISTS update_transactions_updated_at ON transactions;
                CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                
                DROP TRIGGER IF EXISTS update_budgets_updated_at ON budgets;
                CREATE TRIGGER update_budgets_updated_at BEFORE UPDATE ON budgets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            ''')
            
            logger.info("✅ Schema do banco criado/atualizado com sucesso")
    
    async def start_command(self, update: Update, context):
        """Comando /start com autenticação"""
        telegram_user = update.effective_user
        
        # Verificar se usuário está cadastrado
        async with self.db_pool.acquire() as conn:
            existing_user = await conn.fetchrow(
                "SELECT id, full_name, is_active FROM users WHERE telegram_id = $1",
                telegram_user.id
            )
        
        if existing_user:
            if existing_user['is_active']:
                # Usuário já cadastrado
                is_authenticated = context.user_data.get('authenticated', False)
                
                if is_authenticated:
                    welcome_text = f"""🤖 *Bem-vindo de volta, {existing_user['full_name']}!* 

✅ *Sistema ativo e funcionando*
💰 Análise de gastos inteligente
📊 Integração com +200 bancos
🎯 Metas financeiras personalizadas
💡 Conselhos de investimento com IA

*Comandos disponíveis:*
/despesas - Gerenciar gastos
/metas - Suas metas financeiras
/resumo - Dashboard completo
/perfil - Seu perfil"""
                    
                    keyboard = [
                        [InlineKeyboardButton("🏦 Conectar Banco", callback_data="connect_bank")],
                        [InlineKeyboardButton("💸 Despesas", callback_data="manage_expenses")],
                        [InlineKeyboardButton("🎯 Metas", callback_data="manage_goals")],
                        [InlineKeyboardButton("📊 Resumo", callback_data="financial_summary")],
                        [InlineKeyboardButton("👤 Perfil", callback_data="user_profile")]
                    ]
                else:
                    welcome_text = f"""🤖 *Olá {telegram_user.first_name}!* 

✅ *Você já possui cadastro no sistema*
🔐 Faça login para acessar suas funcionalidades

*Após o login:*
💰 Análise de gastos inteligente
📊 Integração com +200 bancos
🎯 Metas financeiras personalizadas
💡 Conselhos de investimento com IA"""
                    
                    keyboard = [
                        [InlineKeyboardButton("🔐 Fazer Login", callback_data="start_login")],
                        [InlineKeyboardButton("ℹ️ Sobre o Sistema", callback_data="about_system")]
                    ]
            else:
                welcome_text = f"""🤖 *Olá {telegram_user.first_name}!* 

⚠️ *Sua conta está inativa*
Entre em contato com o suporte para reativar.

📧 Suporte disponível através do comando /ajuda"""
                
                keyboard = [
                    [InlineKeyboardButton("📧 Solicitar Suporte", callback_data="contact_support")]
                ]
        else:
            # Novo usuário - precisa se cadastrar
            welcome_text = f"""🤖 *Bem-vindo {telegram_user.first_name}!* 

🚀 *Bot IA Financeiro - Sistema Completo*
💰 Análise de gastos inteligente
📊 Integração com +200 bancos brasileiros
🎯 Metas financeiras personalizadas
💡 Conselhos de investimento com IA
🔒 Total segurança com criptografia

📝 *Para começar, você precisa se cadastrar:*"""
            
            keyboard = [
                [InlineKeyboardButton("📝 Criar Conta", callback_data="start_registration")],
                [InlineKeyboardButton("ℹ️ Sobre o Sistema", callback_data="about_system")],
                [InlineKeyboardButton("🔒 Segurança", callback_data="security_info")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def callback_handler(self, update: Update, context):
        """Handler para callbacks dos botões"""
        query = update.callback_query
        data = query.data
        
        await query.answer()
        
        if data == "start_login":
            await query.edit_message_text(
                "🔐 Para fazer login, use o comando /login\n\n"
                "Suas credenciais são protegidas com criptografia."
            )
        elif data == "start_registration":
            await query.edit_message_text(
                "📝 Para criar sua conta, use o comando /cadastro\n\n"
                "Este processo é seguro e criptografado."
            )
        elif data == "about_system":
            await query.edit_message_text(
                """ℹ️ **Sobre o Bot IA Financeiro**

🤖 **Sistema Inteligente:**
• IA avançada com OpenAI GPT-4
• Análise comportamental de gastos
• Recomendações personalizadas

🏦 **Integração Bancária:**
• +200 bancos brasileiros via Pluggy
• Open Finance certificado
• Dados sincronizados em tempo real

🔒 **Segurança Total:**
• Criptografia end-to-end
• Credenciais nunca no código
• Conformidade com LGPD
• Auditoria de segurança

💡 **Funcionalidades:**
• Controle de gastos inteligente
• Metas financeiras automatizadas
• Conselhos de investimento personalizados
• Alertas de gastos excessivos""",
                parse_mode='Markdown'
            )
        elif data == "connect_bank":
            await query.edit_message_text(
                "🏦 **Conectar Conta Bancária**\n\n"
                "📱 **Integração Pluggy - Open Finance**\n\n"
                "✅ **Suporte a +200 bancos brasileiros:**\n"
                "• Banco Inter\n"
                "• Nubank\n"
                "• Bradesco\n"
                "• Itaú\n"
                "• Santander\n"
                "• Banco do Brasil\n"
                "• C6 Bank\n"
                "• BTG Pactual\n"
                "• E muitos outros...\n\n"
                "🔒 **Conexão 100% segura e criptografada**\n"
                "🏦 **Certificado pelo Banco Central**\n"
                "📊 **Dados sincronizados em tempo real**\n\n"
                "**Para conectar sua conta:**\n"
                "1. Use o comando /conectar\n"
                "2. Escolha seu banco\n"
                "3. Faça login seguro via Pluggy\n"
                "4. Autorize o acesso\n\n"
                "💡 Suas credenciais ficam apenas no Pluggy, nunca conosco!"
            )
        elif data == "manage_expenses":
            await query.edit_message_text(
                "💸 **Gestão de Despesas**\n\n"
                "Comandos disponíveis:\n"
                "• /despesas - Menu completo\n"
                "• /resumo - Análise detalhada\n"
                "• /nova_despesa - Adicionar gasto\n\n"
                "Use qualquer um dos comandos acima para continuar."
            )
        elif data == "manage_goals":
            await query.edit_message_text(
                "🎯 **Gestão de Metas**\n\n"
                "Comandos disponíveis:\n"
                "• /metas - Menu completo\n"
                "• /nova_meta - Criar meta\n"
                "• /progresso - Acompanhar evolução\n\n"
                "Use qualquer um dos comandos acima para continuar."
            )
        elif data == "financial_summary":
            await query.edit_message_text(
                "📊 **Resumo Financeiro**\n\n"
                "Comandos disponíveis:\n"
                "• /resumo - Dashboard completo\n"
                "• /relatorio - Análise detalhada\n"
                "• /analise - Insights com IA\n\n"
                "Use qualquer um dos comandos acima para continuar."
            )
        elif data == "user_profile":
            await query.edit_message_text(
                "👤 **Perfil do Usuário**\n\n"
                "Comandos disponíveis:\n"
                "• /perfil - Ver perfil completo\n"
                "• /trocar_senha - Alterar senha\n"
                "• /logout - Sair do sistema\n\n"
                "Use qualquer um dos comandos acima para continuar."
            )
        else:
            await query.edit_message_text(
                "❌ Opção não reconhecida. Use /start para voltar ao menu principal."
            )

    async def get_or_create_user(self, telegram_user):
        """Obter ou criar usuário"""
        try:
            # Verificar se o usuário já existe
            existing_user = await self.get_user_by_telegram_id(telegram_user.id)
            if existing_user:
                return existing_user
            
            # Criar novo usuário
            user_data = (
                telegram_user.id,
                telegram_user.username or telegram_user.first_name,
                telegram_user.first_name or "Usuário"
            )
            
            query = """
                INSERT INTO users (telegram_id, username, full_name) 
                VALUES ($1, $2, $3) 
                RETURNING id, telegram_id, username, full_name, created_at
            """
            
            user = await self.execute_query_one(query, user_data)
            logger.info(f"Novo usuário criado: {user['full_name']} (ID: {user['telegram_id']})")
            return user
            
        except Exception as e:
            logger.error(f"Erro ao criar/obter usuário: {e}")
            raise

    async def get_user_by_telegram_id(self, telegram_id):
        """Buscar usuário por ID do Telegram"""
        try:
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT * FROM users WHERE telegram_id = $1 AND is_active = true",
                    telegram_id
                )
                return dict(user) if user else None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário {telegram_id}: {e}")
            return None

    async def execute_query_one(self, query, params=None):
        """Executar query que retorna um registro"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *(params or []))
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Erro na query: {e}")
            raise

    async def execute_query(self, query, params=None):
        """Executar query que retorna múltiplos registros"""
        try:
            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(query, *(params or []))
                return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Erro na query: {e}")
            raise

    async def get_user_accounts(self, user_id):
        """Buscar contas bancárias do usuário"""
        try:
            query = """
                SELECT * FROM bank_accounts 
                WHERE user_id = $1 AND is_active = true
                ORDER BY bank_name
            """
            accounts = await self.execute_query(query, (user_id,))
            
            # Se não há contas na base local, tentar buscar via Pluggy
            if not accounts:
                accounts = await self.sync_pluggy_accounts(user_id)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Erro ao buscar contas do usuário {user_id}: {e}")
            return []

    async def sync_pluggy_accounts(self, user_id):
        """Sincronizar contas do Pluggy"""
        try:
            logger.info(f"Tentativa de sincronização Pluggy para usuário {user_id}")
            
            # Verificar se temos credenciais do Pluggy
            client_id = os.getenv('PLUGGY_CLIENT_ID')
            client_secret = os.getenv('PLUGGY_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.warning("Credenciais Pluggy não configuradas - modo local")
                return []
            
            # Importar cliente Pluggy
            try:
                from pluggy_client import PluggyClient
                
                # Usar Pluggy para buscar contas do usuário
                try:
                    async with PluggyClient(client_id, client_secret, sandbox=True) as pluggy:
                        # Usar user_id como clientUserId
                        items = await pluggy.get_items(str(user_id))
                        accounts = []
                        
                        for item in items:
                            try:
                                item_accounts = await pluggy.get_accounts(item['id'])
                                for account in item_accounts:
                                    # Salvar conta no banco local
                                    await self.save_account_to_db(user_id, item, account)
                                    accounts.append({
                                        'bank_name': item.get('connector', {}).get('name', 'Banco'),
                                        'account_type': account.get('type', 'Conta Corrente'),
                                        'balance': account.get('balance', 0),
                                        'currency': account.get('currencyCode', 'BRL')
                                    })
                            except Exception as account_error:
                                logger.warning(f"Erro ao processar item {item.get('id')}: {account_error}")
                                continue
                        
                        logger.info(f"Sincronizadas {len(accounts)} contas para usuário {user_id}")
                        return accounts
                        
                except Exception as pluggy_error:
                    logger.warning(f"API Pluggy indisponível: {pluggy_error}")
                    return []
                    
            except ImportError:
                logger.warning("Cliente Pluggy não disponível no sistema")
                return []
            
        except Exception as e:
            logger.warning(f"Erro geral na sincronização Pluggy: {e}")
            return []

    async def save_account_to_db(self, user_id, item, account):
        """Salvar conta no banco de dados local"""
        try:
            query = """
                INSERT INTO bank_accounts (
                    user_id, bank_name, account_type, account_number, 
                    balance, currency_code, is_active, pluggy_item_id, pluggy_account_id
                ) VALUES ($1, $2, $3, $4, $5, $6, true, $7, $8)
                ON CONFLICT (user_id, pluggy_account_id) 
                DO UPDATE SET 
                    balance = EXCLUDED.balance,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            params = (
                user_id,
                item.get('connector', {}).get('name', 'Banco'),
                account.get('type', 'Conta Corrente'),
                account.get('number', '****'),
                float(account.get('balance', 0)),
                account.get('currencyCode', 'BRL'),
                item.get('id'),
                account.get('id')
            )
            
            await self.execute_query_one(query, params)
            logger.info(f"Conta salva no DB: {account.get('id')}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar conta no DB: {e}")

    async def generate_connect_url(self, user_id):
        """Gerar URL de conexão Pluggy com Connect Token"""
        try:
            client_id = os.getenv('PLUGGY_CLIENT_ID')
            client_secret = os.getenv('PLUGGY_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.warning("Credenciais Pluggy não configuradas - modo offline")
                return None
            
            # Importar e usar cliente Pluggy
            from pluggy_client import PluggyClient
            
            try:
                async with PluggyClient(client_id, client_secret, sandbox=True) as pluggy:
                    # Criar connect token genérico (sem connector específico)
                    connect_data = await pluggy.create_connect_token_generic(str(user_id))
                    
                    if connect_data and 'accessToken' in connect_data:
                        # URL do Pluggy Connect com token
                        base_url = "https://connect.sandbox.pluggy.ai" # Sandbox
                        # base_url = "https://connect.pluggy.ai" # Produção
                        
                        connect_url = f"{base_url}?connectToken={connect_data['accessToken']}"
                        
                        logger.info(f"Connect URL gerada para usuário {user_id}")
                        return connect_url
                    else:
                        logger.warning("Falha ao gerar connect token - resposta inválida")
                        return None
                        
            except Exception as pluggy_error:
                logger.warning(f"Pluggy API indisponível: {pluggy_error}")
                return None
                    
        except Exception as e:
            logger.warning(f"Erro geral ao gerar connect URL: {e}")
            return None

async def main():
    """Função principal"""
    # Iniciar servidor de health check em thread separada APENAS se não estiver em loop asyncio
    try:
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        PORT = int(os.getenv('PORT', 8080))
        logger.info(f"🌐 Servidor de health check iniciado na porta {PORT}")
    except Exception as e:
        logger.warning(f"Health server warning: {e}")
    
    bot = FinancialBot()
    
    # Inicializar banco de dados
    await bot.init_database()
    
    # Configurar aplicação do Telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers básicos
    application.add_handler(CommandHandler("start", bot.start_command))
    
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
    )
    
    goal_handler = ConversationHandler(
        entry_points=[CommandHandler('metas', bot_commands.goals_command)],
        states={
            WAITING_GOAL_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_goal_title)],
            WAITING_GOAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.receive_goal_amount)],
            WAITING_GOAL_TYPE: [CallbackQueryHandler(bot_commands.process_goal_type)],
        },
        fallbacks=[CommandHandler('cancelar', bot_commands.cancel_operation)],
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
    
    # Iniciar bot
    logger.info("🤖 Bot Telegram IA Financeiro iniciado!")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

async def main_bot_only():
    """Executar apenas o bot sem health server"""
    bot = FinancialBot()
    
    # Inicializar banco de dados
    await bot.init_database()
    
    # Configurar aplicação do Telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers básicos
    application.add_handler(CommandHandler("start", bot.start_command))
    
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
    
    # Iniciar bot
    logger.info("🤖 Bot Telegram IA Financeiro iniciado!")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Em produção no Railway, executar bot sem health server para evitar conflito
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("🚀 Modo Railway - executando apenas bot")
        asyncio.run(main_bot_only())
    else:
        # Localmente, executar com health server
        asyncio.run(main())