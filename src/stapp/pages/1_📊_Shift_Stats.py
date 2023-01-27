import streamlit as st 

import datetime
import pandas as pd

from typing import Tuple

import config as cf
from schedexp import schedexp as sched

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
    bd = sched.load_block_dates(cf.BLOCK_DATES_FN).set_index('Block')
    res = sched.load_residents(cf.RESIDENTS_FN)
    return bd, res

# Set Title
st.set_page_config(page_title='Shift Statistics', page_icon='📊')

# Load helper data
bd, res = get_helper_data()

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

    exclude_nonem = st.checkbox('Exclude off-service residents', value=True)

st.title('Shift Statistics')
st.markdown('*Useful statistics for evaluating the schedule*')

df = get_api_sched(start_date, end_date)
if exclude_nonem:
    df = df[df['userID'].isin(res['userID'])]
groups, users, facs, shifts = sched.full_df_to_rel(df)

st.markdown(f'Between **{start_date}** and **{end_date}**, there are **{len(df)}** scheduled shifts, ' +
    ('**for EM residents**, ' if exclude_nonem else '') +
    f'totaling **{int(df["shiftHours"].sum())}** person-hours ' +
    f'across **{len(df["userID"].unique())}** residents.')

st.markdown('## Shift Totals by Date')

st.markdown('## Shift Totals by Resident')

# st.dataframe(df)