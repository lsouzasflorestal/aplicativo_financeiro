try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Aviso: Módulo supabase não encontrado. Instale com: pip install supabase")

import os
from datetime import datetime
from pathlib import Path
from calendar import monthrange
import hashlib

from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

from functools import lru_cache

# ==== Autenticação (hardcoded) ====

def authenticate_user(username, password):
    """Autentica um usuário com senha hashada."""
    # Usuários cadastrados (adicione novos usuários aqui editando o código)
    # Para adicionar: "novo_user": hashlib.sha256("senha".encode()).hexdigest()
    users = {
        "admin": hashlib.sha256("admin123".encode()).hexdigest(),
        # Exemplo: "user2": hashlib.sha256("password2".encode()).hexdigest(),
    }
    if username in users and users[username] == hashlib.sha256(password.encode()).hexdigest():
        return username
    return None

# ==== Cliente Supabase (singleton para evitar reconexões) ====
@lru_cache(maxsize=1)
def _create_supabase_client():
    if not SUPABASE_AVAILABLE:
        raise Exception("Supabase não disponível")
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

@lru_cache(maxsize=1)
def _create_supabase_admin_client():
    if not SUPABASE_AVAILABLE:
        raise Exception("Supabase não disponível")
    if SUPABASE_SERVICE_ROLE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _create_supabase_client()

def get_supabase():
    return _create_supabase_client()

def get_supabase_admin():
    return _create_supabase_admin_client()

# Cache helpers (invalidate after writes)
_cached_funcs = []

def _cache(func):
    cached = lru_cache(maxsize=128)(func)
    _cached_funcs.append(cached)
    return cached

def _clear_caches():
    for fn in _cached_funcs:
        fn.cache_clear()

