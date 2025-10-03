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

# # Import custom scripts
sys.path.append(project_dir)
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])
from scripts.sub_id import extract
from scripts.paths import load_paths

paths = load_paths()
project_dir = paths["project_dir"]
surveys_dir = paths["surveys_dir"]

# Register page into dash app as pagename
dash.register_page(__name__, path="/dashboard")


# Set up logging
logging.basicConfig(
    filename='dashboard.log',        # File to write logs to, saved in working directory
    filemode='a',              # 'a' for append, 'w' to overwrite each time
    level=logging.INFO,        # Minimum logging level
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

# This iterates through all .xlsx files within the subject logs folder and saves them into a dict
# Creating a dictionary called 'subs'
# With keys of each sub-ID (ex: sub-PCR200)
# And within each key, a df which has 3 columns: key, value and readable_name
subs = {}
sub_logs_path = get_path('subject_logs', project_dir)
if sub_logs_path:
    for file in os.listdir(sub_logs_path):
        if file.startswith("~$") or not file.endswith((".xlsx", ".xls")):
            continue  # skip temp or non-excel files
        sub = extract(file)
        if sub is not None:
            subs[sub] = pd.read_excel(os.path.join(sub_logs_path, file),sheet_name='JSON_formatted')

# This next code below makes it into a df with all subs concatenated
logging.info(f'Subs in dashboard.py has keys {subs.keys()}')
subs_df = pd.concat([sub[['readable_names','value']].T for sub in subs.values()], axis=0, ignore_index=True)
# Set column names
subs_df.columns = subs_df.iloc[0] # This makes the "keys" into the column names
# This deletes any duplicate rows of the column names, which have 'id' as key instead of a subject-id
subs_df = subs_df[subs_df['PCR ID'] != 'PCR ID'] 
# Skip displaying some irrelevant fields
heatmap_columns = [col for col in subs_df.columns if isinstance(col, str) and not 'notes' in col and not 'diagnosis' in col]

# Now the structure is:
# |key:     | id  | diagnosis |  mri_surveys  | <-- these are all columns in heatmap_columns
# |PCR200   |  1  |     1     |      0        | ...




# App layout
layout = html.Div([
    html.H1('Subject Tasks Completed'),
    dcc.Dropdown(
        id='subject_id',
        options=[{'label': sub_id, 'value': sub_id} for sub_id in subs_df['PCR ID'].unique()],
        placeholder="Select a subject",
    ),
    dcc.Graph(figure={}, id='dashboard-graph')
])


# Controls to filter the figure by subject ID and 
@callback(
    Output('dashboard-graph', 'figure'),
    Input('subject_id', 'value')
)

def cb(subject_id):
    if subject_id is None:
        filtered_df = subs_df
    else:
        filtered_df = subs_df[subs_df['PCR ID'] == subject_id]
    # Binarize non-zero values
    filtered_df_bin = filtered_df.where(filtered_df == 0, 1)
    # Create the figure
    fig = px.imshow(filtered_df_bin, origin='lower',
                    title="Tasks Completed by Participants",
                    zmin=0, zmax=1, color_continuous_scale=[[0, "white"], [1, "black"]],
                    labels=dict(x="Tasks Completed", y="Subject", color="Done = Black"),
                    x=subs_df.columns,
                    y=subs_df['PCR ID'])
    return fig

