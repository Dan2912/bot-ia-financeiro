# 🔐 Segurança de Credenciais

## ⚠️ REGRAS CRÍTICAS DE SEGURANÇA

### ❌ NUNCA FAÇA ISSO:
- Não coloque credenciais no código
- Não commite arquivos .env
- Não compartilhe tokens em mensagens
- Não deixe credenciais em comentários
- Não use credenciais de produção em desenvolvimento

### ✅ SEMPRE FAÇA ISSO:
- Configure variáveis de ambiente no Railway
- Use .env apenas localmente para testes
- Mantenha credenciais em local seguro
- Use diferentes chaves para dev/prod
- Regenere chaves comprometidas imediatamente

## 🛡️ Configuração Segura no Railway

### 1. Acessar Variáveis
1. Entre no Railway.app
2. Selecione seu projeto
3. Vá na aba "Variables"
4. Adicione uma por uma

### 2. Variáveis Obrigatórias
```bash
# Bot Telegram
TELEGRAM_BOT_TOKEN=123456789:AAA...

# Pluggy (https://pluggy.ai)
PLUGGY_CLIENT_ID=sua_client_id
PLUGGY_CLIENT_SECRET=sua_client_secret  
PLUGGY_SANDBOX=true

# OpenAI (https://platform.openai.com)
OPENAI_API_KEY=sk-proj-...

# PostgreSQL (Railway gera automaticamente)
DATABASE_URL=postgresql://...
```

### 3. Variáveis Opcionais
```bash
# Google Gemini
GEMINI_API_KEY=AIza...

# Ambiente
ENV=production
PORT=8080
```

## 🔑 Como Obter Credenciais

### Telegram Bot Token
1. Abra o Telegram
2. Procure por `@BotFather`
3. Digite `/newbot`
4. Siga as instruções
5. **Copie o token e guarde em local seguro**

### Pluggy API
1. Acesse https://pluggy.ai
2. Crie uma conta
3. Vá no dashboard
4. Copie Client ID e Client Secret
5. **Use primeiro em modo sandbox**

### OpenAI API Key
1. Acesse https://platform.openai.com
2. Faça login/cadastro
3. Vá em "API Keys"
4. Clique "Create new secret key"
5. **Copie imediatamente (só aparece uma vez)**

## 🚨 Se Suas Credenciais Vazaram

### Ação Imediata:
1. **Regenere todas as chaves comprometidas**
2. **Atualize no Railway imediatamente**  
3. **Revogue acesso das chaves antigas**
4. **Monitore uso não autorizado**

### Telegram Bot:
- Vá no @BotFather
- Digite `/revoke` + nome do bot
- Gere novo token

### OpenAI:
- Vá no dashboard OpenAI
- Delete a chave comprometida
- Crie uma nova

### Pluggy:
- Acesse o dashboard Pluggy
- Regenere as credenciais
- Atualize no Railway

## 📋 Checklist de Segurança

- [ ] .env está no .gitignore
- [ ] Nenhuma credencial no código
- [ ] Variáveis configuradas no Railway
- [ ] Tokens funcionando corretamente
- [ ] Backup seguro das credenciais
- [ ] Sandbox ativo em desenvolvimento
- [ ] Monitoramento de uso ativo

## 🎯 Exemplo de .env Local (Apenas Teste)

```bash
# ⚠️  APENAS PARA TESTE LOCAL - NUNCA COMMITAR!

# Use tokens de desenvolvimento/sandbox
TELEGRAM_BOT_TOKEN=123:AAA-teste-local
PLUGGY_CLIENT_ID=test_id
PLUGGY_CLIENT_SECRET=test_secret
PLUGGY_SANDBOX=true
OPENAI_API_KEY=sk-test-...

# Banco local
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=123456
DB_NAME=go_control_dev
```

**Lembre-se:** Este arquivo .env local **NUNCA** deve ser commitado!

## 📞 Suporte de Segurança

Se tiver dúvidas sobre segurança:
- **GitHub Issues:** https://github.com/Danillo2912/go_control/issues
- **Telegram:** @Danillo2912

**Segurança em primeiro lugar! 🛡️**