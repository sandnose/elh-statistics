# -*- coding: utf-8 -*-
"""
@author: christsa
"""
# Import external libraries
import streamlit as st
from st_pages import show_pages_from_config

# app config
st.set_page_config(layout='wide', menu_items={'About': "# Elhub statistikk. Skrive noe mer?"},
                   initial_sidebar_state="collapsed")
no_sidebar_style = """
    <style>
        div[data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(no_sidebar_style, unsafe_allow_html=True)

# init pages in src/
show_pages_from_config()

# testpage
st.header('Elhub statistikk')
st.write('Test side for landing')