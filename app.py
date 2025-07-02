import streamlit as st
import pandas as pd
import plotly.express as px
import json

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
    with open("data/Limite_de_Bairros_Completo_Com_CISP.geojson", "r", encoding="utf-8") as f:
        geojson = json.load(f)
    return df, geojson

df, geojson = carregar_dados()

# ---------- EXTRAIR BAIRROS DO GEOJSON ----------
bairros_geojson = sorted({f["properties"].get("bairro") for f in geojson["features"] if f["properties"].get("bairro")})

st.title("🔍 Análise Interativa de Criminalidade no Rio de Janeiro")

# ---------- FILTROS MAPA DE CALOR ----------
st.header("🗺️ Mapa de Calor por Bairro")
col1, col2, col3, col4 = st.columns(4)
with col1:
    tipo_crime_mapa = st.selectbox("Tipo de Crime (Mapa)", [
        'hom_doloso', 'lesao_corp_morte', 'latrocinio', 'estupro',
        'roubo_transeunte', 'roubo_veiculo', 'roubo_rua',
        'furto_veiculos', 'ameaca', 'pessoas_desaparecidas'
    ])
with col2:
    usar_taxa_mapa = st.checkbox("Exibir taxa por 10k hab. (Mapa)", value=True)
with col3:
    anos_mapa = sorted(df["ano"].dropna().unique())
    anos_sel_mapa = st.multiselect("Ano(s) (Mapa)", anos_mapa, default=[anos_mapa[-1]])
with col4:
    meses_mapa = sorted(df["mes"].dropna().unique())
    meses_sel_mapa = st.multiselect("Mês(es) (Mapa)", meses_mapa, default=[meses_mapa[-1]])

coluna_mapa = f"Taxa_{tipo_crime_mapa}_por_10k" if usar_taxa_mapa else tipo_crime_mapa
df_mapa = df[df["ano"].isin(anos_sel_mapa) & df["mes"].isin(meses_sel_mapa)].copy()
df_mapa["valor"] = df_mapa[coluna_mapa]

# Agregar por Unidade Territorial para aplicar aos bairros
agg_bairro = df_mapa.groupby("Unidade Territorial")["valor"].sum().reset_index()

# Atribuir valores aos bairros do GeoJSON
for f in geojson["features"]:
    unidade = f["properties"].get("unidade_territorial")
    val = agg_bairro.loc[agg_bairro["Unidade Territorial"] == unidade, "valor"]
    f["properties"]["valor"] = float(val.values[0]) if not val.empty else None

fig = px.choropleth_mapbox(
    geojson=geojson,
    data_frame=agg_bairro,
    locations="Unidade Territorial",
    featureidkey="properties.unidade_territorial",
    color="valor",
    mapbox_style="carto-positron",
    center={"lat": -22.9, "lon": -43.2},
    zoom=9.5,
    opacity=0.65,
    title=f"Mapa de {coluna_mapa.replace('_', ' ').title()} por Bairro"
)
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

# ---------- DASHBOARD: RANKING POR BAIRRO ----------
st.header("📊 Ranking de Bairros Mais Seguros")
col5, col6, col7, col8 = st.columns(4)
with col5:
    tipo_crime_rank = st.selectbox("Tipo de Crime (Ranking)", [
        'hom_doloso', 'lesao_corp_morte', 'latrocinio', 'estupro',
        'roubo_transeunte', 'roubo_veiculo', 'roubo_rua',
        'furto_veiculos', 'ameaca', 'pessoas_desaparecidas'
    ])
with col6:
    usar_taxa_rank = st.checkbox("Exibir taxa por 10k hab. (Ranking)", value=True)
with col7:
    anos_rank = sorted(df["ano"].dropna().unique())
    anos_sel_rank = st.multiselect("Ano(s) (Ranking)", anos_rank, default=[anos_rank[-1]])

coluna_rank = f"Taxa_{tipo_crime_rank}_por_10k" if usar_taxa_rank else tipo_crime_rank
df_rank = df[df["ano"].isin(anos_sel_rank)].copy()
df_rank["valor"] = df_rank[coluna_rank]

if "bairro" in df_rank.columns:
    ranking = df_rank.groupby(["bairro"])["valor"].sum().reset_index().sort_values("valor", ascending=True)
    fig_rank = px.bar(ranking.head(10), x="valor", y="bairro", orientation="h",
                      title=f"Top 10 Bairros Mais Seguros ({coluna_rank})")
    fig_rank.update_layout(xaxis_title="Valor", yaxis_title="Bairro")
    st.plotly_chart(fig_rank, use_container_width=True)
else:
    st.warning("A base não contém a coluna 'bairro'. Certifique-se de incluí-la para rankings por bairro.")
