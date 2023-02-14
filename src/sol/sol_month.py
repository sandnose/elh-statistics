# -*- coding: utf-8 -*-
"""
@author: christsa
"""
# Import external libraries
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# config
st.set_page_config(layout='wide', initial_sidebar_state="collapsed")
elh_colors = ["#006600", '#F2E500', '#785F4B', '#005886', '#c2e9c4']
month_names = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']

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
    st.header('Detaljer per måned')
    st.write('Klikk på valg i menyen til høyre for å vise/fjerne. Dobbelklikk på et valg for å vise alene.')
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