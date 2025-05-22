import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from unidecode import unidecode

# Configuración de la página
st.set_page_config(layout="wide", page_title="Mapa de Mortalidad Materna en Costa Rica")

# Título
st.title("📊 Mortalidad Materna por Cantón (2017-2023)")

# --- 1. Cargar y limpiar datos ---
@st.cache_data
def load_data():
    # Cargar Excel y limpiar nombres de cantones
    df = pd.read_excel("df_merge.xlsx")
    df["canton"] = df["canton"].str.upper().apply(unidecode)
    return df

df = load_data()

# --- 2. Obtener datos geoespaciales ---
@st.cache_data
def get_geodata():
    url = "https://services.arcgis.com/LjCtRQt1uf8M6LGR/arcgis/rest/services/Cantones_CR/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
    gdf = gpd.read_file(url)
    gdf["NOM_CANT1"] = gdf["NOM_CANT1"].str.upper().apply(unidecode)  # Limpiar nombres para matching
    return gdf

gdf = get_geodata()

# --- 3. Sidebar con controles ---
st.sidebar.header("Filtros")
year = st.sidebar.selectbox("Año", options=sorted(df["year"].unique(), reverse=True)[:7])  # Últimos 7 años
metric = st.sidebar.radio("Métrica a visualizar", ["tasa_mortalidad_materna", "cantidad_defunciones_maternas"])

# Filtrar datos
df_filtered = df[df["year"] == year].dropna(subset=[metric])

# --- 4. Unir datos geoespaciales con estadísticas ---
gdf_merged = gdf.merge(
    df_filtered,
    left_on="NOM_CANT1",
    right_on="canton",
    how="left"
)

# --- 5. Crear mapa interactivo ---
col1, col2 = st.columns([3, 1])

with col1:
    # Mapa base centrado en Costa Rica
    m = folium.Map(location=[9.6, -84], zoom_start=7, tiles="CartoDB positron")

    # Capa coroplética
    folium.Choropleth(
        geo_data=gdf_merged,
        name="Choropleth",
        data=gdf_merged,
        columns=["NOM_CANT1", metric],
        key_on="feature.properties.NOM_CANT1",
        fill_color="YlOrRd" if metric == "tasa_mortalidad_materna" else "OrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Tasa de mortalidad materna" if metric == "tasa_mortalidad_materna" else "Defunciones maternas",
        highlight=True
    ).add_to(m)

    # Tooltips interactivos
    folium.features.GeoJson(
        gdf_merged,
        name="Labels",
        style_function=lambda x: {"color": "transparent", "fillColor": "transparent", "weight": 0},
        tooltip=folium.features.GeoJsonTooltip(
            fields=["NOM_CANT1", metric, "cantidad_nacimientos"],
            aliases=["Cantón", metric.replace("_", " ").title(), "Nacimientos"],
            localize=True
        )
    ).add_to(m)

    folium_static(m, width=800, height=600)

with col2:
    # Estadísticas resumidas
    st.metric("Año seleccionado", year)
    st.metric(
        "Tasa promedio" if metric == "tasa_mortalidad_materna" else "Total defunciones",
        f"{gdf_merged[metric].mean():.2f}" if metric == "tasa_mortalidad_materna" else int(gdf_merged[metric].sum())
    )
    
    # Top 5 cantones
    st.subheader(f"Top 5 {metric.replace('_', ' ')}")
    top_cantones = df_filtered.sort_values(metric, ascending=False).head(5)
    st.dataframe(top_cantones[["canton", metric]], hide_index=True)

# --- 6. Mostrar datos brutos ---
st.divider()
with st.expander("Ver datos completos"):
    st.dataframe(df_filtered.sort_values(metric, ascending=False))

# --- Instrucciones para requirements.txt ---
"""
En tu repositorio GitHub, crea también un archivo requirements.txt con:
streamlit
pandas
geopandas
folium
streamlit-folium
unidecode
"""
