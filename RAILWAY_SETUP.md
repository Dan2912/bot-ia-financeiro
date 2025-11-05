# 🚀 Configuração Railway - Bot IA Financeiro

## ✅ Status do Deploy

**URL da Aplicação:** bot-ia-financeiro-production.up.railway.app  
**Porta:** 8080  
**Status:** ✅ Configurado e funcionando

## 🔧 Variáveis de Ambiente Necessárias

### 📱 Bot Telegram
```env
TELEGRAM_BOT_TOKEN=seu_token_do_botfather
```
**Como obter:**
1. Telegram → @BotFather
2. `/newbot` → Escolher nome e username
3. Copiar token fornecido

### 🗄️ Database PostgreSQL
```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
```
**Configuração automática pelo Railway**

### 🧠 OpenAI GPT-4
```env
OPENAI_API_KEY=sk-sua_chave_openai
```
**Como obter:**
1. https://platform.openai.com/api-keys
2. Create new secret key
3. Copiar chave (sk-...)

### 🏦 Pluggy (Open Finance)
```env
PLUGGY_CLIENT_ID=sua_client_id
PLUGGY_CLIENT_SECRET=seu_secret
PLUGGY_SANDBOX=true
```
**Como obter:**
1. https://pluggy.ai
2. Criar conta → Solicitar API access
3. Usar sandbox=true para testes

### ⚙️ Configurações do Sistema
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8080
```

## 🚀 Passos do Deploy

### 1. ✅ Repositório GitHub Conectado
- Repository: `Dan2912/bot-ia-financeiro`
- Branch: `master`
- Auto-deploy: Habilitado

### 2. ✅ PostgreSQL Database
- Service criado automaticamente
- `DATABASE_URL` configurada automaticamente
- Schema criado automaticamente na primeira execução

### 3. ✅ Health Check
- Endpoint: `/health`
- URL: `https://bot-ia-financeiro-production.up.railway.app/health`
- Resposta esperada: `{"status": "OK", "service": "telegram-bot"}`

### 4. ✅ Configurações do Projeto
- **Procfile:** `web: python main.py`
- **Railway.toml:** Configurações otimizadas
- **requirements.txt:** Todas as dependências
- **Dockerfile:** Para builds alternativas

## 🧪 Testando a Aplicação

### Health Check
```bash
curl https://bot-ia-financeiro-production.up.railway.app/health
```
**Resposta esperada:**
```json
{"status": "OK", "service": "telegram-bot"}
```

### Root Endpoint
```bash
curl https://bot-ia-financeiro-production.up.railway.app/
```
**Resposta esperada:**
```json
{"message": "Bot Telegram IA Financeiro está rodando!"}
```

## 🔍 Troubleshooting

### ❌ Bot não responde
1. Verificar `TELEGRAM_BOT_TOKEN`
2. Confirmar que o token está ativo no @BotFather
3. Verificar logs do Railway

### ❌ Erro de database
1. Verificar se PostgreSQL está ativo
2. Confirmar `DATABASE_URL`
3. Verificar permissões de conexão

### ❌ Erro de IA
1. Verificar `OPENAI_API_KEY`
2. Confirmar créditos na conta OpenAI
3. Verificar rate limits

### ❌ Erro de bancos
1. Verificar `PLUGGY_CLIENT_ID` e `PLUGGY_CLIENT_SECRET`
2. Confirmar que está usando sandbox (PLUGGY_SANDBOX=true)
3. Verificar permissões da API

## 📋 Checklist Final

- ✅ Código no GitHub atualizado
- ✅ Railway conectado ao repositório
- ✅ PostgreSQL database criada
- ✅ Health check funcionando na porta 8080
- ✅ Variáveis de ambiente configuradas
- ⏳ **TELEGRAM_BOT_TOKEN** - Precisa configurar
- ⏳ **OPENAI_API_KEY** - Precisa configurar  
- ⏳ **PLUGGY_CLIENT_ID** - Opcional para testes
- ⏳ **PLUGGY_CLIENT_SECRET** - Opcional para testes

## 🎯 Próximos Passos

1. **Configurar tokens no Railway Dashboard**
2. **Testar bot no Telegram**
3. **Verificar logs e performance**
4. **Configurar monitoramento**

---

**Seu Bot IA Financeiro está pronto para funcionar! 🚀**  
Após configurar os tokens, o sistema estará 100% operacional.