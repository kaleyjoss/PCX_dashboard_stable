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
import scripts.paths 
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])
if 'scripts.sub_id' in sys.modules:
    importlib.reload(sys.modules['scripts.sub_id'])
from scripts.paths import load_paths
paths = load_paths()
mindlamp_dir = paths['mindlamp_dir']

def return_recent_df(sub: str, sensor: str):
    mindlamp_data_path = os.path.join(mindlamp_dir, 'data', sub, 'processed','phone', sensor)
    if not os.path.exists(mindlamp_data_path):
        return None
    
    all_files = os.listdir(mindlamp_data_path)
    matches = sorted(re.findall(r'to\d+\.', all_files), reverse=True)
    if not matches:
        return None
    most_recent_file = matches[0]
    return most_recent_file
    
    

def update_dfs(sub:str, sensor:str):
    # Set up logging
    logging.basicConfig(
        filename='update_dataframes.log',        # File to write logs to, saved in working directory
        filemode='a',              # 'a' for append, 'w' to overwrite each time
        level=logging.INFO,        # Minimum logging level
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

    data_path = os.path.join(mindlamp_dir, 'data', sub, 'phone', 'processed', sensor)
    if os.path.exists(data_path):
        most_recent_file = return_recent_df(sub, sensor)
        if most_recent_file is not None:
            df = pd.read_csv(os.path.join(data_path, most_recent_file))
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

