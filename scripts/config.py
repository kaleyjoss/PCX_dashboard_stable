from datetime import datetime as dt
import os
import sys
import logging
import pandas as pd


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Import custom scripts
repo_dir = os.path.basename(os.getcwd())
sys.path.append(repo_dir)
from scripts.utils import extract_survey_date, get_most_recent_survey
from scripts.update_dataframes import update_dfs

data_dir = os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR/PCX')

# project where survey exports live
surveys_dir = os.path.join(data_dir, 'behavioral')

# folder where your fmriprep reports live
REPORTS_DIR = os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR/PCX/fmriprep_reports')
tracker_df=pd.read_excel(os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Subject_tracker_PCR.xlsx'), sheet_name='tracker')


survey_names = ['clinical_administered_data','clinical_self_report_data',
                     'mri_self_report_data','supplemental_self_report_data']
subsurvey_key = {
    'panss': 'clinical_administered_data',
    'madrs': 'clinical_administered_data',
    'ymrs': 'clinical_administered_data',
    'bprs': 'clinical_administered_data',
    'cssrs': 'clinical_administered_data',

}

surveys={}
recoded_surveys={}
filepath=None
for root, dirs, files in os.walk(surveys_dir):
    for survey in survey_names: 
        if survey in dirs: 
            surveys[survey] = []
            survey_dir = os.path.join(root, survey)
            try:
                filepath = get_most_recent_survey(survey_dir)
                filepath_recoded = get_most_recent_survey(survey_dir, recoded=True)
            except Exception as e:
                logging.error(f'For survey_dir {survey_dir}, {e}')
            if filepath is not None:
                logging.info(f'most recent survey for {survey}: {os.path.basename(filepath)}')
                surveys[survey] = pd.read_csv(filepath)
                recoded_surveys[survey]=pd.read_csv(filepath_recoded)

first_df = surveys['clinical_administered_data']
subject_ids_all = first_df['SUBJECT_ID'].unique()
subject_ids = [sub for sub in subject_ids_all if 'qual' in sub and '{' not in sub and 'Subject ID' not in sub]


# Set PCX Project Data path
pcx_dir = os.path.expanduser("~/Library/CloudStorage/Box-Box/(Restricted)_PCR/PCX")

# Update DFs
subs_df, mindlamp_df, selected_cols, readable_cols = update_dfs(pcx_dir)
power_df = mindlamp_df[mindlamp_df['sensor']=='power']
accel_df = mindlamp_df[mindlamp_df['sensor']=='accel']
gps_df = mindlamp_df[mindlamp_df['sensor']=='gps']
