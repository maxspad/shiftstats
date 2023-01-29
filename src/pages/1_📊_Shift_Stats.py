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
bd.index = [f'Block {b}' for b in bd.index]

# Configure sidebar
with st.sidebar:
    bd_list = {
        f'{b}: {r["Start Date"].date()} to {r["End Date"].date()}' : b
        for b, r in bd.iterrows()
    }
    bd_list['Custom Date Range'] = 'Custom'
    bd_list['Year to Date'] = 'YTD'
    sel = st.selectbox('Choose a block or date range:', bd_list.keys())
    sel_block = bd_list[sel]
    if sel_block == 'YTD':
        start_date = datetime.date(2022, 7, 1)
        end_date = datetime.date.today()
    elif sel_block == 'Custom':
        start_date = st.date_input('Custom start date:', value=datetime.date.today())
        end_date = st.date_input('Custom end date:', value=datetime.date.today() + datetime.timedelta(days=14))
    else:
        start_date = bd.loc[sel_block,'Start Date']
        end_date = bd.loc[sel_block,'End Date']
    # sel_start_date = bd.loc[sel_block,'Start Date']
    # sel_end_date = bd.loc[sel_block,'End Date']

    # cg = h.CheckGroup(values=[1,2,3,4], labels=['PGY1','PGY2','PGY3','PGY4'], 
            # caption='Filter by Class:', horizontal=False)

    abs_vs_rel =st.radio('Show shift counts as:', ('Absolute','Relative'), horizontal=True)
    use_rel = (abs_vs_rel == 'Relative')
    exclude_nonem = True # st.checkbox('Exclude off-service residents', value=True)

st.title('Shift Statistics')
st.markdown('*Useful statistics for evaluating the schedule*')

# Download the shiftadmin data
try:
    s = load_schedule(start_date, end_date, res, exclude_nonem)
except sched.ScheduleError:
    st.error('End Date must come after Start Date')
    st.stop()


# s = s[s['PGY'].isin(cg.get_selected())]

st.markdown('## Overall Shift Breakdown')

st.markdown(f'Between **{start_date}** and **{end_date}**, there are **{len(s)}** shifts, ' +
    f'totaling **{int(s["Length"].sum())}** person-hours ' +
    f'across **{len(s["Resident"].unique())}** residents.')
pgy_counts = s['PGY'].value_counts().sort_index()
pgy_norm = s['PGY'].value_counts(normalize=True).sort_index() * 100
tod_counts = s['Type'].value_counts()
tod_norm = s['Type'].value_counts(normalize=True) * 100
site_counts = s['Site'].value_counts()
site_norm = s['Site'].value_counts(normalize=True) * 100
md_breakdown_str = ('\t* By class, ' + ', '.join([f'**{pgy_counts[i]}** ({pgy_norm[i]:.0f}%) are worked by PGY{i:.0f}s' for i in pgy_counts.index]) + '.\n' +
                   '\t* By time of day, ' + ', '.join([f'**{tod_counts[t]}** ({tod_norm[t]:.0f}%) are {t} shifts' for t in ['Morning','Evening','Night']]) + '.\n' +
                   '\t* By site, ' + ', '.join([f'**{site_counts[s]}** ({site_norm[s]:.0f}%) are at {s}' for s in ['UM','SJ','HMC']]) + '.')
st.markdown(md_breakdown_str)

import plotly.express as px

cols = st.columns(3)

# plt = px.pie(pgy_counts.reset_index(), values='PGY', names='index', hole=0.3,  
#         title='Shifts by Class')
# plt = px.bar(pgy_counts.reset_index().rename({'index':'PGY', 'PGY':'Number of Shifts'}, axis=1), x='PGY', y='Number of Shifts', color='PGY', title='Shifts by Class')
plt = px.histogram(s, x='PGY', color='PGY',
        title='Shifts by Class',
        category_orders={'PGY':[1,2,3,4]},
        color_discrete_map=h.PGY_COLORS_MAP)
plt.update_layout(bargap=0.2)
cols[0].plotly_chart(plt, use_container_width=True)

# plt = px.pie(tod_counts.reset_index(), values='Type', names='index', hole=0.3, 
#         color_discrete_sequence=[h.TOD_COLORS_MAP[t] for t in tod_counts.index], 
#         title='Shifts by Time of Day')
plt = px.histogram(s, x='Type', color='Type',
        color_discrete_map=h.TOD_COLORS_MAP,
        title='Shifts by Time of Day')
# plt = px.bar(tod_counts.reset_index().rename({'index': 'Time of Day', 'Type':'Number of Shifts'}, axis=1),
            # x='Time of Day', y='Number of Shifts', color='Time of Day',
            # color_discrete_sequence=[h.TOD_COLORS_MAP[t] for t in tod_counts.index],
            # title='Shifts by Time of Day',
            # category_orders=['Morning','Evening','Night'])
cols[1].plotly_chart(plt, use_container_width=True)

plt = px.histogram(s, x='Site', color='Site',
        color_discrete_map=h.SITE_COLORS_MAP,
        title='Shifts by Site')
# plt = px.pie(site_counts.reset_index(), values='Site', names='index', hole=0.3, 
#         color_discrete_sequence=[h.SITE_COLORS_MAP[s] for s in site_counts.index], 
#         title='Shifts by Site')
cols[2].plotly_chart(plt, use_container_width=True)

st.markdown('## Shift Breakdown by *Class*')

st.markdown('## Shift Breakdown by *Resident*')
st.markdown('Shift counts by individual resident')
cols = st.columns([2,2,6])
sel_exp_type = cols[0].selectbox('Explore shift totals by:',
    ['Time of Day', 'Site'])
sel_class = cols[1].selectbox('Filter to class:',
    ['All',1,2,3,4], format_func=lambda x: f'PGY{x}' if type(x) == int else x)

plot_func = h.res_type_cat_plot if sel_exp_type == 'Time of Day' else h.res_site_cat_plot

st.markdown(f'## Shift Totals by {sel_exp_type}')
st.caption(f'Between {start_date} and {end_date}')

# if sel_class == 'All':
h.two_by_two_plot(plot_func, s, use_relative=use_rel)
# else:
    # st.plotly_chart(plot_func(s, sel_class, use_relative=use_rel))