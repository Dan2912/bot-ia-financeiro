# 🤖 Bot IA Financeiro - Sistema Manual Completo

> **Gestão financeira pessoal inteligente com sistema manual e IA integrada**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Railway](https://img.shields.io/badge/Deploy-Railway-purple.svg)](https://railway.app)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)](https://postgresql.org)
[![OpenAI](https://img.shields.io/badge/AI-OpenAI_GPT--4-green.svg)](https://openai.com)
[![Sistema](https://img.shields.io/badge/Status-Ativo-green.svg)](https://t.me/seu_bot)

## 🎯 **Visão Geral**

Bot do Telegram para controle financeiro pessoal com **sistema manual completo**, eliminando dependências de APIs bancárias externas. Focado na **experiência do usuário** com interfaces guiadas, dados reais controlados pelo próprio usuário e análises de IA personalizadas.

### **✨ Diferenciais**
- 🔄 **Sistema 100% Manual** - Controle total dos seus dados
- 🏦 **Contas Predefinidas** - Inter, C6, Nubank, Santander (PJ/PF)  
- 💳 **Parcelamento Inteligente** - Até 24x com cálculo automático
- 🤖 **IA Personalizada** - OpenAI GPT-4 para análises financeiras
- 📱 **UX Guiada** - Interface conversacional intuitiva
- 🔒 **Segurança Total** - Dados exclusivamente seus, sem integrações bancárias

## 🚀 **Funcionalidades Principais**

### � **Sistema de Receitas**
- ✅ **Categorias Inteligentes**: Salário, Fornecedor, Freelance, Investimentos
- ✅ **Contas de Receita**: Inter PF/PJ como padrão
- ✅ **Interface Guiada**: Processo passo-a-passo com validações
- ✅ **Recorrência**: Receitas fixas mensais automáticas

### 💸 **Sistema de Despesas**  
- ✅ **Parcelamento Avançado**: 1x até 24x com datas automáticas
- ✅ **Contas Diversificadas**: C6, Nubank, Santander (PJ/PF)
- ✅ **Categorização Automática**: 8 categorias padrão + personalizáveis
- ✅ **Controle de Vencimentos**: Gestão completa de datas

### 🏦 **Gestão de Contas**
- ✅ **8 Contas Predefinidas**: Configuradas e prontas para uso
- ✅ **Codificação por Cores**: Identificação visual rápida
- ✅ **Separação Inteligente**: Receitas (Inter) vs Despesas (outros bancos)
- ✅ **Flexibilidade Total**: Adicione suas próprias contas

### 🤖 **Inteligência Artificial**
- ✅ **Análises Personalizadas**: OpenAI GPT-4 para insights financeiros
- ✅ **Conselhos Inteligentes**: Baseados no seu perfil de gastos
- ✅ **Detecção de Padrões**: Identificação de tendências e anomalias
- ✅ **Projeções Futuras**: Previsões baseadas no histórico

## 📱 **Comandos Essenciais**

### 🔐 **Autenticação**
```bash
/start          # Iniciar o bot e ver menu principal
/cadastro       # Criar conta no sistema  
/login          # Login tradicional com senha
/entrar         # Login automático (recomendado)
/reset_senha    # Resetar senha para 123456
```

### � **Gestão Financeira**
```bash
/receitas       # Sistema completo de receitas
/gastos         # Sistema completo de despesas  
/contas         # Gerenciar contas bancárias
/demo          # Dados de exemplo para teste
```

### 📊 **Análises e Relatórios**
```bash
/resumo         # Visão geral da situação financeira
/analise        # Análise detalhada com IA
/relatorio      # Relatório mensal completo
/metas          # Gerenciar objetivos financeiros
```

### 🛠️ **Comandos de Debug** (para testes)
```bash
/debug_user     # Ver informações da conta
/emergency_login # Login de emergência
/simple_login   # Login simplificado
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
- 
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
