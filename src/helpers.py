import pandas as pd
from typing import Callable
import streamlit as st
import plotly.express as px

def two_by_two_plot(plot_func : Callable, df : pd.DataFrame, use_relative=False):
    cols = st.columns(2)
    for i, c in enumerate(cols):
        c.plotly_chart(plot_func(df, i+1, use_relative=use_relative), use_container_width=True)
    cols = st.columns(2)
    for i, c in enumerate(cols):
        c.plotly_chart(plot_func(df, i+3, use_relative=use_relative), use_container_width=True)

def res_type_cat_plot(df : pd.DataFrame, pgy : int, use_relative=False):
    df_pgy = df[df['PGY'] == pgy].sort_values('Last Name', ascending=False)
    plt = px.histogram(df_pgy, y='Resident', color='Type', 
                orientation='h', category_orders={'Type': ['Night','Evening','Morning']},
                barnorm=('percent' if use_relative else None),
                title=f'Shifts by Time of Day: PGY {pgy}')
    return plt

def res_site_cat_plot(df : pd.DataFrame, pgy : int, use_relative=False):
    df_pgy = df[df['PGY'] == pgy].sort_values('Last Name', ascending=False)
    plt = px.histogram(df_pgy, y='Resident', color='Site', 
                orientation='h', category_orders={'Site': ['UM','SJ','HMC']},
                barnorm=('percent' if use_relative else None),
                title=f'Shifts by Site: PGY {pgy}')
    return plt
