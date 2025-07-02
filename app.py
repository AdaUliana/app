import streamlit as st
import pandas as pd
import plotly.express as px
import json
import geopandas as gpd

# ---------- CONFIGURAÇÃO DO TEMA ----------
st.set_page_config(layout="wide", page_title="Mapa de Crimes RJ")

st.markdown(
    """
    <style>
    body { background-color: #FAFAFA; color: #333333; }
    .stButton>button { background-color: #F2C94C; color: #333333; }
    .stPlotlyChart { padding: 0px !important; }
    </style>
    """, unsafe_allow_html=True
)

# ---------- DADOS ----------
@st.cache_data
def carregar_dados():
    df = pd.read_csv("data/Base_Crimes_Com_Delegacia.csv", sep=";", encoding="utf-8-sig")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce")
    df["cisp"] = pd.to_numeric(df["cisp"], errors="coerce")
    geo = gpd.read_file("data/GeoJSON_Unidade_Territorial.geojson")
    return df, geo

df, geo = carregar_dados()

st.title("🔍 Análise Interativa de Criminalidade no Rio de Janeiro")

# ---------- FILTROS MAPA DE CALOR ----------
st.header("🗺️ Mapa de Calor por Unidade Territorial")
col1, col2, col3, col4 = st.columns(4)
with col1:
    tipo_crime_mapa = st.selectbox("Tipo de Crime (Mapa)", ["Todos"] + [
        'hom_doloso', 'lesao_corp_morte', 'latrocinio', 'estupro',
        'roubo_transeunte', 'roubo_veiculo', 'roubo_rua',
        'furto_veiculos', 'ameaca', 'pessoas_desaparecidas'
    ])
with col2:
    usar_taxa_mapa = st.checkbox("Exibir taxa por 10k hab. (Mapa)", value=True)
with col3:
    anos_mapa = sorted(df["ano"].dropna().unique())
    anos_sel_mapa = st.multiselect("Ano(s) (Mapa)", ["Todos"] + anos_mapa, default=[anos_mapa[-1]])
with col4:
    meses_mapa = sorted(df["mes"].dropna().unique())
    meses_sel_mapa = st.multiselect("Mês(es) (Mapa)", ["Todos"] + meses_mapa, default=[meses_mapa[-1]])

# ---------- PREPARAR DADOS MAPA ----------
df_mapa = df.copy()
if "Todos" not in anos_sel_mapa:
    df_mapa = df_mapa[df_mapa["ano"].isin(anos_sel_mapa)]
if "Todos" not in meses_sel_mapa:
    df_mapa = df_mapa[df_mapa["mes"].isin(meses_sel_mapa)]

if tipo_crime_mapa != "Todos":
    coluna_mapa = f"Taxa_{tipo_crime_mapa}_por_10k" if usar_taxa_mapa else tipo_crime_mapa
    df_mapa["valor"] = df_mapa[coluna_mapa]
else:
    df_mapa["valor"] = 0

agg_mapa = df_mapa.groupby("Unidade Territorial")["valor"].sum().reset_index()
geo_mapa = geo.merge(agg_mapa, on="Unidade Territorial", how="left")

fig = px.choropleth_mapbox(
    geo_mapa,
    geojson=geo_mapa.geometry,
    locations=geo_mapa.index,
    color="valor",
    mapbox_style="carto-positron",
    center={"lat": -22.9, "lon": -43.2},
    zoom=9.5,
    opacity=0.65,
    title=f"Mapa de {tipo_crime_mapa if tipo_crime_mapa != 'Todos' else 'Todos os Crimes'} por Unidade Territorial"
)
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

# ---------- DASHBOARD: RANKING POR UNIDADE ----------
st.header("📊 Ranking de Unidades Territoriais Mais Seguras")
col5, col6, col7 = st.columns(3)
with col5:
    tipo_crime_rank = st.selectbox("Tipo de Crime (Ranking)", ["Todos"] + [
        'hom_doloso', 'lesao_corp_morte', 'latrocinio', 'estupro',
        'roubo_transeunte', 'roubo_veiculo', 'roubo_rua',
        'furto_veiculos', 'ameaca', 'pessoas_desaparecidas'
    ])
with col6:
    usar_taxa_rank = st.checkbox("Exibir taxa por 10k hab. (Ranking)", value=True)
with col7:
    anos_rank = sorted(df["ano"].dropna().unique())
    anos_sel_rank = st.multiselect("Ano(s) (Ranking)", ["Todos"] + anos_rank, default=[anos_rank[-1]])

# ---------- PREPARAR DADOS RANKING ----------
df_rank = df.copy()
if "Todos" not in anos_sel_rank:
    df_rank = df_rank[df_rank["ano"].isin(anos_sel_rank)]

if tipo_crime_rank != "Todos":
    coluna_rank = f"Taxa_{tipo_crime_rank}_por_10k" if usar_taxa_rank else tipo_crime_rank
    df_rank["valor"] = df_rank[coluna_rank]
else:
    df_rank["valor"] = 0

ranking = df_rank.groupby("Unidade Territorial")["valor"].sum().reset_index().sort_values("valor", ascending=True)
fig_rank = px.bar(ranking.head(10), x="valor", y="Unidade Territorial", orientation="h",
                  title=f"Top 10 Unidades Mais Seguras ({tipo_crime_rank})")
fig_rank.update_layout(xaxis_title="Valor", yaxis_title="Unidade Territorial")
st.plotly_chart(fig_rank, use_container_width=True)

#
