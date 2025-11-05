import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import asyncpg
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class FinancialManager:
    """Sistema completo de gestão financeira"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    # ========================
    # GESTÃO DE CATEGORIAS
    # ========================
    
    async def create_default_categories(self, user_id: int):
        """Criar categorias padrão para novo usuário"""
        default_categories = [
            # Despesas
            ('Alimentação', 'expense', '#FF6B6B', '🍽️'),
            ('Transporte', 'expense', '#4ECDC4', '🚗'),
            ('Moradia', 'expense', '#45B7D1', '🏠'),
            ('Saúde', 'expense', '#96CEB4', '🏥'),
            ('Educação', 'expense', '#FFEAA7', '📚'),
            ('Lazer', 'expense', '#DDA0DD', '🎮'),
            ('Roupas', 'expense', '#98D8C8', '👕'),
            ('Outros', 'expense', '#A0A0A0', '📦'),
            
            # Receitas
            ('Salário', 'income', '#55A3FF', '💼'),
            ('Freelance', 'income', '#26de81', '💻'),
            ('Investimentos', 'income', '#FD79A8', '📈'),
            ('Outros', 'income', '#FDCB6E', '💰')
        ]
        
        try:
            async with self.db_pool.acquire() as conn:
                for name, cat_type, color, icon in default_categories:
                    await conn.execute("""
                        INSERT INTO categories (user_id, name, type, color, icon)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (user_id, name, type) DO NOTHING
                    """, user_id, name, cat_type, color, icon)
            
            logger.info(f"Categorias padrão criadas para usuário {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar categorias padrão: {e}")
            return False
    
    async def get_user_categories(self, user_id: int, category_type: Optional[str] = None) -> List[Dict]:
        """Buscar categorias do usuário"""
        try:
            async with self.db_pool.acquire() as conn:
                if category_type:
                    categories = await conn.fetch("""
                        SELECT * FROM categories 
                        WHERE user_id = $1 AND type = $2 AND is_active = true
                        ORDER BY name
                    """, user_id, category_type)
                else:
                    categories = await conn.fetch("""
                        SELECT * FROM categories 
                        WHERE user_id = $1 AND is_active = true
                        ORDER BY type, name
                    """, user_id)
                
                return [dict(cat) for cat in categories]
                
        except Exception as e:
            logger.error(f"Erro ao buscar categorias: {e}")
            return []
    
    async def create_category(self, user_id: int, name: str, category_type: str, 
                            color: str = None, icon: str = None) -> Dict[str, Any]:
        """Criar nova categoria"""
        try:
            async with self.db_pool.acquire() as conn:
                category = await conn.fetchrow("""
                    INSERT INTO categories (user_id, name, type, color, icon)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING *
                """, user_id, name, category_type, color, icon)
                
                return {
                    'success': True,
                    'category': dict(category),
                    'message': f'Categoria "{name}" criada com sucesso!'
                }
                
        except asyncpg.UniqueViolationError:
            return {
                'success': False,
                'error': 'duplicate_category',
                'message': f'Categoria "{name}" já existe para {category_type}s'
            }
        except Exception as e:
            logger.error(f"Erro ao criar categoria: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Erro ao criar categoria. Tente novamente.'
            }
    
    # ========================
    # GESTÃO DE METAS
    # ========================
    
    async def create_goal(self, user_id: int, title: str, goal_type: str, 
                         target_amount: Decimal, target_date: date = None,
                         description: str = None, category_id: int = None,
                         priority: int = 1) -> Dict[str, Any]:
        """Criar nova meta financeira"""
        try:
            async with self.db_pool.acquire() as conn:
                goal = await conn.fetchrow("""
                    INSERT INTO goals (
                        user_id, title, description, goal_type, target_amount,
                        target_date, category_id, priority
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING *
                """, user_id, title, description, goal_type, target_amount,
                    target_date, category_id, priority)
                
                return {
                    'success': True,
                    'goal': dict(goal),
                    'message': f'Meta "{title}" criada com sucesso!'
                }
                
        except Exception as e:
            logger.error(f"Erro ao criar meta: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Erro ao criar meta. Tente novamente.'
            }
    
    async def get_user_goals(self, user_id: int, include_completed: bool = False) -> List[Dict]:
        """Buscar metas do usuário"""
        try:
            async with self.db_pool.acquire() as conn:
                if include_completed:
                    goals = await conn.fetch("""
                        SELECT g.*, c.name as category_name, c.icon as category_icon
                        FROM goals g
                        LEFT JOIN categories c ON g.category_id = c.id
                        WHERE g.user_id = $1 AND g.is_active = true
                        ORDER BY g.priority DESC, g.created_at DESC
                    """, user_id)
                else:
                    goals = await conn.fetch("""
                        SELECT g.*, c.name as category_name, c.icon as category_icon
                        FROM goals g
                        LEFT JOIN categories c ON g.category_id = c.id
                        WHERE g.user_id = $1 AND g.is_active = true AND g.is_completed = false
                        ORDER BY g.priority DESC, g.created_at DESC
                    """, user_id)
                
                return [dict(goal) for goal in goals]
                
        except Exception as e:
            logger.error(f"Erro ao buscar metas: {e}")
            return []
    
    async def update_goal_progress(self, goal_id: int, amount: Decimal) -> Dict[str, Any]:
        """Atualizar progresso da meta"""
        try:
            async with self.db_pool.acquire() as conn:
                # Buscar meta atual
                goal = await conn.fetchrow("""
                    SELECT * FROM goals WHERE id = $1 AND is_active = true
                """, goal_id)
                
                if not goal:
                    return {
                        'success': False,
                        'error': 'goal_not_found',
                        'message': 'Meta não encontrada'
                    }
                
                new_current = goal['current_amount'] + amount
                is_completed = new_current >= goal['target_amount']
                
                # Atualizar meta
                updated_goal = await conn.fetchrow("""
                    UPDATE goals SET 
                        current_amount = $1,
                        is_completed = $2,
                        completed_at = CASE WHEN $2 THEN CURRENT_TIMESTAMP ELSE NULL END
                    WHERE id = $3
                    RETURNING *
                """, new_current, is_completed, goal_id)
                
                # Criar alerta se meta foi completada
                if is_completed and not goal['is_completed']:
                    await self.create_alert(
                        user_id=goal['user_id'],
                        alert_type='goal_completed',
                        title='🎉 Meta Conquistada!',
                        message=f'Parabéns! Você atingiu a meta "{goal["title"]}"',
                        related_id=goal_id,
                        related_type='goal'
                    )
                
                return {
                    'success': True,
                    'goal': dict(updated_goal),
                    'was_completed': is_completed and not goal['is_completed'],
                    'message': 'Progresso atualizado com sucesso!'
                }
                
        except Exception as e:
            logger.error(f"Erro ao atualizar progresso da meta: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Erro ao atualizar progresso. Tente novamente.'
            }
    
    # ========================
    # GESTÃO DE TRANSAÇÕES
    # ========================
    
    async def create_transaction(self, user_id: int, title: str, amount: Decimal,
                               transaction_type: str, category_id: int = None,
                               goal_id: int = None, description: str = None,
                               transaction_date: date = None, due_date: date = None,
                               is_installment: bool = False, total_installments: int = None,
                               is_recurring: bool = False, recurrence_type: str = None,
                               tags: List[str] = None, notes: str = None) -> Dict[str, Any]:
        """Criar nova transação"""
        try:
            async with self.db_pool.acquire() as conn:
                if transaction_date is None:
                    transaction_date = date.today()
                
                # Criar transação principal
                transaction = await conn.fetchrow("""
                    INSERT INTO transactions (
                        user_id, title, description, amount, type, category_id,
                        goal_id, transaction_date, due_date, is_installment,
                        total_installments, is_recurring, recurrence_type,
                        tags, notes, status
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    RETURNING *
                """, user_id, title, description, amount, transaction_type, category_id,
                    goal_id, transaction_date, due_date, is_installment,
                    total_installments, is_recurring, recurrence_type,
                    tags, notes, 'paid' if transaction_date <= date.today() else 'pending')
                
                created_transactions = [dict(transaction)]
                
                # Criar parcelas se necessário
                if is_installment and total_installments and total_installments > 1:
                    installment_amount = amount / total_installments
                    
                    for i in range(2, total_installments + 1):
                        installment_date = transaction_date.replace(
                            month=transaction_date.month + i - 1
                        ) if transaction_date.month + i - 1 <= 12 else \
                        transaction_date.replace(
                            year=transaction_date.year + 1,
                            month=transaction_date.month + i - 13
                        )
                        
                        installment = await conn.fetchrow("""
                            INSERT INTO transactions (
                                user_id, title, description, amount, type, category_id,
                                goal_id, transaction_date, is_installment, installment_number,
                                total_installments, parent_transaction_id, tags, notes, status
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                            RETURNING *
                        """, user_id, f"{title} ({i}/{total_installments})", description,
                            installment_amount, transaction_type, category_id, goal_id,
                            installment_date, True, i, total_installments,
                            transaction['id'], tags, notes,
                            'paid' if installment_date <= date.today() else 'pending')
                        
                        created_transactions.append(dict(installment))
                
                # Atualizar progresso da meta se associada
                if goal_id and transaction_type == 'income':
                    await self.update_goal_progress(goal_id, amount)
                
                return {
                    'success': True,
                    'transactions': created_transactions,
                    'message': f'{"Transação" if not is_installment else f"Parcelamento ({total_installments}x)"} criada com sucesso!'
                }
                
        except Exception as e:
            logger.error(f"Erro ao criar transação: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Erro ao criar transação. Tente novamente.'
            }
    
    async def get_user_transactions(self, user_id: int, start_date: date = None,
                                  end_date: date = None, transaction_type: str = None,
                                  category_id: int = None, limit: int = 50) -> List[Dict]:
        """Buscar transações do usuário"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT t.*, c.name as category_name, c.icon as category_icon,
                           g.title as goal_title
                    FROM transactions t
                    LEFT JOIN categories c ON t.category_id = c.id
                    LEFT JOIN goals g ON t.goal_id = g.id
                    WHERE t.user_id = $1
                """
                params = [user_id]
                param_count = 1
                
                if start_date:
                    param_count += 1
                    query += f" AND t.transaction_date >= ${param_count}"
                    params.append(start_date)
                
                if end_date:
                    param_count += 1
                    query += f" AND t.transaction_date <= ${param_count}"
                    params.append(end_date)
                
                if transaction_type:
                    param_count += 1
                    query += f" AND t.type = ${param_count}"
                    params.append(transaction_type)
                
                if category_id:
                    param_count += 1
                    query += f" AND t.category_id = ${param_count}"
                    params.append(category_id)
                
                query += " ORDER BY t.transaction_date DESC, t.created_at DESC"
                
                if limit:
                    param_count += 1
                    query += f" LIMIT ${param_count}"
                    params.append(limit)
                
                transactions = await conn.fetch(query, *params)
                return [dict(tx) for tx in transactions]
                
        except Exception as e:
            logger.error(f"Erro ao buscar transações: {e}")
            return []
    
    # ========================
    # GESTÃO DE ORÇAMENTOS
    # ========================
    
    async def create_budget(self, user_id: int, category_id: int, 
                          month_year: date, budget_limit: Decimal) -> Dict[str, Any]:
        """Criar orçamento mensal para categoria"""
        try:
            async with self.db_pool.acquire() as conn:
                budget = await conn.fetchrow("""
                    INSERT INTO budgets (user_id, category_id, month_year, budget_limit)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id, category_id, month_year)
                    DO UPDATE SET budget_limit = $4, is_active = true
                    RETURNING *
                """, user_id, category_id, month_year, budget_limit)
                
                return {
                    'success': True,
                    'budget': dict(budget),
                    'message': 'Orçamento criado com sucesso!'
                }
                
        except Exception as e:
            logger.error(f"Erro ao criar orçamento: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Erro ao criar orçamento. Tente novamente.'
            }
    
    async def get_monthly_budgets(self, user_id: int, month_year: date) -> List[Dict]:
        """Buscar orçamentos do mês"""
        try:
            async with self.db_pool.acquire() as conn:
                budgets = await conn.fetch("""
                    SELECT b.*, c.name as category_name, c.icon as category_icon,
                           COALESCE(SUM(t.amount), 0) as actual_spent
                    FROM budgets b
                    LEFT JOIN categories c ON b.category_id = c.id
                    LEFT JOIN transactions t ON t.category_id = b.category_id 
                        AND t.user_id = b.user_id 
                        AND t.type = 'expense'
                        AND DATE_TRUNC('month', t.transaction_date) = b.month_year
                        AND t.status = 'paid'
                    WHERE b.user_id = $1 AND b.month_year = $2 AND b.is_active = true
                    GROUP BY b.id, c.name, c.icon
                    ORDER BY c.name
                """, user_id, month_year)
                
                return [dict(budget) for budget in budgets]
                
        except Exception as e:
            logger.error(f"Erro ao buscar orçamentos: {e}")
            return []
    
    # ========================
    # ANÁLISES E RELATÓRIOS
    # ========================
    
    async def get_monthly_summary(self, user_id: int, month_year: date) -> Dict[str, Any]:
        """Resumo financeiro do mês"""
        try:
            async with self.db_pool.acquire() as conn:
                # Receitas e despesas do mês
                summary = await conn.fetchrow("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
                        COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expenses,
                        COUNT(CASE WHEN type = 'income' THEN 1 END) as income_count,
                        COUNT(CASE WHEN type = 'expense' THEN 1 END) as expense_count
                    FROM transactions
                    WHERE user_id = $1 
                    AND DATE_TRUNC('month', transaction_date) = $2
                    AND status = 'paid'
                """, user_id, month_year)
                
                # Gastos por categoria
                expenses_by_category = await conn.fetch("""
                    SELECT c.name, c.icon, COALESCE(SUM(t.amount), 0) as total
                    FROM categories c
                    LEFT JOIN transactions t ON t.category_id = c.id 
                        AND t.user_id = $1
                        AND t.type = 'expense'
                        AND DATE_TRUNC('month', t.transaction_date) = $2
                        AND t.status = 'paid'
                    WHERE c.user_id = $1 AND c.type = 'expense'
                    GROUP BY c.id, c.name, c.icon
                    HAVING COALESCE(SUM(t.amount), 0) > 0
                    ORDER BY total DESC
                """, user_id, month_year)
                
                # Metas ativas
                active_goals = await conn.fetch("""
                    SELECT * FROM goals
                    WHERE user_id = $1 AND is_active = true AND is_completed = false
                    ORDER BY priority DESC
                    LIMIT 5
                """, user_id)
                
                return {
                    'total_income': summary['total_income'],
                    'total_expenses': summary['total_expenses'],
                    'balance': summary['total_income'] - summary['total_expenses'],
                    'income_count': summary['income_count'],
                    'expense_count': summary['expense_count'],
                    'expenses_by_category': [dict(cat) for cat in expenses_by_category],
                    'active_goals': [dict(goal) for goal in active_goals]
                }
                
        except Exception as e:
            logger.error(f"Erro ao buscar resumo mensal: {e}")
            return {}
    
    async def get_spending_analysis(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Análise de gastos dos últimos dias"""
        try:
            async with self.db_pool.acquire() as conn:
                start_date = date.today() - timedelta(days=days)
                
                # Análise geral
                analysis = await conn.fetchrow("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_spent,
                        COALESCE(AVG(CASE WHEN type = 'expense' THEN amount ELSE NULL END), 0) as avg_expense,
                        COUNT(CASE WHEN type = 'expense' THEN 1 END) as expense_count,
                        MAX(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as max_expense
                    FROM transactions
                    WHERE user_id = $1 
                    AND transaction_date >= $2
                    AND type = 'expense'
                    AND status = 'paid'
                """, user_id, start_date)
                
                # Top categorias
                top_categories = await conn.fetch("""
                    SELECT c.name, c.icon, SUM(t.amount) as total,
                           COUNT(t.id) as count,
                           AVG(t.amount) as avg_amount
                    FROM transactions t
                    JOIN categories c ON t.category_id = c.id
                    WHERE t.user_id = $1 
                    AND t.transaction_date >= $2
                    AND t.type = 'expense'
                    AND t.status = 'paid'
                    GROUP BY c.id, c.name, c.icon
                    ORDER BY total DESC
                    LIMIT 10
                """, user_id, start_date)
                
                # Tendência (comparar com período anterior)
                prev_period = await conn.fetchrow("""
                    SELECT COALESCE(SUM(amount), 0) as prev_total
                    FROM transactions
                    WHERE user_id = $1 
                    AND transaction_date >= $2
                    AND transaction_date < $3
                    AND type = 'expense'
                    AND status = 'paid'
                """, user_id, start_date - timedelta(days=days), start_date)
                
                current_total = analysis['total_spent']
                prev_total = prev_period['prev_total']
                trend = ((current_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
                
                return {
                    'period_days': days,
                    'total_spent': current_total,
                    'avg_expense': analysis['avg_expense'],
                    'expense_count': analysis['expense_count'],
                    'max_expense': analysis['max_expense'],
                    'top_categories': [dict(cat) for cat in top_categories],
                    'trend_percent': round(trend, 2),
                    'daily_average': current_total / days if days > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Erro na análise de gastos: {e}")
            return {}
    
    # ========================
    # SISTEMA DE ALERTAS
    # ========================
    
    async def create_alert(self, user_id: int, alert_type: str, title: str,
                         message: str, related_id: int = None, related_type: str = None,
                         priority: int = 1) -> bool:
        """Criar novo alerta"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO alerts (
                        user_id, alert_type, title, message, related_id,
                        related_type, priority
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, user_id, alert_type, title, message, related_id, related_type, priority)
                
                return True
                
        except Exception as e:
            logger.error(f"Erro ao criar alerta: {e}")
            return False
    
    async def get_user_alerts(self, user_id: int, unread_only: bool = True) -> List[Dict]:
        """Buscar alertas do usuário"""
        try:
            async with self.db_pool.acquire() as conn:
                if unread_only:
                    alerts = await conn.fetch("""
                        SELECT * FROM alerts
                        WHERE user_id = $1 AND is_read = false
                        AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                        ORDER BY priority DESC, created_at DESC
                    """, user_id)
                else:
                    alerts = await conn.fetch("""
                        SELECT * FROM alerts
                        WHERE user_id = $1
                        AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                        ORDER BY is_read, priority DESC, created_at DESC
                        LIMIT 50
                    """, user_id)
                
                return [dict(alert) for alert in alerts]
                
        except Exception as e:
            logger.error(f"Erro ao buscar alertas: {e}")
            return []
    
    async def mark_alert_read(self, alert_id: int, user_id: int) -> bool:
        """Marcar alerta como lido"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE alerts SET is_read = true
                    WHERE id = $1 AND user_id = $2
                """, alert_id, user_id)
                
                return result == 'UPDATE 1'
                
        except Exception as e:
            logger.error(f"Erro ao marcar alerta como lido: {e}")
            return False
    
    # ========================
    # UTILITÁRIOS
    # ========================
    
    def format_currency(self, amount: Decimal) -> str:
        """Formatar valor em moeda brasileira"""
        return f"R$ {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def calculate_percentage(self, current: Decimal, target: Decimal) -> float:
        """Calcular porcentagem"""
        if target == 0:
            return 0
        return float((current / target) * 100)
    
    def get_goal_type_emoji(self, goal_type: str) -> str:
        """Emoji para tipo de meta"""
        emojis = {
            'saving': '💰',
            'spending_limit': '🛑',
            'investment': '📈',
            'debt_payment': '💳',
            'emergency_fund': '🆘',
            'vacation': '🏖️',
            'purchase': '🛒'
        }
        return emojis.get(goal_type, '🎯')
    
    def get_transaction_status_emoji(self, status: str) -> str:
        """Emoji para status de transação"""
        emojis = {
            'pending': '⏳',
            'paid': '✅',
            'overdue': '🔴',
            'cancelled': '❌'
        }
        return emojis.get(status, '❓')