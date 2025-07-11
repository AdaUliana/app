import streamlit as st
import pandas as pd
import plotly.express as px
import json
import geopandas as gpd

# ---------- CONFIGURAÇÃO DO TEMA ----------
st.set_page_config(layout="wide", page_title="MAPA DE CRIMES RJ")

st.markdown(
    """
    <style>
    h1, h2, h3, .stTitle, .stHeader {
        color: #F2C94C !important;
        text-align: center !important;
    }
    .stButton>button {
        background-color: #F2C94C;
        color: #2C2C2C;
    }
    .stPlotlyChart { padding: 0px !important; }
    </style>
    """,
    unsafe_allow_html=True
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

st.title("🔍 MAPA DE CRIMES RJ")

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
geo_mapa["label"] = geo_mapa["Unidade Territorial"] + "<br>" + geo_mapa["valor"].round(2).astype(str) + " ocorrências por 10k hab."

fig = px.choropleth_mapbox(
    geo_mapa,
    geojson=geo_mapa.geometry,
    locations=geo_mapa.index,
    color="valor",
    mapbox_style="carto-positron",
    center={"lat": -22.9, "lon": -43.2},
    zoom=9.5,
    opacity=0.65,
    title=f"Mapa de {tipo_crime_mapa if tipo_crime_mapa != 'Todos' else 'Todos os Crimes'} por Unidade Territorial",
    hover_name="label",
    color_continuous_scale="Reds"
)
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

# ---------- DASHBOARD: RANKING SEGUINDO MAPA DE CALOR ----------
st.header("📊 Top 5 Unidades com Maior Número de Ocorrências")
ranking_mapa = df_mapa.groupby("Unidade Territorial")["valor"].sum().reset_index().sort_values("valor", ascending=False)
fig_rank_top5 = px.bar(
    ranking_mapa.head(5),
    x="valor", y="Unidade Territorial", orientation="h",
    title=f"Top 5 Unidades com Maior Número de Ocorrências ({tipo_crime_mapa})",
    color_discrete_sequence=["#F2C94C"]
)
fig_rank_top5.update_layout(
    xaxis_title="Valor", 
    yaxis_title="Unidade Territorial"
)
st.plotly_chart(fig_rank_top5, use_container_width=True)

# ---------- EXPORTAÇÃO ----------
st.subheader("📤 Exportar dados filtrados")
@st.cache_data
def converter_para_csv(df):
    return df.to_csv(index=False).encode("utf-8-sig")

csv_data = converter_para_csv(df_mapa)
st.download_button(
    label="⬇️ Baixar dados filtrados como CSV",
    data=csv_data,
    file_name="dados_filtrados.csv",
    mime="text/csv"
)

# ---------- GLOSSÁRIO ----------
st.header("ℹ️ Glossário e Explicações dos Indicadores")

with st.expander("📌 Taxa por 10 mil habitantes"):
    st.markdown("""
    Este indicador representa a quantidade de ocorrências de um determinado tipo de crime a cada 10.000 habitantes na área analisada.

    **Fórmula:**  
    `taxa = (número de ocorrências / população) * 10.000`

    Esse cálculo permite comparar áreas de diferentes tamanhos populacionais de forma proporcional.
    """)

with st.expander("🚨 Tipos de crime analisados"):
    st.markdown("""
    - **Homicídio doloso**: Quando há intenção de matar.
    - **Lesão corporal seguida de morte**: Agressão que resulta em morte.
    - **Latrocínio**: Roubo seguido de morte.
    - **Estupro**: Violação sexual sem consentimento.
    - **Roubo a transeunte**: Roubo cometido contra pedestres.
    - **Roubo de veículo**: Subtração de veículos com uso de violência ou ameaça.
    - **Roubo de rua**: Inclui roubo de celular, bolsa, entre outros em via pública.
    - **Furto de veículos**: Subtração sem violência.
    - **Ameaça**: Ato de intimidar alguém verbalmente ou fisicamente.
    - **Pessoas desaparecidas**: Casos registrados de sumiço sem paradeiro conhecido.
    """)

with st.expander("🏙️ Unidade Territorial"):
    st.markdown("""
    Agrupamento de bairros com base na área de cobertura de uma Delegacia de Polícia (CISP).  
    Utilizada para representar espacialmente a jurisdição policial nos mapas.
    """)
