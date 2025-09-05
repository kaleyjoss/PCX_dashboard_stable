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
# Import custom scripts
sys.path.append(os.path.basename(os.getcwd()))
import scripts.paths as paths
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])

def update_dfs(pcx_dir):
    # Set up logging
    logging.basicConfig(
        filename='update_dataframes.log',        # File to write logs to, saved in working directory
        filemode='a',              # 'a' for append, 'w' to overwrite each time
        level=logging.INFO,        # Minimum logging level
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

    subs_df=pd.read_excel(os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Subject_tracker_PCR.xlsx'), sheet_name='tracker')

    
    power = {}
    gps = {}
    accel = {}
    mindlamp_data_path = paths.get_path('mindlamp_data', pcx_dir, isdir=True)
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
        power_df['sensor'] = 'power'
    except Exception as e:
        logging.error(e)
        raise e
    try:
        accel_df = pd.concat([sub for sub in accel.values()], axis=0, ignore_index=True)
        # accel_df = accel_df.set_index(['subject_id'])
        accel_df['sensor'] = 'accel'
    except Exception as e:
        logging.error(e)
        raise e
    try:
        gps_df = pd.concat([sub for sub in gps.values()], axis=0, ignore_index=True)
        # gps_df = gps_df.set_index(['subject_id'])
        gps_df['sensor'] = 'gps'
    except Exception as e:
        logging.error(e)
        raise e

    

    # Extract the relevant columns 
    selected_cols = [col for col in power_df.columns if isinstance(col, str) and 'activityScore' in col]
    legend_path = paths.get_path('key_to_readable_name.xlsx', pcx_dir, isdir=False)
    if legend_path:
        legend = pd.read_excel(legend_path)
        legend = legend.set_index('key')
        readable_cols = [legend.loc[key, 'readable_name'] for key in selected_cols]
    else:
        print("Could not find file key_to_readable_name.xlsx, using input column names.")
        readable_cols = selected_cols

    # Average the daily hour scores
    power_df['daily_hr_average'] = power_df[selected_cols].mean(axis=1)
    accel_df['daily_hr_average'] = accel_df[selected_cols].mean(axis=1)
    gps_df['daily_hr_average'] = gps_df[selected_cols].mean(axis=1)

    # Sum the daily hour scores to get a daily number
    power_df['daily_mins'] = power_df[selected_cols].sum(axis=1)
    accel_df['daily_mins'] = accel_df[selected_cols].sum(axis=1)
    gps_df['daily_mins'] = gps_df[selected_cols].sum(axis=1)

    accel_path = os.path.join(mindlamp_data_path, 'aggregated_dfs', 'accel_activityScores_hourly.csv')
    accel_df.to_csv(accel_path)
    power_path = os.path.join(mindlamp_data_path, 'aggregated_dfs', 'power_activityScores_hourly.csv')
    power_df.to_csv(power_path)
    gps_path = os.path.join(mindlamp_data_path, 'aggregated_dfs', 'gps_activityScores_hourly.csv')
    gps_df.to_csv(gps_path)
    subs_path = os.path.join(mindlamp_data_path, 'aggregated_dfs', 'subs_df.csv')
    subs_df.to_csv(subs_path)

    mindlamp_df = pd.concat([accel_df, power_df, gps_df], ignore_index=True, join='outer')
    
    mindlamp_path = os.path.join(mindlamp_data_path, 'aggregated_dfs', 'mindlamp.csv')
    mindlamp_df.to_csv(mindlamp_path)
    
    return subs_df, mindlamp_df, selected_cols, readable_cols