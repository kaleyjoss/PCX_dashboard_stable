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
import os
import sys


# Import custom scripts
dashboard_dir = os.path.basename(os.getcwd())
sys.path.append(dashboard_dir)
from scripts.update_dataframes import update_dfs
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])
from scripts.update_dataframes import update_dfs
from scripts.paths import load_paths
from scripts.surveys import load_surveys

# Register page into dash app as pagename
# dash.register_page(__name__, path="/passive_data", title='Passive Data', name='Passive Data')
paths_dict = load_paths()
pcx_dir = paths_dict["pcx_dir"]
surveys_dir = paths_dict['surveys_dir']
mindlamp_dir = paths_dict['mindlamp_dir']
surveys, recoded_surveys = load_surveys(surveys_dir)

first_df = surveys['clinical_administered_data']
subject_ids = first_df['SUBJECT_ID'].unique()

logging.basicConfig(
        filename='update_dataframes.log',        # File to write logs to, saved in working directory
        filemode='a',              # 'a' for append, 'w' to overwrite each time
        level=logging.INFO,        # Minimum logging level
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

def return_recent_df(sub: str, sensor: str, data_path:str):    
    all_files = os.listdir(data_path)
    matches = []
    most_recent_files = []
    for f in all_files:
        matches.extend(re.findall(r'to\d+\.', f))
    if not matches:
        return None, None
    matches = sorted(matches, reverse=True)
    day = matches[0].replace('d','').replace('.','')
    for file in all_files:
        if day in file:
            most_recent_files.extend(file)
        
    return most_recent_files, day
    

def update_dfs(sub:str, sensor:str):
    # Set up logging

    data_path = os.path.join(mindlamp_dir, 'data', sub, 'phone', 'processed', sensor)
    if os.path.exists(data_path):
        most_recent_files, day = return_recent_df(sub, sensor, data_path)
        if most_recent_files is not None:
            for file in most_recent_files:
                df = pd.read_csv(os.path.join(data_path, most_recent_files))
                df['subject_id'] = sub
                df['sensor'] = sensor

            # Build mapping for renaming to readable names
            rename_map = {
                f"activityScore_hour{str(i).zfill(2)}": f"{i-1}:00"
                for i in range(1, 25)
            }

            # Apply rename
            df = df.rename(columns=rename_map)

            return df
        else:
            logging.warning(f"No recent {sensor} data found for {sub}")
            return None
    else:
        logging.warning(f"No {sensor} data found for {sub}")
        return None





# App layout
layout = html.Div([
    dcc.RadioItems(id='sensor', value='power',
        options=['power','accel','gps']),
    dcc.RadioItems(id='days', value='All days',
        options=['All days','Weekdays','Weekends']),
    dcc.Graph(figure={}, id='sensor-graph'),

])

# Add controls to build the interaction
@callback(
    Output(component_id='sensor-graph', component_property='figure'),
    Input(component_id='subject-id', component_property='data'),
    Input(component_id='days', component_property='value'),
    Input(component_id='sensor', component_property='value'),
)

def cb(subject_id, days, sensor):
    if not subject_id:
        return None
    
    sub_clean = subject_id.lower().replace('_','').replace('qualr','PCR').replace('qualm','PCM')

    sub_df = update_dfs(sub_clean, sensor)

    """Callback to update the figure based on the selected id"""
    if subject_id is None:
        return None
    if sub_df is None:
        data_path = os.path.join(mindlamp_dir, 'data', subject_id, 'phone', 'processed', sensor)
        return None, f'No data found for {subject_id} in {data_path}'
    if days == 'Weekdays':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('1|2|3|4|5')]
    elif days == 'Weekends':
        sub_df = sub_df[sub_df['weekday'].astype(str).str.contains('6|7')]
    xr_power = xr.DataArray(sub_df.select_dtypes(include=['number']).values, 
                        dims=["Days", "Hours of the Day"],
                        coords={"Days": sub_df['day'], "Hours of the Day": sub_df.select_dtypes(include=['number']).columns})
    
    fig = px.imshow(xr_power, origin='lower', title=f'{sensor} Activity (minutes each hour) for {sub_clean}',
                    zmin=0,zmax=60,height=400, width=600)
    return fig

