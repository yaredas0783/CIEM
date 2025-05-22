import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

# Título de la app
st.title("Mapa de Mortalidad Materna en Costa Rica")

# Cargar datos
@st.cache_data
def cargar_geojson():
    return gpd.read_file("costaricacantonesv10.geojson")

@st.cache_data
def cargar_excel():
    return pd.read_excel("df_merge.xlsx")

gdf = cargar_geojson()
df = cargar_excel()

# Filtrar años desde 2017
df = df[df['year'] >= 2017]

# Mostrar selección de año
anios_disponibles = sorted(df['year'].unique())
anio_seleccionado = st.selectbox("Selecciona un año", anios_disponibles)

# Filtrar dataframe según año seleccionado
df_filtrado = df[df['year'] == anio_seleccionado]

# Unir DataFrame con GeoDataFrame
gdf_merged = gdf.merge(df_filtrado, how="left", left_on="NAME_2", right_on="canton")

# Crear mapa centrado en Costa Rica
m = folium.Map(location=[9.7489, -83.7534], zoom_start=8)

# Definir la función de color según tasa de mortalidad materna
def color_por_tasa(tasa):
    if pd.isnull(tasa):
        return 'gray'
    elif tasa == 0:
        return 'green'
    elif tasa < 20:
        return 'orange'
    else:
        return 'red'

# Agregar polígonos al mapa
for _, row in gdf_merged.iterrows():
    color = color_por_tasa(row['tasa_mortalidad_materna'])
    folium.GeoJson(
        row['geometry'],
        style_function=lambda feature, color=color: {
            'fillColor': color,
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.5
        },
        tooltip=folium.Tooltip(f"""
            <strong>Cantón:</strong> {row['NAME_2']}<br>
            <strong>Tasa Mortalidad Materna:</strong> {row['tasa_mortalidad_materna']}<br>
            <strong>Defunciones Maternas:</strong> {row['cantidad_defunciones_maternas']}
        """)
    ).add_to(m)

# Mostrar mapa en Streamlit
st_folium(m, width=800, height=600)
