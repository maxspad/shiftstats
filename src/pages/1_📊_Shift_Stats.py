import streamlit as st 

import datetime
import pandas as pd
import plotly.io as pio
import plotly.express as px

from typing import Tuple

import config as cf
import schedexp as sched

pio.templates.default = 'seaborn'

@st.experimental_memo
def load_schedule(start_date : datetime.date, end_date : datetime.date, 
    res : pd.DataFrame, exclude_nonem: bool):

    s = sched.load_sched_api(start_date, end_date)
    s = sched.add_res_to_sched(s, res)
    if exclude_nonem:
        s = s.dropna(subset=['PGY'])
    return s

@st.experimental_memo
def get_helper_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    '''Load helper dataframes'''
    bd = sched.load_block_dates(cf.BLOCK_DATES_FN).set_index('Block')
    res = sched.load_residents(cf.RESIDENTS_FN)
    return bd, res

# Set Title 
st.set_page_config(page_title='Shift Statistics', page_icon='📊')

# Load helper data
bd, res = get_helper_data()

# Configure sidebar
with st.sidebar:
    bd_list = {
        f'Block {b}: {r["Start Date"].date()} to {r["End Date"].date()}' : b
        for b, r in bd.iterrows()
    }
    sel = st.selectbox('Choose a block:', bd_list.keys())
    sel_block = bd_list[sel]
    sel_start_date = bd.loc[sel_block,'Start Date']
    sel_end_date = bd.loc[sel_block,'End Date']

    start_date = st.date_input('or you can choose a custom start date:', value=sel_start_date)
    end_date = st.date_input('and end date:', value=sel_end_date)

    abs_vs_rel =st.radio('Show shift counts as:', ('Absolute','Relative'), horizontal=True)
    exclude_nonem = st.checkbox('Exclude off-service residents', value=True)

st.title('Shift Statistics')
st.markdown('*Useful statistics for evaluating the schedule*')

# Download the shiftadmin data
try:
    s = load_schedule(start_date, end_date, res, exclude_nonem)
except sched.ScheduleError:
    st.error('End Date must come after Start Date')
    st.stop()

st.markdown(f'Between **{start_date}** and **{end_date}**, there are **{len(s)}** shifts, ' +
    f'totaling **{int(s["Length"].sum())}** person-hours ' +
    f'across **{len(s["Resident"].unique())}** residents.')

st.markdown('## Shift Totals by Resident')
sel_pgy = st.selectbox('Class (PGY):', [1,2,3,4])

st.markdown('### Time of Day (Morning/Evening/Night)')

def res_type_cat_plot(df : pd.DataFrame, pgy : int, use_relative=False):
    df_pgy = df[df['PGY'] == pgy].sort_values('Last Name', ascending=False)
    plt = px.histogram(df_pgy, y='Resident', color='Type', 
                orientation='h', category_orders={'Type': ['Night','Evening','Morning']},
                barnorm=('percent' if use_relative else None))
    return plt

st.plotly_chart(res_type_cat_plot(s, sel_pgy, use_relative=(abs_vs_rel == 'Relative')))

st.markdown('### Sites (UM/SJ/Hurley)')
def res_site_cat_plot(df : pd.DataFrame, pgy : int, use_relative=False):
    df_pgy = df[df['PGY'] == pgy].sort_values('Last Name', ascending=False)
    plt = px.histogram(df_pgy, y='Resident', color='Site', 
                orientation='h', category_orders={'Site': ['UM','SJ','HMC']},
                barnorm=('percent' if use_relative else None))
    return plt

st.plotly_chart(res_site_cat_plot(s, sel_pgy, use_relative=(abs_vs_rel == 'Relative')))

cols = st.columns([5,5])
cols[0].plotly_chart(res_site_cat_plot(s, 1, use_relative=(abs_vs_rel == 'Relative')), use_container_width=True)
cols[1].plotly_chart(res_site_cat_plot(s, 2, use_relative=(abs_vs_rel == 'Relative')), use_container_width=True)
st.markdown('## Shift Totals by Class')
st.markdown('*Does not include off-service residents*')

s_no_os = s.dropna(subset=['PGY'])
plt = px.histogram(s_no_os, y=('PGY' + s_no_os['PGY'].astype('int').astype('str')), 
        color='Type', orientation='h',
        labels={'y': 'PGY'},
        category_orders={'y': ['PGY1','PGY2','PGY3','PGY4'], 'Type': ['Night','Evening','Morning']},
        barnorm=('percent' if abs_vs_rel == 'Relative' else None))
# plt.update_layout(bargap=0.2)
st.plotly_chart(plt)

# shiftTypeCatBar = px.histogram(df, x='Resident', color='shiftType', 
#                     nbins=len(df['userID'].unique()),
#                     labels={'shiftType': 'Shift Type', 'userID': 'Resident'},
#                     category_orders={'shiftType':['Morning','Evening','Night']},
#                     title='Shift Types by Resident', text_auto=True)
# # shiftTypeCatBar.update_layout(bargap=0.2, yaxis_title='Number of Shifts')
# st.plotly_chart(shiftTypeCatBar)
