import os
import sys
import re
import dash
from dash import html, dcc, callback, Input, Output
import plotly 
import plotly.express as px
import pandas as pd
import xarray as xr
import importlib
import logging
import pickle
import inspect

# Set project dir
project_dir = os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2')

# Import custom scripts
sys.path.append(project_dir)
import scripts.paths as paths
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])

# Register page into dash app as pagename
dash.register_page(__name__, path="/subject") 


# Set up logging
logging.basicConfig(
    filename='subject.log',        # File to write logs to, saved in working directory
    filemode='a',              # 'a' for append, 'w' to overwrite each time
    level=logging.INFO,        # Minimum logging level
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

# Save subject logs to subs df
subs = {}
sub_logs_path = paths.get_path('subject_logs', project_dir, isdir=True)
if sub_logs_path:
    for file in os.listdir(sub_logs_path):
        if file.startswith("~$") or not file.endswith((".xlsx", ".xls")):
            continue  # skip temp or non-excel files
        sub = sub_id.extract(file)
        if sub is not None:
            subs[sub] = pd.read_excel(os.path.join(sub_logs_path, file),sheet_name='JSON_formatted')
logging.info(f'Subs in subject.py has keys {subs.keys()}')
 
power = {}
gps = {}
accel = {}
mindlamp_data_path = paths.get_path('mindlamp_data', project_dir, isdir=True)
if mindlamp_data_path:
    for dirpath, dirnames, filenames in os.walk(mindlamp_data_path):
        # Search for specific file type
        power_files = [file for file in filenames if 'power_activityScores' in file]

        # Iterate through all those files
        for file in power_files:  
            # Extract subject id
            sub = sub_id.extract(file)
            if sub:
                # Ingest data file into directory
                power[sub] = pd.read_csv(os.path.join(dirpath, file))
                # Add column 'subject_id' to the data file
                power[sub]['subject_id'] = sub

        # Search for specific file type
        accel_files = [file for file in filenames if 'accel_activityScores' in file]

        # Iterate through all those files
        for file in accel_files:  
            # Extract subject id
            sub = sub_id.extract(file)
            if sub:
                # Ingest data file into directory
                accel[sub] = pd.read_csv(os.path.join(dirpath, file))
                # Add column 'subject_id' to the data file
                accel[sub]['subject_id'] = sub

        # Search for specific file type
        gps_files = [file for file in filenames if 'gps_dist' in file]

        # Iterate through all those files
        for file in gps_files:  
            # Extract subject id
            sub = sub_id.extract(file)
            if sub:
                # Ingest data file into directory
                gps[sub] = pd.read_csv(os.path.join(dirpath, file))
                # Add column 'subject_id' to the data file
                gps[sub]['subject_id'] = sub

logging.info(f'Found power files for: {power.keys()}')
logging.info(f'Found accel files for: {power.keys()}')
logging.info(f'Found gps files for: {power.keys()}')


# Convert the nested dict into a dataframe of all the subjects concatenated
try:
    power_df = pd.concat([sub for sub in power.values()], axis=0, ignore_index=True)
    # power_df = power_df.set_index(['subject_id'])
except Exception as e:
    logging.error(e)
    raise e
try:
    accel_df = pd.concat([sub for sub in accel.values()], axis=0, ignore_index=True)
    # accel_df = accel_df.set_index(['subject_id'])
except Exception as e:
    logging.error(e)
    raise e
try:
    gps_df = pd.concat([sub for sub in gps.values()], axis=0, ignore_index=True)
    # gps_df = gps_df.set_index(['subject_id'])
except Exception as e:
    logging.error(e)
    raise e


# Extract the relevant columns 
selected_cols = [col for col in power_df.columns if isinstance(col, str) and 'activityScore' in col]
legend_path = paths.get_path('key_to_readable_name.xlsx', project_dir, isdir=False)
if legend_path:
    legend = pd.read_excel(legend_path)
    legend = legend.set_index('key')
    readable_cols = [legend.loc[key, 'readable_name'] for key in selected_cols]
else:
    print("Could not find file key_to_readable_name.xlsx, using input column names.")
    readable_cols = selected_cols

power_df['average'] = power_df[selected_cols].mean(axis=1)
accel_df['average'] = accel_df[selected_cols].mean(axis=1)
gps_df['average'] = gps_df[selected_cols].mean(axis=1)
accel_df.to_csv(os.path.join(mindlamp_data_path, 'aggregated_dfs', 'accel_activityScores_hourly.csv'))
power_df.to_csv(os.path.join(mindlamp_data_path, 'aggregated_dfs', 'power_activityScores_hourly.csv'))
gps_df.to_csv(os.path.join(mindlamp_data_path, 'aggregated_dfs', 'gps_activityScores_hourly.csv'))

# App layout
layout = html.Div([
    html.H1('Data by Subject'),
    dcc.Dropdown(id="subject_id", value='PCT927', clearable=False,
        options=[{"label": f'{y}', "value": y} for y in power_df['subject_id'].unique()]),
    dcc.RadioItems(id='days', value='percentHome', 
        options=['All days','Weekdays','Weekends']),

    dcc.Graph(figure={}, id='phone_use-graph'),
    dcc.Graph(figure={}, id='activity-graph'),
    dcc.Graph(figure={}, id='gps-graph')

])

# Add controls to build the interaction
@callback(
    Output(component_id='phone_use-graph', component_property='figure'),
    Input(component_id='subject_id', component_property='value'),
    Input(component_id='days', component_property='value')
)


def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    sub = subject_id
    sub_df = power_df.query("subject_id == @sub")
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df[selected_cols].values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
    
    fig = px.imshow(xr_power, origin='lower', title=f'Phone Activity (minutes each hour) for sub-{sub}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig

# Add controls to build the interaction
@callback(
    Output(component_id='activity-graph', component_property='figure'),
    Input(component_id='subject_id', component_property='value'),
    Input(component_id='days', component_property='value')
)

def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    sub = subject_id
    sub_df = accel_df.query("subject_id == @sub")
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df[selected_cols].values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
    
    fig = px.imshow(xr_power, origin='lower', title=f'Physical Activity (acceleration speed) minutes each hour for sub-{sub}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig



@callback(
    Output(component_id='gps-graph', component_property='figure'),
    Input(component_id='subject_id', component_property='value'),
    Input(component_id='days', component_property='value')
)


def cb(subject_id, days):
    """Callback to update the figure based on the selected id"""
    sub = subject_id
    sub_df = gps_df.query("subject_id == @sub")
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df[selected_cols].values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": readable_cols})
    
    fig = px.imshow(xr_power, origin='lower', title=f'Mobility (distance each hour) for sub-{sub}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig

"""Callback to update the figure based on the selected id"""
sub = 'sub-PCX-PCT927'
sub_df = accel_df.query("subject_id == @sub")
logging.info(sub_df.head())
