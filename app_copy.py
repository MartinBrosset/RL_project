import pandas as pd
import pandas as pd
import folium
import matplotlib.pyplot as plt
import numpy as np
from folium.plugins import HeatMapWithTime, HeatMap
import pickle
import streamlit as st
from streamlit_folium import st_folium
from streamlit_folium import folium_static
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import plotly.express as px




st.set_page_config(
    page_title="NYC Check-ins analysis",
    page_icon="🔎",
    layout="wide"
)

@st.cache_data
def load_data_temporal(vue):
    if vue == 'Daily vision':
        fichier_pickle = "ny_per_hour.pickle"
    else:  # vue == 'Weekly vision'
        fichier_pickle = "ny_per_dow.pickle"

    with open(fichier_pickle, "rb") as fichier:
        data = pickle.load(fichier)

    m = folium.Map([40.73, -73.94], tiles="CartoDB Positron", zoom_start=11, scrollWheelZoom=False)

    ny_uni = pd.read_csv('newyork_uni.csv')
    text_analysis = {'School':{'Daily vision':'Here we see the pike around 8AM which corresponds to the opening of the school buildings. After 6PM the schools start to close and the visits frequency drop.',
                        'Weekly vision': 'The schools are less frequencted the week-end where students take a break'},
                'Night Club': {'Daily vision':'The nightclubs are active during the night, with a gradual increase up to midnight and a quick decrease.',
                                'Weekly vision': 'The nightclubs are getting crowded at the end of the week when the New-Yorkers need a break from their stressful week.'},
                'Shopping': {'Daily vision':'The shopping venues are getting more and more visited untill 6PM, after that the visits decrease strongly',
                                'Weekly vision': 'The New-Yorkers are pretty constant when it comes to shopping, the venues visits are pretty stable.'},
                'Restaurant': {'Daily vision':'The Ney-Yorkers eat all day long but we observe 3 pikes : the breakfast one around 9AM and then lunch and diner respectively around 1PM and 7PM',
                                'Weekly vision': 'The New-Yorkers are pretty constant when it comes to restaurants visits, but we can see a slight increase over the week and then a decrase on Sunday. The New-Yorkers appear to eat more at home on this special day.'},
                }
    
    repartition = {}
    types = list(data.keys())
    periods = list(data[types[0]].keys())

    # for period in periods:
    #     repartition[period] = {}
    #     for type_ in types:
    #         repartition[period][type_] = len(data[type_][period])

    repartition = pd.DataFrame(columns=['Place', 'period', 'checkins'])
    types = list(data.keys())
    periods = list(data[types[0]].keys())
    for type_ in types:
        for period in periods:
            repartition = pd.concat([repartition, pd.DataFrame({'Place': [type_], 'period': [period], 'checkins': len(data[type_][period])})])

    return data, m, ny_uni, text_analysis, repartition


@st.cache_data
def load_data_geo():
    ny_uni = pd.read_csv('newyork_uni.csv')
    nybb = gpd.read_file("neighborhoods.geojson")
    m = folium.Map([40.73, -73.94], tiles="CartoDB Positron", zoom_start=11, scrollWheelZoom=False)
    ny_gdf_neighborhoods = pd.read_csv('newyork_df.csv')
    
    data = pd.DataFrame(nybb["ntaname"])

    # Nightclub
    nightclub_df = ny_gdf_neighborhoods[ny_gdf_neighborhoods["Category"] == "NightClub"]
    nightclub_counts = nightclub_df.groupby("ntaname").size().reset_index(name="Night Club").sort_values(by='Night Club', ascending=False)
    data = pd.merge(data, nightclub_counts, on='ntaname', how='left').fillna(0)

    # Restaurant
    resto_df = ny_gdf_neighborhoods[ny_gdf_neighborhoods["Category"] == "Restaurant"]
    resto_counts = resto_df.groupby("ntaname").size().reset_index(name="Restaurant").sort_values(by='Restaurant', ascending=False)
    data = pd.merge(data, resto_counts, on='ntaname', how='left').fillna(0)

    # Shopping
    shop_df = ny_gdf_neighborhoods[ny_gdf_neighborhoods["Category"] == "Shopping"]
    shop_counts = shop_df.groupby("ntaname").size().reset_index(name="Shopping").sort_values(by='Shopping', ascending=False)
    data = pd.merge(data, shop_counts, on='ntaname', how='left').fillna(0)

    # School
    school_df = ny_gdf_neighborhoods[ny_gdf_neighborhoods["Category"] == "School"]
    school_counts = school_df.groupby("ntaname").size().reset_index(name="School").sort_values(by='School', ascending=False)
    data = pd.merge(data, school_counts, on='ntaname', how='left').fillna(0)

    data = pd.merge(nybb[['ntaname', 'geometry']], data, on='ntaname', how='inner')

    return m, nybb, data, ny_uni


