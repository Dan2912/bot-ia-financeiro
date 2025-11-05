# 💰 Sistema Financeiro Manual - Bot IA Telegram

> **Documentação técnica completa do sistema de gestão financeira manual**

## 🎯 **Arquitetura do Sistema Manual**

### 🏦 **Sistema de Contas Predefinidas**

O sistema utiliza **8 contas bancárias** predefinidas para organização e controle:

#### **💚 Contas de Receita (Inter)**
```python
🟢 Inter PF  # Banco Inter Pessoa Física
            # - Salários, freelances, renda pessoal
            
🔵 Inter PJ  # Banco Inter Pessoa Jurídica  
            # - Faturamento empresarial, fornecedores
```

#### **💳 Contas de Despesa (Múltiplos Bancos)**
```python
🟣 C6 Bank PF      # C6 Bank Pessoa Física
🟪 C6 Bank PJ      # C6 Bank Pessoa Jurídica
🟡 Nubank PF       # Nubank Pessoa Física
🟠 Nubank PJ       # Nubank Pessoa Jurídica  
🔴 Santander PF    # Santander Pessoa Física
🔶 Santander PJ    # Santander Pessoa Jurídica
```

### 🗄️ **Schema do Banco de Dados (PostgreSQL)**

#### **Tabela `users`** - Sistema de Usuários
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Tabela `accounts`** - Contas Bancárias
```sql
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    account_name VARCHAR(100) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(50), -- 'PF' ou 'PJ'
    color VARCHAR(20),
    is_revenue_account BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Tabela `categories`** - Categorias de Transações
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(20),
    category_type VARCHAR(20), -- 'receita' ou 'despesa'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Tabela `transactions`** - Receitas e Despesas
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    account_id INTEGER REFERENCES accounts(id),
    category_id INTEGER REFERENCES categories(id),
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    transaction_type VARCHAR(20), -- 'receita' ou 'despesa'
    transaction_date DATE DEFAULT CURRENT_DATE,
    is_installment BOOLEAN DEFAULT FALSE,
    installment_number INTEGER,
    total_installments INTEGER,
    parent_transaction_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Tabela `installments`** - Controle de Parcelamento
```sql
CREATE TABLE installments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    parent_transaction_id INTEGER REFERENCES transactions(id),
    installment_number INTEGER NOT NULL,
    total_installments INTEGER NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    due_date DATE NOT NULL,
    is_paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Tabela `goals`** - Metas Financeiras
```sql
CREATE TABLE goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    target_amount DECIMAL(12,2) NOT NULL,
    current_amount DECIMAL(12,2) DEFAULT 0,
    goal_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Tabela `budgets`** - Orçamentos por Categoria
```sql
CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    amount DECIMAL(12,2) NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Tabela `user_sessions`** - Controle de Sessões
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    telegram_id BIGINT NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## 📱 **Comandos Disponíveis**

### **🔐 Autenticação (Obrigatória)**
```
/cadastro - Criar conta no sistema
/login - Fazer login
/logout - Sair do sistema
/perfil - Ver informações da conta
/trocar_senha - Alterar senha
```

### **💸 Gestão de Despesas**
```
/despesas - Menu principal de despesas
  ├── 💸 Nova Despesa - Cadastrar gasto
  ├── 📊 Relatório - Análise detalhada
  ├── 📂 Categorias - Gerenciar categorias
  └── 🔄 Parcelamentos - Ver parcelamentos ativos

/relatorio - Relatório detalhado dos últimos 30 dias
```

### **🎯 Gestão de Metas**
```
/metas - Menu principal de metas
  ├── 🎯 Nova Meta - Criar meta financeira
  ├── 📊 Progresso - Acompanhar evolução
  ├── 💰 Depositar - Adicionar valor à meta
  └── 📋 Todas as Metas - Listar todas

Tipos de Meta:
• 💰 Poupança
• 📈 Investimento
• 🏖️ Viagem
• 🏠 Compra
• 🆘 Emergência
• 💳 Quitação
```

### **📊 Relatórios e Análises**
```
/resumo - Resumo financeiro completo
  ├── 💸 Despesas do mês
  ├── 💰 Receitas do mês
  ├── 🎯 Progresso das metas
  ├── 🔔 Alertas não lidos
  └── ⚙️ Configurações

/analise - Análise IA personalizada (OpenAI)
```

## 🎯 **Tipos de Metas Financeiras**

### **💰 Poupança**
- Meta de valor a ser poupado
- Progresso manual ou automático
- Ideal para reservas gerais

### **🏖️ Viagem**
- Planejamento de viagens
- Associação com categoria "Lazer"
- Data limite configurável

