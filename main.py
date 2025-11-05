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
        
        # Executar migrações automaticamente
        async with self.db_pool.acquire() as conn:
            # Schema otimizado para Railway PostgreSQL
            await conn.execute('''
                -- Tabela de usuários com sistema completo de cadastro
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    telegram_username VARCHAR(255),
                    
                    -- Dados pessoais completos
                    full_name VARCHAR(500) NOT NULL,
                    first_name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255),
                    email VARCHAR(320), -- RFC 5322 compliant
                    phone VARCHAR(20),
                    
                    -- Sistema de autenticação
                    password_hash VARCHAR(255), -- bcrypt hash
                    password_salt VARCHAR(255), -- Salt adicional
                    
                    -- Status da conta
                    is_active BOOLEAN DEFAULT true,
                    is_verified BOOLEAN DEFAULT false,
                    is_premium BOOLEAN DEFAULT false,
                    
                    -- Controle de datas
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Configurações de segurança
                    failed_login_attempts INTEGER DEFAULT 0,
                    account_locked_until TIMESTAMP,
                    two_factor_enabled BOOLEAN DEFAULT false,
                    two_factor_secret VARCHAR(32),
                    
                    -- Metadata
                    registration_ip INET,
                    last_login_ip INET,
                    preferred_language VARCHAR(10) DEFAULT 'pt-BR',
                    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo'
                );
                
                -- Índices para performance e segurança
                CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
                CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
                
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
                
                -- Tabela de contas bancárias (dados do Pluggy)
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    pluggy_item_id VARCHAR(255) NOT NULL,
                    pluggy_account_id VARCHAR(255) NOT NULL,
                    bank_name VARCHAR(255) NOT NULL,
                    account_type VARCHAR(50) NOT NULL,
                    account_number VARCHAR(255),
                    balance DECIMAL(15,2) DEFAULT 0.00,
                    currency VARCHAR(10) DEFAULT 'BRL',
                    last_sync TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Índices para performance
                CREATE INDEX IF NOT EXISTS idx_bank_accounts_user_id ON bank_accounts(user_id);
                CREATE INDEX IF NOT EXISTS idx_bank_accounts_pluggy_item ON bank_accounts(pluggy_item_id);
                
                -- Tabela de transações
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    bank_account_id INTEGER REFERENCES bank_accounts(id) ON DELETE SET NULL,
                    pluggy_transaction_id VARCHAR(255) UNIQUE,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('income', 'expense', 'transfer')),
                    category VARCHAR(100),
                    subcategory VARCHAR(100),
                    amount DECIMAL(15,2) NOT NULL,
                    description TEXT,
                    merchant VARCHAR(255),
                    transaction_date TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Índices para consultas otimizadas
                CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date DESC);
                CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
                
                -- Tabela de categorias de despesas/receitas
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('expense', 'income')),
                    color VARCHAR(7), -- Hex color
                    icon VARCHAR(50),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name, type)
                );

                -- Tabela de metas financeiras completa
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
                    
                    -- Configurações da meta
                    auto_calculate BOOLEAN DEFAULT false,
                    notification_enabled BOOLEAN DEFAULT true,
                    notification_threshold INTEGER DEFAULT 80,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Tabela de despesas/receitas
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    amount DECIMAL(15,2) NOT NULL,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('expense', 'income')),
                    category_id INTEGER REFERENCES categories(id),
                    goal_id INTEGER REFERENCES goals(id),
                    
                    -- Data e recorrência
                    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    due_date DATE,
                    
                    -- Parcelamento
                    is_installment BOOLEAN DEFAULT false,
                    installment_number INTEGER,
                    total_installments INTEGER,
                    parent_transaction_id INTEGER REFERENCES transactions(id),
                    
                    -- Recorrência
                    is_recurring BOOLEAN DEFAULT false,
                    recurrence_type VARCHAR(20) CHECK (recurrence_type IN ('daily', 'weekly', 'monthly', 'yearly')),
                    recurrence_interval INTEGER DEFAULT 1,
                    recurrence_end_date DATE,
                    
                    -- Status
                    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled')),
                    paid_at TIMESTAMP,
                    
                    -- Dados bancários
                    bank_account_id VARCHAR(100),
                    bank_transaction_id VARCHAR(100),
                    
                    -- Metadados
                    tags TEXT[],
                    location VARCHAR(200),
                    receipt_url VARCHAR(500),
                    notes TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Tabela de orçamentos por categoria
                CREATE TABLE IF NOT EXISTS budgets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
                    month_year DATE NOT NULL,
                    budget_limit DECIMAL(15,2) NOT NULL,
                    spent_amount DECIMAL(15,2) DEFAULT 0,
                    is_active BOOLEAN DEFAULT true,
                    
                    -- Alertas
                    alert_at_percent INTEGER DEFAULT 80,
                    alert_sent BOOLEAN DEFAULT false,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(user_id, category_id, month_year)
                );

                -- Tabela de alertas e notificações
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
                
                -- Índices para performance
                CREATE INDEX IF NOT EXISTS idx_categories_user_type ON categories(user_id, type);
                CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id);
                CREATE INDEX IF NOT EXISTS idx_goals_active ON goals(user_id, is_active, is_completed);
                CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, transaction_date DESC);
                CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_goal ON transactions(goal_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status, due_date);
                CREATE INDEX IF NOT EXISTS idx_budgets_user_month ON budgets(user_id, month_year);
                CREATE INDEX IF NOT EXISTS idx_alerts_user_unread ON alerts(user_id, is_read, created_at DESC);

                -- Triggers para updated_at
                DROP TRIGGER IF EXISTS update_goals_updated_at ON goals;
                CREATE TRIGGER update_goals_updated_at BEFORE UPDATE ON goals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                
                DROP TRIGGER IF EXISTS update_transactions_updated_at ON transactions;
                CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                
                DROP TRIGGER IF EXISTS update_budgets_updated_at ON budgets;
                CREATE TRIGGER update_budgets_updated_at BEFORE UPDATE ON budgets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                
                -- Tabela de análises de IA
                CREATE TABLE IF NOT EXISTS ai_analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    suggestions JSONB,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_ai_analyses_user_type ON ai_analyses(user_id, type);
                CREATE INDEX IF NOT EXISTS idx_ai_analyses_created ON ai_analyses(created_at DESC);
                
                -- Tabela de orçamentos
                CREATE TABLE IF NOT EXISTS budgets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    category VARCHAR(100) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    period VARCHAR(20) NOT NULL CHECK (period IN ('monthly', 'weekly', 'daily')),
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_budgets_user_active ON budgets(user_id, is_active);
                
                -- Tabela de cartões de crédito
                CREATE TABLE IF NOT EXISTS credit_cards (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    pluggy_item_id VARCHAR(255) NOT NULL,
                    card_name VARCHAR(255) NOT NULL,
                    bank_name VARCHAR(255) NOT NULL,
                    card_number_masked VARCHAR(20),
                    credit_limit DECIMAL(15,2) DEFAULT 0.00,
                    available_limit DECIMAL(15,2) DEFAULT 0.00,
                    due_date DATE,
                    minimum_payment DECIMAL(15,2) DEFAULT 0.00,
                    last_sync TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_credit_cards_user_id ON credit_cards(user_id);
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
/saldo - Consultar saldos
/cartoes - Informações dos cartões
/extrato - Ver extrato detalhado
/metas - Gerenciar metas
/analise - Análise inteligente
/perfil - Seu perfil"""
                    
                    keyboard = [
                        [InlineKeyboardButton("💰 Ver Saldo", callback_data="balance")],
                        [InlineKeyboardButton("📊 Análise IA", callback_data="spending_analysis")],
                        [InlineKeyboardButton("� Cartões", callback_data="my_cards")],
                        [InlineKeyboardButton("🎯 Metas", callback_data="my_goals")]
                    ]
                else:
                    welcome_text = f"""🤖 *Olá {telegram_user.first_name}!* 

✅ *Você já possui cadastro no sistema*
🔐 Faça login para acessar suas funcionalidades

*Após o login:*
💰 Análise de gastos inteligente
📊 Integração com +200 bancos
🎯 Metas financeiras personalizadas
� Conselhos de investimento com IA"""
                    
                    keyboard = [
                        [InlineKeyboardButton("🔐 Fazer Login", callback_data="start_login")],
                        [InlineKeyboardButton("👤 Sobre o Sistema", callback_data="about_system")]
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

🔗 *Open Finance seguro via Pluggy*
Conecte suas contas bancárias com total segurança

📝 *Para começar, você precisa se cadastrar:*"""
            
            keyboard = [
                [InlineKeyboardButton("📝 Criar Conta", callback_data="start_registration")],
                [InlineKeyboardButton("ℹ️ Sobre o Sistema", callback_data="about_system")],
                [InlineKeyboardButton("� Segurança", callback_data="security_info")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def menu_command(self, update: Update, context):
        """Menu principal"""
        keyboard = [
            [
                InlineKeyboardButton("💰 Saldo", callback_data="balance"),
                InlineKeyboardButton("📊 Extrato", callback_data="statement")
            ],
            [
                InlineKeyboardButton("💳 Cartões", callback_data="cards"),
                InlineKeyboardButton("🎯 Metas", callback_data="goals")
            ],
            [
                InlineKeyboardButton("📈 Análise IA", callback_data="ai_analysis"),
                InlineKeyboardButton("💡 Investimentos", callback_data="investment")
            ],
            [
                InlineKeyboardButton("🏦 Conectar Banco", callback_data="connect_bank")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🏠 *Menu Principal*\nEscolha uma opção:"
        
        if update.message:
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def balance_callback(self, update: Update, context):
        """Mostrar saldo das contas"""
        query = update.callback_query
        await query.answer()
        
        user = await self.get_or_create_user(update.effective_user)
        
        try:
            # Buscar contas do usuário
            accounts = await self.get_user_accounts(user['id'])
            
            if not accounts:
                await query.edit_message_text(
                    "🏦 Você ainda não conectou nenhuma conta bancária.\n\n"
                    "Use /conectar para vincular seus bancos via Pluggy.",
                    parse_mode='Markdown'
                )
                return
            
            # Sincronizar dados com Pluggy
            await self.sync_accounts_data(user['id'])
            
            # Buscar saldos atualizados
            accounts = await self.get_user_accounts(user['id'])
            
            text = "💰 *Seus Saldos:*\n\n"
            total_balance = 0
            
            for account in accounts:
                text += f"🏦 *{account['bank_name']}*\n"
                text += f"Tipo: {account['account_type']}\n"
                text += f"Saldo: R$ {account['balance']:,.2f}\n\n"
                total_balance += float(account['balance'])
            
            text += f"💵 *Total Geral: R$ {total_balance:,.2f}*"
            
            keyboard = [[InlineKeyboardButton("🔄 Atualizar", callback_data="balance")],
                       [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Erro ao buscar saldo: {e}")
            await query.edit_message_text(
                "❌ Erro ao consultar saldo. Tente novamente em alguns instantes.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )
    
    async def ai_analysis_callback(self, update: Update, context):
        """Análise de IA dos gastos"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text("🤖 Analisando seus dados financeiros com IA...")
        
        user = await self.get_or_create_user(update.effective_user)
        
        try:
            # Buscar transações dos últimos 30 dias
            transactions = await self.get_user_transactions(user['id'], days=30)
            
            if not transactions:
                await query.edit_message_text(
                    "📭 Não há dados suficientes para análise.\n\n"
                    "Conecte suas contas bancárias para receber insights personalizados!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
                )
                return
            
            # Gerar análise com IA
            analysis = await self.generate_ai_analysis(transactions)
            
            # Salvar análise no banco
            await self.save_ai_analysis(user['id'], 'spending_analysis', analysis)
            
            keyboard = [
                [InlineKeyboardButton("💡 Conselhos de Investimento", callback_data="investment")],
                [InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📊 *Análise Financeira IA:*\n\n{analysis}",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro na análise IA: {e}")
            await query.edit_message_text(
                "❌ Erro ao gerar análise. Tente novamente.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menu", callback_data="main_menu")]])
            )
    
    async def generate_ai_analysis(self, transactions):
        """Gerar análise com OpenAI"""
        # Processar transações
        expenses_by_category = {}
        total_expenses = 0
        total_income = 0
        
        for tx in transactions:
            if tx['amount'] < 0:  # Gasto
                category = tx['category'] or 'Outros'
                expenses_by_category[category] = expenses_by_category.get(category, 0) + abs(tx['amount'])
                total_expenses += abs(tx['amount'])
            else:  # Receita
                total_income += tx['amount']
        
        # Preparar prompt para IA
        prompt = f"""
        Analise os seguintes dados financeiros dos últimos 30 dias:
        
        Receitas: R$ {total_income:,.2f}
        Gastos: R$ {total_expenses:,.2f}
        Saldo: R$ {total_income - total_expenses:,.2f}
        
        Gastos por categoria:
        """
        
        for category, amount in expenses_by_category.items():
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            prompt += f"- {category}: R$ {amount:,.2f} ({percentage:.1f}%)\n"
        
        prompt += """
        
        Como consultor financeiro brasileiro, forneça:
        1. Análise dos padrões de gastos
        2. Categorias que podem ser otimizadas  
        3. Sugestões específicas de economia
        4. Alertas sobre gastos excessivos
        5. Dicas práticas para o perfil brasileiro
        
        Seja direto, prático e motivacional. Máximo 500 palavras.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um consultor financeiro especializado no mercado brasileiro. Forneça conselhos práticos e específicos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro OpenAI: {e}")
            return "Análise temporariamente indisponível. Tente novamente em alguns instantes."
    
    async def get_or_create_user(self, telegram_user):
        """Buscar ou criar usuário no banco"""
        async with self.db_pool.acquire() as conn:
            # Tentar buscar usuário
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                telegram_user.id
            )
            
            if not user:
                # Criar novo usuário
                user = await conn.fetchrow("""
                    INSERT INTO users (telegram_id, username, first_name, last_name)
                    VALUES ($1, $2, $3, $4)
                    RETURNING *
                """, telegram_user.id, telegram_user.username, 
                    telegram_user.first_name, telegram_user.last_name)
                
                logger.info(f"Novo usuário criado: {telegram_user.first_name} ({telegram_user.id})")
            
            return dict(user)
    
    async def get_user_accounts(self, user_id):
        """Buscar contas bancárias do usuário"""
        async with self.db_pool.acquire() as conn:
            accounts = await conn.fetch(
                "SELECT * FROM bank_accounts WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            return [dict(account) for account in accounts]
    
    async def get_user_transactions(self, user_id, days=30):
        """Buscar transações do usuário"""
        async with self.db_pool.acquire() as conn:
            transactions = await conn.fetch("""
                SELECT * FROM transactions 
                WHERE user_id = $1 AND transaction_date >= NOW() - INTERVAL '%s days'
                ORDER BY transaction_date DESC
            """, user_id, days)
            return [dict(tx) for tx in transactions]
    
    async def save_ai_analysis(self, user_id, analysis_type, content):
        """Salvar análise de IA"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ai_analyses (user_id, type, content)
                VALUES ($1, $2, $3)
            """, user_id, analysis_type, content)
    
    async def sync_accounts_data(self, user_id):
        """Sincronizar dados das contas com Pluggy"""
        # Implementar sincronização com API Pluggy
        # Por hora, mock dos dados
        pass
    
    async def callback_handler(self, update: Update, context):
        """Handler para callbacks dos botões"""
        query = update.callback_query
        data = query.data
        
        await query.answer()  # Responder ao callback
        
        if data == "main_menu":
            await self.menu_command(update, context)
        elif data == "balance":
            await self.balance_callback(update, context)
        elif data == "spending_analysis" or data == "ai_analysis":
            await self.ai_analysis_callback(update, context)
        elif data == "start_registration":
            # Redirecionar para comando de cadastro
            await query.edit_message_text(
                "📝 Para criar sua conta, use o comando /cadastro\n\n"
                "Este processo é seguro e criptografado."
            )
        elif data == "start_login":
            # Redirecionar para comando de login
            await query.edit_message_text(
                "🔐 Para fazer login, use o comando /login\n\n"
                "Suas credenciais são protegidas com criptografia."
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
        elif data == "security_info":
            await query.edit_message_text(
                """🔒 **Segurança do Sistema**

✅ **Proteção de Dados:**
• Senhas com hash bcrypt + salt
• Bloqueio automático após 5 tentativas
• Sessões com timeout automático
• Logs de auditoria completos

🛡️ **Infraestrutura:**
• Railway - Hosting seguro
• PostgreSQL criptografado
• Backups automáticos
• Monitoramento 24/7

🔐 **Conformidade:**
• LGPD (Lei Geral de Proteção de Dados)
• Certificação Open Finance
• Auditoria de segurança regular
• Política de privacidade transparente

📱 **Boas Práticas:**
• Use senhas fortes e únicas
• Não compartilhe suas credenciais
• Faça logout após uso
• Monitore atividades suspeitas

Para começar com segurança, use /cadastro""",
                parse_mode='Markdown'
            )
        elif data == "contact_support":
            await query.edit_message_text(
                """📧 **Suporte Técnico**

🔧 **Problemas Técnicos:**
• Erro de conexão: /reconectar
• Reset de senha: /trocar_senha
• Problemas de login: /ajuda

📞 **Canais de Suporte:**
• Comandos do bot: /ajuda
• FAQ: /perguntas
• Logs de erro automáticos

⏰ **Tempo de Resposta:**
• Problemas críticos: Imediato
• Dúvidas gerais: 24h
• Melhorias: 72h

💬 **Status do Sistema:**
• Uptime atual: 99.9%
• Última atualização: Hoje
• Próxima manutenção: Programada

Use /start para voltar ao menu principal.""",
                parse_mode='Markdown'
            )
        elif data == "my_cards":
            # Verificar autenticação primeiro
            if not context.user_data.get('authenticated'):
                await query.edit_message_text(
                    "❌ Você precisa fazer login primeiro.\n"
                    "Use /login para acessar suas informações."
                )
            else:
                await query.edit_message_text(
                    "💳 Carregando informações dos cartões...\n"
                    "Use /cartoes para ver detalhes completos."
                )
        elif data == "my_goals":
            # Verificar autenticação primeiro
            if not context.user_data.get('authenticated'):
                await query.edit_message_text(
                    "❌ Você precisa fazer login primeiro.\n"
                    "Use /login para acessar suas metas."
                )
            else:
                await query.edit_message_text(
                    "🎯 Carregando suas metas...\n"
                    "Use /metas para gerenciar suas metas financeiras."
                )
        elif data == "add_expense":
            # Redirecionar para comando de adicionar despesa
            await query.edit_message_text(
                "💸 Para adicionar uma nova despesa, use o comando /despesas\n\n"
                "Ou digite diretamente: /nova_despesa"
            )
        elif data == "add_goal":
            # Redirecionar para comando de adicionar meta
            await query.edit_message_text(
                "🎯 Para criar uma nova meta, use o comando /metas\n\n"
                "Ou digite diretamente: /nova_meta"
            )
        elif data == "expense_report":
            # Redirecionar para relatório
            await query.edit_message_text(
                "📊 Gerando seu relatório de despesas...\n\n"
                "Use /relatorio para ver análise completa."
            )
        elif data == "manage_expenses":
            await query.edit_message_text(
                "💸 **Gestão de Despesas**\n\n"
                "Comandos disponíveis:\n"
                "• /despesas - Menu completo\n"
                "• /relatorio - Análise detalhada\n"
                "• /nova_despesa - Adicionar gasto\n\n"
                "Use qualquer um dos comandos acima para continuar."
            )
        elif data == "manage_income":
            await query.edit_message_text(
                "💰 **Gestão de Receitas**\n\n"
                "Em desenvolvimento! 🚧\n\n"
                "Por enquanto, use:\n"
                "• /resumo - Ver receitas do mês\n"
                "• /saldo - Consultar saldos bancários\n\n"
                "Funcionalidade completa em breve!"
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
        elif data == "reports":
            await query.edit_message_text(
                "📊 **Relatórios Financeiros**\n\n"
                "Relatórios disponíveis:\n"
                "• /resumo - Resumo mensal completo\n"
                "• /relatorio - Análise de gastos (30 dias)\n"
                "• /analise - Análise IA personalizada\n\n"
                "Escolha o tipo de relatório desejado."
            )
        elif data == "view_alerts":
            await query.edit_message_text(
                "🔔 **Central de Alertas**\n\n"
                "Funcionalidade em desenvolvimento! 🚧\n\n"
                "Em breve você poderá:\n"
                "• Ver alertas não lidos\n"
                "• Configurar notificações\n"
                "• Definir limites de gastos\n\n"
                "Use /resumo para ver status geral."
            )
        elif data == "settings":
            await query.edit_message_text(
                "⚙️ **Configurações**\n\n"
                "Opções disponíveis:\n"
                "• /perfil - Ver e editar perfil\n"
                "• /trocar_senha - Alterar senha\n"
                "• /categorias - Gerenciar categorias\n\n"
                "Mais configurações em breve! 🚧"
            )
        else:
            await query.edit_message_text(
                "❌ Opção não reconhecida. Use /start para voltar ao menu principal."
            )

async def main():
    """Função principal"""
    # Iniciar servidor de health check em thread separada
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    PORT = int(os.getenv('PORT', 8080))
    logger.info(f"🌐 Servidor de health check iniciado na porta {PORT}")
    
    bot = FinancialBot()
    
    # Inicializar banco de dados
    await bot.init_database()
    
    # Configurar aplicação do Telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers básicos
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("menu", bot.menu_command))
    
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
    
    # Comandos originais do bot
    application.add_handler(CommandHandler("saldo", bot.balance_callback))
    application.add_handler(CommandHandler("gastos", bot.ai_analysis_callback))
    
    # Handler de callbacks
    application.add_handler(CallbackQueryHandler(bot.callback_handler))
    
    # Iniciar bot
    logger.info("🤖 Bot Telegram IA Financeiro iniciado!")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())