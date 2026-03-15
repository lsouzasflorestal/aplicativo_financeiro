import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from calendar import monthrange
import pandas as pd
import time
import streamlit_authenticator as stauth

from database import (
    init_database,
    get_bancos, get_categorias, get_transacoes,
    add_transacao, update_transacao, delete_transacao, get_transacao_by_id,
    add_banco, delete_banco, add_categoria, delete_categoria,
    get_saldo_total, get_resumo_mes, get_gastos_por_categoria, get_receitas_por_categoria
)
from utils import (
    formatar_moeda, formatar_percentual, get_mes_atual, get_ano_atual,
    get_nomes_meses, inicializar_session_state, criar_espacamento
)

# Configuração do autenticador
config = {
    "credentials": {
        "usernames": {
            "admin": {
                "email": "admin@example.com",
                "name": "Administrador",
                "password": stauth.Hasher.hash("admin123")  # Senha: admin123
            }
        }
    },
    "cookie": {
        "expiry_days": 30,
        "key": "random_signature_key",
        "name": "streamlit_authenticator"
    },
    "preauthorized": {
        "emails": ["admin@example.com"]
    }
}
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Configuração da página
st.set_page_config(
    page_title="Planejador Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state
inicializar_session_state()

# Autenticação
authenticator.login(location='unrendered')

if st.session_state.get('authentication_status', False):
    st.session_state.username = st.session_state.get('username')
    # Inicializar banco do usuário se não existir
    init_database(st.session_state.username)
else:
    st.title("🔐 Login - Planejador Financeiro")
    
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if username and password:
            # Verificar credenciais
            if username in config['credentials']['usernames'] and stauth.Hasher.check(password, config['credentials']['usernames'][username]['password']):
                st.session_state['authentication_status'] = True
                st.session_state['username'] = username
                st.session_state['name'] = config['credentials']['usernames'][username]['name']
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        else:
            st.error("Preencha todos os campos.")

# Verificar se usuário está logado
if st.session_state.get('authentication_status', False):
    
    st.stop()  # Para a execução se não estiver logado

# Inicializar banco de dados do usuário
init_database(st.session_state.username)

# CSS personalizado
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 28px;
    }
    .banco-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .categoria-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }

    /* Navegação superior estilo abas (botões) - Dark mode como padrão */
    .stButton button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: 1px solid transparent !important;
        margin: 0 2px 4px 0 !important;
        background: transparent !important;
        color: #f9fafb !important;  /* Branco */
    }
    .stButton button:hover {
        background: rgba(75, 85, 99, 0.2) !important;
    }
    .stButton button[data-testid*="primary"] {
        border-bottom: 4px solid #9ca3af !important;
        background: rgba(75, 85, 99, 0.3) !important;
        color: #ffffff !important;  /* Branco mais intenso */
        font-weight: 700 !important;
    }

    /* Light mode adjustments */
    [data-theme="light"] .stButton button {
        color: #374151 !important;
    }
    [data-theme="light"] .stButton button:hover {
        background: rgba(156, 163, 175, 0.1) !important;
    }
    [data-theme="light"] .stButton button[data-testid*="primary"] {
        border-bottom: 4px solid #374151 !important;
        background: rgba(107, 114, 128, 0.1) !important;
        color: #111827 !important;
    }

    /* Força o menu a ficar responsivo */
    @media (max-width: 640px) {
        .stButton button {
            display: block !important;
            width: 100% !important;
            box-sizing: border-box !important;
            text-align: center !important;
            margin-bottom: 4px !important;
        }
        .stMetric {
            margin-bottom: 16px !important;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            font-size: 1.5rem !important;
        }
        .stColumns {
            gap: 8px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ======================== TOPO / NAVEGAÇÃO ========================
# Navbar horizontal (melhor para visualização mobile)
pages = ["Dashboard", "Lançamentos", "Categorias", "Bancos", "Relatórios", "Editar/Deletar"]

page = st.session_state.get('page', 'Dashboard')
if page not in pages:
    page = 'Dashboard'

# Cabeçalho com logout
col1, col2 = st.columns([5, 1])
with col1:
    st.markdown(f"### BEM-VINDO(A)!  —  {st.session_state.username}")
with col2:
    if st.button("🚪 Sair"):
        authenticator.logout()
        st.session_state.username = None
        st.rerun()

# Navegação em estilo “abas” (botões clicáveis)
cols = st.columns(len(pages))
for i, p in enumerate(pages):
    if cols[i].button(p, width='stretch', type="secondary" if p != page else "primary"):
        page = p
        st.session_state.page = page
        st.rerun()

# Filtros de data (aplicável em Dashboard e Relatórios)
if page in ["Dashboard", "Relatórios"]:
    with st.expander("📅 Filtros (Clique para abrir/fechar)", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            meses = get_nomes_meses()
            mes = st.selectbox(
                "Mês:",
                options=list(meses.keys()),
                format_func=lambda x: meses[x],
                index=get_mes_atual()-1
            )
            st.session_state.mes_selecionado = mes

        with col2:
            ano = st.selectbox(
                "Ano:",
                options=range(2020, 2031),
                index=(get_ano_atual()-2020)
            )
            st.session_state.ano_selecionado = ano

# ======================== PÁGINAS ========================

# PÁGINA: DASHBOARD
if page == "Dashboard":
    st.title("📊 Acompanhamento Financeiro")
    
    mes = st.session_state.mes_selecionado
    ano = st.session_state.ano_selecionado
    meses_dict = get_nomes_meses()
    
    # Título com mês/ano
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"## {meses_dict[mes]} de {ano}")
    
    criar_espacamento()
    
    # Resumo mensal
    resumo = get_resumo_mes(st.session_state.username, mes, ano)
    receita_total = resumo.get('Receita', 0)
    despesa_total = resumo.get('Despesa', 0)
    investimento_total = resumo.get('Investimento', 0)
    
    # Calcular saldo acumulado até o mês/ano selecionado
    todas_transacoes = get_transacoes(st.session_state.username)
    saldo_acumulado = 0
    
    # Data do último dia do mês selecionado
    _, ultimo_dia = monthrange(ano, mes)
    data_filtro = datetime(ano, mes, ultimo_dia).date()
    
    for transacao in todas_transacoes:
        data_transacao = datetime.strptime(transacao['data'], '%Y-%m-%d').date()
        
        # Só contabilizar até o mês/ano selecionado
        if data_transacao <= data_filtro:
            if transacao['tipo'] == 'Receita':
                saldo_acumulado += transacao['valor']
            elif transacao['tipo'] == 'Despesa':
                saldo_acumulado -= transacao['valor']
    
    # Métricas principais (2x2 para melhor visualização em mobile)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 Receita do Mês", formatar_moeda(receita_total), delta=None)
    with col2:
        st.metric("📉 Despesas do Mês", formatar_moeda(despesa_total), delta=None)

    col3, col4 = st.columns(2)
    with col3:
        st.metric("📈 Investimentos", formatar_moeda(investimento_total), delta=None)
    with col4:
        if saldo_acumulado >= 0:
            st.metric("💵 Saldo Acumulado", formatar_moeda(saldo_acumulado), delta=None)
        else:
            st.metric("⚠️ Saldo Acumulado", formatar_moeda(saldo_acumulado), delta=None)

    criar_espacamento()
    
    # Gráfico de receita vs despesa vs investimento - 12 meses de 2026
    st.subheader("Receitas, Despesas e Investimentos ao Longo do Ano")
    
    # Dados de todos os 12 meses do ano vigente (2026)
    dados_ano = []
    for m in range(1, 13):
        resumo_mes = get_resumo_mes(st.session_state.username, m, ano)
        dados_ano.append({
            'Mês': meses_dict[m],
            'Receita': resumo_mes.get('Receita', 0),
            'Despesa': resumo_mes.get('Despesa', 0),
            'Investimento': resumo_mes.get('Investimento', 0)
        })
    
    df_ano = pd.DataFrame(dados_ano)
    
    fig = go.Figure(data=[
        go.Bar(
            name='Receita',
            x=df_ano['Mês'],
            y=df_ano['Receita'],
            marker_color='#22C55E',
            text=df_ano['Receita'].apply(lambda x: f"R$ {x:.0f}" if x > 0 else ""),
            textposition='outside',
            textfont=dict(size=10)
        ),
        go.Bar(
            name='Despesa',
            x=df_ano['Mês'],
            y=df_ano['Despesa'],
            marker_color='#EF4444',
            text=df_ano['Despesa'].apply(lambda x: f"R$ {x:.0f}" if x > 0 else ""),
            textposition='outside',
            textfont=dict(size=10)
        ),
        go.Bar(
            name='Investimento',
            x=df_ano['Mês'],
            y=df_ano['Investimento'],
            marker_color='#3B82F6',
            text=df_ano['Investimento'].apply(lambda x: f"R$ {x:.0f}" if x > 0 else ""),
            textposition='outside',
            textfont=dict(size=10)
        )
    ])
    fig.update_layout(
        barmode='group',
        height=500,
        showlegend=True,
        yaxis=dict(showgrid=False, zeroline=False),
        xaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
    
    criar_espacamento()
    
    criar_espacamento()
    
    # Gastos por categoria  
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💸 Despesas por Categoria")
        gastos = get_gastos_por_categoria(st.session_state.username, mes, ano)
        
        if gastos:
            df_gastos = pd.DataFrame(gastos)
            # Paleta de cores para despesas (tons de vermelho)
            cores_despesa = ['#DC2626', '#EF4444', '#F87171', '#FCA5A5', '#FECACA', '#FEE2E2', '#FFE4E6', '#FFD1D5']
            cores = [cores_despesa[i % len(cores_despesa)] for i in range(len(df_gastos))]
            
            fig_gastos = go.Figure(data=[
                go.Pie(
                    labels=df_gastos['nome'],
                    values=df_gastos['total'],
                    marker_colors=cores,
                    textinfo='label+percent',
                    textfont=dict(size=11)
                )
            ])
            fig_gastos.update_layout(
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.4,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig_gastos, width='stretch', config={'displayModeBar': False})
        else:
            st.info("Nenhuma despesa neste mês")
    
    with col2:
        st.subheader("💵 Receitas por Categoria")
        receitas = get_receitas_por_categoria(st.session_state.username, mes, ano)
        
        if receitas:
            df_receitas = pd.DataFrame(receitas)
            # Paleta de cores para receitas (tons de verde)
            cores_receita = ['#059669', '#10B981', '#34D399', '#6EE7B7', '#A7F3D0', '#DCFCE7', '#F0FDF4']
            cores = [cores_receita[i % len(cores_receita)] for i in range(len(df_receitas))]
            
            fig_receitas = go.Figure(data=[
                go.Pie(
                    labels=df_receitas['nome'],
                    values=df_receitas['total'],
                    marker_colors=cores,
                    textinfo='label+percent',
                    textfont=dict(size=11)
                )
            ])
            fig_receitas.update_layout(
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.4,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig_receitas, width='stretch', config={'displayModeBar': False})
        else:
            st.info("Nenhuma receita neste mês")
    
    with col3:
        st.subheader("📊 Investimentos por Categoria")
        transacoes_investimento = get_transacoes(st.session_state.username, tipo='Investimento', mes=mes, ano=ano)
        
        if transacoes_investimento:
            df_invest = pd.DataFrame(transacoes_investimento)
            df_invest_grupo = df_invest.groupby('categoria_nome')['valor'].sum().reset_index()
            df_invest_grupo.columns = ['nome', 'total']
            
            # Paleta de cores para investimentos (tons de azul e roxo)
            cores_invest = ['#0369A1', '#0284C7', '#0EA5E9', '#38BDF8', '#7DD3FC', '#BAE6FD', '#E0F2FE']
            cores = [cores_invest[i % len(cores_invest)] for i in range(len(df_invest_grupo))]
            
            fig_invest = go.Figure(data=[
                go.Pie(
                    labels=df_invest_grupo['nome'],
                    values=df_invest_grupo['total'],
                    marker_colors=cores,
                    textinfo='label+percent',
                    textfont=dict(size=11)
                )
            ])
            fig_invest.update_layout(
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.4,
                    xanchor="center",
                    x=0.5
                )
            )
            st.plotly_chart(fig_invest, width='stretch', config={'displayModeBar': False})
        else:
            st.info("Nenhum investimento neste mês")

# PÁGINA: LANÇAMENTOS
elif page == "Lançamentos":
    st.title("📝 Registrar Transação")
    
    # Inicializar session_state para tipo de transação
    if 'tipo_transacao' not in st.session_state:
        st.session_state.tipo_transacao = "Receita"
    
    # Callback para atualizar tipo
    def atualizar_tipo():
        st.session_state.tipo_transacao = st.session_state.select_tipo
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo = st.selectbox(
            "Tipo de Transação:",
            ["Receita", "Despesa", "Investimento"],
            index=["Receita", "Despesa", "Investimento"].index(st.session_state.tipo_transacao),
            key="select_tipo",
            on_change=atualizar_tipo
        )
    
    with col2:
        categorias = get_categorias(st.session_state.username, tipo)
        if categorias:
            categoria_id = st.selectbox(
                "Categoria:",
                options=[c['id'] for c in categorias],
                format_func=lambda x: next(c['nome'] for c in categorias if c['id'] == x)
            )
        else:
            st.warning(f"Nenhuma categoria de {tipo} cadastrada!")
            categoria_id = None
    
    with st.form("form_transacao"):
        col1, col2 = st.columns(2)
        
        with col1:
            bancos = get_bancos(st.session_state.username)
            if bancos:
                banco_id = st.selectbox(
                    "Banco:",
                    options=[b['id'] for b in bancos],
                    format_func=lambda x: next(b['nome'] for b in bancos if b['id'] == x),
                    key="form_banco"
                )
            else:
                st.warning("Nenhum banco cadastrado!")
                banco_id = None
        
        with col2:
            valor = st.number_input(
                "Valor Total (R$):",
                value=0.00,
                min_value=0.00,
                format="%.2f",
                key="form_valor"
            )
        
        descricao = st.text_input("Descrição (opcional):", key="form_descricao")
        data = st.date_input("Data:", value=datetime.now().date(), key="form_data")
        
        # Campo de parcelas (apenas para Despesa)
        col1, col2 = st.columns(2)
        with col1:
            if tipo == "Despesa":
                parcelas = st.number_input(
                    "Número de Parcelas:",
                    value=1,
                    min_value=1,
                    max_value=120,
                    key="form_parcelas"
                )
            else:
                parcelas = 1
        
        with col2:
            if tipo == "Despesa" and parcelas > 1:
                valor_parcela = valor / parcelas
                st.metric("Valor por Parcela", formatar_moeda(valor_parcela))
        
        submitted = st.form_submit_button("💾 Registrar Transação")
        
        if submitted:
            if valor <= 0:
                st.error("O valor deve ser maior que zero!")
            elif categoria_id is None:
                st.error("Selecione uma categoria!")
            elif banco_id is None:
                st.error("Selecione um banco!")
            else:
                # Se for despesa com múltiplas parcelas, registrar cada parcela
                if tipo == "Despesa" and parcelas > 1:
                    valor_parcela = valor / parcelas
                    for i in range(int(parcelas)):
                        # Data de cada parcela (incrementa um mês)
                        data_parcela = data + timedelta(days=30*i)
                        descricao_parcela = f"{descricao} (Parcela {i+1}/{int(parcelas)})" if descricao else f"Parcela {i+1}/{int(parcelas)}"
                        add_transacao(st.session_state.username, tipo, categoria_id, banco_id, valor_parcela, descricao_parcela, data_parcela)
                    st.success(f"✅ {tipo} de {formatar_moeda(valor)} registrada em {int(parcelas)} parcelas!")
                else:
                    add_transacao(st.session_state.username, tipo, categoria_id, banco_id, valor, descricao, data)
                    st.success(f"✅ {tipo} de {formatar_moeda(valor)} registrada com sucesso!")
                st.rerun()
    
    criar_espacamento()
    
    # Histórico de transações
    st.subheader("📋 Lançamentos Registrados")
    
    # Filtros de mês e ano
    col1, col2, col3 = st.columns([1, 1, 2])
    
    meses = get_nomes_meses()
    
    with col1:
        mes_filtro = st.selectbox(
            "Filtrar por Mês:",
            options=list(meses.keys()),
            format_func=lambda x: meses[x],
            index=get_mes_atual()-1,
            key="filtro_mes_lancamentos"
        )
    
    with col2:
        ano_filtro = st.selectbox(
            "Filtrar por Ano:",
            options=range(2020, 2031),
            index=(get_ano_atual()-2020),
            key="filtro_ano_lancamentos"
        )
    
    with col3:
        st.write("")
        if st.button("🔄 Limpar Filtros", width='stretch'):
            st.session_state.filtro_mes_lancamentos = get_mes_atual() - 1
            st.session_state.filtro_ano_lancamentos = get_ano_atual() - 2020
            st.rerun()
    
    # Obter transações com filtro
    transacoes = get_transacoes(st.session_state.username, mes=mes_filtro, ano=ano_filtro)
    
    if transacoes:
        # Exibir transações com botões de editar e deletar
        transacoes_ordenadas = sorted(transacoes, key=lambda x: x['data'], reverse=True)
        
        # Usar container com scroll horizontal
        with st.container(border=True):
            st.markdown("""
            <style>
            .transaction-table {
                overflow-x: auto;
                width: 100%;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Criar tabela com botões em um layout melhor
            cols = st.columns([0.6, 1.2, 1, 1.5, 1.5, 1, 2, 0.8, 0.8])
            cols[0].write("**ID**")
            cols[1].write("**Data**")
            cols[2].write("**Tipo**")
            cols[3].write("**Categoria**")
            cols[4].write("**Banco**")
            cols[5].write("**Valor**")
            cols[6].write("**Descrição**")
            cols[7].write("**Editar**")
            cols[8].write("**Deletar**")
            
            st.divider()
            
            for transacao in transacoes_ordenadas:
                cols = st.columns([0.6, 1.2, 1, 1.5, 1.5, 1, 2, 0.8, 0.8])
                
                with cols[0]:
                    st.caption(str(transacao['id']))
                with cols[1]:
                    st.caption(str(transacao['data']))
                with cols[2]:
                    st.caption(transacao['tipo'])
                with cols[3]:
                    st.caption(transacao['categoria_nome'][:20] if len(transacao['categoria_nome']) > 20 else transacao['categoria_nome'])
                with cols[4]:
                    st.caption(transacao['banco_nome'][:15] if len(transacao['banco_nome']) > 15 else transacao['banco_nome'])
                with cols[5]:
                    st.caption(formatar_moeda(transacao['valor']))
                with cols[6]:
                    desc_curta = transacao['descricao'][:25] if transacao['descricao'] else "-"
                    st.caption(desc_curta)
                with cols[7]:
                    if st.button("✏️", key=f"edit_{transacao['id']}", help=f"Editar transação ID {transacao['id']}"):
                        st.session_state.id_transacao_editar = transacao['id']
                        st.session_state.page = "Editar/Deletar"
                        st.rerun()
                with cols[8]:
                    if st.button("🗑️", key=f"delete_{transacao['id']}", help=f"Deletar transação ID {transacao['id']}"):
                        delete_transacao(st.session_state.username, transacao['id'])
                        st.success("✓ Transação deletada!")
                        st.rerun()
    else:
        st.info("Nenhuma transação registrada")

# PÁGINA: CATEGORIAS
elif page == "Categorias":
    st.title("🏷️ Gerenciar Categorias")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Adicionar Categoria")
        
        with st.form("form_categoria"):
            nome = st.text_input("Nome da Categoria:")
            tipo = st.selectbox("Tipo:", ["Receita", "Despesa", "Investimento"])
            submitted = st.form_submit_button("➕ Adicionar")
            
            if submitted:
                if nome:
                    if add_categoria(st.session_state.username, nome, tipo):
                        st.success(f"✅ Categoria '{nome}' adicionada!")
                        st.rerun()
                    else:
                        st.error("Essa categoria já existe!")
                else:
                    st.error("Digite um nome para a categoria!")
    
    with col2:
        st.subheader("Deletar Categoria")
        
        categorias = get_categorias(st.session_state.username)
        if categorias:
            categoria_selecionada = st.selectbox(
                "Selecione uma categoria:",
                options=[c['id'] for c in categorias],
                format_func=lambda x: next(c['nome'] for c in categorias if c['id'] == x),
                key="select_delete_cat"
            )
            
            if st.button("🗑️ Deletar Categoria"):
                delete_categoria(st.session_state.username, categoria_selecionada)
                st.success("✅ Categoria deletada!")
                st.rerun()
        else:
            st.info("Nenhuma categoria disponível")
    
    criar_espacamento()
    
    # Lista de categorias
    st.subheader("📚 Categorias Cadastradas")
    
    for tipo in ["Receita", "Despesa", "Investimento"]:
        st.markdown(f"### {tipo}")
        
        categorias = get_categorias(st.session_state.username, tipo)
        if categorias:
            for categoria in categorias:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{categoria['nome']}**")
                with col2:
                    if st.button("❌", key=f"del_cat_{categoria['id']}"):
                        delete_categoria(st.session_state.username, categoria['id'])
                        st.success("Deletada!")
                        st.rerun()
        else:
            st.write(f"Nenhuma categoria de {tipo}")

# PÁGINA: BANCOS
elif page == "Bancos":
    st.title("🏦 Gerenciar Bancos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Adicionar Banco")
        
        with st.form("form_banco"):
            nome = st.text_input("Nome do Banco:")
            saldo = st.number_input("Saldo Inicial (R$):", value=0.00, min_value=0.00, format="%.2f")
            submitted = st.form_submit_button("➕ Adicionar")
            
            if submitted:
                if nome:
                    if add_banco(st.session_state.username, nome, saldo):
                        st.success(f"✅ Banco '{nome}' adicionado!")
                        st.rerun()
                    else:
                        st.error("Esse banco já existe!")
                else:
                    st.error("Digite um nome para o banco!")
    
    with col2:
        st.subheader("Deletar Banco")
        
        bancos = get_bancos(st.session_state.username)
        if bancos:
            banco_selecionado = st.selectbox(
                "Selecione um banco:",
                options=[b['id'] for b in bancos],
                format_func=lambda x: next(b['nome'] for b in bancos if b['id'] == x),
                key="select_delete_bank"
            )
            
            if st.button("🗑️ Deletar Banco"):
                delete_banco(st.session_state.username, banco_selecionado)
                st.success("✅ Banco deletado!")
                st.rerun()
        else:
            st.info("Nenhum banco disponível")
    
    criar_espacamento()
    
    # Lista de bancos
    st.subheader("📚 Bancos Cadastrados")
    
    bancos = get_bancos(st.session_state.username)
    if bancos:
        for banco in bancos:
            col1, col2, col3 = st.columns([ 3, 1, 1])
            with col1:
                st.write(f"**{banco['nome']}**")
                st.caption(f"Saldo Inicial: {formatar_moeda(banco['saldo_inicial'])}")
            with col2:
                st.write("")
            with col3:
                if st.button("❌", key=f"del_bank_{banco['id']}"):
                    delete_banco(st.session_state.username, banco['id'])
                    st.success("Deletado!")
                    st.rerun()
    else:
        st.info("Nenhum banco cadastrado")

# PÁGINA: RELATÓRIOS
elif page == "Relatórios":
    st.title("📈 Relatórios")
    
    mes = st.session_state.mes_selecionado
    ano = st.session_state.ano_selecionado
    meses_dict = get_nomes_meses()
    
    st.markdown(f"## Relatório de {meses_dict[mes]}/{ano}")
    
    criar_espacamento()
    
    # Resumo detalhado
    resumo = get_resumo_mes(st.session_state.username, mes, ano)
    receita_total = resumo.get('Receita', 0)
    despesa_total = resumo.get('Despesa', 0)
    investimento_total = resumo.get('Investimento', 0)
    saldo = receita_total - despesa_total
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total Receita", formatar_moeda(receita_total))
    with col2:
        st.metric("📉 Total Despesa", formatar_moeda(despesa_total))
    with col3:
        st.metric("📈 Total Investimento", formatar_moeda(investimento_total))
    with col4:
        st.metric("💵 Saldo Líquido", formatar_moeda(saldo))
    
    criar_espacamento()
    
    # Tabela completa de transações do mês
    st.subheader("Todas as Transações do Mês")
    
    transacoes = get_transacoes(st.session_state.username, mes=mes, ano=ano)
    if transacoes:
        df = pd.DataFrame(transacoes)
        df = df[['id', 'data', 'tipo', 'categoria_nome', 'banco_nome', 'valor', 'descricao']]
        df.columns = ['ID', 'Data', 'Tipo', 'Categoria', 'Banco', 'Valor', 'Descrição']
        df['Valor'] = df['Valor'].apply(formatar_moeda)
        df = df.sort_values('Data', ascending=False)
        
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("Nenhuma transação neste mês")

# PÁGINA: EDITAR/DELETAR
elif page == "Editar/Deletar":
    st.title("✏️ Editar Transação")
    
    transacoes = get_transacoes(st.session_state.username)
    
    if not transacoes:
        st.info("Nenhuma transação para editar")
    else:
        # Campo para inserir ID da transação
        col1, col2, col3 = st.columns([2, 0.8, 0.8])
        
        with col1:
            transacao_id = st.number_input(
                "Digite o ID da Transação:",
                value=int(st.session_state.get('id_transacao_editar', 0)),
                min_value=0,
                step=1,
                key="input_id_transacao"
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("🔍 Buscar", width='stretch'):
                if transacao_id > 0:
                    transacao_temp = get_transacao_by_id(st.session_state.username, transacao_id)
                    if transacao_temp:
                        st.session_state.id_transacao_editar = transacao_id
                    else:
                        st.error(f"ID {transacao_id} não encontrado!")
        
        with col3:
            st.write("")
            st.write("")
            if st.button("🗑️ Limpar", width='stretch'):
                st.session_state.id_transacao_editar = 0
                st.rerun()
        
        st.divider()
        
        if transacao_id > 0:
            transacao = get_transacao_by_id(st.session_state.username, transacao_id)
            
            if transacao:
                # Exibir informações atuais
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Data", transacao['data'])
                    with col2:
                        st.metric("Tipo", transacao['tipo'])
                    with col3:
                        st.metric("Categoria", transacao['categoria_nome'])
                    with col4:
                        st.metric("Valor Atual", formatar_moeda(transacao['valor']))
                
                st.divider()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("✏️ Editar Dados")
                    
                    with st.form("form_edit_transacao"):
                        tipo = st.selectbox(
                            "Tipo:",
                            ["Receita", "Despesa", "Investimento"],
                            index=["Receita", "Despesa", "Investimento"].index(transacao['tipo']),
                            key="form_tipo"
                        )
                        
                        categorias = get_categorias(st.session_state.username, tipo)
                        if categorias:
                            categoria_id = st.selectbox(
                                "Categoria:",
                                options=[c['id'] for c in categorias],
                                format_func=lambda x: next(c['nome'] for c in categorias if c['id'] == x),
                                index=next((i for i, c in enumerate(categorias) if c['id'] == transacao['categoria_id']), 0),
                                key="form_categoria"
                            )
                        else:
                            st.warning(f"Nenhuma categoria de {tipo} disponível")
                            categoria_id = None
                        
                        bancos = get_bancos(st.session_state.username)
                        if bancos:
                            banco_id = st.selectbox(
                                "Banco:",
                                options=[b['id'] for b in bancos],
                                format_func=lambda x: next(b['nome'] for b in bancos if b['id'] == x),
                                index=next((i for i, b in enumerate(bancos) if b['id'] == transacao['banco_id']), 0),
                                key="form_banco"
                            )
                        else:
                            st.warning("Nenhum banco disponível")
                            banco_id = None
                        
                        valor = st.number_input(
                            "Valor (R$):",
                            value=float(transacao['valor']),
                            min_value=0.00,
                            format="%.2f",
                            key="form_valor"
                        )
                        
                        descricao = st.text_input(
                            "Descrição:",
                            value=transacao['descricao'] or "",
                            key="form_descricao"
                        )
                        
                        data = st.date_input(
                            "Data:",
                            value=datetime.strptime(transacao['data'], '%Y-%m-%d').date(),
                            key="form_data"
                        )
                        
                        submitted = st.form_submit_button("💾 Atualizar Transação")
                        
                        if submitted:
                            if valor <= 0:
                                st.error("O valor deve ser maior que zero!")
                            elif categoria_id is None:
                                st.error("Selecione uma categoria válida!")
                            elif banco_id is None:
                                st.error("Selecione um banco válido!")
                            else:
                                try:
                                    update_transacao(
                                        st.session_state.username, transacao_id,
                                        tipo, categoria_id, banco_id, valor, descricao, data
                                    )
                                    st.success("✅ Transação atualizada com sucesso!")
                                    st.session_state.id_transacao_editar = 0
                                    time.sleep(1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao atualizar: {str(e)}")
                
                with col2:
                    st.subheader("🗑️ Deletar")
                    
                    st.warning("⚠️ Esta ação é irreversível!")
                    
                    if st.button("🗑️ Deletar Transação", type="secondary"):
                        try:
                            delete_transacao(st.session_state.username, transacao_id)
                            st.success("✅ Transação deletada com sucesso!")
                            st.session_state.id_transacao_editar = 0
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao deletar: {str(e)}")
            else:
                st.warning(f"⚠️ ID {transacao_id} não encontrado. Verifique o número do ID.")
        else:
            st.info("🔍 Digite o ID da transação no campo acima e clique em 'Buscar' para editar")
