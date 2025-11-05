# Sistema de Gestão Financeira - Bot IA Telegram

## 💰 Funcionalidades Implementadas

### 🗄️ **Estrutura do Banco de Dados**

#### **Tabela `categories`**
- Categorias personalizadas para despesas e receitas
- Suporte a ícones e cores
- Categorias padrão criadas automaticamente

#### **Tabela `transactions`**
- Despesas e receitas com detalhamento completo
- Sistema de parcelamento automático
- Recorrência configurável
- Status de pagamento
- Tags e anotações

#### **Tabela `goals`**
- Metas financeiras com diferentes tipos
- Progresso automático e manual
- Notificações configuráveis
- Prioridades e datas limite

#### **Tabela `budgets`**
- Orçamentos mensais por categoria
- Alertas de limite atingido
- Comparação com gastos reais

#### **Tabela `alerts`**
- Sistema de notificações inteligentes
- Diferentes tipos de alerta
- Controle de leitura e expiração

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