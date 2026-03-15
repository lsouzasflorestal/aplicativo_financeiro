# Planejador Financeiro

Aplicativo web para controle financeiro pessoal, desenvolvido com Streamlit e Supabase.

## Funcionalidades

- Dashboard com visão geral das finanças
- Lançamento de receitas, despesas e investimentos
- Categorias personalizáveis
- Bancos e contas
- Relatórios mensais e anuais
- Gráficos interativos

## Configuração

### 1. Supabase

1. Crie um projeto no [Supabase](https://supabase.com).
2. No painel do Supabase, vá para **SQL Editor** e execute os comandos para criar as tabelas (veja `config_template.py` para referência).

### 2. Configuração Local

1. Clone o repositório.
2. Instale as dependências: `pip install -r requirements.txt`
3. Copie `config_template.py` para `config.py` e preencha com suas credenciais do Supabase.
4. Para usuários, edite `users.py` (não commitado por segurança).
5. Execute: `streamlit run main.py`

### 3. Deploy no GitHub/Streamlit Cloud

1. Faça push do código para um repositório GitHub (arquivos sensíveis estão no `.gitignore`).
2. No Streamlit Cloud, conecte o repositório.
3. Configure as variáveis de ambiente:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY` (opcional)

## Arquivos Sensíveis

Os seguintes arquivos não são commitados por segurança:
- `config.py` (credenciais Supabase)
- `users.py` (dados de usuários)
- `security.toml` (configurações de segurança)

Use `config_template.py` como base para `config.py`.

## Tecnologias

- **Frontend**: Streamlit
- **Backend**: Supabase (PostgreSQL)
- **Gráficos**: Plotly
AS $$
BEGIN
  EXECUTE query;
END;
$$;
```

**Atenção:** Esta função permite execução arbitrária de SQL. Use apenas em desenvolvimento ou com cuidado em produção.

## Usuários

Os usuários são definidos no arquivo `users.py`. Adicione usuários lá no dicionário `USERS`.

Formato:
```python
USERS = {
    "username": hash_password("password"),
    # ...
}
```

## Estrutura de Dados

Cada usuário tem suas próprias tabelas prefixadas com `user_{username}_`:

- `user_{username}_categorias`
- `user_{username}_bancos`
- `user_{username}_transacoes`

## Executando

Execute o aplicativo com:
```bash
streamlit run main.py
```

## Notas

- As funções de relatório (`get_saldo_total`, etc.) podem precisar de ajustes para funcionar com Supabase. Considere criar views ou funções RPC no Supabase para cálculos complexos.
- Certifique-se de que as políticas RLS (Row Level Security) estão configuradas adequadamente no Supabase se necessário.