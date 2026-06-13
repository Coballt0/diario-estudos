import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
from datetime import date
import os

# ── Configuração da página ─────────────────────────────────────
st.set_page_config(
    page_title='Diário de Estudos',
    page_icon='📚',
    layout='centered'
)

# ── Conexão com Supabase ───────────────────────────────────────
load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

@st.cache_resource
def conectar():
    return create_client(url, key)

supabase = conectar()

# ── Funções de dados ───────────────────────────────────────────
def carregar_estudos():
    resultado = supabase.table('estudos').select('*').order('data', desc=True).execute()
    return resultado.data

def carregar_materias():
    resultado = supabase.table('materias').select('*').order('nome').execute()
    return [m['nome'] for m in resultado.data]

def salvar_estudo(data, materia, conteudo, horas):
    from datetime import timedelta
    revisao1 = (date.fromisoformat(str(data)) + timedelta(days=1)).isoformat()
    revisao2 = (date.fromisoformat(str(data)) + timedelta(days=14)).isoformat()
    supabase.table('estudos').insert({
        'data':     str(data),
        'materia':  materia,
        'conteudo': conteudo,
        'horas':    horas,
        'revisao1': revisao1,
        'revisao2': revisao2,
    }).execute()

def deletar_estudo(id):
    supabase.table('estudos').delete().eq('id', id).execute()

def editar_estudo(id, data, materia, conteudo, horas):
    from datetime import timedelta
    revisao1 = (date.fromisoformat(str(data)) + timedelta(days=1)).isoformat()
    revisao2 = (date.fromisoformat(str(data)) + timedelta(days=14)).isoformat()
    supabase.table('estudos').update({
        'data':     str(data),
        'materia':  materia,
        'conteudo': conteudo,
        'horas':    horas,
        'revisao1': revisao1,
        'revisao2': revisao2,
    }).eq('id', id).execute()

def adicionar_materia(nome):
    supabase.table('materias').insert({'nome': nome}).execute()

def deletar_materia(nome):
    supabase.table('materias').delete().eq('nome', nome).execute()

# ── Menu lateral ───────────────────────────────────────────────
st.sidebar.title('📚 Diário de Estudos')
pagina = st.sidebar.selectbox('Menu', [
    '📝 Registrar',
    '📅 Histórico',
    '📊 Gráficos',
    '🔔 Lembretes',
    '⚙️ Matérias'
])

# ══════════════════════════════════════════════════════════════
# PÁGINA 1 — REGISTRAR
# ══════════════════════════════════════════════════════════════
if pagina == '📝 Registrar':
    st.title('📝 Registrar sessão de estudo')

    materias = carregar_materias()

    data     = st.date_input('Data', value=date.today())
    opcoes   = materias + ['➕ Nova matéria...']
    escolha  = st.selectbox('Matéria', opcoes)

    if escolha == '➕ Nova matéria...':
        materia = st.text_input('Digite o nome da nova matéria')
    else:
        materia = escolha

    conteudo = st.text_area('Conteúdo estudado', placeholder='Descreva o que você estudou...')
    horas    = st.number_input('Horas estudadas', min_value=0.5, max_value=24.0, step=0.5, value=1.0)

    if st.button('💾 Salvar sessão'):
        if materia.strip() == '':
            st.error('Preencha o nome da matéria!')
        elif conteudo.strip() == '':
            st.error('Preencha o conteúdo estudado!')
        else:
            if escolha == '➕ Nova matéria...' and materia.strip() not in materias:
                adicionar_materia(materia.strip())

            salvar_estudo(data, materia.strip(), conteudo.strip(), horas)

            from datetime import timedelta
            r1 = date.fromisoformat(str(data)) + timedelta(days=1)
            r2 = date.fromisoformat(str(data)) + timedelta(days=14)

            st.success(f'✅ Sessão de **{materia}** salva com sucesso!')
            st.info(f'🔔 Revisões agendadas para **{r1}** e **{r2}**')