def hash_password(password):
    """Gera um hash da senha"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_table_prefix(username):
    """Retorna o prefixo das tabelas do usuário"""
    return ''

def create_user_tables(username):
    """Cria as tabelas do usuário se não existirem e insere categorias padrão"""
    if not SUPABASE_AVAILABLE:
        print("Erro: Supabase não está disponível. Instale com: pip install supabase")
        return
    
    # Assumir que as tabelas já existem (devem ser criadas manualmente no Supabase)
    # Inserir categorias padrão se não existirem para o usuário
    try:
        supabase = get_supabase()
        response = supabase.table('categorias').select('id').eq('user_id', username).limit(1).execute()
        if not response.data:
            default_categories = [
                ("Moradia", "Despesa"), ("Comunicação", "Despesa"), ("Alimentação", "Despesa"),
                ("Transporte", "Despesa"), ("Saúde", "Despesa"), ("Pessoais", "Despesa"),
                ("Educação", "Despesa"), ("Lazer", "Despesa"), ("Serv. Financeiros", "Despesa"),
                ("Empresa", "Despesa"), ("Dependentes", "Despesa"), ("Diversos", "Despesa"),
                ("Salário", "Receita"), ("Freelance", "Receita"), ("Investimentos", "Receita"),
                ("Ações", "Investimento"), ("Criptomoedas", "Investimento"),
                ("Imóveis", "Investimento"), ("Renda Fixa", "Investimento")
            ]
            for nome, tipo in default_categories:
                try:
                    supabase.table('categorias').insert({'nome': nome, 'tipo': tipo, 'user_id': username}).execute()
                except:
                    pass
    except:
        pass

def init_database(username):
    """Inicializa o banco de dados do usuário"""
    create_user_tables(username)

# Funções CRUD para Categorias
def _check_supabase():
    """Verifica se Supabase está disponível"""
    if not SUPABASE_AVAILABLE:
        raise Exception("Supabase não está disponível. Instale com: pip install supabase")

# Funções CRUD para Categorias
@_cache
def get_categorias(username, tipo=None):
    _check_supabase()
    """Obtém todas as categorias ou filtrado por tipo"""
    supabase = get_supabase()
    if tipo:
        response = supabase.table('categorias').select('*').eq('user_id', username).eq('tipo', tipo).order('nome').execute()
    else:
        response = supabase.table('categorias').select('*').eq('user_id', username).order('nome').execute()
    return response.data

def add_categoria(username, nome, tipo):
    _check_supabase()
    """Adiciona uma nova categoria"""
    try:
        supabase = get_supabase()
        supabase.table('categorias').insert({'nome': nome, 'tipo': tipo, 'user_id': username}).execute()
        _clear_caches()
        return True
    except:
        return False

def delete_categoria(username, categoria_id):
    _check_supabase()
    """Deleta uma categoria"""
    supabase = get_supabase()
    supabase.table('categorias').delete().eq('id', categoria_id).eq('user_id', username).execute()
    _clear_caches()

# Funções CRUD para Bancos
@_cache
def get_bancos(username):
    _check_supabase()
    """Obtém todos os bancos"""
    supabase = get_supabase()
    response = supabase.table('bancos').select('*').eq('user_id', username).order('nome').execute()
    return response.data

def add_banco(username, nome, saldo_inicial=0):
    _check_supabase()
    """Adiciona um novo banco"""
    try:
        supabase = get_supabase()
        supabase.table('bancos').insert({'nome': nome, 'saldo_inicial': saldo_inicial, 'user_id': username}).execute()
        _clear_caches()
        return True
    except:
        return False

def delete_banco(username, banco_id):
    _check_supabase()
    """Deleta um banco"""
    supabase = get_supabase()
    supabase.table('bancos').delete().eq('id', banco_id).eq('user_id', username).execute()
    _clear_caches()

# Funções CRUD para Transações
@_cache
def get_transacoes(username, tipo=None, mes=None, ano=None):
    _check_supabase()
    """Obtém transações com filtros opcionais"""
    supabase = get_supabase()
    query = supabase.table('transacoes').select('*').eq('user_id', username)

    if tipo:
        query = query.eq('tipo', tipo)

    if mes and ano:
        start_date = f'{ano}-{mes:02d}-01'
        end_date = f'{ano}-{mes:02d}-{monthrange(ano, mes)[1]}'
        query = query.gte('data', start_date).lte('data', end_date)

    response = query.order('data', desc=True).execute()
    transacoes = response.data
    
    # Buscar nomes de categoria e banco (usa cache para não sofrer múltiplos hits)
    categoria_dict = {c['id']: c['nome'] for c in get_categorias(username)}
    banco_dict = {b['id']: b['nome'] for b in get_bancos(username)}

    for t in transacoes:
        t['categoria_nome'] = categoria_dict.get(t['categoria_id'], 'Desconhecida')
        t['banco_nome'] = banco_dict.get(t['banco_id'], 'Desconhecido')

    return transacoes

def add_transacao(username, tipo, categoria_id, banco_id, valor, descricao, data):
    _check_supabase()
    """Adiciona uma nova transação"""
    supabase = get_supabase()
    response = supabase.table('transacoes').insert({
        'user_id': username,
        'tipo': tipo,
        'categoria_id': categoria_id,
        'banco_id': banco_id,
        'valor': valor,
        'descricao': descricao,
        'data': data
    }).execute()
    _clear_caches()
    return response.data[0]['id']

def update_transacao(username, transacao_id, tipo, categoria_id, banco_id, valor, descricao, data):
    _check_supabase()
    """Atualiza uma transação"""
    supabase = get_supabase()
    supabase.table('transacoes').update({
        'tipo': tipo,
        'categoria_id': categoria_id,
        'banco_id': banco_id,
        'valor': valor,
        'descricao': descricao,
        'data': data
    }).eq('id', transacao_id).eq('user_id', username).execute()
    _clear_caches()


def delete_transacao(username, transacao_id):
    _check_supabase()
    """Deleta uma transação"""
    supabase = get_supabase()
    supabase.table('transacoes').delete().eq('id', transacao_id).eq('user_id', username).execute()
    _clear_caches()

def get_transacao_by_id(username, transacao_id):
    _check_supabase()
    """Obtém uma transação pelo ID com informações de categoria e banco"""
    supabase = get_supabase()
    response = supabase.table('transacoes').select('*').eq('id', transacao_id).eq('user_id', username).execute()
    if response.data:
        t = response.data[0]
        categoria_dict = {c['id']: c['nome'] for c in get_categorias(username)}
        banco_dict = {b['id']: b['nome'] for b in get_bancos(username)}
        t['categoria_nome'] = categoria_dict.get(t['categoria_id'], 'Desconhecida')
        t['banco_nome'] = banco_dict.get(t['banco_id'], 'Desconhecido')
        return t
    return None

# Funções para relatórios
def get_saldo_total(username):
    _check_supabase()
    """Calcula o saldo total de todos os bancos (incluindo saldos iniciais)"""
    # Soma saldos iniciais dos bancos
    bancos = get_bancos(username)
    saldo_inicial_total = sum(b['saldo_inicial'] for b in bancos)
    
    # Soma efeitos das transações
    transacoes = get_transacoes(username)
    saldo_transacoes = 0
    for t in transacoes:
        if t['tipo'] in ['Receita', 'Investimento']:
            saldo_transacoes += t['valor']
        elif t['tipo'] == 'Despesa':
            saldo_transacoes -= t['valor']
    
    return saldo_inicial_total + saldo_transacoes

def get_resumo_mes(username, mes, ano):
    _check_supabase()
    """Obtém resumo do mês"""
    transacoes = get_transacoes(username, mes=mes, ano=ano)
    resumo = {}
    for t in transacoes:
        tipo = t['tipo']
        valor = t['valor']
        resumo[tipo] = resumo.get(tipo, 0) + valor
    return resumo

def get_gastos_por_categoria(username, mes, ano):
    _check_supabase()
    """Obtém gastos por categoria no mês"""
    transacoes = get_transacoes(username, tipo='Despesa', mes=mes, ano=ano)
    gastos = {}
    for t in transacoes:
        nome = t['categoria_nome']
        valor = t['valor']
        gastos[nome] = gastos.get(nome, 0) + valor
    return [{'nome': k, 'total': v} for k, v in sorted(gastos.items(), key=lambda x: x[1], reverse=True)]

def get_receitas_por_categoria(username, mes, ano):
    _check_supabase()
    """Obtém receitas por categoria no mês"""
    transacoes = get_transacoes(username, tipo='Receita', mes=mes, ano=ano)
    receitas = {}
    for t in transacoes:
        nome = t['categoria_nome']
        valor = t['valor']
        receitas[nome] = receitas.get(nome, 0) + valor
    return [{'nome': k, 'total': v} for k, v in sorted(receitas.items(), key=lambda x: x[1], reverse=True)]