### **🏠 Compra**
- Grandes aquisições
- Casa, carro, eletrodomésticos
- Acompanhamento de progresso

### **🆘 Emergência**
- Reserva de emergência
- Recomendação: 6x gastos mensais
- Alta prioridade

### **📈 Investimento**
- Metas de investimento
- Integração futura com APIs financeiras
- Acompanhamento de rentabilidade

### **💳 Quitação**
- Pagamento de dívidas
- Controle de parcelas
- Redução de juros

## 💸 **Sistema de Despesas**

### **Cadastro de Despesa**
1. **Título/Descrição**: Ex: "Almoço no restaurante"
2. **Valor**: Ex: R$ 25,50
3. **Categoria**: Seleção entre categorias existentes
4. **Opções Avançadas**:
   - 📅 Data personalizada
   - 🔄 Parcelamento
   - 🔁 Recorrência
   - 🏷️ Tags
   - 📝 Observações

### **Categorias Padrão**
**Despesas:**
- 🍽️ Alimentação
- 🚗 Transporte  
- 🏠 Moradia
- 🏥 Saúde
- 📚 Educação
- 🎮 Lazer
- 👕 Roupas
- 📦 Outros

**Receitas:**
- 💼 Salário
- 💻 Freelance
- 📈 Investimentos
- 💰 Outros

### **Sistema de Parcelamento**
- Criação automática de parcelas futuras
- Status individual por parcela
- Controle de pagamento
- Visualização do cronograma

## 📊 **Análises e Relatórios**

### **Relatório Mensal**
```
📊 Resumo do Mês:
• Total gasto: R$ 2.450,00
• Número de gastos: 45
• Saldo do mês: R$ 1.250,00
• Categoria top: 🍽️ Alimentação (35%)
```

### **Análise de Tendências**
- Comparação com mês anterior
- Identificação de padrões
- Alertas de gastos excessivos
- Sugestões de economia

### **Top Categorias**
- Ranking de gastos por categoria
- Percentual do total
- Evolução temporal
- Média por transação

## 🔔 **Sistema de Alertas**

### **Tipos de Alerta**
- **📈 goal_progress**: Progresso de meta
- **💸 budget_exceeded**: Orçamento ultrapassado
- **📅 bill_due**: Conta vencendo
- **🎉 goal_completed**: Meta atingida
- **⚠️ overspending**: Gasto excessivo

### **Configurações**
- Prioridade (1-5)
- Expiração automática
- Controle de leitura
- Integração com Telegram

## 🤖 **Integração com IA**

### **Análise Inteligente**
- **OpenAI GPT-4** para análises personalizadas
- Conselhos baseados no perfil de gastos
- Sugestões de economia específicas
- Alertas comportamentais

### **Prompt Personalizado**
```
Analise os dados financeiros:
• Receitas: R$ X
• Despesas: R$ Y  
• Categorias principais: Z
• Forneça insights práticos para o perfil brasileiro
```

## 📈 **Próximas Implementações**

### **1. Receitas Detalhadas**
- Sistema completo de receitas
- Fontes múltiplas de renda
- Previsões e projeções

### **2. Orçamentos Inteligentes**
- Orçamento automático baseado no histórico
- Alertas preventivos
- Ajustes dinâmicos

### **3. Integração Bancária**
- Sincronização automática via Pluggy
- Importação de extratos
- Categorização automática

### **4. Dashboard Web**
- Interface web complementar
- Gráficos interativos
- Exportação de relatórios

### **5. Investimentos**
- Carteira de investimentos
- Acompanhamento de rendimentos
- Rebalanceamento automático

## 🔒 **Segurança e Privacidade**

### **Proteção de Dados**
- Criptografia de dados sensíveis
- Logs de auditoria
- Backup automático
- Conformidade LGPD

### **Controle de Acesso**
- Autenticação obrigatória
- Sessões seguras
- Logs de atividade
- Bloqueio por tentativas

## 🚀 **Fluxo de Uso Completo**

### **1. Primeiro Acesso**
```
/start → /cadastro → /login
```

### **2. Configuração Inicial**
```
/despesas → Cadastrar primeiras despesas
/metas → Criar metas financeiras
/resumo → Visualizar situação inicial
```

### **3. Uso Diário**
```
💸 Cadastrar despesas conforme ocorrem
📊 Consultar progresso das metas
🔔 Verificar alertas
📈 Análises semanais/mensais
```

### **4. Gestão Avançada**
```
📂 Personalizar categorias
🎯 Ajustar metas
💡 Análises IA personalizadas
📊 Relatórios detalhados
```

O sistema está pronto para uso completo com funcionalidades de nível profissional! 🚀💰