import streamlit as st
from datetime import datetime
import locale

# Tentar definir locale para português
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    pass

def formatar_moeda(valor):
    """Formata um valor como moeda brasileira"""
    return f"R$ {valor:,.2f}".replace(',', '#').replace('.', ',').replace('#', '.')

def formatar_percentual(valor, total):
    """Calcula e formata percentual"""
    if total == 0:
        return "0%"
    return f"{(valor / total * 100):.1f}%"

def get_mes_atual():
    """Retorna o mês atual"""
    return datetime.now().month

def get_ano_atual():
    """Retorna o ano atual"""
    return datetime.now().year

def get_nomes_meses():
    """Retorna nomes dos meses em português"""
    return {
        1: "Janeiro", 2: "Fevereiro", 3: "Março",
        4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro",
        10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }

def inicializar_session_state():
    """Inicializa as variáveis de sessão do Streamlit"""
    if 'page' not in st.session_state:
        st.session_state.page = 'Dashboard'
    if 'mes_selecionado' not in st.session_state:
        st.session_state.mes_selecionado = get_mes_atual()
    if 'ano_selecionado' not in st.session_state:
        st.session_state.ano_selecionado = get_ano_atual()
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = False
    if 'name' not in st.session_state:
        st.session_state.name = None

def criar_espacamento(linhas=1):
    """Cria espaçamento vertical"""
    for _ in range(linhas):
        st.write("")
