import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import requests
import unidecode

# --------- Configuración de la página ----------
st.set_page_config(page_title="Mapa de Mortalidad Materna en Costa Rica", layout="wide")

st.title("📊 Mapa de Mortalidad Materna en Costa Rica por Cantón")

# --------- Cargar datos ---------
@st.cache_data
def cargar_datos():
    # Leer el Excel desde el archivo en el repositorio
    df = pd.read_excel("df_merge.xlsx")

    # Normalizar la columna 'canton'
    df['canton'] = df['canton'].apply(lambda x: unidecode.unidecode(str(x)).upper())

    return df

df = cargar_datos()

# --------- Cargar GeoJSON ---------
@st.cache_data
def cargar_geojson():
    url = "https://services.arcgis.com/LjCtRQt1uf8M6LGR/arcgis/rest/services/Cantones_CR/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
    response = requests.get(url)
    geojson_data = response.json()
    return geojson_data

geojson_data = cargar_geojson()

# --------- Interfaz de usuario ---------
años_disponibles = sorted(df['year'].unique())
año_seleccionado = st.selectbox("Selecciona el año:", años_disponibles)

# Filtrar el dataframe por año seleccionado
df_filtrado = df[df['year'] == año_seleccionado]

# --------- Crear el mapa ---------
m = folium.Map(location=[9.7489, -83.7534], zoom_start=8)

# Añadir los polígonos de los cantones
folium.Choropleth(
    geo_data=geojson_data,
    name="Tasa Mortalidad Materna",
    data=df_filtrado,
    columns=["canton", "tasa_mortalidad_materna"],
    key_on="feature.attributes.NOM_CANTON",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Tasa Mortalidad Materna",
    nan_fill_color="lightgray"
).add_to(m)

# Añadir tooltips con información adicional
for feature in geojson_data['features']:
    canton_nombre = unidecode.unidecode(feature['attributes']['NOM_CANTON']).upper()
    datos_canton = df_filtrado[df_filtrado['canton'] == canton_nombre]

    if not datos_canton.empty:
        tasa = datos_canton.iloc[0]['tasa_mortalidad_materna']
        defunciones = datos_canton.iloc[0]['cantidad_defunciones_maternas']
        popup_text = f"<b>{canton_nombre}</b><br>Tasa Mortalidad: {tasa}<br>Defunciones: {defunciones}"
    else:
        popup_text = f"<b>{canton_nombre}</b><br>Sin datos"

    folium.GeoJson(
        feature,
        tooltip=folium.Tooltip(popup_text)
    ).add_to(m)

# Mostrar mapa en Streamlit
st_folium(m, width=900, height=600)
