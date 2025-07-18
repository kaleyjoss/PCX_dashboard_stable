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

subs_df=pd.read_excel('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Data/Subject_tracker_PCR.xlsx', sheet_name='clean_data')

# Skip displaying some irrelevant fields if necessary, change
heatmap_columns = subs_df.columns.to_list()
subs_df_binary = subs_df.fillna(0)
subs_df_filtered = subs_df_binary.loc[subs_df_binary['Clinical Interview Session Date'] != 0, :]

# # Now the structure is:
# # |PCR ID:  | Qual ID    |    diagnosis    |  mri_surveys  | <-- these are all columns in clean_data
# # |PCR200   |  qualr200  |     <value>     |      0        | ...



# App layout
layout = html.Div([
    html.H1('Subject Tasks Completed',  style={'margin':20}),
    dcc.Dropdown(
        id='subject_id',
        options=['All']+[sub_id for sub_id in subs_df_filtered['Qual ID'].unique()],
        placeholder="Select a subject",
        value='All'
    ),
    dcc.Graph(figure={}, id='dashboard-graph')
])


# Controls to filter the figure by subject ID and
@callback(
    Output('dashboard-graph', 'figure'),
    Input('subject_id', 'value')
)

def cb(subject_id):
    if subject_id == "All":
        filtered_df = subs_df_filtered
    else:
        filtered_df = subs_df_filtered[subs_df_filtered['Qual ID'] == subject_id]
    # Binarize non-zero values
    filtered_df_bin = filtered_df.where(filtered_df == 0, 1)
    #display(filtered_df_bin)
    
    # Create the figure
    fig = px.imshow(filtered_df_bin, origin='lower',
                    title="Tasks Completed by Participants",
                    zmin=0, zmax=1, color_continuous_scale=[[0, "white"], [1, "black"]],
                    labels=dict(x="Tasks Completed", y="Subject", color="Done = Black"),
                    x=subs_df_filtered.columns,
                    y=subs_df_filtered['Qual ID'])
    return fig

