# Bot Telegram IA Financeiro - Instruções do Copilot

Este projeto é um bot do Telegram desenvolvido em Go com funcionalidades de IA para gerenciamento financeiro pessoal integrado com Open Finance API do Banco Inter.

## Funcionalidades Principais

- **Integração Pluggy**: Conexão com +200 bancos brasileiros via API segura
- **Gestão Financeira**: Controle de metas, despesas e receitas
- **IA Avançada**: Análise de gastos e recomendações personalizadas com OpenAI
- **Interface Telegram**: Bot interativo com comandos intuitivos
- **Segurança Total**: Credenciais apenas no Railway, nunca no código

## Estrutura do Projeto

- `cmd/bot/`: Ponto de entrada da aplicação
- `internal/`: Código interno da aplicação
  - `bot/`: Lógica do bot Telegram
  - `openfinance/`: Integração com API Pluggy
  - `ai/`: Motor de IA para análises e recomendações
  - `database/`: Camada de persistência PostgreSQL
  - `models/`: Estruturas de dados
- `migrations/`: Scripts de banco de dados
- `SECURITY.md`: Guia de segurança de credenciais

## Tecnologias

- **Go 1.21+**: Linguagem principal
- **Telegram Bot API**: Interface de comunicação
- **PostgreSQL**: Banco de dados
- **Pluggy API**: Integração com +200 bancos brasileiros
- **OpenAI GPT-4**: IA para análises e recomendações
- **Railway**: Deploy e hospedagem
- **Docker**: Containerização