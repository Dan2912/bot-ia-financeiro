# 🤖 Bot IA Financeiro - Telegram

> **Sistema completo de gestão financeira pessoal com Inteligência Artificial**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Railway](https://img.shields.io/badge/Deploy-Railway-purple.svg)](https://railway.app)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)](https://postgresql.org)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI_GPT--4-green.svg)](https://openai.com)

## 🚀 **Funcionalidades Principais**

### 💸 **Gestão de Despesas**
- ✅ Cadastro rápido de gastos com categorização automática
- ✅ Sistema de parcelamento inteligente  
- ✅ 8 categorias padrão + personalizáveis
- ✅ Relatórios detalhados com análise de tendências

### 🎯 **Metas Financeiras**
- ✅ 6 tipos de meta (Poupança, Viagem, Compra, Emergência, Investimento, Quitação)
- ✅ Progresso automático e manual
- ✅ Sistema de prioridades e notificações
- ✅ Acompanhamento visual com percentuais

### 🏦 **Integração Bancária**
- ✅ Pluggy API - Conexão com +200 bancos brasileiros
- ✅ Open Finance certificado e seguro
- ✅ Sincronização automática de saldos e extratos
- ✅ Suporte a múltiplas contas bancárias

### 🤖 **Inteligência Artificial**
- ✅ OpenAI GPT-4 para análises personalizadas
- ✅ Conselhos de investimento baseados no perfil
- ✅ Alertas inteligentes de gastos excessivos
- ✅ Projeções e tendências financeiras

### 🔒 **Segurança Enterprise**
- ✅ Autenticação completa com hash bcrypt
- ✅ Controle de sessões e tentativas de login
- ✅ Conformidade com LGPD
- ✅ Credenciais exclusivamente no Railway (nunca no código)

## 📱 **Comandos Principais**

```bash
# 🔐 Autenticação
/cadastro      # Criar conta no sistema
/login         # Fazer login seguro
/perfil        # Ver informações da conta

# 💸 Gestão de Despesas  
/despesas      # Menu completo de gastos
/nova_despesa  # Cadastro rápido de despesa
/relatorio     # Análise detalhada (30 dias)

# 🎯 Metas Financeiras
/metas         # Gerenciar objetivos financeiros
/nova_meta     # Criar meta rapidamente

# 📊 Análises
/resumo        # Visão geral da situação
/analise       # Análise IA personalizada
```

## 🏗️ **Arquitetura Técnica**

### **Backend**
- **Python 3.11+** - Linguagem principal
- **python-telegram-bot 20.7** - Framework do bot
- **FastAPI** - API para health checks
- **AsyncPG** - Driver PostgreSQL assíncrono

### **Banco de Dados**
- **PostgreSQL** (Railway) - Banco principal
- **5 Tabelas principais**: users, categories, transactions, goals, budgets, alerts
- **Índices otimizados** para performance
- **Triggers automáticos** para auditoria

### **APIs Externas**
- **Pluggy API** - Integração com +200 bancos brasileiros
- **OpenAI GPT-4** - Análises e conselhos personalizados
- **Telegram Bot API** - Interface do usuário

### **Infraestrutura**
- **Railway** - Hosting e deploy automático
- **PostgreSQL Railway** - Banco gerenciado
- **Health Check** endpoint para monitoramento
- **Environment Variables** para todas as credenciais

## � **Estrutura do Projeto**

```
bot-ia-financeiro/
├── 📄 main.py                    # Aplicação principal do bot
├── 🤖 bot_commands.py           # Comandos de autenticação e financeiros
├── 🔐 user_auth.py              # Sistema de autenticação completo
├── 💰 financial_manager.py      # Gestão financeira e metas
├── 🏦 pluggy_client.py          # Cliente da API Pluggy
├── ⚡ health_server.py          # Health check para Railway
├── 📋 requirements.txt          # Dependências Python
├── 🐳 Dockerfile               # Container Docker
├── 🚄 railway.toml             # Configuração Railway
├── 📚 Documentação/
│   ├── AUTHENTICATION.md       # Sistema de autenticação
│   ├── FINANCIAL_SYSTEM.md     # Sistema financeiro
│   ├── QUICK_GUIDE.md          # Guia rápido de uso
│   ├── SECURITY.md             # Guia de segurança
│   └── DATABASE.md             # Configuração PostgreSQL
└── 🔒 .env.example             # Exemplo de variáveis
```

## 🚀 **Deploy Rápido**

### **1. Clonar o Repositório**
```bash
git clone https://github.com/Danillo2912/bot-ia-financeiro.git
cd bot-ia-financeiro
```

### **2. Configurar Railway**
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Fazer login
railway login

# Criar novo projeto
railway new

# Conectar PostgreSQL
railway add postgresql

# Deploy automático
railway up
```

### **3. Configurar Variáveis no Railway**
```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=seu_token_aqui

# OpenAI
OPENAI_API_KEY=sua_chave_aqui

# Pluggy (opcional)
PLUGGY_CLIENT_ID=seu_client_id
PLUGGY_CLIENT_SECRET=seu_client_secret

# PostgreSQL (automático)
DATABASE_URL=postgresql://... (gerado automaticamente)
```

## 🎯 **Como Usar**

### **1. Primeiro Acesso**
1. Inicie uma conversa com o bot no Telegram
2. `/start` - Ver opções disponíveis
3. `/cadastro` - Criar sua conta segura
4. `/login` - Fazer login no sistema

### **2. Cadastrar Primeira Despesa**
1. `/nova_despesa` - Atalho rápido
2. Digite o título: "Almoço restaurante"
3. Digite o valor: "25.50"
4. Selecione a categoria: 🍽️ Alimentação

### **3. Criar Primeira Meta**
1. `/nova_meta` - Atalho rápido  
2. Digite o título: "Viagem para Europa"
3. Digite o valor: "15000.00"
4. Selecione o tipo: 🏖️ Viagem

### **4. Acompanhar Progresso**
- `/resumo` - Situação geral atual
- `/relatorio` - Análise detalhada dos gastos
- `/metas` - Acompanhar evolução das metas

## 🔧 **Pré-requisitos para Deploy**

1. **Conta Railway** (https://railway.app)
2. **Token Bot Telegram** ([BotFather](https://t.me/botfather))
3. **API Key OpenAI** (https://platform.openai.com)
4. **Credenciais Pluggy** (https://pluggy.ai) - Opcional

## 📊 **Exemplos de Uso**

### **💸 Registro de Despesa**
```
Usuário: /nova_despesa
Bot: Digite o título da despesa:
Usuário: Supermercado Pão de Açúcar
Bot: Digite o valor:
Usuário: 158.90
Bot: Selecione a categoria: [🍽️ Alimentação] [🏠 Moradia] [🚗 Transporte]
Usuário: [Clica em 🍽️ Alimentação]
Bot: ✅ Despesa cadastrada com sucesso!
     📝 Supermercado Pão de Açúcar  
     💰 R$ 158,90
     📂 Alimentação
     📅 05/11/2025
```

### **🎯 Criação de Meta**
```
Usuário: /nova_meta
Bot: Digite o nome da sua meta:
Usuário: Reserva de Emergência
Bot: Digite o valor objetivo:
Usuário: 10000.00
Bot: Qual o tipo da meta: [💰 Poupança] [🆘 Emergência] [🏖️ Viagem]
Usuário: [Clica em 🆘 Emergência]
Bot: 🎉 Meta criada com sucesso!
     🆘 Reserva de Emergência
     💰 Objetivo: R$ 10.000,00
     📈 Progresso: 0%
```

## 🔒 **Segurança e Privacidade**

### **✅ O que é Seguro**
- Senhas criptografadas com bcrypt + salt
- Autenticação obrigatória para todos os comandos financeiros
- Dados armazenados exclusivamente no PostgreSQL Railway
- Credenciais apenas em variáveis de ambiente
- Conformidade total com LGPD

### **⚠️ Nunca Commitamos**
- Tokens de API
- Senhas de banco de dados
- Chaves privadas
- Dados pessoais dos usuários
- Logs com informações sensíveis

## 🚀 **Próximas Funcionalidades**

- 📱 **App Mobile Nativo** - Interface ainda mais intuitiva
- 🔄 **Sync Automática** - Importação automática de extratos bancários
- 📊 **Dashboard Web** - Visualização avançada com gráficos
- 💎 **Versão Premium** - Recursos avançados e suporte prioritário
- 🌍 **Multi-idiomas** - Suporte a outros países
- 🤖 **IA Avançada** - Previsões e análises preditivas

## 📞 **Suporte e Contribuição**

### **🐛 Reportar Bugs**
- Abra uma [Issue](https://github.com/Danillo2912/bot-ia-financeiro/issues)
- Descreva o problema detalhadamente
- Inclua prints se possível

### **💡 Sugestões**
- Use [Discussions](https://github.com/Danillo2912/bot-ia-financeiro/discussions)
- Compartilhe ideias de melhorias
- Vote nas sugestões da comunidade

### **🤝 Contribuir**
1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

**Desenvolvido com ❤️ para revolucionar sua gestão financeira!**

*"O controle financeiro é o primeiro passo para a liberdade financeira."*
```bash
# Fazer commit das alterações
git add .
git commit -m "Initial bot setup"
git push origin main
```

### 2. Configurar Railway
1. Acesse [Railway.app](https://railway.app)
2. Conecte seu repositório GitHub
3. Adicione PostgreSQL como serviço
4. Configure as variáveis de ambiente

### 3. Variáveis de Ambiente Obrigatórias
```env
# Bot Telegram (obter no @BotFather)
TELEGRAM_BOT_TOKEN=seu_token_aqui

# Banco de Dados (Railway configura automaticamente)
DATABASE_URL=postgresql://...

# Pluggy Open Finance (https://pluggy.ai)
PLUGGY_CLIENT_ID=seu_client_id
PLUGGY_CLIENT_SECRET=seu_client_secret
PLUGGY_SANDBOX=true

# OpenAI (https://platform.openai.com)
OPENAI_API_KEY=sk-...

# Opcional: Google Gemini
GEMINI_API_KEY=...
```

⚠️ **IMPORTANTE:** Configure essas variáveis **APENAS no Railway**, nunca no código!

### 4. Deploy Automático
O Railway detecta automaticamente o `railway.toml` e faz o deploy.

## 📱 Como Usar o Bot

### Comandos Básicos
- `/start` - Iniciar o bot e ver boas-vindas
- `/menu` - Menu principal com botões interativos
- `/saldo` - Consultar saldo das contas
- `/extrato` - Ver extrato dos últimos 30 dias
- `/cartao` - Informações do cartão de crédito

### Comandos Avançados
- `/metas` - Ver e gerenciar metas financeiras
- `/gastos` - Análise inteligente de gastos
- `/investir` - Conselhos de investimento personalizados
- `/orcamento` - Controle de orçamento por categoria
- `/analise` - Análise financeira completa com IA

### Comandos de Entrada de Dados
- `/addgasto [valor] [categoria] [descrição]` - Adicionar gasto manual
- `/addreceita [valor] [descrição]` - Adicionar receita
- `/addmeta [nome] [valor]` - Criar nova meta

## 🔐 Segurança e Privacidade

- ✅ Todas as comunicações são criptografadas
- ✅ Dados bancários acessados apenas via Open Finance oficial
- ✅ Informações sensíveis não são armazenadas em texto plano
- ✅ Conformidade com LGPD e regulamentações bancárias
- ✅ Auditoria completa de todas as transações

## 🤖 Funcionalidades de IA

### Análise de Gastos
- Identificação de padrões de consumo
- Detecção de gastos anômalos
- Sugestões de economia por categoria
- Alertas de orçamento

### Conselhos de Investimento
- Análise de perfil de risco
- Recomendações de produtos financeiros brasileiros
- Estratégias de diversificação
- Acompanhamento de metas de investimento

### Planejamento Financeiro
- Projeções de fluxo de caixa
- Simulações de cenários
- Otimização de orçamento
- Conselhos personalizados

## 📊 Integrações

### Pluggy Open Finance
- Integração com +200 bancos e fintechs brasileiras
- Contas corrente, poupança e investimentos
- Cartões de crédito de qualquer banco
- Histórico completo de transações
- Dados sempre atualizados e seguros

### APIs de IA
- **OpenAI GPT-4** - Análises e conselhos
- **Google Gemini** - Backup de IA
- Modelos especializados em finanças

## 🔧 Configuração Avançada

### Certificados Open Finance
Para produção, você precisará de certificados válidos do Banco Inter:
```bash
mkdir certs
# Coloque seus certificados em:
# certs/inter_cert.pem
# certs/inter_key.pem
```

### Personalização de IA
Edite `internal/ai/service.go` para ajustar prompts e comportamento da IA.

### Banco de Dados
O esquema é criado automaticamente. Para customizar, edite os arquivos em `migrations/`.

## 📈 Monitoramento

### Logs
```bash
# Ver logs no Railway
railway logs

# Logs locais
go run cmd/bot/main.go
```

### Métricas
- Health check em `/health`
- Monitoramento de uptime
- Alertas de erro automáticos

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Faça push para a branch
5. Abra um Pull Request

## 📞 Suporte

- **GitHub Issues:** [Reportar bugs](https://github.com/Danillo2912/go_control/issues)
- **Telegram:** @Danillo2912
- **Email:** danillo2912@gmail.com

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🎯 Roadmap

### Próximas Funcionalidades
- [ ] Integração com mais bancos
- [ ] Notificações push personalizadas  
- [ ] Dashboard web complementar
- [ ] Exportação de relatórios
- [ ] API pública para desenvolvedores
- [ ] Integração com carteiras de investimento
- [ ] Alertas de vencimento de contas
- [ ] Categorização automática de gastos

### Melhorias de IA
- [ ] Modelo próprio treinado em dados financeiros brasileiros
- [ ] Previsão de gastos mensais
- [ ] Detecção de fraudes
- [ ] Recomendações proativas

---

**Desenvolvido com ❤️ por [@Danillo2912](https://github.com/Danillo2912)**

*Bot inteligente para suas finanças pessoais no Brasil* 🇧🇷