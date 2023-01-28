import streamlit as st 

import datetime
import pandas as pd
import plotly.io as pio

from typing import Tuple

import helpers as h
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
st.set_page_config(page_title='Shift Statistics', page_icon='📊', layout='wide')

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
    use_rel = (abs_vs_rel == 'Relative')
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

cols = st.columns(2)
sel_exp_type = cols[0].selectbox('Explore shift totals by:',
    ['Time of Day', 'Site'])
sel_class = cols[1].selectbox('Filter to class:',
    ['All',1,2,3,4], format_func=lambda x: f'PGY{x}' if type(x) == int else x)

plot_func = h.res_type_cat_plot if sel_exp_type == 'Time of Day' else h.res_site_cat_plot

st.markdown(f'## Shift Totals by {sel_exp_type}')

if sel_class == 'All':
    h.two_by_two_plot(plot_func, s, use_relative=use_rel)
else:
    st.plotly_chart(plot_func(s, sel_class, use_relative=use_rel))

# st.markdown('### Time of Day (Morning/Evening/Night)')

# h.two_by_two_plot(h.res_type_cat_plot, s, use_relative=(abs_vs_rel == 'Relative'))

# st.markdown('### Sites (UM/SJ/Hurley)')


# h.two_by_two_plot(h.res_site_cat_plot, s, use_relative=(abs_vs_rel == 'Relative'))