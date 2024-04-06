import pandas as pd
import pandas as pd
import folium
import numpy as np
from folium.plugins import HeatMapWithTime, HeatMap
import pickle
import streamlit as st
from streamlit_folium import st_folium
from streamlit_folium import folium_static


st.set_page_config(
    page_title="st_folium Example",
    page_icon="🔎",
    layout="wide"
)

st.title('New York City Check-Ins Analysis')

@st.cache_data()
def charger_donnees():
    ny_gdf_neighborhoods = pd.read_csv('newyork_df.csv') 
    ny_uni = pd.read_csv('newyork_uni.csv') 
    with open("ny_per_hour.pickle", "rb") as fichier:
        data = pickle.load(fichier)

    m = folium.Map([40.73, -73.94], tiles="CartoDB Positron",
               zoom_start=11, scrollWheelZoom=False)

    return data, m, ny_uni



data, m, ny_uni = charger_donnees()


elements = ['School', 'Restaurant', 'Shopping', 'Night Club']
valeur_selectionnee = st.sidebar.radio("Select", elements)
st.write('Selected :', valeur_selectionnee)


if valeur_selectionnee == "School":

    for lat, lng, name in zip(ny_uni['Latitude'], ny_uni['Longitude'], ny_uni["NAME"]):
        folium.CircleMarker(
        [lat, lng],
        radius=2,
        tooltip=name,
        color='blue',
        fill=True,
        weight=7,
        fill_color='black',
        fill_opacity=0.75,
        opacity=0,
        parse_html=False).add_to(m)


hm = HeatMapWithTime(data=list(data[valeur_selectionnee].values()),
                     index=[str(hour) + "h" for hour in data[valeur_selectionnee].keys()], 
                     radius=6,
                     blur=1,
                     auto_play=True,
                     max_speed=3,
                     min_speed=0.5,
                     max_opacity=1,
                     position='bottomright')
hm.add_to(m)


folium_static(m)