# ══════════════════════════════════════════════════════════════
# PÁGINA 2 — HISTÓRICO
# ══════════════════════════════════════════════════════════════
elif pagina == '📅 Histórico':
    st.title('📅 Histórico de estudos')

    estudos = carregar_estudos()

    if not estudos:
        st.info('Nenhuma sessão registrada ainda!')
    else:
        materias_unicas = ['Todas'] + list(set(e['materia'] for e in estudos))
        filtro = st.selectbox('Filtrar por matéria', materias_unicas)

        if filtro != 'Todas':
            filtrados = [e for e in estudos if e['materia'] == filtro]
        else:
            filtrados = estudos

        for i, e in enumerate(filtrados):
            with st.expander(f"**{i+1}. {e['materia']}** — {e['data']} ({e['horas']}h)"):
                st.write(f"📝 {e['conteudo']}")
                st.write(f"🔔 Revisão 1: {e['revisao1']}  |  Revisão 2: {e['revisao2']}")

                col1, col2 = st.columns(2)

                if col1.button('🗑️ Deletar', key=f'del_{e["id"]}'):
                    deletar_estudo(e['id'])
                    st.success('Sessão deletada!')
                    st.rerun()

                if col2.button('✏️ Editar', key=f'edit_{e["id"]}'):
                    st.session_state['editando'] = e['id']

                if st.session_state.get('editando') == e['id']:
                    materias = carregar_materias()
                    nova_data     = st.date_input('Nova data',
                                                   value=date.fromisoformat(e['data']),
                                                   key=f'data_{e["id"]}')
                    nova_materia  = st.selectbox('Nova matéria', materias,
                                                  index=materias.index(e['materia'])
                                                  if e['materia'] in materias else 0,
                                                  key=f'mat_{e["id"]}')
                    novo_conteudo = st.text_area('Novo conteúdo',
                                                  value=e['conteudo'],
                                                  key=f'cont_{e["id"]}')
                    novas_horas   = st.number_input('Novas horas', min_value=0.5,
                                                     max_value=24.0, step=0.5,
                                                     value=float(e['horas']),
                                                     key=f'hrs_{e["id"]}')

                    if st.button('💾 Salvar edição', key=f'save_{e["id"]}'):
                        if novo_conteudo.strip() == '':
                            st.error('Preencha o conteúdo!')
                        else:
                            editar_estudo(e['id'], nova_data, nova_materia,
                                          novo_conteudo.strip(), novas_horas)
                            del st.session_state['editando']
                            st.success('Sessão editada!')
                            st.rerun()

        total = sum(e['horas'] for e in filtrados)
        st.metric('Total de horas', f'{total:.1f}h')

# ══════════════════════════════════════════════════════════════
# PÁGINA 3 — GRÁFICOS
# ══════════════════════════════════════════════════════════════
elif pagina == '📊 Gráficos':
    st.title('📊 Gráficos de estudo')

    estudos = carregar_estudos()

    if not estudos:
        st.info('Nenhuma sessão registrada ainda!')
    else:
        import pandas as pd

        df = pd.DataFrame(estudos)

        col1, col2, col3 = st.columns(3)
        col1.metric('Total de horas', f"{df['horas'].sum():.1f}h")
        col2.metric('Matérias estudadas', df['materia'].nunique())
        col3.metric('Sessões registradas', len(df))

        st.divider()

        st.write('**📊 Horas por matéria:**')
        horas_materia = df.groupby('materia')['horas'].sum().sort_values(ascending=False)
        st.bar_chart(horas_materia)

        st.write('**📈 Horas por dia:**')
        horas_dia = df.groupby('data')['horas'].sum()
        st.line_chart(horas_dia)

# ══════════════════════════════════════════════════════════════
# PÁGINA 4 — LEMBRETES
# ══════════════════════════════════════════════════════════════
elif pagina == '🔔 Lembretes':
    st.title('🔔 Revisões de hoje')

    hoje = date.today().isoformat()
    estudos = carregar_estudos()

    if not estudos:
        st.info('Nenhuma sessão registrada ainda!')
    else:
        revisao1 = [e for e in estudos if e['revisao1'] == hoje]
        revisao2 = [e for e in estudos if e['revisao2'] == hoje]

        if not revisao1 and not revisao2:
            st.success('Nenhuma revisão para hoje! Continue estudando. 🎉')

        if revisao1:
            st.subheader('📖 Revisão do dia seguinte')
            for e in revisao1:
                st.warning(f"**{e['materia']}** — estudado em {e['data']}")
                st.write(f"📝 {e['conteudo']}")
                st.divider()

        if revisao2:
            st.subheader('📖 Revisão de 14 dias')
            for e in revisao2:
                st.warning(f"**{e['materia']}** — estudado em {e['data']}")
                st.write(f"📝 {e['conteudo']}")
                st.divider()

        st.subheader('📅 Próximas revisões')
        proximas = sorted(
            [e for e in estudos if e['revisao1'] > hoje or e['revisao2'] > hoje],
            key=lambda x: min(x['revisao1'], x['revisao2'])
        )

        if proximas:
            for e in proximas[:10]:
                proxima = min(e['revisao1'], e['revisao2'])
                st.write(f"📅 **{proxima}** — {e['materia']}: {e['conteudo'][:50]}...")
        else:
            st.info('Nenhuma revisão futura agendada.')

# ══════════════════════════════════════════════════════════════
# PÁGINA 5 — MATÉRIAS
# ══════════════════════════════════════════════════════════════
elif pagina == '⚙️ Matérias':
    st.title('⚙️ Gerenciar Matérias')

    materias = carregar_materias()

    st.subheader('📋 Matérias cadastradas')
    for m in materias:
        col1, col2 = st.columns([4, 1])
        col1.write(f'• {m}')
        if col2.button('🗑️', key=f'del_{m}'):
            deletar_materia(m)
            st.success(f'**{m}** removida!')
            st.rerun()

    st.divider()

    st.subheader('➕ Adicionar nova matéria')
    nova = st.text_input('Nome da matéria')
    if st.button('Adicionar'):
        if nova.strip() == '':
            st.error('Digite o nome da matéria!')
        elif nova.strip() in materias:
            st.warning('Essa matéria já existe!')
        else:
            adicionar_materia(nova.strip())
            st.success(f'**{nova}** adicionada!')
            st.rerun()