def plot_pie_chart(hour, repartition):
    data = repartition[hour]
    labels = list(data.keys())
    values = list(data.values())
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.update_layout(showlegend=True)
    
    return fig



st.title('New York City Check-Ins Analysis')
st.write("")

analysis = st.sidebar.selectbox(
    'Select the analysis',
    ('Temporal analysis', 'Geographical analysis'), key="disabled")

if analysis == "Temporal analysis":

    col1, col2 = st.columns(2)

    vue_choisie = st.sidebar.radio("Select the analysis temporality", ('Daily vision', 'Weekly vision'))

    data, m, ny_uni, text_analysis, repartition = load_data_temporal(vue_choisie)

    elements = ['School', 'Restaurant', 'Shopping', 'Night Club']
    valeur_selectionnee = st.sidebar.radio("Select the establishement type", elements)

    

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

    if vue_choisie == 'Daily vision':
        indexx = [str(hour) + "h" for hour in data[valeur_selectionnee].keys()]
    else:  
        indexx = [dow for dow in data[valeur_selectionnee].keys()]


    hm = HeatMapWithTime(data=list(data[valeur_selectionnee].values()),
                        index=indexx, 
                        radius=6,
                        blur=1,
                        auto_play=True,
                        max_speed=3,
                        min_speed=0.5,
                        max_opacity=0.5,
                        position='bottomright')
    hm.add_to(m)

    with col1:
        st.markdown(f"### <center> Geographical view of the visits to {valeur_selectionnee.lower()}s over time with a {vue_choisie.lower()}</center>", unsafe_allow_html=True)
        folium_static(m, width=500)

    with col2:
        st.markdown(f"### <center> Aggregated view of the visits with a {vue_choisie.lower()}</center>", unsafe_allow_html=True)

        if valeur_selectionnee in data:
            keys = list(data[valeur_selectionnee].keys())
            frequences = [len(data[valeur_selectionnee][key]) for key in keys]
            total_check_ins = sum(frequences)

            if total_check_ins > 0:
                frequences = [freq / total_check_ins for freq in frequences]

            fig = go.Figure(go.Bar(x=keys, y=frequences))

            if vue_choisie == 'Daily vision':
                fig.update_layout(xaxis_title='Hour of the day')
            else:  # 'Weekly vision'
                fig.update_layout(xaxis_title='Day of the week')

            fig.update_layout(yaxis_title='Visits frequency (%)',
                            title=f'When do New Yorker visit {valeur_selectionnee}s ?',
                            xaxis=dict(tickangle=45),
                            yaxis_tickformat=",.0%",
                            width=800,
                            height=500)
            fig.update_layout(title=dict(x=0.33))
            fig.update_layout(width=850, height=600)
            st.plotly_chart(fig)

        st.markdown(f"{text_analysis[valeur_selectionnee][vue_choisie]}", unsafe_allow_html=True)

    # # Add the pie chart
    # if vue_choisie == 'Daily vision':
    #     selected_hour = st.slider('Select Hour:', min_value=0, max_value=23, value=12, step=1)
    #     st.markdown(f"### Check-Ins Distribution by Place Type at {selected_hour}h")
    #     st.plotly_chart(plot_pie_chart(selected_hour, repartition))
    
    # else:
    #     days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    #     selected_day_n = st.slider('Select Day:', min_value=1, max_value=7, value=1, step=1)
    #     selected_day = days[selected_day_n - 1]
    #     st.markdown(f"### Check-Ins Distribution by Place Type on {selected_day}")
    #     st.plotly_chart(plot_pie_chart(selected_day, repartition))

    # Stacked line plot
    fig = px.area(repartition, x="period", y="checkins", color="Place", line_group="Place")

    if vue_choisie == 'Daily vision':
        st.markdown(f"### Number of check-ins by establishment over time")
        fig.update_layout(xaxis_title='Hour of the day', yaxis_title='Number of check-ins', title = 'How does the city that never sleeps live ?')
        st.plotly_chart(fig)
    elif vue_choisie == 'Weekly vision':
        st.markdown(f"<h2 style='text-align: center;'>### Number of check-ins by establishment over time</h2>", unsafe_allow_html=True)
        fig.update_layout(xaxis_title='Day of the week', yaxis_title='Number of check-ins', title = 'How does the city that never sleeps live ?')
        st.plotly_chart(fig, use_container_width=True)  

