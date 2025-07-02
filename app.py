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

# ---------- SIDEBAR DE FILTROS ----------
st.title("🔍 Análise Interativa de Criminalidade no Rio de Janeiro")

col1, col2, col3, col4 = st.columns(4)
with col1:
    tipo_crime = st.selectbox("Tipo de Crime", [
        'hom_doloso', 'lesao_corp_morte', 'latrocinio', 'estupro',
        'roubo_transeunte', 'roubo_veiculo', 'roubo_rua',
        'furto_veiculos', 'ameaca', 'pessoas_desaparecidas'
    ])
with col2:
    usar_taxa = st.checkbox("Exibir taxa por 10k hab.", value=True)
with col3:
    anos = sorted(df["ano"].dropna().unique())
    anos_selecionados = st.multiselect("Ano(s)", anos, default=[anos[-1]])
with col4:
    meses = sorted(df["mes"].dropna().unique())
    meses_selecionados = st.multiselect("Mês(es)", meses, default=[meses[-1]])

bairros = ["Todos"] + sorted(df["bairro"].dropna().unique())
bairro = st.selectbox("Bairro (opcional)", bairros)

# ---------- FILTRAGEM ----------
coluna = f"Taxa_{tipo_crime}_por_10k" if usar_taxa else tipo_crime
df_filt = df[df["ano"].isin(anos_selecionados) & df["mes"].isin(meses_selecionados)].copy()
if bairro != "Todos":
    df_filt = df_filt[df_filt["bairro"] == bairro]

# ---------- AGREGAÇÃO ----------
df_filt["total"] = df_filt[coluna]
agg = df_filt.groupby("cisp")["total"].sum().reset_index()
agg["cisp"] = agg["cisp"].astype(str)

# ---------- APLICAR AO GEOJSON ----------
for f in geojson["features"]:
    cisp_codigo = str(f["properties"].get("CISP"))
    taxa = agg.loc[agg["cisp"] == cisp_codigo, "total"]
    f["properties"]["total"] = float(taxa.values[0]) if not taxa.empty else None

# ---------- MAPA ----------
if not df_filt.empty:
    titulo = f"{coluna.replace('_', ' ').title()} – {', '.join(map(str, meses_selecionados))}/{', '.join(map(str, anos_selecionados))}"
    fig = px.choropleth_mapbox(
        geojson=geojson,
        data_frame=agg,
        locations="cisp",
        featureidkey="properties.CISP",
        color="total",
        mapbox_style="carto-positron",
        center={"lat": -22.9, "lon": -43.2},
        zoom=9.5,
        opacity=0.65,
        title=titulo
    )
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nenhum dado disponível para os filtros selecionados.")
