import streamlit as st 

import datetime
import pandas as pd
import plotly.io as pio
import plotly.express as px

from typing import Tuple

import config as cf
from schedexp import schedexp as sched

pio.templates.default = 'seaborn'

@st.experimental_memo
def get_api_sched(start_date : datetime.date, end_date : datetime.date) -> pd.DataFrame:
    '''Use the ShiftAdmin API to get the schedule'''
    return sched.load_df_api(start_date, end_date)

def validate_dates(start_date : datetime.date, end_date : datetime.date) -> bool:
    '''Ensure the chosen dates are valid'''
    return (
        (end_date >= start_date)
    )

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

    if not validate_dates(start_date, end_date):
        st.error('End date must be after start date')
        st.stop()

    abs_vs_rel =st.radio('Show shift counts as:', ('Absolute','Relative'), horizontal=True)
    exclude_nonem = st.checkbox('Exclude off-service residents', value=True)

st.title('Shift Statistics')
st.markdown('*Useful statistics for evaluating the schedule*')

# Download the shiftadmin data
df = get_api_sched(start_date, end_date)
# Add PGY year
df = df.merge(res[['userID','pgy']], how='left', on='userID')
# Exclude non-em residents if selected
if exclude_nonem:
    df = df.dropna(subset=['pgy'])
# Breakdown into relative pieces
# groups, users, facs, shifts = sched.full_df_to_rel(df)

st.markdown(f'Between **{start_date}** and **{end_date}**, there are **{len(df)}** scheduled shifts, ' +
    ('**for EM residents**, ' if exclude_nonem else '') +
    f'totaling **{int(df["shiftHours"].sum())}** person-hours ' +
    f'across **{len(df["userID"].unique())}** residents.')

# st.markdown('## Shift Totals by Date')

# shiftTypeCatBar = px.histogram(df, x='shiftStartDay', color='shiftType', 
#                     nbins=len(df['shiftStartDay'].unique()),
#                     labels={'shiftType': 'Shift Type', 'shiftStartDay': 'Date'},
#                     category_orders={'shiftType':['Morning','Evening','Night']},
#                     title='Shift Types by Day', text_auto=True)
# shiftTypeCatBar.update_layout(bargap=0.2, yaxis_title='Number of Shifts')
# st.plotly_chart(shiftTypeCatBar)

# facilityCatBar = px.histogram(df, x='shiftStartDay', color='facilityAbbreviation',
#                     nbins=len(df['shiftStartDay'].unique()),
#                     labels={'facilityAbbreviation':'Site','shiftStartDay':'Date'},
#                     category_orders={'facilityAbbreviation': ['UM','SJ','HMC']},
#                     title='Number of Shifts at Each Site by Day')
# facilityCatBar.update_layout(bargap=0.2, yaxis_title='Number of Shifts')
# st.plotly_chart(facilityCatBar)


st.markdown('## Shift Totals by Resident')

def res_cat_plot(df : pd.DataFrame, pgy : int, use_relative=False):
    # df_pgy = df.merge(res[['userID','pgy']], how='inner', on='userID')
    df_pgy = df[df['pgy'] == pgy].sort_values('lastName', ascending=False)
    plt = px.histogram(df_pgy, y='Resident', color='shiftType', 
                orientation='h', category_orders={'shiftType': ['Night','Evening','Morning']},
                barnorm=('percent' if use_relative else None))
    return plt

sel_pgy = st.selectbox('Class (PGY):', [1,2,3,4])


st.plotly_chart(res_cat_plot(df, sel_pgy, use_relative=(abs_vs_rel == 'Relative')))

st.markdown('## Shift Totals by Class')

plt = px.histogram(df, y=('PGY' + df['pgy'].astype('int').astype('str')), 
        color='shiftType', orientation='h',
        labels={'y': 'PGY', 'shiftType':'Shift Type'},
        category_orders={'y': ['PGY1','PGY2','PGY3','PGY4'], 'shiftType': ['Night','Evening','Morning']},
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