elif analysis == 'Geographical analysis':
    
    m, nybb, data, ny_uni = load_data_geo()

    col1, col2 = st.columns(2)

    elements = ['School', 'Restaurant', 'Shopping', 'Night Club']
    valeur_selectionnee = st.sidebar.radio("Select the establishement type", elements)

    data_selected = data[["ntaname", "geometry", valeur_selectionnee]]

    folium.Choropleth(
        geo_data=data_selected,
        name='choropleth',
        data=data_selected,
        columns=['ntaname', valeur_selectionnee],
        key_on='feature.properties.ntaname',
        fill_color='plasma_r',  # Utiliser un dégradé de couleur de jaune à bleu
        fill_opacity=0.7,
        line_opacity=0.4,
        legend_name=f'Number of {valeur_selectionnee.lower()} check-ins by neighborhood.',
        bins=50,
        highlight=True,

    ).add_to(m)

    feature = folium.features.GeoJson(
                data=data_selected,
                name='North Carolina',
                smooth_factor=2,
                style_function=lambda x: {'color':'black','fillColor':'transparent','weight':0.5},
                tooltip=folium.features.GeoJsonTooltip(
                    fields=['ntaname',
                            valeur_selectionnee],
                    aliases=["NTA :",
                                'Number of check-ins:'], 
                    localize=True,
                    sticky=False,
                    labels=True,
                    style="""
                        background-color: #F0EFEF;
                        border: 2px solid black;
                        border-radius: 3px;
                        box-shadow: 3px;
                    """,
                    max_width=800,),
                        highlight_function=lambda x: {'weight':3,'fillColor':'grey'},
                    ).add_to(m)    

    if valeur_selectionnee == "School":

        for lat, lng, name in zip(ny_uni['Latitude'], ny_uni['Longitude'], ny_uni["NAME"]):
            folium.CircleMarker(
            [lat, lng],
            radius=3,
            tooltip=name,
            color='blue',
            fill=True,
            weight=7,
            fill_color='black',
            fill_opacity=0.75,
            opacity=0,
            parse_html=False).add_to(m)

    fig = px.bar(data_selected.sort_values(by=valeur_selectionnee, ascending=False).head(10), x='ntaname', y=valeur_selectionnee, title = " ", labels={valeur_selectionnee: 'Count', 'ntaname': 'Neighborhood'})
    fig.update_layout(title=dict(x=0.25))

    top_nb = data_selected.sort_values(by=valeur_selectionnee, ascending=False).head(10).index
    repartition = {}
    for nb in top_nb:
        repartition[data.iloc[nb]['ntaname']] = {'School': data.iloc[nb]['School'],
                                                'Restaurant': data.iloc[nb]['Restaurant'],
                                                'Shopping': data.iloc[nb]['Shopping'],
                                                'Night Club': data.iloc[nb]['Night Club']}

    with col1:
        st.markdown(f"### <center> Neighboorhod frequentation of {valeur_selectionnee.lower()}s </center>", unsafe_allow_html=True)
        folium_static(m, 500)
        text_analysis2 = {'School': "The most visited neighbordhoods are the ones with schools (represented by black dots) in them. \n Center of Manhattan and Downtown Brooklyn are the area that receive the most students.",
                         'Night Club': "The West Manhattan wins the palm of merrymakers. These neighborhoods are known to be the place to be to celebrate something." ,
                         'Shopping': "It is no surprise that center Manhattan is the shopping spree of New York, especially the Time-Square which is known for its many shops that make tourists turn their heads.",
                         'Restaurant': "The whole south of the Manhattan island appears to be the home of many restaurants."}
        st.markdown(text_analysis2[valeur_selectionnee])

    with col2:
        st.markdown(f'### <center> Top 10 Most Frequented Neighborhoods For {valeur_selectionnee}s </center>', unsafe_allow_html=True)
        fig.update_layout(width=850, height=650)
        st.plotly_chart(fig, use_container_width=True)

    n = st.slider('Select the top n neighborhood :', min_value=1, max_value=10, value=1, step=1)
    selected_nb = data.iloc[top_nb[n-1]]['ntaname']
    st.markdown(f"<h2 style='text-align: center;'>Check-Ins Distribution by Place Type in {selected_nb}</h2>", unsafe_allow_html=True)
    st.plotly_chart(plot_pie_chart(selected_nb, repartition), use_container_width=True)