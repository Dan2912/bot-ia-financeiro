# 🗄️ Configuração do Banco PostgreSQL no Railway

## 📋 Como Configurar o Banco no Railway

### 1. Adicionar PostgreSQL ao Projeto

1. **Acesse seu projeto no Railway:**
   - Vá para https://railway.app
   - Entre no seu projeto

2. **Adicionar PostgreSQL:**
   - Clique em "New Service"
   - Selecione "Database"
   - Escolha "PostgreSQL"
   - Railway criará automaticamente

### 2. Variáveis Automáticas

O Railway gera automaticamente estas variáveis:
```bash
DATABASE_URL=postgresql://postgres:senha@host.railway.app:5432/railway
PGHOST=host.railway.app
PGPORT=5432
PGDATABASE=railway
PGUSER=postgres
PGPASSWORD=senha_aleatoria
```

### 3. Conexão Automática

O bot usa apenas a `DATABASE_URL` que o Railway fornece automaticamente. Não precisa configurar nada manualmente!

## 🚀 Vantagens do PostgreSQL Railway

### ✅ **Benefícios:**
- **Setup automático** - Zero configuração
- **Backups automáticos** - Dados sempre seguros
- **Escalabilidade** - Cresce conforme necessário
- **Monitoramento** - Métricas em tempo real
- **SSL/TLS** - Conexões seguras
- **Replicação** - Alta disponibilidade

### 📊 **Recursos Inclusos:**
- **Conexões simultâneas:** Até 100
- **Armazenamento:** Generoso para bots
- **RAM:** Suficiente para análises IA
- **CPU:** Optimizada para PostgreSQL
- **Rede:** Baixa latência global

## 🔧 Configuração no Código

### Schema Otimizado
O bot cria automaticamente:
- ✅ **Tabelas** com índices otimizados
- ✅ **Constraints** para integridade
- ✅ **JSONB** para dados flexíveis
- ✅ **Timestamps** automáticos
- ✅ **Foreign keys** com cascata

### Pool de Conexões
```python
# Configuração otimizada para Railway
self.db_pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=1,      # Mínimo de conexões
    max_size=10,     # Máximo para Railway
    command_timeout=60  # Timeout adequado
)
```

## 📈 Monitoramento

### 1. Dashboard Railway
- **CPU e RAM:** Uso em tempo real
- **Conexões ativas:** Quantas em uso
- **Queries:** Performance das consultas
- **Storage:** Espaço utilizado

### 2. Logs do Banco
```bash
# Ver logs no Railway
railway logs --service=postgresql
```

### 3. Métricas do Bot
O bot loga automaticamente:
- ✅ Conexão estabelecida
- ✅ Schema criado/atualizado
- ✅ Número de usuários ativos
- ❌ Erros de conexão

## 🛠️ Comandos Úteis

### Conectar Diretamente (se necessário)
```bash
# Via Railway CLI
railway connect postgresql

# Via psql (se tiver instalado)
psql $DATABASE_URL
```

### Backup Manual
```bash
# Fazer backup
pg_dump $DATABASE_URL > backup.sql

# Restaurar backup
psql $DATABASE_URL < backup.sql
```

## 🔍 Troubleshooting

### Erro: "DATABASE_URL não configurada"
- Verifique se adicionou PostgreSQL no Railway
- Confirme se o serviço está rodando
- Redeploy o bot se necessário

### Erro: "Connection timeout"
- Verifique a conectividade
- Railway pode estar fazendo manutenção
- Tente novamente em alguns minutos

### Erro: "Too many connections"
- Reduza `max_size` no pool
- Verifique se há loops infinitos no código
- Monitore no dashboard Railway

## 📋 Checklist de Setup

- [ ] PostgreSQL adicionado no Railway
- [ ] `DATABASE_URL` aparece nas variáveis
- [ ] Bot faz conexão sem erros
- [ ] Tabelas são criadas automaticamente
- [ ] Dados persistem entre restarts
- [ ] Logs mostram conexão bem-sucedida

## 🎯 Exemplo de Uso

```python
# O bot automaticamente:
async def example():
    # 1. Conecta ao PostgreSQL
    await bot.init_database()
    
    # 2. Cria schema se não existir
    # (Tabelas, índices, constraints)
    
    # 3. Pool de conexões pronto
    async with bot.db_pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users")
        print(f"Usuários cadastrados: {len(users)}")
```

## 🚀 Próximos Passos

1. **Deploy no Railway** - Banco será criado automaticamente
2. **Testar conexão** - Verifique nos logs
3. **Monitorar performance** - Use dashboard Railway
4. **Fazer backup** - Configure política de backup
5. **Otimizar queries** - Monitore queries lentas

**Railway PostgreSQL é a melhor opção para seu bot! 🗄️✨**