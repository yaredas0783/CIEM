import streamlit as st
import pandas as pd
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
    df = pd.read_excel("df_merge.xlsx")
    df['canton'] = df['canton'].astype(str).apply(lambda x: unidecode.unidecode(x).upper())
    return df

# Cargar DataFrame
df = cargar_datos()

# --------- Cargar y transformar GeoJSON de ArcGIS ---------
@st.cache_data
def cargar_geojson():
    url = (
        "https://services.arcgis.com/LjCtRQt1uf8M6LGR/arcgis/rest/services/"
        "Cantones_CR/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
    )
    resp = requests.get(url)
    arcgis = resp.json()
    features = []
    for feat in arcgis.get('features', []):
        geom = feat.get('geometry')
        props = feat.get('attributes')
        feature = {
            'type': 'Feature',
            'geometry': geom,
            'properties': props,
        }
        features.append(feature)
    geojson = {'type': 'FeatureCollection', 'features': features}
    return geojson

# Cargar GeoJSON
geojson_data = cargar_geojson()

# --------- Interfaz de usuario ---------
años = sorted(df['year'].unique())
año_sel = st.selectbox("Selecciona el año:", años)

df_f = df[df['year'] == año_sel]

# --------- Crear el mapa ---------
m = folium.Map(location=[9.7489, -83.7534], zoom_start=8)

# Choropleth para tasa de mortalidad
folium.Choropleth(
    geo_data=geojson_data,
    name="Tasa Mortalidad Materna",
    data=df_f,
    columns=["canton", "tasa_mortalidad_materna"],
    key_on="feature.properties.NOM_CANTON",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Tasa Mortalidad Materna",
    nan_fill_color="lightgray"
).add_to(m)

# Añadir tooltips con tasa y defunciones
for feat in geojson_data['features']:
    props = feat['properties']
    nombre = unidecode.unidecode(str(props.get('NOM_CANTON', ''))).upper()
    datos = df_f[df_f['canton'] == nombre]
    if not datos.empty:
        tasa = datos.iloc[0]['tasa_mortalidad_materna']
        defs = datos.iloc[0]['cantidad_defunciones_maternas']
        popup = f"<b>{nombre}</b><br>Tasa: {tasa}<br>Defunciones: {defs}"
    else:
        popup = f"<b>{nombre}</b><br>Sin datos"
    folium.GeoJson(
        feat,
        style_function=lambda x: {'fillOpacity': 0, 'weight': 0},
        tooltip=folium.Tooltip(popup)
    ).add_to(m)

# Mostrar el mapa
st_folium(m, width=900, height=600)
