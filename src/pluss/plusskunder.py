# -*- coding: utf-8 -*-
"""
@author: christsa
"""
# Import external libraries
import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# config
st.set_page_config(layout='wide', initial_sidebar_state="collapsed")
pd.options.display.float_format = '{:,.2f}'.format
elh_colors = ["#006600", '#F2E500', '#785F4B', '#005886', '#c2e9c4']
month_names = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
reduce_header_height_style = """
    <style>
        div.block-container {padding-top:1rem;}
    </style>
"""
st.markdown(reduce_header_height_style, unsafe_allow_html=True)

# functions
# can be cached if wanted
def load_data() -> pd.DataFrame():
    ''' load needed data for current page '''
    _df = pd.read_csv('data/solar.csv')
    _map = pd.read_csv('data/mapping/postKODE_postSTED.csv', sep=';')

    _df['valid_from'] = pd.to_datetime(_df['valid_from'], utc=True).dt.tz_convert('Europe/Oslo')
    _df['valid_to'] = pd.to_datetime(_df['valid_to'], utc=True, errors='coerce').dt.tz_convert('Europe/Oslo')
    _df = _df.merge(_map, left_on='postal_code', right_on='Postnummer')

    return _df

# uncached function
def monthify(_df, col: str) -> pd.DataFrame:
    ''' extracting monthly installed units & capacity, with a yearly sum '''
    _monthly_open = _df[col].groupby([_df['valid_from'].dt.year, _df['valid_from'].dt.month]).count().unstack()
    _monthly_close = _df[col].groupby([_df['valid_to'].dt.year, _df['valid_to'].dt.month]).count().unstack()
    _monthly = _monthly_open - _monthly_close
    _monthly['sum'] = _monthly.sum(axis=1)
    _monthly['cumsum'] = _monthly['sum'].cumsum()
    _monthly.index = _monthly.index.astype(int)
    return _monthly

# loading data
df = load_data()
inst_monthly = monthify(df, 'mtr_pt_id')[2:]
cap_monthly = monthify(df, 'mtr_pt_installed_capacity')[2:]/100

with st.container():
    st.subheader('Plusskundeinstallasjoner')
    st.markdown('Hvor mange installasjoner er det, og hva kan de potensielt produsere?')
    st.info('Klikk på valg i menyen til høyre for å vise/fjerne. Dobbelklikk på et valg for å vise alene.')
    tab1, tab2, tab3 = st.tabs(['Graf', 'Tabell antall', 'Tabell effekt'])

    with tab1:
        # plotting in a subplot to achieve double y-axis
        fig = make_subplots(specs=[[{'secondary_y': True}]])
        fig.add_trace(
            go.Scatter(x=inst_monthly.index, y=inst_monthly['sum'], name='Nye anlegg',
            line=go.scatter.Line(color=elh_colors[0])),
            secondary_y=False)
        fig.add_trace(
            go.Scatter(x=cap_monthly.index, y=cap_monthly['cumsum'], name='Installert effekt',
            line=go.scatter.Line(color=elh_colors[3])),
            secondary_y=True)
        fig.add_bar(x=inst_monthly.index, y=inst_monthly['cumsum'], name='Total anlegg',
                    marker={'color': elh_colors[-1]})
        fig.update_layout(title='Plusskundeinstallasjoner i Norge',
            legend=dict(
                bgcolor='#f0f2f6',
                bordercolor='black'
                ),
                paper_bgcolor='rgb(209,232,250)',
                plot_bgcolor='#f0f2f6'
                )
        fig.update_xaxes(title_text='År')
        fig.update_yaxes(title_text='Antall', secondary_y=False)
        fig.update_yaxes(title_text='Installert effekt MW', secondary_y=True)

        st.plotly_chart(fig, use_container_width=True)
        st.caption('Merk at installert effekt ikke er kvalitetssikret.')

    with tab2:
        st.write('Tabell, interaktiv. Her kan vi rydde i data som vi ønsker')
        st.dataframe(inst_monthly.fillna(0).astype(int), use_container_width=True)

    with tab3:
        st.write('Tabell, interaktiv. Her kan vi rydde i data som vi ønsker')
        st.dataframe(cap_monthly.fillna(0).astype(int), use_container_width=True)
        
with st.container():
    st.subheader('Detaljer per måned')
    st.markdown('Her er årene fordelt per måned. Vi kan se en trend på bla bla')
    fig = make_subplots(specs=[[{'secondary_y': True}]])

    for year in inst_monthly.index:
        inst = inst_monthly[inst_monthly.index == year].T[:12]
        fig.add_bar(x=inst.index, y=inst[year], name=f'Anlegg i {year}')

    fig.update_layout(title='Plusskundeinstallasjoner detaljert per måned',
        legend=dict(
            bgcolor='#f0f2f6',
            bordercolor='black'
            ),
            xaxis=dict(
                tickmode='array',
                tickvals=inst.index[:12],
                ticktext=month_names
                ),
            paper_bgcolor='rgb(209,232,250)',
            plot_bgcolor='#f0f2f6'
            )
    fig.update_xaxes(title_text='Måned')
    fig.update_yaxes(title_text='Antall', secondary_y=False)
    fig.update_yaxes(title_text='Installert effekt', secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

with st.container():
    st.subheader('Geografisk fremstilling')
    st.markdown('''Hvor er plusskundeanleggene i landet? \nHold inne _ctrl_ og bruk musepekeren
    for å vinkle kartet. Bruk pilen oppe i høyre hjørne for fullskjerm.  \nHer kan vi legge disse 
    fargede feltene akkurat som vi vil, men behøver hjelp for å få definerte koordinater for 
    prisområdene.''')

    df_map = pd.DataFrame({'lat': df['Latitude'], 'lon': df['Longitude']})
    df_map = df_map[df_map['lat'] != '(blank)']
    df_map = df_map.apply(pd.to_numeric)
    no1 = [[[10, 59.65], [10,  60.65], [11, 60.65], [11.5, 60], [11, 59.65]]]
    no2 = [[[6.5, 59], [6.9, 58.7], [7.4, 59], [7.3, 59.2], [7, 59.3]]]

    hex_layer = pdk.Layer(
        "HexagonLayer",
        df_map,
        pickable=True,
        auto_highlight=True,
        elevation_scale=20,
        extruded=True,
        get_position=['lon', 'lat'],
        colorScaleType='ordinal'
    )

    poly_no1 = pdk.Layer(
        'PolygonLayer',
        no1,
        stroked=False,
        get_polygon='-',
        get_fill_color=[255, 10, 120, 70]
    )

    poly_no2 = pdk.Layer(
        'PolygonLayer',
        no2,
        stroked=False,
        get_polygon='-',
        get_fill_color=[51, 255, 120, 70]
    )

    view_state = pdk.ViewState(latitude=60.2, longitude=10, zoom=5, bearing=0, pitch=30)

    map_design = st.selectbox('Velg design på kart',
        options=['light', 'dark', 'road'],
        format_func=str.capitalize)
    st.write(f'Bruker kart design: {map_design}')
    # Render
    r = pdk.Deck(
        layers=[hex_layer, poly_no1, poly_no2],
        initial_view_state=view_state,
        map_style='road',
        tooltip={"text": "Her kan det stå forskjellige ting, fx:\nGPS: {position}\nAntall: {elevationValue}"},
    )
    st.pydeck_chart(r, use_container_width=True)