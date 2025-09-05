import os
import glob
import pandas as pd
import sys
import logging
import importlib
import scripts.paths as paths
import scripts.sub_id as sub_id
if 'scripts.paths' in sys.modules:
    importlib.reload(sys.modules['scripts.paths'])


def update_dfs(base_dir):
    """
    Update dataframes by loading activityScore data from structured filepaths:
    /data/mindlamp/sub-<XXX>/<sensor>/<sensor>_activityScore_hourly.csv
    
    Parameters:
    base_dir (str): Base directory where data is stored
    
    Returns:
    tuple: (subjects_df, mindlamp_df, selected_cols, readable_cols)
    """
    # Define path to mindlamp data
    mindlamp_path = os.path.join(base_dir, "data", "mindlamp")
    
    # Define sensors
    sensors = ['gps','power', 'accel']
    sensor_types = ['dist','freq','freq2','homeStay', 'activityScores','use', 'availability24h']
    temps = ['hourly','daily']
    
    all_data = []
    subjects = []
    
    # Check if the mindlamp directory exists
    if not os.path.exists(mindlamp_path):
        logging.warning(f"Directory not found: {mindlamp_path}. Creating a demo dataframe.")
        # If directory doesn't exist, try to load example data

    # Find all subject directories
    subject_dirs = glob.glob(os.path.join(mindlamp_path, "sub-*"))
    
    for subject_dir in subject_dirs:
        subject_id = os.path.basename(subject_dir)
        subjects.append(subject_id)
        
    # Find all subject directories
    subject_dirs = glob.glob(os.path.join(base_dir,  "data", "mindlamp", "sub-*"))
    
    for subject_dir in subject_dirs:
        subject_id = os.path.basename(subject_dir)
        
        for sensor in sensors:
            for type in sensor_types:
                for temp in temps:
                    sensor_dir = os.path.join(subject_dir, "processed", sensor)
                    if os.path.exists(sensor_dir):
                        id = subject_id.replace('sub-','')
                        sensor_file = paths.find_file(fr"{id}-phone_{sensor}_{type}_{temp}-day(\d+)to(\d+).csv", sensor_dir, regex=True)
                        if sensor_file is not None:
                            logging.info(f"Found file {sensor_file}")
                            file_path = os.path.join(sensor_dir, sensor_file)
                        
                            # If the file exists, read it
                            if os.path.exists(file_path):
                                try:
                                    df = pd.read_csv(file_path)
                                    df['subject_id'] = subject_id   # add sub ID to file as a column, for concatenating
                                    df['sensor'] = sensor  # add sensor to file as a column, for concatenating
                                    df['type'] = type   # add sensor type (dist, freq, activityScores)
                                    df['temp'] = temp   # add frequency col (daily, hourly)

                                except Exception as e:
                                    logging.error(f"Error reading {file_path}: {e}")
    
    # Create subjects dataframe
    subjects_df = pd.DataFrame({'subject_id': subjects})
    
    # Combine all sensor data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        # Extract column names for UI components
        selected_cols = [col for col in combined_df.columns if col not in ['subject_id', 'sensor']]
        readable_cols = {col: col.replace('_', ' ').title() for col in selected_cols}
        
        return combined_df, subjects_df, selected_cols, readable_cols
    else:
        logging.info("No data files found, using example data")
        example_df = pd.read_csv("data/gps_activityScores_test.csv")
        subjects_df = pd.DataFrame()
        selected_cols=[]
        readable_cols=[]
        return example_df, subjects_df, selected_cols, readable_cols
