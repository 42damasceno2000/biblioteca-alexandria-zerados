import streamlit as st
import pandas as pd
import os
import re
import random

# CONFIGURAR PÁGINA
st.set_page_config(
    page_title="Alexandria dos Zerados",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "É só para se divertir, rapaziada... Simbora Jogar! 😎"
    }
)
    
st.title("🎮 A Biblioteca de Alexandria (dos Jogos Zerados) 🎮")

# LINK PLANILHA
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTq--KnMAlHhAwvWQ4mEnapM5P_wdlBYYE5bIk5u_pw5jhYQDvzWZeXbFtoINhnfy6h35tRYxeX2WqJ/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data():
    return pd.read_csv(sheet_url, dtype=str)

# FUNÇÕES AUXILIARES
def resolve_imagem(nome_jogo):
    if not isinstance(nome_jogo, str): return None
    nome_limpo = nome_jogo.strip().replace(':', '').replace('?', '').replace('/', '')
    caminhos = [f"capas/{nome_limpo}.jpg", f"capas/{nome_limpo}.png", f"capas/{nome_limpo}.jpeg"]
    for caminho in caminhos:
        if os.path.exists(caminho): return caminho 
    return f"https://www.google.com/search?tbm=isch&q={nome_jogo.replace(' ', '+')}+game+cover"

def limpar_horas(texto):
    if not isinstance(texto, str): return "-"
    # Extrai apenas os números (ex: "1807 [Horas]" -> "1807")
    match = re.search(r'(\d+)', texto)
    if match:
        return f"{match.group(1)}h"
    return texto

def classificar_status(texto):
    if not isinstance(texto, str): return "Pendentes"
    u = texto.upper()
    if "ESTOU JOGANDO" in u or "JOGANDO" in u: return "Jogando"
    if "QUERO" in u or "DESEJADO" in u: return "Desejados"
    if "JOGUEI E" in u or "NÃO ZEREI" in u or "INCOMPLETO" in u: return "Incompletos"
    simbolos = ['⭐', '🌟', '❤', '❤️', '💓', '☢', '½', '✅', '🏆', '🥇']
    tem_simbolo = any(s in texto for s in simbolos)
    tem_palavra = "ZERADO" in u or "CONCLUÍDO" in u or "TERMINADO" in u or "FINALIZADO" in u
    eh_negativo = "NÃO" in u and not tem_simbolo
    if (tem_simbolo or tem_palavra) and not eh_negativo: return "Zerados"
    return "Pendentes"

def calcular_nota_0_11(texto):
    if not isinstance(texto, str): return None
    t = texto.strip()
    if '❤️' in t or '❤' in t or '💓' in t: return 11.0
    if '☢' in t: return 0.0
    score = (t.count('⭐') * 2) + (1 if '½' in t else 0)
    if score == 0 and '½' not in t and '☢' not in t: return None
    return score

# COMEMORAÇÃO
def celebrar_aleatoriamente():
    # Sorteia entre Balões e Neve
    efeito = random.choice([st.balloons, st.snow])
    efeito()
    
