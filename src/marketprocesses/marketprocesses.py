# -*- coding: utf-8 -*-
"""
@author: christsa
"""
# Import external libraries
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# config
st.set_page_config(layout='wide', initial_sidebar_state="collapsed")
pd.options.display.float_format = '{:,.2f}'.format
elhex_colors = ["#006600", '#F2E500', '#785F4B', '#005886', '#c2e9c4']
elrgb_colors = [[0, 102, 0], [120, 95, 75], [242, 229, 0], [213, 210, 195], [209, 232, 250]]
month_names = ['jan', 'feb', 'mar', 'apr', 'mai',
               'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
st.markdown('''<style> div.block-container {padding-top:1rem;}</style>''', unsafe_allow_html=True)

# functions
# can be cached if wanted
def load_data() -> pd.DataFrame():
    ''' by doing the loading an manipulation inside a cached function the process will not have to
    be redone when refreshing the page '''
    dat = pd.read_csv('data/mplog.csv')
    brs = pd.read_csv('data/mapping/dim_brs.csv')
    mpstate = pd.read_csv('data/mapping/dim_mpstate.csv')

    dat = pd.merge(dat, brs, left_on='brs', right_on='id')
    dat = pd.merge(dat, mpstate, left_on='state', right_on='id')
    dat = dat[['usage_date', 'process_code', 'group', 'status_kode', 'count']]
    dat.columns = ['usage_date', 'brs', 'group', 'state', 'count']
    dat['year'] = [datetime.strptime(row, '%b-%y ').year for row in dat['usage_date']]
    dat['month'] = [datetime.strptime(row, '%b-%y ').month for row in dat['usage_date']]
    dat['count'] = dat['count'].astype('Int64')

    return dat

def group_change():
    ''' a "on_change" function for the multiselect button, makes sure certain elements are refreshed
     when option is selected '''
    #col2.write(df['brs'][df['group'].isin(st.session_state['groupKey'])].unique().tolist())
    st.session_state['optionKey'] = mplog['brs'][mplog['group'].\
        isin(st.session_state['groupKey'])].unique().tolist()
    return

mplog = load_data()

# selection groups
groups = mplog['group'].unique().tolist()
options = mplog['brs'].unique().tolist()
state = mplog['state'].unique().tolist()

if 'optionKey' not in st.session_state:
    st.session_state['groupKey'] = groups[:-6]
    group_change()

with st.container():
    # container 2
    st.subheader('Markedsprosesser')
    col1, col2 = st.columns([8,3], gap='large')
    col1.markdown('''Oversikt over antall markedsprosesser på månedsbasis fordelt på typer og
                tilstand. Diagrammet viser antall initierte markedsprosesser Elhub mottok per måned.
                Initierte markedsprosesser er alle prosesser som er sendt inn før Elhub prosesserer
                og validerer, og eventuelt godkjenner eller avviser.  
                Bruk knappene til høyre for å laste ned hele grunnlaget eller grunnlaget for
                utsnittet du har valgt under.  
                Du kan lese mer om markedsprosessene på våre
                [dokumentasjonsider](https://dok.elhub.no/ediel1141/brs-markedsprosesser)''')
    st.info('''Du kan velge ønskede år i menyen til høyre for grafen, dobbelklikk for å markere kun
            ett år, dobbelklikk igjen for å markere alle.  
            Man kan også zoome slik man ønsker i grafen, og dobbelklikke midt i bildet for å
            resette. Eller du kan bruke menyen oppe til høyre for grafen.''')

    # multiselect buttons in columns within container
    col3, col4 = st.columns(2)
    button_groups = col3.multiselect('Velg markedsprossessgruppe', groups, groups[:-6],
                                     key='groupKey', on_change=group_change)
    button_options = col4.multiselect('''Spesifiser enkelt BRS om ønskelig
                                      (påvirker ikke gruppevalg)''', options,
                                      options,
                                      key='optionKey')
    button_state = col3.selectbox('Velg tilstand', state, 1)

    # data engineering for container plot
    mplog_copy = mplog['count'].groupby([mplog['year'], mplog['month'], mplog['brs'],
                                         mplog['state']]).sum().unstack(0)
    years = mplog_copy.columns
    mplog_copy = mplog_copy.reset_index()
    mplog_copy = mplog_copy[years][(mplog_copy['brs'].isin(button_options)) &
                                   (mplog_copy['state'] == button_state)].groupby(
                                       [mplog_copy['month'], mplog_copy['state']]).sum()
    mplog_copy.replace(0, np.nan, inplace=True)

    try:
        fig = px.line(mplog_copy, x=mplog_copy.index.get_level_values(0), y=mplog_copy.columns,
                      markers=True, color_discrete_sequence=elhex_colors)
        fig.update_layout(title=f'''{button_state} prosesser''',
                             xaxis_title='Mnd', yaxis_title='Antall', legend_title='År',
                             xaxis={'tickmode': 'array',
                                    'tickvals': mplog_copy.index.get_level_values(0),
                                    'ticktext': month_names},
                             legend={'title': 'År', 'bgcolor': '#f0f2f6', 'bordercolor': 'black'},
                             paper_bgcolor='rgb(209,232,250)',
                             plot_bgcolor='#f0f2f6',
                             height=700
                             )

        st.plotly_chart(fig, use_container_width=True)
        st.caption(f'''Markedsprosesser i vsiningen: {', '.join(button_options)}''')
    except ValueError:
        st.error('Vennligst velg minst en markedsprosess')

    col2.download_button(label='Last ned hele grunnlaget som CSV',
                         data=mplog.to_csv(index=False).encode('utf-8-sig'),
                         file_name=f'elhub-markedsprosesser-{pd.Timestamp.today()}.csv',
                         mime='text/csv',
                         help='''Returnerer en .csv fil med alle markedsprosessene elhub har mottatt
                         gruppert på måned og år.''')
    col2.download_button(label='Last ned utsnitt som CSV',
                         data=mplog_copy.to_csv().encode('utf-8-sig'),
                         file_name=f'elhub-markedsprosesser-{pd.Timestamp.today()}.csv',
                         mime='text/csv',
                         help='''Returnerer en .csv fil med markedsprosessene du har valgt i menyene
                         under.''')
