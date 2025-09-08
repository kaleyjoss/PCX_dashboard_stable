import dash
from dash import html, Input, Output, callback, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import logging
import os
import sys
import dash
from dash import html, dcc, callback, Input, Output
import dash
from dash import html, dcc, callback, Input, Output
import plotly 
import plotly.express as px
import pandas as pd
import xarray as xr
import importlib
import logging
import re
import pickle
import inspect
import datetime
from datetime import datetime as dt
import numpy as np

# Set project dir
project_dir = os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2')


dash.register_page(__name__, 
    path='/', # these 3 are automatically generated like this, but you can edit them
    title='Home',
    name='Home'
)

# # Import custom scripts
sys.path.append(project_dir)
import scripts.paths as paths
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])
from scripts.sub_id import extract
from scripts.paths import get_path
from scripts.config import subject_ids, surveys, recoded_surveys, subsurvey_key


# Set up logging
logging.basicConfig(
    filename='dashboard.log',        # File to write logs to, saved in working directory
    filemode='a',              # 'a' for append, 'w' to overwrite each time
    level=logging.INFO,        # Minimum logging level
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

rmr_df = pd.read_excel(os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Admin/RMR/RMR_running.xlsx'))
tracker_df=pd.read_excel(os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Subject_tracker_PCR.xlsx'), sheet_name='tracker')
subs_df=pd.read_excel(os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Subject_tracker_PCR.xlsx'), sheet_name='tracker')
# num phone data: in accel_df, gps_df, power_df
# num mri data: in surveys['mri_self_report_data']
# num clin interview session: in surveys['clinical_administered_data']
# goal: in rmr

# RMR visual
session1 = surveys['clinical_administered_data']
session1_r = session1.loc[session1['SUBJECT_ID'].str.contains('qualr')]
session1_m = session1.loc[session1['SUBJECT_ID'].str.contains('qualm')]
session2 = surveys['mri_self_report_data']
session2_r = session2.loc[session2['SUBJECT_ID'].str.contains('qualr')]
session2_m = session2.loc[session2['SUBJECT_ID'].str.contains('qualm')]
total_real = len(session1_r) + len(session1_m)

today = datetime.datetime.today()
today_str = today.strftime('%b %d %Y')
rate_per_day = 0.22
start = 'Dec 1 2024'
beginning = dt.strptime(start, '%b %d %Y')
days_of_study = today - beginning
today_goal = int(days_of_study.days * rate_per_day)
today_site = today_goal / 2
today_c = pd.DataFrame([today_str, np.nan, np.nan, today_site, today_site, today_goal, len(session1_r), len(session1_r), len(session2_r), len(session1_m), len(session1_m), len(session2_m), total_real])
today_row = today_c.T
today_row.columns = rmr_df.columns.to_list()
rmr_df_today = pd.concat([rmr_df, today_row])
rmr_df_today['Quarter'] = rmr_df_today['Quarter'].apply(lambda x: dt.strptime(x, '%b %d %Y'))
rmr_df_today = rmr_df_today.sort_values('Quarter').reset_index(drop=True)
rmr_df_today = rmr_df_today.reset_index()
today_row = rmr_df_today.loc[rmr_df_today['Quarter']==today_str]
today_index = today_row['index'].values.squeeze()
two_quarters_out=today_index+2
rmr_df_today = rmr_df_today[:two_quarters_out]


rmr_goal = px.line(rmr_df_today, x='Quarter', y=['Total Goal', 'Total Real'], width=500, height=300, title='Total Subjects Consented: Goal and Real')
r_goal = px.line(rmr_df_today, x='Quarter', y=['Rutgers Goal', 'Rutgers Consented', 'Rutgers Clinical Interview', 'Rutgers Scan'], width=500, height=300, title='Subjects at Rutgers vs. Goal')
m_goal = px.line(rmr_df_today, x='Quarter', y=['McLean Goal', 'McLean Consented', 'McLean Clinical Interview', 'McLean Scan'], width=500, height=300, title='Subjects at McLean vs. Goal')


# Subject 1-liners



# Tracker Visual
subs_df_binary = subs_df.fillna(0)
subs_df_filtered = subs_df_binary.loc[subs_df_binary['Clinical Interview Session Date'] != 0, :]
subs_df_filtered = subs_df_filtered.loc[:, ~subs_df_filtered.columns.str.contains('Unnamed', case=False)]
tags_row = subs_df_filtered.iloc[0]

def filter_by_tag(df, tags_row, desired_tags):
    matching_cols = []
    for tag in desired_tags:
        matching = tags_row[tags_row.astype(str).str.contains(tag, na=False)].index.tolist()
        matching_cols.extend(matching)

    # Remove duplicates while preserving order
    matching_cols = list(dict.fromkeys(matching_cols))

    return df[matching_cols]

tracker_df = filter_by_tag(subs_df_filtered, tags_row, ['id','tracker'])

# # Now the structure is:
# # |PCR ID:  | SUBJECT_ID |     Session Date    |   Session Time     | <-- these are all columns in tracker
# # |tags     |  id     | tracker, scheduling | tracker, scheduling| ...
# # |PCR200   |qualr200 |     <value>         |       <value>      | ...

# App layout
layout = html.Div([
    html.H1('Subject Tasks Completed',  style={'margin':20}),
    html.Div(id='graphs', children=[
        dcc.Graph(figure=rmr_goal, id='rmr-goal'),
        dcc.Graph(figure=r_goal, id='rutgers-goal'),
        dcc.Graph(figure=m_goal, id='mclean-goal'),
    ]),
    
    dcc.Graph(figure={}, id='dashboard-graph', style={
        'width': '100%',
        'height': '100%',
        'padding': 10,
        'flex': 1,})
])


# Controls to filter the figure by subject ID and
@callback(
    Output('dashboard-graph', 'figure'),
    Input('subject-id', 'data')
)

def cb(subject_id):
    if subject_id is None:
        filtered_df = tracker_df
    else:
        filtered_df = tracker_df[tracker_df['SUBJECT_ID'] == subject_id]
    
    # Binarize non-zero values
    filtered_df_bin = filtered_df.where(filtered_df == 0, 1)
    #display(filtered_df_bin)
    
    # Create the figure
    fig = px.imshow(filtered_df_bin, origin='lower',
                    title="Tasks Completed by Participants",
                    zmin=0, zmax=1, color_continuous_scale=[[0, "white"], [1, "black"]],
                    labels=dict(x="Tasks Completed", y="Subject", color="Done = Black"),
                    x=filtered_df.columns,
                    y=filtered_df['SUBJECT_ID'],
                    width=1500, height=800)
    return fig