try:
    df_raw = load_data()
    
    # CONFIGURAÇÃO INICIAL
    col_videogames = df_raw.columns[0]
    colunas_players = [c for c in df_raw.columns if "Player" in c]
    if 'Nota' in df_raw.columns: df_raw.rename(columns={'Nota': 'Nota Média'}, inplace=True)
    col_nota_media = 'Nota Média'

    # ABA ESTATÍSTICAS (LOBBY)
    df_stats = df_raw.iloc[0:7].copy()
    if "Estatísticas & Capas" in df_stats.columns:
        df_stats.rename(columns={"Estatísticas & Capas": "Estatísticas"}, inplace=True)
        df_stats.loc[0, "Estatísticas"] = "Finalizados"
    df_stats = df_stats[~df_stats["Estatísticas"].astype(str).str.contains("Gráfico", case=False, na=False)]

    # LISTA DE JOGOS
    df_games = df_raw.iloc[7:].copy() 
    df_games = df_games[df_games[col_videogames].notna() & (df_games[col_videogames] != "")]

    # INTERFACE
    st.sidebar.header("Navegação")
    modo = st.sidebar.radio("Escolha a Visão:", ["🏰 Lobby Principal", "👤 Ficha do Jogador"])
    
    if modo == "🏰 Lobby Principal":
        tab1, tab2 = st.tabs(["📊 Estatísticas", "⚔️ Jogador VS Jogador"])
        with tab1:
            # LIMPEZA DO LOBBY
            cols_lobby_clean = ["Estatísticas"] + colunas_players
            cols_exist = [c for c in cols_lobby_clean if c in df_stats.columns]
            st.dataframe(df_stats[cols_exist], use_container_width=True, hide_index=True)
            
        with tab2:
            busca = st.text_input("🔍 Buscar:", placeholder="Ex: Metal Gear...")
            cols_pvp = [col_videogames, "Duração", col_nota_media] + colunas_players
            cols_final = [c for c in cols_pvp if c in df_games.columns]

            # CELEBRAÇÃO
            df_show = df_games[cols_final]
            if busca: 
                celebrar_aleatoriamente()
                df_show = df_show[df_show[col_videogames].str.contains(busca, case=False, na=False)]
                
            st.dataframe(df_show, use_container_width=True, hide_index=True)

    else:
        # FICHA INDIVIDUAL
        player_col = st.sidebar.selectbox("Selecione o Jogador:", colunas_players, index=0)
        
        # PROCESSAMENTO
        df_games["Categoria"] = df_games[player_col].apply(classificar_status)
        df_games["Pontos"] = df_games[player_col].apply(calcular_nota_0_11)
        df_games["Visual"] = df_games[col_videogames].apply(resolve_imagem)

        # FILTROS
        st.sidebar.divider()
        busca = st.sidebar.text_input("Buscar Jogo:")
        filtro_cat = st.sidebar.multiselect("Filtrar Status:", options=["Zerados", "Pendentes", "Jogando", "Desejados", "Incompletos"])
        
        # FILTRO CONDICIONAL DE NOTA
        # Só aparece se "Zerados" estiver selecionado no filtro acima
        filtro_nota = []
        if filtro_cat and "Zerados" in filtro_cat:
            # Pega apenas as notas que existem para esse jogador
            notas_existentes = df_games[df_games["Categoria"] == "Zerados"]["Pontos"].dropna().unique()
            # Ordena do maior (11) para o menor
            notas_ordenadas = sorted(notas_existentes, reverse=True)
            filtro_nota = st.sidebar.multiselect("Filtrar Nota:", options=notas_ordenadas)

        # AUTOMÁTICO: Celebra se qualquer filtro for usado
        if busca or filtro_cat or filtro_nota:
            celebrar_aleatoriamente()

        # MÉTRICAS
        counts = df_games["Categoria"].value_counts()
        media = df_games["Pontos"].mean()
        
        try:
            horas_raw = df_stats[df_stats["Estatísticas"].astype(str).str.contains("Horas: Total", na=False)][player_col].values[0]
            horas_clean = limpar_horas(horas_raw)
        except:
            horas_clean = "-"

        # PAINEL SUPERIOR
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Acervo Total", len(df_games))
        c2.metric("Zerados", int(counts.get("Zerados", 0)))
        c3.metric("Pendentes", int(counts.get("Pendentes", 0)))
        c4.metric("Sua Média (⭐)", f"{media:.2f}" if pd.notna(media) else "-")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Jogando", int(counts.get("Jogando", 0)))
        c6.metric("Desejados", int(counts.get("Desejados", 0)))
        c7.metric("Incompletos", int(counts.get("Incompletos", 0)))
        c8.metric("Tempo de Vida Gasto", horas_clean)

        st.divider()

        # TABELA FINAL
        df_show = df_games.copy()
        if busca: df_show = df_show[df_show[col_videogames].str.contains(busca, case=False, na=False)]
        if filtro_cat: df_show = df_show[df_show["Categoria"].isin(filtro_cat)]
        if filtro_nota: df_show = df_show[df_show["Pontos"].isin(filtro_nota)]
        
        # COLUNAS ORDENADAS
        cols_ordered = [player_col, col_videogames, "Duração", col_nota_media, "Visual"]
        cols_final_exist = [c for c in cols_ordered if c in df_show.columns]
        
        st.dataframe(
            df_show[cols_final_exist],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Visual": st.column_config.ImageColumn("Capa") if os.path.exists("capas") else st.column_config.LinkColumn("Capa", display_text="🖼️ Ver"),
                player_col: st.column_config.TextColumn("Seu Status"),
                col_videogames: st.column_config.TextColumn("Jogo"),
            }
        )

    # BOTÃO COMEMORAÇÃO
    st.sidebar.markdown("---")
    if st.sidebar.button("Tchêeeeee!!! 🚀"):
        celebrar_aleatoriamente()

except Exception as e:
    st.error(f"Erro Crítico: {e}")


