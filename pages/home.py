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


# Set up logging
logging.basicConfig(
    filename='dashboard.log',        # File to write logs to, saved in working directory
    filemode='a',              # 'a' for append, 'w' to overwrite each time
    level=logging.INFO,        # Minimum logging level
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

subs_df=pd.read_excel(os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Subject_tracker_PCR.xlsx'), sheet_name='tracker')

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
    dcc.Dropdown(
        id='subject_id',
        options=['All']+[sub_id for sub_id in subs_df_filtered['SUBJECT_ID'].unique()],
        placeholder="Select a subject",
        value='All', style={'width': '90%', 'margin': '10 auto', 'display': 'block'}
    ),
    dcc.Graph(figure={}, id='dashboard-graph', style={
        'width': '100%',
        'height': '100%',
        'padding': 10,
        'flex': 1,})
])


# Controls to filter the figure by subject ID and
@callback(
    Output('dashboard-graph', 'figure'),
    Input('subject_id', 'value')
)

def cb(subject_id):
    if subject_id == "All":
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

