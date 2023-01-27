import streamlit as st 
from schedexp import schedexp as sched
import datetime
import pandas as pd

@st.experimental_memo
def get_api_sched(start_date : datetime.date, end_date : datetime.date) -> pd.DataFrame:
    return sched.load_df_api(start_date, end_date)

def validate_dates(start_date : datetime.date, end_date : datetime.date) -> bool:
    return (
        (end_date >= start_date)
    )

st.set_page_config(page_title='Shift Statistics', page_icon='📊')

with st.sidebar:
    start_date = st.date_input('Start Date')
    end_date = st.date_input('End Date')
    if not validate_dates(start_date, end_date):
        st.error('End date must be after start date')
        st.stop()

st.title('Shift Statistics')
st.markdown('*Useful statistics for evaluating the schedule*')


df = get_api_sched(start_date, end_date)
groups, users, facs, shifts = sched.full_df_to_rel(df)

st.markdown(f'Between **{start_date}** and **{end_date}**, there are **{len(df)}** scheduled shifts, ' +
    f'totaling **{int(df["shiftHours"].sum())}** person-hours')

st.markdown('## Shift Totals by Date')

st.markdown('## Shift Totals by Resident')

st.dataframe(df)