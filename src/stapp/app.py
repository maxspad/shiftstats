import streamlit as st 
from schedexp import schedexp as sched
import datetime
import pandas as pd

@st.experimental_memo
def get_api_sched(start_date : datetime.date, end_date : datetime.date) -> pd.DataFrame:
    return sched.load_df_api(start_date, end_date)

with st.sidebar:
    start_date = st.date_input('Start Date')
    end_date = st.date_input('End Date')

st.write('# Hello!')

df = get_api_sched(start_date, end_date)
groups, users, facs, shifts = sched.full_df_to_rel(df)

st.dataframe(df)