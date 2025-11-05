# 🔧 Guia de Instalação - Windows

Este guia te ajudará a instalar e configurar tudo que é necessário para executar o Bot Telegram IA Financeiro no Windows.

## 📋 Pré-requisitos

### 1. Instalar Python

1. **Download do Python:**
   - Acesse https://python.org/downloads/
   - Baixe Python 3.11+ para Windows (ex: `python-3.11.x-amd64.exe`)

2. **Instalação:**
   - Execute o arquivo `.exe` baixado
   - ⚠️ **IMPORTANTE:** Marque "Add Python to PATH"
   - Siga o assistente de instalação

3. **Verificar Instalação:**
   ```powershell
   # Abra um novo PowerShell e teste:
   python --version
   # Deve mostrar algo como: Python 3.11.x
   
   pip --version
   # Deve mostrar a versão do pip
   ```

### 2. Instalar Visual Studio Code (Recomendado)

1. **Download:** https://code.visualstudio.com/
2. **Instale a extensão Python:**
   - Abra VS Code
   - Vá em Extensions (Ctrl+Shift+X)
   - Procure por "Python" (da Microsoft)
   - Instale

### 3. Instalar Git (se não tiver)

1. **Download:** https://git-scm.com/download/win
2. **Instalação:** Execute o instalador com as opções padrão
3. **Verificar:** `git --version`

### 4. Criar Bot no Telegram

1. **Encontre o BotFather:**
   - Abra o Telegram
   - Procure por `@BotFather`
   - Inicie uma conversa

2. **Criar o Bot:**
   ```
   /newbot
   # Siga as instruções:
   # - Nome do bot (ex: "Meu Bot Financeiro")  
   # - Username (ex: "meubot_financeiro_bot")
   ```

3. **Salvar o Token:**
   - O BotFather enviará um token como: `123456789:ABCdef...`
   - **GUARDE ESTE TOKEN!** Você precisará dele depois

## 🚀 Executar o Projeto

### 1. Clone o Repositório
```powershell
# Navegue para onde quer o projeto (ex: Desktop)
cd C:\Users\SeuUsuario\Desktop

# Clone o repositório  
git clone https://github.com/Danillo2912/go_control.git
cd go_control
```

### 2. Configurar Variáveis de Ambiente
```powershell
# Copie o arquivo de exemplo
copy .env.example .env

# Edite o arquivo .env no Bloco de Notas ou VS Code
notepad .env
```

**⚠️ IMPORTANTE:** Configure apenas para teste local. **NUNCA commite este arquivo!**

```env
# ⚠️  APENAS TESTE LOCAL - NÃO COMMITAR!

# Token do seu bot (obtido do BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdef...

# OpenAI (obtenha em: https://platform.openai.com/)
OPENAI_API_KEY=sk-...

# Pluggy (https://pluggy.ai) - USE SANDBOX PARA TESTE
PLUGGY_CLIENT_ID=test_client_id  
PLUGGY_CLIENT_SECRET=test_secret
PLUGGY_SANDBOX=true

# Banco de dados (para teste local - PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_NAME=go_control
DB_SSLMODE=disable
```

**Para produção, configure tudo no Railway!** Veja `SECURITY.md` e `DATABASE.md` para detalhes.

### 3. Banco de Dados

**✅ Recomendado: PostgreSQL do Railway**
- Não precisa instalar nada local
- Railway fornece banco automático
- Zero configuração necessária

**❓ Opcional: PostgreSQL Local (só para desenvolvimento)**
```powershell
# Se quiser testar localmente (não obrigatório):
docker run --name postgres -e POSTGRES_PASSWORD=123456 -p 5432:5432 -d postgres:15
```

**💡 Dica:** Use Railway para produção, é muito mais fácil!

### 4. Executar o Bot
```powershell
# Criar ambiente virtual (recomendado)
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar o bot
python main.py
```

Se tudo estiver correto, você verá:
```
🌐 Servidor de health check iniciado na porta 8000
🤖 Bot Telegram IA Financeiro iniciado!
```

### 5. Testar o Bot

1. Abra o Telegram
2. Procure pelo nome do seu bot (ex: `@meubot_financeiro_bot`)
3. Envie `/start`
4. Se funcionar, parabéns! 🎉

## 🌐 Deploy no Railway (Recomendado)

Para um bot em produção, use o Railway:

### 1. Criar Conta
- Acesse https://railway.app
- Faça login com GitHub

### 2. Subir Código
```powershell
# Se ainda não criou repositório:
git init
git add .
git commit -m "Bot financeiro inicial"

# Crie um repositório no GitHub e suba:
git remote add origin https://github.com/Danillo2912/go_control.git
git branch -M main
git push -u origin main
```

### 3. Configurar Railway
1. No Railway, clique "Deploy from GitHub repo"
2. Selecione seu repositório
3. Adicione PostgreSQL: "Add Service" → "Database" → "PostgreSQL"
4. **Adicionar PostgreSQL:**
   - Clique "New Service" → "Database" → "PostgreSQL"
   - Railway criará automaticamente o banco
   - A `DATABASE_URL` será gerada sozinha

5. **⚠️ PASSO CRÍTICO:** Configure as variáveis de ambiente na aba "Variables":
   - `TELEGRAM_BOT_TOKEN` (do BotFather)
   - `OPENAI_API_KEY` (da OpenAI)
   - `PLUGGY_CLIENT_ID` (da Pluggy)
   - `PLUGGY_CLIENT_SECRET` (da Pluggy)
   - `PLUGGY_SANDBOX=true` (para início)
   - ✅ `DATABASE_URL` já estará lá automaticamente!

### 4. Deploy Automático
O Railway detecta o `railway.toml` e faz deploy automaticamente!

**🛡️ LEMBRE-SE:** Credenciais ficam APENAS no Railway, nunca no código!

## 🔐 Configurar Pluggy Open Finance

Para integração real com bancos via Pluggy:

1. **Criar Conta Pluggy:**
   - Acesse https://pluggy.ai
   - Crie uma conta de desenvolvedor
   - Obtenha suas credenciais da API

2. **Configurar no Railway (NUNCA no código!):**
   - Vá para seu projeto no Railway
   - Aba "Variables"
   - Adicione:
     ```
     PLUGGY_CLIENT_ID=sua_client_id
     PLUGGY_CLIENT_SECRET=seu_client_secret
     PLUGGY_SANDBOX=true
     ```

3. **Vantagens do Pluggy:**
   - ✅ +200 instituições financeiras
   - ✅ Todos os grandes bancos (Itaú, Bradesco, Santander, etc.)
   - ✅ Fintechs (Nubank, Inter, C6, etc.)
   - ✅ Mais seguro e fácil que Open Finance direto
   - ✅ Não precisa de certificados

## ⚠️ Solução de Problemas

### Erro: "go: command not found"
- Reinstale o Go seguindo os passos acima
- Verifique variáveis de ambiente
- Reinicie o PowerShell

### Erro: "Cannot connect to database"
- Verifique se PostgreSQL está rodando
- Confirme dados no arquivo `.env`
- Para Railway, use a `DATABASE_URL` fornecida

### Bot não responde
- Verifique se o token está correto
- Teste se o bot está online no BotFather
- Veja os logs no console

### Erro de OpenAI
- Verifique se a API key está correta
- Confirme se tem créditos na conta OpenAI
- Teste a chave em: https://platform.openai.com/playground

## 📞 Suporte

Se precisar de ajuda:
- **GitHub Issues:** https://github.com/Danillo2912/go_control/issues
- **Telegram:** @Danillo2912

---

**Boa sorte com seu bot financeiro! 🚀**