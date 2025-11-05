# 🚀 Deploy do Bot IA Financeiro

## 📋 **Checklist Pré-Deploy**

### ✅ **Repositório Local Pronto**
- [x] Git inicializado
- [x] Primeiro commit realizado (dc808ab)
- [x] 19 arquivos commitados
- [x] .gitignore configurado para segurança

### 📚 **Documentação Completa**
- [x] README.md - Documentação principal
- [x] AUTHENTICATION.md - Sistema de login
- [x] FINANCIAL_SYSTEM.md - Gestão financeira
- [x] QUICK_GUIDE.md - Guia rápido
- [x] SECURITY.md - Guia de segurança
- [x] DATABASE.md - PostgreSQL Railway

## 🐙 **1. Criar Repositório no GitHub**

### **Método 1: Via Interface Web**
1. Acesse [GitHub.com](https://github.com)
2. Clique em "New Repository"
3. Nome sugerido: `bot-ia-financeiro`
4. Descrição: "🤖 Bot Telegram IA para gestão financeira com OpenAI e Pluggy"
5. **Marcar como Público** (ou Privado se preferir)
6. **NÃO** inicializar com README (já temos)
7. Clique "Create Repository"

### **Método 2: Via GitHub CLI** (se tiver instalado)
```bash
gh repo create bot-ia-financeiro --public --description "🤖 Bot IA Financeiro - Gestão completa com OpenAI GPT-4 e Pluggy API"
```

## 🔗 **2. Conectar Repositório Local ao GitHub**

Após criar no GitHub, execute:

```bash
# Adicionar remote origin (seu usuário GitHub)
git remote add origin https://github.com/Danillo2912/bot-ia-financeiro.git

# Renomear branch para main (padrão atual)  
git branch -M main

# Push inicial
git push -u origin main
```

## 🚄 **3. Deploy no Railway**

### **Passo 1: Criar Conta**
1. Acesse [Railway.app](https://railway.app)
2. Cadastre-se com GitHub (recomendado)
3. Confirme email

### **Passo 2: Novo Projeto**
1. Dashboard → "New Project"
2. "Deploy from GitHub repo"
3. Selecione `bot-ia-financeiro`
4. Railway detectará automaticamente o `railway.toml`

### **Passo 3: Adicionar PostgreSQL**
1. No dashboard do projeto → "Add Service"
2. "Database" → "PostgreSQL"
3. Railway criará automaticamente a `DATABASE_URL`

### **Passo 4: Configurar Variáveis**
No dashboard Railway → "Variables":

```env
# 🤖 Telegram Bot (obter em @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCDefghijklmnopqrstuvwxyz

# 🧠 OpenAI (https://platform.openai.com)
OPENAI_API_KEY=sk-proj-...

# 🏦 Pluggy (https://pluggy.ai) - Opcional
PLUGGY_CLIENT_ID=seu_client_id_aqui
PLUGGY_CLIENT_SECRET=seu_client_secret_aqui
PLUGGY_SANDBOX=true

# 📊 Health Check (Railway configura automaticamente)
PORT=8000
```

⚠️ **IMPORTANTE**: A `DATABASE_URL` é criada automaticamente pelo PostgreSQL Railway!

## 🎯 **4. Obter Credenciais Necessárias**

### **🤖 Token do Bot Telegram**
1. Abra o Telegram
2. Procure por `@BotFather`
3. Digite `/newbot`
4. Siga as instruções
5. Copie o token gerado

### **🧠 OpenAI API Key**
1. Acesse [platform.openai.com](https://platform.openai.com)
2. Cadastre-se/Faça login
3. Vá em "API Keys"
4. "Create new secret key"
5. Copie a chave (começa com `sk-`)

### **🏦 Pluggy (Opcional)**
1. Acesse [pluggy.ai](https://pluggy.ai)
2. Cadastre-se como desenvolvedor
3. Crie uma aplicação
4. Copie Client ID e Client Secret
5. Use `PLUGGY_SANDBOX=true` para testes

## 🚀 **5. Deploy Final**

### **Verificar Build**
1. Railway iniciará build automaticamente
2. Acompanhe logs em tempo real
3. Status deve ficar "Active" (verde)

### **Testar Bot**
1. No Telegram, procure seu bot
2. Digite `/start`
3. Teste `/cadastro` → `/login`
4. Cadastre uma despesa com `/nova_despesa`

### **Monitorar Saúde**
- URL de health check: `https://seu-app.railway.app/health`
- Deve retornar: `{"status": "healthy", "timestamp": "..."}`

## 🔧 **6. Configurações Avançadas**

### **Custom Domain** (Opcional)
1. Railway Dashboard → "Settings"  
2. "Domains" → "Custom Domain"
3. Configure seu domínio

### **Environment Variables**
```env
# Opcional: Configurações avançadas
PYTHONPATH=/app
TZ=America/Sao_Paulo
LOG_LEVEL=INFO
```

### **Scaling** (Se necessário)
- Railway escala automaticamente
- Monitore uso no dashboard
- Upgrade plano se necessário

## ✅ **7. Checklist Final**

### **Repositório GitHub**
- [ ] Repositório criado
- [ ] Código enviado (`git push`)
- [ ] README.md visível
- [ ] Issues/Discussions habilitados

### **Deploy Railway**
- [ ] Projeto criado e conectado ao GitHub  
- [ ] PostgreSQL adicionado
- [ ] Todas as variáveis configuradas
- [ ] Build executado com sucesso
- [ ] Status "Active" (verde)
- [ ] Health check funcionando

### **Bot Telegram**
- [ ] Bot criado no @BotFather
- [ ] Token configurado no Railway
- [ ] Bot responde ao `/start`
- [ ] Sistema de cadastro funcionando
- [ ] Comandos financeiros operacionais

## 🆘 **Troubleshooting**

### **Build Failed**
- Verifique `requirements.txt`
- Confirme Python version no `railway.toml`
- Veja logs detalhados no Railway

### **Bot Não Responde**
- Confirme `TELEGRAM_BOT_TOKEN` correto
- Verifique se aplicação está "Active"
- Teste health check endpoint

### **Erro de Banco**
- Confirme PostgreSQL adicionado
- `DATABASE_URL` deve ser automática
- Veja logs da aplicação

### **OpenAI Error**
- Verifique `OPENAI_API_KEY` válida
- Confirme créditos na conta OpenAI
- Teste com comando `/analise`

## 🎉 **Parabéns!**

Seu **Bot IA Financeiro** está:
- ✅ Versionado no GitHub
- ✅ Deployado no Railway  
- ✅ Conectado ao PostgreSQL
- ✅ Integrado com OpenAI
- ✅ Pronto para usuários!

**Próximos passos:**
1. Compartilhe o bot com amigos para testar
2. Monitore logs e performance
3. Implemente melhorias baseadas no uso
4. Configure alertas de monitoramento

---

🚀 **Seu sistema financeiro inteligente está no ar!** 🚀