import hashlib
import bcrypt
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UserAuthSystem:
    """Sistema completo de autenticação e gerenciamento de usuários"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """
        Validar força da senha
        Retorna: {'valid': bool, 'score': int, 'messages': list}
        """
        issues = []
        score = 0
        
        # Verificações básicas
        if len(password) < 8:
            issues.append("Senha deve ter pelo menos 8 caracteres")
        elif len(password) >= 12:
            score += 2
        else:
            score += 1
            
        if not re.search(r'[a-z]', password):
            issues.append("Senha deve conter pelo menos uma letra minúscula")
        else:
            score += 1
            
        if not re.search(r'[A-Z]', password):
            issues.append("Senha deve conter pelo menos uma letra maiúscula") 
        else:
            score += 1
            
        if not re.search(r'\d', password):
            issues.append("Senha deve conter pelo menos um número")
        else:
            score += 1
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Senha deve conter pelo menos um caractere especial")
        else:
            score += 2
            
        # Verificações avançadas
        if len(set(password)) < len(password) * 0.7:
            issues.append("Senha tem muitos caracteres repetidos")
        else:
            score += 1
            
        # Senhas comuns
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', '12345678', 'admin', 'letmein', 'welcome'
        ]
        if password.lower() in common_passwords:
            issues.append("Senha muito comum, escolha uma mais segura")
            score = max(0, score - 3)
        
        return {
            'valid': len(issues) == 0,
            'score': min(score, 10),  # Max 10
            'strength': 'Muito Fraca' if score <= 2 else 'Fraca' if score <= 4 else 'Média' if score <= 6 else 'Forte' if score <= 8 else 'Muito Forte',
            'messages': issues
        }
    
    @staticmethod
    def hash_password(password: str) -> tuple[str, str]:
        """
        Criar hash seguro da senha com bcrypt + salt adicional
        Retorna: (password_hash, salt)
        """
        # Gerar salt adicional
        salt = secrets.token_hex(16)
        
        # Combinar senha com salt
        salted_password = password + salt
        
        # Hash com bcrypt (já inclui salt interno)
        password_hash = bcrypt.hashpw(salted_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        
        return password_hash.decode('utf-8'), salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verificar senha contra hash armazenado"""
        try:
            salted_password = password + salt
            return bcrypt.checkpw(salted_password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {e}")
            return False
    
    async def register_user(self, telegram_user, full_name: str, password: str, 
                           email: Optional[str] = None, phone: Optional[str] = None,
                           registration_ip: Optional[str] = None) -> Dict[str, Any]:
        """
        Registrar novo usuário completo
        """
        # Validar senha
        password_validation = self.validate_password(password)
        if not password_validation['valid']:
            return {
                'success': False,
                'error': 'password_weak',
                'messages': password_validation['messages']
            }
        
        # Validar email se fornecido
        if email and not self.validate_email(email):
            return {
                'success': False,
                'error': 'invalid_email',
                'message': 'Email inválido'
            }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Verificar se usuário já existe
                existing = await conn.fetchrow(
                    "SELECT id FROM users WHERE telegram_id = $1 OR email = $2",
                    telegram_user.id, email
                )
                
                if existing:
                    return {
                        'success': False,
                        'error': 'user_exists',
                        'message': 'Usuário já cadastrado'
                    }
                
                # Hash da senha
                password_hash, salt = self.hash_password(password)
                
                # Inserir usuário
                user = await conn.fetchrow("""
                    INSERT INTO users (
                        telegram_id, telegram_username, full_name, first_name, 
                        last_name, email, phone, password_hash, password_salt,
                        registration_ip, is_active, is_verified
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id, created_at
                """, 
                    telegram_user.id,
                    telegram_user.username,
                    full_name,
                    telegram_user.first_name,
                    telegram_user.last_name,
                    email,
                    phone,
                    password_hash,
                    salt,
                    registration_ip,
                    True,  # is_active
                    False  # is_verified - precisa verificar email
                )
                
                logger.info(f"Novo usuário registrado: {full_name} (ID: {user['id']})")
                
                return {
                    'success': True,
                    'user_id': user['id'],
                    'message': 'Usuário cadastrado com sucesso!',
                    'password_strength': password_validation['strength']
                }
                
        except Exception as e:
            logger.error(f"Erro ao registrar usuário: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Erro interno. Tente novamente.'
            }
    
    async def authenticate_user(self, telegram_id: int, password: str, 
                              login_ip: Optional[str] = None) -> Dict[str, Any]:
        """Autenticar usuário com controle de tentativas"""
        try:
            async with self.db_pool.acquire() as conn:
                # Buscar usuário
                user = await conn.fetchrow("""
                    SELECT id, full_name, password_hash, password_salt, is_active,
                           failed_login_attempts, account_locked_until
                    FROM users WHERE telegram_id = $1
                """, telegram_id)
                
                if not user:
                    return {
                        'success': False,
                        'error': 'user_not_found',
                        'message': 'Usuário não encontrado'
                    }
                
                # Verificar se conta está ativa
                if not user['is_active']:
                    return {
                        'success': False,
                        'error': 'account_inactive',
                        'message': 'Conta inativa. Entre em contato com o suporte.'
                    }
                
                # Verificar se conta está bloqueada
                if user['account_locked_until'] and user['account_locked_until'] > datetime.now():
                    return {
                        'success': False,
                        'error': 'account_locked',
                        'message': f'Conta bloqueada até {user["account_locked_until"].strftime("%H:%M")}'
                    }
                
                # Verificar senha
                if self.verify_password(password, user['password_hash'], user['password_salt']):
                    # Login bem-sucedido
                    await conn.execute("""
                        UPDATE users SET 
                            last_login = CURRENT_TIMESTAMP,
                            last_login_ip = $1,
                            failed_login_attempts = 0,
                            account_locked_until = NULL
                        WHERE id = $2
                    """, login_ip, user['id'])
                    
                    return {
                        'success': True,
                        'user_id': user['id'],
                        'full_name': user['full_name'],
                        'message': 'Login realizado com sucesso!'
                    }
                else:
                    # Login falhou - incrementar tentativas
                    new_attempts = user['failed_login_attempts'] + 1
                    lock_until = None
                    
                    # Bloquear após 5 tentativas por 30 minutos
                    if new_attempts >= 5:
                        lock_until = datetime.now() + timedelta(minutes=30)
                    
                    await conn.execute("""
                        UPDATE users SET 
                            failed_login_attempts = $1,
                            account_locked_until = $2
                        WHERE id = $3
                    """, new_attempts, lock_until, user['id'])
                    
                    remaining_attempts = max(0, 5 - new_attempts)
                    
                    return {
                        'success': False,
                        'error': 'invalid_password',
                        'message': f'Senha incorreta. {remaining_attempts} tentativas restantes.',
                        'attempts_remaining': remaining_attempts
                    }
                    
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Erro interno. Tente novamente.'
            }
    
    async def change_password(self, user_id: int, old_password: str, 
                             new_password: str) -> Dict[str, Any]:
        """Alterar senha do usuário"""
        # Validar nova senha
        password_validation = self.validate_password(new_password)
        if not password_validation['valid']:
            return {
                'success': False,
                'error': 'password_weak',
                'messages': password_validation['messages']
            }
        
        try:
            async with self.db_pool.acquire() as conn:
                # Verificar senha atual
                user = await conn.fetchrow("""
                    SELECT password_hash, password_salt, is_active
                    FROM users WHERE id = $1
                """, user_id)
                
                if not user or not user['is_active']:
                    return {
                        'success': False,
                        'error': 'user_not_found',
                        'message': 'Usuário não encontrado ou inativo'
                    }
                
                # Verificar senha atual
                if not self.verify_password(old_password, user['password_hash'], user['password_salt']):
                    return {
                        'success': False,
                        'error': 'invalid_current_password',
                        'message': 'Senha atual incorreta'
                    }
                
                # Gerar hash da nova senha
                new_hash, new_salt = self.hash_password(new_password)
                
                # Atualizar senha
                await conn.execute("""
                    UPDATE users SET 
                        password_hash = $1,
                        password_salt = $2,
                        password_changed_at = CURRENT_TIMESTAMP,
                        failed_login_attempts = 0,
                        account_locked_until = NULL
                    WHERE id = $3
                """, new_hash, new_salt, user_id)
                
                logger.info(f"Senha alterada para usuário ID: {user_id}")
                
                return {
                    'success': True,
                    'message': 'Senha alterada com sucesso!',
                    'password_strength': password_validation['strength']
                }
                
        except Exception as e:
            logger.error(f"Erro ao alterar senha: {e}")
            return {
                'success': False,
                'error': 'database_error', 
                'message': 'Erro interno. Tente novamente.'
            }
    
    async def update_user_status(self, user_id: int, is_active: bool, 
                                admin_user_id: int) -> Dict[str, Any]:
        """Ativar/desativar usuário (admin only)"""
        try:
            async with self.db_pool.acquire() as conn:
                # Verificar se admin existe
                admin = await conn.fetchrow(
                    "SELECT is_premium FROM users WHERE id = $1 AND is_active = true",
                    admin_user_id
                )
                
                if not admin or not admin['is_premium']:
                    return {
                        'success': False,
                        'error': 'unauthorized',
                        'message': 'Acesso negado'
                    }
                
                # Atualizar status
                result = await conn.execute("""
                    UPDATE users SET is_active = $1 
                    WHERE id = $2
                """, is_active, user_id)
                
                if result == 'UPDATE 1':
                    action = 'ativado' if is_active else 'desativado'
                    logger.info(f"Usuário {user_id} {action} pelo admin {admin_user_id}")
                    
                    return {
                        'success': True,
                        'message': f'Usuário {action} com sucesso!'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'user_not_found',
                        'message': 'Usuário não encontrado'
                    }
                    
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")
            return {
                'success': False,
                'error': 'database_error',
                'message': 'Erro interno. Tente novamente.'
            }
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Buscar perfil completo do usuário"""
        try:
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow("""
                    SELECT 
                        id, telegram_id, telegram_username, full_name,
                        first_name, last_name, email, phone, is_active,
                        is_verified, is_premium, created_at, updated_at,
                        last_login, password_changed_at, preferred_language,
                        timezone, failed_login_attempts
                    FROM users WHERE id = $1
                """, user_id)
                
                if user:
                    return dict(user)
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar perfil: {e}")
            return None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None